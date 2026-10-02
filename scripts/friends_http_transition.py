"""Paced, redacted HTTP acceptance and an injected readiness-first transaction.

No production command or credential discovery is performed by this module.
The caller supplies scoped installation/switch/rollback actions and owner proof.
"""
from datetime import datetime, timezone
import base64
import errno
import http.client
import json
from pathlib import Path
import re
import runpy
import secrets
import socket
import ssl
import time
from urllib.parse import urlsplit

_receipts = runpy.run_path(str(Path(__file__).with_name('friends_http_acceptance.py')))
PATHS, ProbeFailed, classify = (_receipts[name] for name in ('PATHS', 'ProbeFailed', 'classify'))
Evidence = _receipts['Evidence']


def timestamp():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def response_metadata(headers, probe_id):
    correlated = headers.get('X-FC-Probe-ID') == probe_id and headers.get('X-FC-Ingress') == 'nginx'
    result = dict(response_origin='unknown', ingress_upstream_status=None,
                  upstream_connect_seconds=None, upstream_header_seconds=None, upstream_error='unknown',
                  active_generation=None, rate_limit_class='unknown', rate_limit_rule_id=None)
    if not correlated:
        return result
    generation = headers.get('X-FC-Generation', '')
    if re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', generation):
        result['active_generation'] = generation
    upstream = headers.get('X-FC-Upstream-Status', '') or '-'
    if re.fullmatch(r'(?:-|[1-5][0-9]{2})', upstream):
        result['ingress_upstream_status'] = upstream
    connect = headers.get('X-FC-Upstream-Connect', '')
    if re.fullmatch(r'[0-9]{1,5}\.[0-9]{3}', connect):
        result['upstream_connect_seconds'] = float(connect)
    header_time = headers.get('X-FC-Upstream-Header', '')
    if re.fullmatch(r'[0-9]{1,5}\.[0-9]{3}', header_time):
        result['upstream_header_seconds'] = float(header_time)
    request_limit = headers.get('X-FC-Request-Limit', '')
    connection_limit = headers.get('X-FC-Connection-Limit', '')
    if request_limit == 'REJECTED':
        result.update(response_origin='ingress', rate_limit_class='request_rejected',
                      rate_limit_rule_id='request_policy:per_ip_or_global_rate')
    elif connection_limit == 'REJECTED':
        result.update(response_origin='ingress', rate_limit_class='connection_rejected',
                      rate_limit_rule_id='connection_policy:connections_or_global_connections')
    else:
        result['rate_limit_class'] = 'not_rejected' if request_limit in ('PASSED', 'DELAYED', '') else 'unknown'
        if upstream == '-':
            result['response_origin'] = 'ingress'
        elif upstream in ('502', '504'):
            result.update(response_origin='ingress_or_upstream', upstream_error='proxy_failure_unresolved')
            if result['upstream_header_seconds'] is not None:
                result.update(response_origin='upstream', upstream_error='upstream_http_error')
            elif header_time == '-':
                result.update(response_origin='ingress', upstream_error='upstream_response_incomplete')
                if connect == '-' and upstream == '502':
                    result['upstream_error'] = 'upstream_connect_not_established'
        elif result['ingress_upstream_status']:
            result['response_origin'] = 'upstream'
    return result


