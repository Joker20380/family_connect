import pytest

from scripts.run_serialized_renewal import SERVICE, TIMER, run_serialized
from test_multi_gateway_renewal import fleet


class Units:
    def __init__(self, timer='active', writer='inactive'):
        self.timer, self.writer = timer, writer
        self.calls = []
        self.now = 0
        self.loaded = True
        self.restore = True

    def control(self, action, unit, *arguments):
        self.calls.append((action, unit))
        if action == 'show':
            active = self.timer if unit == TIMER else self.writer
            return 'LoadState=' + ('loaded' if self.loaded else 'not-found') + '\nActiveState=' + active + '\nMainPID=' + ('23' if unit == SERVICE and active == 'active' else '0')
        assert unit == TIMER
        if action == 'stop':
            self.timer = 'inactive'
        elif action == 'start' and self.restore:
            self.timer = 'active'
        return ''

    def sleep(self, seconds):
        self.now += seconds

    def run(self, controller, sleep=None):
        return run_serialized(controller, control=self.control, clock=lambda: self.now, sleep=sleep or self.sleep)


def test_waits_for_real_publisher_lock_then_existing_fleet_controller(fleet):
    fleet.now += 12000
    publisher = fleet.nodes['RU'].operation.lock()
    publisher.__enter__()
    units = Units(writer='active')

    def finish_publisher(seconds):
        assert units.timer == 'inactive'
        units.sleep(seconds)
        publisher.__exit__(None, None, None)
        units.writer = 'inactive'

    result = units.run(lambda: fleet.scheduled('serialized-publisher'), finish_publisher)
    assert result['result'] == 'COMMITTED'
    assert units.now == 1 and units.timer == 'active'
    assert units.calls.count(('stop', TIMER)) == units.calls.count(('start', TIMER)) == 1


@pytest.mark.parametrize('result', [0, 1, 75])
@pytest.mark.parametrize('timer', ['active', 'inactive'])
def test_preserves_controller_exit_and_original_timer_state(result, timer):
    units = Units(timer=timer)
    assert units.run(lambda: result) == result
    assert units.timer == timer
    assert (('start', TIMER) in units.calls) == (timer == 'active')
    assert not any(action in ('start', 'stop') and unit == SERVICE for action, unit in units.calls)


@pytest.mark.parametrize('error', [OSError, KeyboardInterrupt])
def test_restores_timer_after_controller_failure_or_interruption(error):
    units = Units()

    def fail():
        raise error

    with pytest.raises(error):
        units.run(fail)
    assert units.timer == 'active'


def test_writer_timeout_never_invokes_controller():
    units = Units(writer='active')
    with pytest.raises(RuntimeError, match='DIRECTORY_WRITER_NOT_QUIESCENT'):
        units.run(lambda: pytest.fail('controller must not start'))
    assert units.timer == 'active' and units.now == 120


def test_missing_unit_never_changes_state():
    units = Units()
    units.loaded = False
    with pytest.raises(RuntimeError, match='DIRECTORY_UNIT_UNAVAILABLE'):
        units.run(lambda: pytest.fail('controller must not start'))
    assert units.calls == [('show', TIMER)]


def test_restore_failure_is_not_success():
    units = Units()
    units.restore = False
    with pytest.raises(RuntimeError, match='DIRECTORY_TIMER_NOT_RESTORED'):
        units.run(lambda: 0)
