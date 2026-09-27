import importlib.util
import json
from pathlib import Path

import pytest


def validator():
    path = Path(__file__).resolve().parents[1] / 'pilot/android-telemost/family_checks.py'
    spec = importlib.util.spec_from_file_location('reliable_gap_runner', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_gap_evidence


def evidence():
    proof = {'injected_sequence': 7, 'tls_survived': True, 'exact_echoes': 8,
             'reliability': {'Retransmissions': 1}}
    remote = [{'event': 'reliability_final', 'stats': {'Events': [
        {'kind': 'gap_sack', 'sequence': 7}, {'kind': 'recovered', 'sequence': 7}]}}]
    return proof, remote


def test_requires_matched_gap_recovery_and_exact_tls_echo():
    proof, remote = evidence()
    assert validator()('RELIABLE_GAP_EVIDENCE ' + json.dumps(proof), remote)['tls_survived']


@pytest.mark.parametrize('missing', ['receiver', 'gap', 'recovered', 'tls', 'echo', 'retransmit'])
def test_does_not_promote_missing_proof(missing):
    proof, remote = evidence()
    if missing == 'receiver':
        remote = []
    elif missing in {'gap', 'recovered'}:
        remote[0]['stats']['Events'].pop(0 if missing == 'gap' else 1)
    elif missing == 'tls':
        proof['tls_survived'] = False
    elif missing == 'echo':
        proof['exact_echoes'] = 7
    else:
        proof['reliability']['Retransmissions'] = 0
    with pytest.raises(RuntimeError):
        validator()('RELIABLE_GAP_EVIDENCE ' + json.dumps(proof), remote)
