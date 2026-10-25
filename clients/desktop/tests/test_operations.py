import os
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
import backend

OWNER='a'*64
OTHER='b'*64


def test_nested_backend_calls_and_busy_threads():
    with backend.connection_operation(owner=OWNER) as lease:
        lease.reserve()
        with backend.connection_operation(mutate=True):pass
        def contender():
            with pytest.raises(backend.ConnectionBusy):
                with backend.connection_operation():pass
        with ThreadPoolExecutor(max_workers=1) as executor:executor.submit(contender).result()
        lease.finish()
    with backend.connection_operation() as lease:assert lease.record['generation']==2


def test_pending_owner_survives_process_death(tmp_path,monkeypatch):
    directory=tmp_path/'operations'
    script='''
import os,sys
from pathlib import Path
import backend
backend.operation_directory=lambda:Path(sys.argv[1])
with backend.connection_operation(owner='a'*64) as lease:
    lease.reserve()
    os._exit(0)
'''
    result=subprocess.run([sys.executable,'-c',script,str(directory)],
        env={**os.environ,'PYTHONPATH':str(Path(backend.__file__).parent)},capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
    with pytest.raises(backend.ConnectionBusy):
        with backend.connection_operation(mutate=True):pass
    with pytest.raises(backend.ConnectionBusy):
        with backend.connection_operation(owner=OTHER):pass
    with backend.connection_operation(owner=OWNER) as lease:
        assert lease.record['pending']==OWNER
        lease.finish()
    with backend.connection_operation(mutate=True):pass


def test_other_process_blocked_even_without_pending_marker(tmp_path):
    script='''
import sys
from pathlib import Path
import backend
backend.operation_directory=lambda:Path(sys.argv[1])
try:
    with backend.connection_operation(mutate=True):pass
except backend.ConnectionBusy:sys.exit(0)
sys.exit(1)
'''
    with backend.connection_operation():
        result=subprocess.run([sys.executable,'-c',script,str(tmp_path/'operations')],
            env={**os.environ,'PYTHONPATH':str(Path(backend.__file__).parent)},capture_output=True,timeout=10)
        assert result.returncode==0


@pytest.mark.parametrize('damage',['missing','corrupt','mode','symlink','hardlink'])
def test_unsafe_coordination_fails_closed(tmp_path,damage):
    with backend.connection_operation():pass
    state=tmp_path/'operations/state.json'
    if damage=='missing':state.unlink()
    elif damage=='corrupt':state.write_text('{}')
    elif damage=='mode':state.chmod(0o644)
    elif damage=='symlink':state.rename(state.with_name('old'));state.symlink_to('old')
    else:state.with_name('other').hardlink_to(state)
    with pytest.raises((backend.BackendError,OSError)):
        with backend.connection_operation(mutate=True):pass


def test_stale_recovery_never_mutates(monkeypatch):
    driver=backend.LinuxTCP();calls=[]
    monkeypatch.setattr(driver,'recover',lambda _:calls.append('recover'))
    with backend.connection_operation() as lease:generation=lease.record['generation']
    with backend.connection_operation(mutate=True):pass
    with pytest.raises(backend.StaleConnection):driver.recover_if_current('old',generation)
    assert calls==[]


@pytest.mark.parametrize('cls',[backend.Linux,backend.LinuxTCP])
@pytest.mark.parametrize('method',['connect','disconnect','recover','import_profile'])
def test_all_gui_mutation_entry_points_refuse_pending(cls,method):
    with backend.connection_operation(owner=OWNER) as lease:lease.reserve()
    with pytest.raises(backend.ConnectionBusy):getattr(cls(),method)('unused')
    with backend.connection_operation(owner=OWNER) as lease:lease.finish()


def test_automatic_recovery_preserves_generation_and_retry_budget(monkeypatch):
    driver=backend.LinuxTCP()
    monkeypatch.setattr(driver,'recover',lambda _:None)
    monkeypatch.setattr(driver,'active',lambda _:True)
    with backend.connection_operation() as lease:generation=lease.record['generation']
    assert driver.recover_if_current('current',generation)
    with backend.connection_operation() as lease:assert lease.record['generation']==generation


def test_control_waits_for_short_gui_poll(tmp_path, monkeypatch):
    import threading
    monkeypatch.setattr(backend, 'operation_directory', lambda: tmp_path/'operations')
    held = threading.Event()
    release = threading.Event()
    def poll():
        with backend.connection_operation():
            held.set()
            assert release.wait(3)
    thread = threading.Thread(target=poll)
    thread.start(); assert held.wait(3)
    timer = threading.Timer(.15, release.set); timer.start()
    try:
        with backend.Linux().control_transaction('a'*64) as lease:
            assert release.is_set() and lease.record['pending'] is None
    finally:
        release.set(); thread.join(3); timer.cancel()


def test_control_contention_is_bounded(tmp_path, monkeypatch):
    from contextlib import contextmanager
    @contextmanager
    def busy(**_):
        raise backend.ConnectionBusy('pending owner')
        yield
    monkeypatch.setattr(backend, 'connection_operation', busy)
    clock=iter([0, 6])
    monkeypatch.setattr(backend.time, 'monotonic', lambda: next(clock))
    with pytest.raises(backend.ConnectionBusy):
        with backend.Linux().control_transaction('a'*64):
            pytest.fail('must not bypass ownership')


@pytest.mark.parametrize('stage', ['profiles', 'active', 'health'])
@pytest.mark.parametrize('read_error', [False, True])
def test_slow_production_poll_does_not_block_one_disconnect(normal_owner, stage, read_error):
    owner = normal_owner
    owner.block_at = stage
    owner.read_error = read_error
    with backend.connection_operation() as lease:
        generation = lease.record['generation']
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix='fc-poll') as executor:
        poll = executor.submit(owner.driver.poll_state, owner.ident, stage == 'health')
        try:
            assert owner.entered.wait(5)
            try:
                owner.driver.disconnect(owner.ident)
            except backend.ConnectionBusy:
                assert owner.active and owner.downs == []
                with pytest.raises(backend.ConnectionBusy):
                    with backend.connection_operation():
                        pass
                raise
            assert owner.downs == [owner.ident] and not owner.active
            with backend.connection_operation() as lease:
                assert lease.record['generation'] == generation + 1
        finally:
            owner.release.set()
        with pytest.raises(backend.StaleConnection):
            poll.result(timeout=5)


