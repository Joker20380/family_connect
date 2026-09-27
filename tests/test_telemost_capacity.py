import importlib.util
import json
from pathlib import Path

import pytest


def capacity():
    path = Path(__file__).resolve().parents[1] / 'pilot/android-telemost/capacity.py'
    spec = importlib.util.spec_from_file_location('telemost_capacity', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('rtt,rate,accepted', [(2000, 0.0655, True), (4000, 0.0327, False), (2000, 0.131, False)])
def test_canonical_baseline_gates_sweep(tmp_path, rtt, rate, accepted):
    path = tmp_path / 'A.jsonl'
    rows = [{'event': 'family_auth', 'accepted': True},
            {'event': 'probe_result', 'payload_bytes': 16384, 'elapsed_s': 60,
             'byte_equal': True, 'carrier_mode': 'vp8', 'mean_rtt_ms': rtt, 'useful_oneway_mbit_s': rate},
            {'event': 'android_exit', 'code': 0}]
    path.write_text('\n'.join(json.dumps(row) for row in rows))
    if accepted:
        assert capacity().baseline_result(path)['mean_rtt_ms'] == rtt
    else:
        with pytest.raises(ValueError, match='mismatch'):
            capacity().baseline_result(path)


def test_short_or_unauthenticated_baseline_rejected(tmp_path):
    path = tmp_path / 'A.jsonl'
    path.write_text('{}\n')
    with pytest.raises(ValueError, match='authenticated'):
        capacity().baseline_result(path)
    path.write_text('{"event":"family_auth","accepted":true}\n')
    with pytest.raises(ValueError, match='>=60s'):
        capacity().baseline_result(path)
