"""Paced, redacted HTTP acceptance and an injected readiness-first transaction.

No production command or credential discovery is performed by this module.
The caller supplies scoped installation/switch/rollback actions and owner proof.
"""
from datetime import datetime, timezone
import base64
import errno
import hashlib
import http.client
import json
from pathlib import Path
import re
import runpy
import secrets
import socket
import ssl
import subprocess
import time
from urllib.parse import urlsplit

_receipts = runpy.run_path(str(Path(__file__).with_name('friends_http_acceptance.py')))
PATHS, ProbeFailed, classify = (_receipts[name] for name in ('PATHS', 'ProbeFailed', 'classify'))
Evidence = _receipts['Evidence']

PORT_OWNERS = {18080: 'documented_xhttp_origin', 18082: 'product_api',
               18084: 'ordinary_friends_http', 18085: 'friends_tcp_xray_api',
               18444: 'restricted_bootstrap_broker'}
CANDIDATE_PORTS = frozenset({18086})
ROUTES = {label: dict(method=method, path=path, expected=expected,
                     owner='nginx_static' if label == 'status' else 'friends_application')
          for label, (method, path, expected) in PATHS.items()}
ROUTES['restricted_readiness'] = dict(method='POST', path='/friends/restricted-readiness',
                                    expected=200, owner='friends_application')
DIRECT_PROBES = tuple(label for label in ROUTES if ROUTES[label]['owner'] == 'friends_application')
EXTERNAL_PROBES = tuple(ROUTES)


def listeners(port):
    result = subprocess.run(['ss', '-ltnpH', 'sport = :' + str(port)],
                            capture_output=True, text=True, check=True, timeout=3)
    records = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) < 5 or fields[0] != 'LISTEN':
            raise ProbeFailed('Unparseable listener metadata')
        address, number = fields[3].rsplit(':', 1)
        if int(number) != port:
            raise ProbeFailed('Unexpected listener port')
        records.append(dict(address=address, pids=set(map(int, re.findall(r'pid=([0-9]+)', line)))))
    return records