class Session:
    """One serialized external probe stream; no concurrent independent observer.

    One request/second is below the deployed shared per-IP two requests/second.
    Existing user traffic can still consume that budget; any 429 remains FAIL.
    """
    def __init__(self, origin, evidence, *, generation=None, interval=1.0,
                 clock=time.monotonic, sleep=time.sleep, context=None):
        self.endpoint = urlsplit(origin)
        if (self.endpoint.username or self.endpoint.password or self.endpoint.path not in ('', '/')
                or self.endpoint.query or self.endpoint.fragment):
            raise ValueError('Invalid origin')
        if self.endpoint.scheme != 'https' and not (
                self.endpoint.scheme == 'http' and self.endpoint.hostname in ('127.0.0.1', '::1', 'localhost')):
            raise ValueError('HTTPS required outside loopback')
        if interval < 1.0:
            raise ValueError('External acceptance interval must be at least one second')
        self.evidence, self.generation, self.interval = evidence, generation, interval
        self.clock, self.sleep, self.context = clock, sleep, context
        self.last = None

    def probe(self, label, body=None, *, expected=None, validate=None):
        method, path, default = PATHS.get(label, ('POST', '/friends/restricted-readiness', 200))
        if label not in PATHS and label != 'restricted_readiness':
            raise ValueError('Unknown probe')
        if self.last is not None:
            self.sleep(max(0, self.interval - (self.clock() - self.last)))
        self.last = self.clock()
        probe_id = secrets.token_hex(16)
        record = dict(timestamp=timestamp(), probe_id=probe_id, label=label,
                      expected=default if expected is None else expected, status=None,
                      transport_error=None, response_class=None, valid=False,
                      **response_metadata({}, probe_id))
        connection, value = None, None
        try:
            connection_type = http.client.HTTPSConnection if self.endpoint.scheme == 'https' else http.client.HTTPConnection
            options = dict(timeout=3)
            if self.endpoint.scheme == 'https' and self.context is not None:
                options['context'] = self.context
            connection = connection_type(self.endpoint.hostname, self.endpoint.port, **options)
            payload = None if method == 'GET' else json.dumps({} if body is None else body).encode()
            if payload is not None and len(payload) > 8192:
                raise ValueError('Oversized request')
            connection.request(method, path, payload, {'Content-Type': 'application/json', 'X-FC-Probe-ID': probe_id})
            response = connection.getresponse()
            record['status'] = response.status
            record.update(response_metadata(response.headers, probe_id))
            raw = response.read(65537)
            record['response_class'] = classify(raw, response.getheader('Content-Type', ''))
            if len(raw) <= 65536:
                try:
                    value = json.loads(raw)
                except (ValueError, UnicodeError, RecursionError):
                    pass
            record['valid'] = (record['status'] == record['expected']
                               and record['response_class'] not in ('oversized', 'invalid-json')
                               and (self.generation is None or record['active_generation'] == self.generation))
            if record['valid'] and validate is not None:
                record['valid'] = validate(value) is True
        except ssl.SSLError:
            record['transport_error'] = 'tls'
        except (socket.timeout, TimeoutError):
            record['transport_error'] = 'timeout'
        except OSError as error:
            record['transport_error'] = 'connection_refused' if error.errno == errno.ECONNREFUSED else 'connection'
        except http.client.HTTPException:
            record['transport_error'] = 'http_protocol'
        except BaseException:
            record['valid'] = False
            record['transport_error'] = 'validation_or_interruption'
            raise
        finally:
            record['elapsed_ms'] = round((self.clock() - self.last) * 1000, 3)
            record['valid'] = record['valid'] and record['transport_error'] is None
            try:
                self.evidence.persist(record)
            finally:
                if connection is not None:
                    connection.close()
        if not record['valid']:
            raise ProbeFailed('Persisted transition probe failure: ' + label)
        return value

    def matrix(self, identities, prove, validate_readiness):
        if not callable(prove) or not callable(validate_readiness) or not identities['non_canary']:
            raise ValueError('Real proof, readiness validator and non-canary required')
        for label in ('status', 'ordinary_challenge', 'ordinary_chat', 'restricted_malformed'):
            self.probe(label)
        for identity in identities['non_canary']:
            self.probe('restricted_non_canary', identity)
        def valid_challenge(value):
            try:
                return (type(value) is dict and set(value) == {'challenge','expires_at','audience'}
                        and value['audience'] == 'family-connect/enrollment/v1'
                        and type(value['expires_at']) is int and time.time() < value['expires_at'] <= time.time()+120
                        and len(base64.b64decode(value['challenge'], validate=True)) == 32)
            except (ValueError, TypeError):
                return False
        challenge = self.probe('restricted_canary', identities['canary'], validate=valid_challenge)
        proof = prove(challenge)
        self.probe('restricted_readiness', proof, validate=validate_readiness)


def transaction(evidence, *, prepare, ready, switch, accept, commit,
                restore, restored, drain, stop_candidate):
    """Keep the old listener alive; rollback routing before draining the candidate.

    All callbacks must be bounded. switch/restore must atomically replace and
    validate/reload only the scoped ingress configuration. restored must confirm
    the old generation; drain must confirm old nginx workers no longer reference
    the candidate. If either cannot be proven, retain candidate for safe recovery.
    """
    switched = False
    def receipt(event, **values):
        evidence.persist(dict(timestamp=timestamp(), event=event, **values))
    try:
        receipt('prepare_intent')
        prepare()
        if ready() is not True:
            raise ProbeFailed('Candidate not ready')
        receipt('candidate_ready')
        receipt('switch_intent')
        switched = True
        switch()
        receipt('switched')
        if accept() is not True:
            raise ProbeFailed('External acceptance incomplete')
        receipt('accepted')
        commit()
        receipt('committed')
        return True
    except BaseException as error:
        persistence_failed = False
        try:
            receipt('failure', failure_class=type(error).__name__ if isinstance(error, Exception) else 'interrupted')
        except OSError:
            persistence_failed = True
        if switched:
            restore()
            if restored() is not True or drain() is not True:
                receipt('rollback_incomplete', candidate_retained=True)
                raise ProbeFailed('Keep candidate alive; routing/drain unconfirmed') from None
            try:
                receipt('routing_restored_and_drained')
            except OSError:
                persistence_failed = True
        stop_candidate()
        receipt('candidate_stopped')
        if persistence_failed:
            raise ProbeFailed('Evidence storage failed; transaction not accepted') from None
        raise
