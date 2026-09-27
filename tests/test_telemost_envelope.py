import importlib.util
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
