import json
from pathlib import Path

import pytest

from control import docker_cold as cold


@pytest.fixture
def transition(tmp_path, monkeypatch):
    engine, config, source = (tmp_path / name for name in ('engine', 'config', 'source'))
    engine.write_bytes(b'synthetic engine')
    source.write_bytes(b'synthetic source')
    value = {'data-root': str(tmp_path / 'new'), 'authorization-plugins': ['test'], 'live-restore': False}
    config.write_text(json.dumps(value))
    plan = dict(schema=1, operation='a' * 32, old_boot='old', old_root=str(tmp_path / 'old'),
                new_root=value['data-root'], engine=str(engine), engine_sha256=cold.digest(engine),
                configuration=str(config), configuration_sha256=cold.digest(config), plugin='test',
                sources={str(source): cold.digest(source)})
    cold.publish(tmp_path / 'plan.json', plan)
    monkeypatch.setattr(cold, 'boot', lambda: 'new')
    return cold.Transition(tmp_path)


def test_old_kernel_never_opens_and_changed_source_refuses(transition, monkeypatch):
    monkeypatch.setattr(cold, 'boot', lambda: 'old')
    with pytest.raises(ValueError, match='COLD_NEW_KERNEL_REQUIRED'):
        transition.guard()
    assert not (transition.root / 'kernel.json').exists()
    monkeypatch.setattr(cold, 'boot', lambda: 'new')
    Path(next(iter(transition.plan['sources']))).write_bytes(b'changed')
    with pytest.raises(ValueError, match='COLD_SOURCE_CHANGED'):
        transition.guard()


def test_lost_response_reconciles_effect_without_replay_or_capture_lease(transition):
    state, effects = [], []
    def execute():
        state.append({'id': 'known'})
        effects.append('once')
        raise TimeoutError('lost response')
    with transition:
        with pytest.raises(TimeoutError):
            transition.step('create', lambda: state[0] if state else None, execute)
    with cold.Transition(transition.root) as replacement:
        expected = replacement.step('create', lambda: state[0], lambda: pytest.fail('replayed'))
        assert replacement.step('create', lambda: state[0], lambda: pytest.fail('replayed')) == expected
    assert effects == ['once']
    assert json.loads((transition.root / 'create-error.json').read_bytes())['category'] == 'TimeoutError'
    assert json.loads((transition.root / 'kernel.json').read_bytes())['capture_lease'] is None


def test_unknown_effect_is_terminal_and_first_reason_survives(transition):
    with transition:
        with pytest.raises(TimeoutError):
            transition.step('create', lambda: None, lambda: (_ for _ in ()).throw(TimeoutError()))
    with cold.Transition(transition.root) as replacement:
        with pytest.raises(ValueError, match='COLD_EFFECT_OUTCOME_UNKNOWN'):
            replacement.step('create', lambda: None, lambda: pytest.fail('replayed'))
        with pytest.raises(ValueError, match='COLD_EFFECT_OUTCOME_UNKNOWN'):
            replacement.refuse('CLEANUP_FAILED')
    with pytest.raises(ValueError, match='COLD_EFFECT_OUTCOME_UNKNOWN'):
        cold.Transition(transition.root).guard()


def test_new_boot_requires_new_operation_and_never_adopts_lease(transition, monkeypatch):
    transition.guard()
    monkeypatch.setattr(cold, 'boot', lambda: 'newer')
    with pytest.raises(ValueError, match='COLD_NEW_OPERATION_REQUIRED'):
        transition.guard()


def test_error_record_failure_never_replaces_original_failure(transition, monkeypatch):
    original = cold.publish
    def publish(path, value):
        if path.name == 'create-error.json':
            raise OSError('storage failure')
        return original(path, value)
    monkeypatch.setattr(cold, 'publish', publish)
    with transition:
        with pytest.raises(TimeoutError, match='first') as caught:
            transition.step('create', lambda: None, lambda: (_ for _ in ()).throw(TimeoutError('first')))
    assert caught.value.__notes__ == ['COLD_ERROR_RECORD_OSError']
    assert (transition.root / 'create-intent.json').exists()


def test_atomic_receipt_failed_publication_does_not_expose_partial_record(tmp_path, monkeypatch):
    original = cold.os.link
    def fail(source, target):
        assert Path(source).read_bytes() == b'{"ready":true}'
        assert not Path(target).exists()
        raise OSError('synthetic publication failure')
    monkeypatch.setattr(cold.os, 'link', fail)
    with pytest.raises(OSError):
        cold.publish(tmp_path / 'receipt', {'ready': True})
    assert list(tmp_path.iterdir()) == []
    monkeypatch.setattr(cold.os, 'link', original)
    cold.publish(tmp_path / 'receipt', {'ready': True})
    cold.publish(tmp_path / 'receipt', {'ready': True})
    with pytest.raises(ValueError, match='COLD_RECORD_CHANGED'):
        cold.publish(tmp_path / 'receipt', {'ready': False})


def test_policy_socket_can_activate_before_engine_but_first_request_must_bind():
    from control.docker_cold_plugin import LazyAdmission
    calls = []
    class Admission:
        def request(self, request):
            return request
    def factory():
        calls.append('bind')
        return Admission()
    proxy = LazyAdmission(factory)
    assert not calls
    assert proxy.request({'request': 1}) == {'request': 1}
    assert proxy.request({'request': 2}) == {'request': 2}
    assert calls == ['bind']


def test_controller_death_reconciles_published_effect_in_new_process(transition):
    import os
    import signal
    process = os.fork()
    effect = transition.root / 'effect'
    if process == 0:
        with transition:
            def execute():
                cold.publish(effect, {'completed': True})
                os.kill(os.getpid(), signal.SIGKILL)
            transition.step('effect', lambda: None, execute)
        os._exit(1)
    _, status = os.waitpid(process, 0)
    assert os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGKILL
    with cold.Transition(transition.root) as replacement:
        replacement.step('effect', lambda: json.loads(effect.read_bytes()), lambda: pytest.fail('replayed'))