@pytest.mark.parametrize('health', [False, True])
def test_production_poll_snapshot_without_mutation(normal_owner, health):
    owner = normal_owner
    with backend.connection_operation() as lease:
        generation = lease.record['generation']
    snapshot = owner.driver.poll_state(owner.ident, health)
    assert snapshot.generation == generation and snapshot.active
    assert snapshot.active_ids == [owner.ident]
    assert snapshot.healthy is (True if health else None)
    with backend.connection_operation() as lease:
        assert lease.record['generation'] == generation
    assert owner.downs == []


def test_poll_revalidation_refuses_pending_owner(normal_owner):
    owner = normal_owner
    owner.block_at = 'profiles'
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix='fc-poll') as executor:
        poll = executor.submit(owner.driver.poll_state, owner.ident)
        try:
            assert owner.entered.wait(5)
            with backend.connection_operation(owner=OWNER) as lease:
                lease.reserve()
        finally:
            owner.release.set()
        with pytest.raises(backend.ConnectionBusy):
            poll.result(timeout=5)
    assert owner.active and owner.downs == []


def test_production_disconnect_still_refuses_durable_owner(normal_owner):
    with backend.connection_operation(owner=OWNER) as lease:
        lease.reserve()
    with pytest.raises(backend.ConnectionBusy):
        normal_owner.driver.disconnect(normal_owner.ident)
    assert normal_owner.active and normal_owner.downs == []


def test_production_disconnect_still_refuses_foreign_process(normal_owner, tmp_path):
    script = '''
import sys
from pathlib import Path
import backend
backend.operation_directory=lambda:Path(sys.argv[1])
with backend.connection_operation(mutate=True):
    print('locked',flush=True)
    sys.stdin.readline()
'''
    process = subprocess.Popen([sys.executable, '-c', script, str(tmp_path/'operations')],
        env={**os.environ, 'PYTHONPATH': str(Path(backend.__file__).parent)},
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        assert process.stdout.readline().strip() == 'locked'
        with pytest.raises(backend.ConnectionBusy):
            normal_owner.driver.disconnect(normal_owner.ident)
        assert normal_owner.active and normal_owner.downs == []
    finally:
        process.communicate('\n', timeout=5)
        assert process.returncode == 0
