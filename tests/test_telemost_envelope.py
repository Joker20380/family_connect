import importlib.util
import json
from pathlib import Path

import pytest


def envelope():
    path = Path(__file__).resolve().parents[1] / 'pilot/android-telemost/envelope.py'
    spec = importlib.util.spec_from_file_location('telemost_envelope', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_complete_quantiles():
    result = envelope().distribution(list(range(1, 101)))
    assert result == {'count': 100, 'avg': 50.5, 'min': 1, 'max': 100, 'p50': 50, 'p95': 95, 'p99': 99}


def test_recent_events_require_full_coverage():
    events = [{'index': index, 'kind': 'recovered', 'delay_ms': index} for index in range(1, 401)]
    final = {'Events': events[:128], 'RecentEvents': events[-128:], 'EventsDropped': 272}
    captured, complete = envelope().reliability_events([], final)
    assert not complete and len(captured) == 256
    captured, complete = envelope().reliability_events([{'reliability': {'Events': events[:128], 'RecentEvents': events[128:272]}}], final)
    assert complete and captured == events


def test_contradictory_evidence_fails():
    with pytest.raises(ValueError, match='contradictory'):
        envelope().reliability_events([{'reliability': {'Events': [{'index': 1, 'kind': 'gap'}]}}],
                                     {'Events': [{'index': 1, 'kind': 'recovered'}]})


@pytest.mark.parametrize('fault', [None, 'sequence', 'count', 'duration', 'corruption', 'exit', 'auth'])
def test_exact_full_duration_proof_is_required(tmp_path, fault):
    result = {'event': 'perf_result', 'utc': '2026-09-27T01:16:00Z', 'warmup': False,
              'status': 'PASS', 'config': {'seconds': 900}, 'measurement_s': 900,
              'blocks_received': 2, 'blocks_sent': 2, 'errors': {'corruption': 0},
              'useful_rx_bytes': 32768, 'useful_tx_bytes': 32768}
    rows = [{'event': 'family_auth', 'accepted': fault != 'auth'},
            {'event': 'perf_warmup', 'sent': 1, 'utc': '2026-09-27T01:01:00Z'},
            {'event': 'perf_blocks', 'warmup': False, 'rows': [[2, 0, 0, 1, 2], [3, 3, 3, 4, 5]]},
            result, {'event': 'android_exit', 'code': 1 if fault == 'exit' else 0}]
    if fault == 'sequence':
        rows[2]['rows'][0][0] = 1
    if fault == 'count':
        result['blocks_received'] = 3
    if fault == 'duration':
        result['measurement_s'] = 899
    if fault == 'corruption':
        result['errors']['corruption'] = 1
    (tmp_path / 'A.jsonl').write_text('\n'.join(json.dumps(row) for row in rows))
    (tmp_path / 'B.jsonl').write_text('{"event":"family_auth","accepted":true}')
    assert envelope().summarize(tmp_path)['correctness_complete'] == (fault is None)
