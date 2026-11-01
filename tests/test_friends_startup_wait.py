from copy import deepcopy

import pytest

from scripts.observe_friends_service import ObservationError, wait_started


def ready():
    return dict(result='OBSERVED', service=dict(NRestarts=0, effective_execstart_matches=True,
        running_argv_matches=True, ActiveState='active', SubState='running', NeedDaemonReload=False), jobs=dict(count=0))


def run(samples, *, timeout=1):
    moment = [0]
    recorded = []
    observations = iter(samples)

    def read(expected):
        assert expected == ['synthetic-python', 'synthetic-http.pyz']
        result = next(observations)
        if isinstance(result, Exception):
            raise result
        return deepcopy(result)

    def pause(seconds):
        moment[0] += seconds

    result = wait_started(['synthetic-python', 'synthetic-http.pyz'], timeout=timeout, interval=.5,
                          read=read, record=recorded.append, clock=lambda: moment[0], pause=pause)
    return result, recorded, moment[0]


@pytest.mark.parametrize('field,value', [
    ('running_argv_matches', False), ('effective_execstart_matches', False),
    ('ActiveState', 'activating'), ('SubState', 'start'), ('NeedDaemonReload', True),
])
def test_startup_wait_records_transient_state_before_exact_ready(field, value):
    first = ready()
    first['service'][field] = value
    result, recorded, elapsed = run([first, ready()])
    assert result == ready() and recorded == [first, ready()] and elapsed == .5


@pytest.mark.parametrize('code', ['NO_MAIN_PID', 'PROC_UNAVAILABLE', 'SERVICE_CHANGED_DURING_READ', 'JOBS_CHANGED_DURING_READ'])
def test_startup_wait_allows_bounded_process_transition(code):
    result, recorded, elapsed = run([ObservationError('process', code), ready()])
    assert result == ready() and elapsed == .5
    assert recorded[0]['code'] == code


def test_startup_wait_pending_jobs_then_exact_ready():
    first = ready()
    first['jobs']['count'] = 1
    assert run([first, ready()])[2] == .5


def test_startup_wait_never_accepts_persistent_mismatch():
    mismatch = ready()
    mismatch['service']['running_argv_matches'] = False
    with pytest.raises(ObservationError, match='STARTUP_NOT_STABLE'):
        run([mismatch, mismatch, mismatch])


def test_startup_wait_rejects_automatic_restart_without_retry():
    restarted = ready()
    restarted['service']['NRestarts'] = 1
    with pytest.raises(ObservationError, match='AUTOMATIC_RESTART_OBSERVED'):
        run([restarted])


def test_startup_wait_does_not_retry_unrecognized_error():
    with pytest.raises(ObservationError, match='INVALID_TYPED_RESPONSE'):
        run([ObservationError('decode', 'INVALID_TYPED_RESPONSE')])


@pytest.mark.parametrize('timeout,interval', [(0, .2), (61, .2), (True, .2), (1, 0), (1, 2)])
def test_startup_wait_requires_bounded_observation(timeout, interval):
    with pytest.raises(ObservationError, match='INVALID_WAIT_BOUNDS'):
        wait_started(['synthetic'], timeout=timeout, interval=interval)
