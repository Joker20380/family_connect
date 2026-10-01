"""Bounded HTTP probes with durable, redacted receipts; never deploy or roll back."""
import argparse
import base64
from datetime import datetime, timezone
import http.client
import json
import os
from pathlib import Path
import re
import secrets
import signal
import socket
import ssl
import time
from urllib.parse import urlsplit


PATHS = {
    'status': ('GET', '/status/server-load.json', 200),
    'ordinary_challenge': ('POST', '/friends/challenge', 400),
    'ordinary_chat': ('POST', '/friends/chat/challenge', 400),
    'restricted_malformed': ('POST', '/friends/restricted-readiness/challenge', 400),
    'restricted_non_canary': ('POST', '/friends/restricted-readiness/challenge', 403),
    'restricted_canary': ('POST', '/friends/restricted-readiness/challenge', 200),
}


class ProbeFailed(RuntimeError):
    pass


class Evidence:
    def __init__(self, directory, generation):
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', generation):
            raise ValueError('Invalid configuration generation')
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.descriptor = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        info = os.fstat(self.descriptor)
        if info.st_uid != os.geteuid() or info.st_mode & 0o077:
            os.close(self.descriptor)
            raise ValueError('Evidence directory must be owner-only')
        self.generation = generation

    def close(self):
        os.close(self.descriptor)

    def persist(self, record):
        record = dict(record, generation=self.generation)
        name = str(time.time_ns()) + '-' + secrets.token_hex(8)
        pending = name + '.pending'
        descriptor = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=self.descriptor)
        with os.fdopen(descriptor, 'w') as output:
            json.dump(record, output, separators=(',', ':'))
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.rename(pending, name + '.json', src_dir_fd=self.descriptor, dst_dir_fd=self.descriptor)
        os.fsync(self.descriptor)


def classify(raw, content_type):
    if len(raw) > 65536:
        return 'oversized'
    if not raw:
        return 'empty'
    if content_type.split(';')[0].lower() == 'application/json':
        try:
            value = json.loads(raw)
        except (ValueError, UnicodeError, RecursionError):
            return 'invalid-json'
        return 'json-object' if type(value) is dict else 'json-other'
    return 'html' if content_type.split(';')[0].lower() == 'text/html' else 'other'


def probe(origin, label, evidence, body=None, timeout=3):
    endpoint = urlsplit(origin)
    if endpoint.username or endpoint.password or endpoint.path not in ('', '/') or endpoint.query or endpoint.fragment:
        raise ValueError('Invalid probe origin')
    if endpoint.scheme != 'https' and not (endpoint.scheme == 'http' and endpoint.hostname in ('127.0.0.1', 'localhost', '::1')):
        raise ValueError('HTTPS required outside loopback')
    method, path, expected = PATHS[label]
    record = dict(timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                  label=label, path=path, method=method, expected=expected,
                  status=None, transport_error=None, response_class=None)
    started = time.monotonic()
    connection = None
    try:
        connection_type = http.client.HTTPSConnection if endpoint.scheme == 'https' else http.client.HTTPConnection
        connection = connection_type(endpoint.hostname, endpoint.port, timeout=timeout)
        payload = None if method == 'GET' else json.dumps({} if body is None else body).encode()
        if payload is not None and len(payload) > 8192:
            raise ValueError('Oversized probe request')
        connection.request(method, path, body=payload, headers={} if payload is None else {'Content-Type': 'application/json'})
        response = connection.getresponse()
        record['status'] = response.status
        raw = response.read(65537)
        record['response_class'] = classify(raw, response.getheader('Content-Type', ''))
        if label == 'restricted_canary' and response.status == 200:
            try:
                value = json.loads(raw)
                valid = (len(raw) <= 65536 and type(value) is dict
                         and set(value) == {'challenge', 'expires_at', 'audience'}
                         and value['audience'] == 'family-connect/enrollment/v1'
                         and type(value['expires_at']) is int and time.time() < value['expires_at'] <= time.time() + 120
                         and len(base64.b64decode(value['challenge'], validate=True)) == 32)
            except (ValueError, TypeError, UnicodeError, RecursionError):
                valid = False
            record['response_class'] = 'restricted-challenge' if valid else 'invalid-challenge'
    except ssl.SSLError:
        record['transport_error'] = 'tls'
    except (socket.timeout, TimeoutError):
        record['transport_error'] = 'timeout'
    except (OSError, http.client.HTTPException):
        record['transport_error'] = 'connection'
    except BaseException:
        record['transport_error'] = 'interrupted'
        raise
    finally:
        record['elapsed_ms'] = round((time.monotonic() - started) * 1000, 3)
        try:
            evidence.persist(record)
        finally:
            if connection is not None:
                connection.close()
    return record


