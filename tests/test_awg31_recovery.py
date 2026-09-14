import pytest
from pilot.awg31.recovery import recover


class Clock:
    def __init__(self):
        self.now = 0
    def read(self):
        return self.now
    def pause(self, seconds):
        self.now += seconds


def run_case(outcomes, **kwargs):
    clock = Clock()
    resets = []
    samples = iter(outcomes)
    def probe():
        clock.pause(1)
        return next(samples, False)
    result = recover(probe, lambda: resets.append(clock.now), lambda: True,
                     clock=clock.read, pause=clock.pause, **kwargs)
    return result, resets


def test_transient_probe_loss_does_not_reset():
    result, resets = run_case([False, False, True])
    assert result.healthy and not resets


def test_recovery_requires_three_failures_then_health():
    result, resets = run_case([False, False, False, True])
    assert result.healthy and result.probes == 4
    assert len(resets) == 1 and resets[0] >= 3


def test_permanent_outage_has_budget_and_cooldown():
    result, resets = run_case([])
    assert not result.healthy and result.reason == 'deadline'
    assert len(resets) == 2 and resets[1]-resets[0] >= 10
    # A bounded probe can finish after the deadline; no new mutation follows it.
    assert result.elapsed <= 21


@pytest.mark.parametrize('change', ['ownership', 'cancel'])
def test_mid_probe_revocation_prevents_mutation(change):
    clock = Clock()
    allowed = True
    cancelled = False
    calls = 0
    def probe():
        nonlocal calls, allowed, cancelled
        calls += 1
        clock.pause(1)
        if calls == 3:
            allowed = change != 'ownership'
            cancelled = change == 'cancel'
        return False
    def forbidden():
        pytest.fail('Reset after revocation')
    result = recover(probe, forbidden, lambda: allowed, cancelled=lambda: cancelled,
                     clock=clock.read, pause=clock.pause)
    assert result.reason == 'ownership_or_cancellation' and result.resets == 0


def test_no_mutation_after_probe_exhausts_budget():
    result, resets = run_case([], timeout=3)
    assert not result.healthy and resets == []


def test_reset_error_is_not_retried():
    clock = Clock()
    attempts = []
    def reset():
        attempts.append(1)
        raise OSError('synthetic reset failure')
    with pytest.raises(OSError):
        recover(lambda: False, reset, lambda: True, clock=clock.read, pause=clock.pause)
    assert attempts == [1]
