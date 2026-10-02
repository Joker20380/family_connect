"""Closed B–G adapter; production owner proofs belong exclusively to the app."""
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from control.friends.readiness_fixture import listener
from scripts.friends_http_transition import Candidate, Evidence, Session, current_authority_check, process_start

DISTRIBUTIONS = {'rns': '1.5.1', 'cryptography': '46.0.7', 'cffi': '2.1.1',
                 'pycparser': '3.0', 'pyserial': '3.5'}


def versions():
    actual = {name: version(name) for name in DISTRIBUTIONS}
    if actual != DISTRIBUTIONS:
        raise ValueError('Locked dependency versions required')
    return actual


def pin(path, digest):
    if (type(digest) is not str or not re.fullmatch('[a-f0-9]{64}', digest)
            or hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest):
        raise ValueError('Artifact pin mismatch')


def configuration(path, bundle, manifest):
    raw = path.read_bytes()
    if len(raw) > 32768:
        raise ValueError('Oversized configuration')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate configuration field')
            result[key] = value
        return result
    config = json.loads(raw, object_pairs_hook=unique)
    required = {'version', 'mode', 'http_artifact', 'http_sha256'}
    if config.get('mode') == 'candidate':
        required |= {'candidate', 'authority'}
    if (set(config) != required or type(config['version']) is not int or config['version'] != 1
            or config['mode'] not in ('fixture', 'candidate')):
        raise ValueError('Invalid configuration')
    artifact = Path(config['http_artifact'])
    if not artifact.is_absolute():
        raise ValueError('Absolute artifact path required')
    pin(artifact, config['http_sha256'])
    native = bundle / 'readiness-delivery-check'
    pin(native, manifest['native_sha256'])
    config.update(native=native, native_sha256=manifest['native_sha256'])
    if config['mode'] == 'candidate':
        candidate = config['candidate']
        if set(candidate) != {'port', 'generation', 'pid', 'start', 'non_canaries'}:
            raise ValueError('Invalid candidate metadata')
        if (type(candidate['pid']) is not int or candidate['pid'] < 1
                or type(candidate['start']) is not str or not candidate['start'].isdigit()
                or type(candidate['non_canaries']) is not list or not candidate['non_canaries']):
            raise ValueError('Candidate identity required')
        Candidate(candidate['port'], candidate['generation'], artifact, config['http_sha256'])
        for identity in candidate['non_canaries']:
            if set(identity) != {'public_identity', 'wireguard_public_key'}:
                raise ValueError('Only public non-canary inputs permitted')
        authority = config['authority']
        if set(authority) != {'runtime', 'sha256', 'database', 'material', 'host', 'ssh_key', 'known_hosts'}:
            raise ValueError('Invalid authority-check configuration')
        if authority['host'] != '186.246.45.246':
            raise ValueError('Unexpected gateway')
        pin(authority['runtime'], authority['sha256'])
    return config


def controlled(config, evidence):
    with listener(config['http_artifact']) as fixture:
        def validate(response):
            pin(config['native'], config['native_sha256'])
            payload = dict(response=response, public=fixture['owner'].public_identity,
                           anchor=fixture['anchor'], now=int(time.time()))
            result = subprocess.run([str(config['native'])], input=json.dumps(payload).encode(),
                                    capture_output=True, timeout=5)
            pin(config['native'], config['native_sha256'])
            return result.returncode == 0 and result.stdout == b'compatible\n'
        session = Session(fixture['origin'], evidence, layer='server_contract_fixture', interval=1.1)
        return session.fixture_matrix(config['http_artifact'], fixture['identities'],
                                      lambda challenge: fixture['owner'].prove_transport_key(challenge['challenge']),
                                      validate)


class ExistingProcess:
    def __init__(self, pid):
        self.pid = pid

    def poll(self):
        try:
            os.kill(self.pid, 0)
            return None
        except ProcessLookupError:
            return 1


def execute(config, directory, record):
    evidence = Evidence(directory / 'probes', 'candidate-readiness')
    try:
        record['step'] = 'controlled_fixture_BG'
        fixture = controlled(config, evidence)
        if config['mode'] == 'candidate':
            record['step'] = 'candidate_identity'
            identity = config['candidate']
            if process_start(identity['pid']) != identity['start']:
                raise ValueError('Candidate start identity changed')
            candidate = Candidate(identity['port'], identity['generation'], config['http_artifact'], config['http_sha256'])
            candidate.capture(ExistingProcess(identity['pid']))
            record['step'] = 'candidate_BE_and_authority'
            authority = dict(config['authority'])
            runtime, digest = authority.pop('runtime'), authority.pop('sha256')
            session = Session('http://127.0.0.1:' + str(candidate.port), evidence,
                              layer='direct_candidate', candidate=candidate, generation=candidate.generation, interval=1.1)
            session.server_matrix(identity['non_canaries'], fixture=fixture,
                                  current_authority=lambda: current_authority_check(evidence, sys.executable, runtime, digest, **authority))
            record['state'] = 'SERVER_CANDIDATE_READY'
            record['candidate'] = dict(port=candidate.port, generation=candidate.generation,
                                       pid=candidate.process.pid, start=candidate.start, http_sha256=candidate.sha256)
        else:
            record['state'] = 'CONTROLLED SERVER CONTRACT FIXTURE'
        record['owner_product_ready'] = False
        pin(config['http_artifact'], config['http_sha256'])
    finally:
        evidence.close()