def accepted(record):
    return (record['transport_error'] is None and record['status'] == record['expected']
            and record['response_class'] not in ('oversized', 'invalid-challenge'))


def gate(origin, evidence, identities):
    for label in ('status', 'ordinary_challenge', 'ordinary_chat', 'restricted_malformed'):
        if not accepted(probe(origin, label, evidence)):
            raise ProbeFailed('Persisted HTTP acceptance failure: ' + label)
    for value in identities['non_canary']:
        if not accepted(probe(origin, 'restricted_non_canary', evidence, value)):
            raise ProbeFailed('Persisted non-canary rejection failure')
    if not accepted(probe(origin, 'restricted_canary', evidence, identities['canary'])):
        raise ProbeFailed('Persisted canary challenge failure')


def wait_backend(origin, evidence, seconds=20):
    deadline = time.monotonic() + seconds
    while True:
        if accepted(probe(origin, 'ordinary_challenge', evidence)):
            return
        if time.monotonic() >= deadline:
            raise ProbeFailed('Persisted backend readiness timeout')
        time.sleep(.1)


def observe(origin, evidence, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        for label in ('status', 'ordinary_challenge', 'ordinary_chat'):
            probe(origin, label, evidence)
        time.sleep(.1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('ready', 'gate', 'observe'))
    parser.add_argument('--origin', required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--generation', required=True)
    parser.add_argument('--identities', type=Path)
    parser.add_argument('--expected-non-canary', type=int, default=26)
    parser.add_argument('--seconds', type=int, default=120)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 600:
        raise ValueError('Observation window out of bounds')
    evidence = Evidence(args.evidence, args.generation)
    try:
        if args.mode == 'ready':
            wait_backend(args.origin, evidence)
        elif args.mode == 'observe':
            observe(args.origin, evidence, args.seconds)
        else:
            descriptor = os.open(args.identities, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, 'rb') as source:
                info = os.fstat(source.fileno())
                if info.st_uid != os.geteuid() or info.st_mode & 0o077:
                    raise ValueError('Identities input must be owner-only')
                raw = source.read(65537)
            if len(raw) > 65536:
                raise ValueError('Oversized identities input')
            identities = json.loads(raw)
            if (set(identities) != {'canary', 'non_canary'} or not isinstance(identities['non_canary'], list)
                    or not 1 <= args.expected_non_canary <= 256
                    or len(identities['non_canary']) != args.expected_non_canary):
                raise ValueError('Invalid identities input')
            for value in [identities['canary'], *identities['non_canary']]:
                if type(value) is not dict or set(value) != {'public_identity', 'wireguard_public_key'}:
                    raise ValueError('Invalid identity fields')
                if any(type(field) is not str for field in value.values()):
                    raise ValueError('Invalid identity values')
            public = [value['public_identity'] for value in [identities['canary'], *identities['non_canary']]]
            if len(set(public)) != len(public):
                raise ValueError('Duplicate identity inputs')
            gate(args.origin, evidence, identities)
    finally:
        evidence.close()
    print('HTTP observations persisted; not an acceptance verdict' if args.mode == 'observe'
          else 'Friends HTTP acceptance passed; receipts persisted')


if __name__ == '__main__':
    def interrupted(number, frame):
        raise SystemExit(128 + number)
    for number in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(number, interrupted)
    try:
        main()
    except (ProbeFailed, OSError, ValueError, TypeError, KeyError, RecursionError):
        raise SystemExit('Friends HTTP acceptance failed; inspect protected receipts') from None
