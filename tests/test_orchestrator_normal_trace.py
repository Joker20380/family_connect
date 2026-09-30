import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('normal_trace', Path(__file__).resolve().parents[1] / 'pilot/android-restricted/normal_trace.py')
TRACE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRACE)


def test_trace_only_retains_allowlisted_reasons_for_controlled_flows():
    trace = TRACE.Trace({'192.0.2.1'})
    trace.accept('[123] received request for tcp:192.0.2.1:443')
    trace.accept('[123] connection ends > connection reset by peer PRIVATE-DATA')
    trace.accept('[456] received request for tcp:192.0.2.2:443 PRIVATE-DATA')
    trace.accept('[123] arbitrary payload PRIVATE-DATA')
    snapshot = trace.snapshot()
    assert snapshot['controlled_flows'] == 1
    assert len(snapshot['events']) == 2
    assert 'PRIVATE-DATA' not in str(snapshot)
    assert '192.0.2.' not in str(snapshot)
    assert snapshot['events'][-1]['labels'] == ['connection ends', 'connection reset by peer']


def test_trace_has_time_and_record_bounds():
    trace = TRACE.Trace({'192.0.2.1'})
    for count in range(1000):
        trace.accept(f'[{count}] received request for tcp:192.0.2.1:443')
    assert len(trace.events) == 512
    expired = TRACE.Trace({'192.0.2.1'})
    expired.started -= 181
    expired.accept('[123] received request for tcp:192.0.2.1:443')
    assert expired.snapshot()['events'] == []