def process_start(pid):
    return (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[19]


class Candidate:
    """Explicit local policy, not a port allocator or a service manager."""
    def __init__(self, port, generation, artifact, sha256):
        if type(port) is not int or port not in CANDIDATE_PORTS or port in PORT_OWNERS:
            raise ValueError('Candidate port is not authorized')
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', generation):
            raise ValueError('Invalid candidate generation')
        if not re.fullmatch(r'[a-f0-9]{64}', sha256):
            raise ValueError('Invalid artifact pin')
        self.port, self.generation = port, generation
        self.artifact, self.sha256 = Path(artifact).resolve(), sha256
        self.process = self.start = None
        self.free = self.direct_pass = self.external_pass = False

    def pinned(self):
        if hashlib.sha256(self.artifact.read_bytes()).hexdigest() != self.sha256:
            raise ProbeFailed('Candidate artifact mismatch')

    def preflight(self, evidence, previous=None):
        self.free = False
        classification = 'inspection_failed'
        try:
            self.pinned()
            occupied = listeners(self.port)
            if occupied:
                classification = 'occupied_other_or_unknown'
                if previous is not None:
                    pid, start = previous
                    if all(row['pids'] == {pid} for row in occupied) and process_start(pid) == start:
                        classification = 'occupied_previous_candidate'
                raise ProbeFailed('Candidate port occupied; never replace its owner')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
                reservation.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                reservation.bind(('127.0.0.1', self.port))
            classification = 'free_at_preflight'
            self.free = True
        except OSError:
            classification = 'bind_unavailable'
            raise ProbeFailed('Candidate port cannot be bound') from None
        finally:
            evidence.persist(dict(timestamp=timestamp(), event='candidate_port_preflight',
                                  candidate_port=self.port, active_generation=self.generation,
                                  artifact_sha256=self.sha256, classification=classification,
                                  passed=self.free))

    def render_unit(self, template):
        if not self.free or template.count('@CANDIDATE_PORT@') != 1:
            raise ProbeFailed('Verified port and exact unit template required')
        return template.replace('@CANDIDATE_PORT@', str(self.port))

    def capture(self, process):
        self.process = process
        if process.poll() is not None:
            raise ProbeFailed('Candidate startup failed; ingress must remain untouched')
        self.start = process_start(process.pid)
        self.verify()

    def verify(self):
        self.pinned()
        if self.process is None or self.process.poll() is not None or process_start(self.process.pid) != self.start:
            raise ProbeFailed('Candidate process generation changed')
        arguments = (Path('/proc') / str(self.process.pid) / 'cmdline').read_bytes().split(b'\0')
        arguments = [value.decode() for value in arguments if value]
        if (len(arguments) < 5 or arguments[1:3] != ['-I', str(self.artifact)]
                or arguments.count('--port') != 1
                or arguments[arguments.index('--port') + 1] != str(self.port)):
            raise ProbeFailed('Candidate command does not match pinned generation')
        bound = listeners(self.port)
        if not bound or any(row['address'] != '127.0.0.1' or row['pids'] != {self.process.pid} for row in bound):
            raise ProbeFailed('Candidate listener must be exclusively owned IPv4 loopback')

    def upstream(self):
        self.verify()
        if not self.direct_pass:
            raise ProbeFailed('Direct matrix must pass before rendering ingress')
        return 'http://127.0.0.1:' + str(self.port)

    def render_upstreams(self, template):
        if template.count('@FRIENDS_HTTP_UPSTREAM@') != 2:
            raise ProbeFailed('Expected ordinary and restricted upstream placeholders')
        return template.replace('@FRIENDS_HTTP_UPSTREAM@', self.upstream())


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
                 layer='ingress_external', candidate=None,
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
        if layer not in ('direct_candidate', 'ingress_external'):
            raise ValueError('Invalid acceptance layer')
        if layer == 'direct_candidate' and (candidate is None or origin != 'http://127.0.0.1:' + str(candidate.port)):
            raise ValueError('Direct probes require the verified loopback candidate')
        if candidate is not None and generation != candidate.generation:
            raise ValueError('Candidate generation mismatch')
        self.layer, self.candidate = layer, candidate
        self.evidence, self.generation, self.interval = evidence, generation, interval
        self.clock, self.sleep, self.context = clock, sleep, context
        self.last = None

    def probe(self, label, body=None, *, expected=None, validate=None):
        if label not in ROUTES:
            raise ValueError('Unknown probe')
        route = ROUTES[label]
        method, path, default = (route[key] for key in ('method', 'path', 'expected'))
        if self.layer == 'direct_candidate' and label not in DIRECT_PROBES:
            raise ValueError('Ingress-owned route is not a candidate readiness probe')
        if self.last is not None:
            self.sleep(max(0, self.interval - (self.clock() - self.last)))
        self.last = self.clock()
        probe_id = secrets.token_hex(16)
        record = dict(timestamp=timestamp(), probe_id=probe_id, label=label,
                      layer=self.layer, route_owner=route['owner'],
                      candidate_port=self.candidate.port if self.candidate else None,
                      expected=default if expected is None else expected, status=None,
                      transport_error=None, response_class=None, valid=False,
                      **response_metadata({}, probe_id))
        connection, value = None, None
        try:
            if self.candidate is not None:
                self.candidate.verify()
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
            if self.layer == 'direct_candidate':
                self.candidate.verify()
                record.update(active_generation=self.candidate.generation,
                              response_origin='direct_application', upstream_error='none',
                              rate_limit_class='not_applicable', ingress_upstream_status=None,
                              upstream_connect_seconds=None, upstream_header_seconds=None,
                              rate_limit_rule_id=None)
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
            if self.layer == 'ingress_external' and self.candidate is not None:
                owner = 'ingress' if route['owner'] == 'nginx_static' else 'upstream'
                record['valid'] = record['valid'] and record['response_origin'] == owner
                if owner == 'upstream':
                    record['valid'] = record['valid'] and record['ingress_upstream_status'] == str(record['status'])
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
        if self.layer == 'direct_candidate':
            self.candidate.direct_pass = False
        elif self.candidate is not None:
            self.candidate.external_pass = False
        for label in ('status', 'ordinary_challenge', 'ordinary_chat', 'restricted_malformed'):
            if self.layer == 'direct_candidate' and label not in DIRECT_PROBES:
                continue
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
        if self.layer == 'direct_candidate':
            self.candidate.verify()
            self.candidate.direct_pass = True
        elif self.candidate is not None:
            self.candidate.external_pass = True


def _transaction(evidence, *, prepare, ready, switch, accept, commit,
                 restore, restored, drain, stop_candidate, candidate_port=None):
    """Keep the old listener alive; rollback routing before draining the candidate.

    All callbacks must be bounded. switch/restore must atomically replace and
    validate/reload only the scoped ingress configuration. restored must confirm
    the old generation; drain must confirm old nginx workers no longer reference
    the candidate. If either cannot be proven, retain candidate for safe recovery.
    """
    switched = False
    def receipt(event, **values):
        evidence.persist(dict(timestamp=timestamp(), event=event, candidate_port=candidate_port, **values))
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


def transaction(evidence, *, candidate, old_healthy, prepare, ready, render, switch,
                accept, commit, restore, restored, drain, stop_candidate,
                old_drained, retire_old):
    def receipt(event, **values):
        evidence.persist(dict(timestamp=timestamp(), event=event, candidate_port=candidate.port,
                              active_generation=candidate.generation, **values))
    if old_healthy() is not True:
        receipt('old_generation_unhealthy')
        raise ProbeFailed('Old generation must be healthy before preparation')
    candidate.preflight(evidence)
    def start():
        candidate.capture(prepare())
        receipt('candidate_process_verified', pid=candidate.process.pid,
                process_start=candidate.start, artifact_sha256=candidate.sha256)
    def direct():
        if ready() is not True or not candidate.direct_pass:
            return False
        upstream = candidate.upstream()
        if render(upstream) is not True:
            raise ProbeFailed('Candidate ingress render/validation failed')
        candidate.verify()
        receipt('candidate_ingress_validated')
        return True
    def activate():
        candidate.verify()
        switch()
    def external():
        candidate.external_pass = False
        return accept() is True and candidate.external_pass
    def stop():
        if candidate.process is not None and candidate.process.poll() is None:
            if candidate.start is None or process_start(candidate.process.pid) != candidate.start:
                receipt('candidate_retained_identity_uncertain')
                raise ProbeFailed('Never stop an unverified process')
            stop_candidate(candidate.process)
    _transaction(evidence, prepare=start, ready=direct, switch=activate, accept=external,
                 commit=commit, restore=restore, restored=restored, drain=drain,
                 stop_candidate=stop, candidate_port=candidate.port)
    if old_drained() is not True:
        receipt('committed_old_retained_drain_unconfirmed')
        raise ProbeFailed('Committed candidate; retain old generation until drained')
    retire_old()
    receipt('old_generation_retirement_complete')
    return True
