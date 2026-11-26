import json
import hashlib
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid

import pytest

from scripts import control_ha_support_replace as replace
from test_control_ha_legacy_support import installed, wait_for, read


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/support_replacement.py'


def eventually(root, recover=False, seconds=15):
    deadline = time.monotonic() + seconds
    while True:
        result = replace.Replacement(root).run(recover=recover)
        if not result.startswith('WAITING_'):
            return result
        assert time.monotonic() < deadline, result
        time.sleep(.1)


@pytest.fixture
def service(tmp_path, installed, request):
    candidate = os.environ.get('FC_TEST_SUPPORT_ARCHIVE')
    if not candidate or os.environ.get('FC_TEST_SYSTEMD_SUPPORT_DRAIN') != '1':
        pytest.skip('requires pinned support archive and owned user-systemd fixtures')
    data = tmp_path / 'data'
    data.mkdir(mode=0o700)
    initialize = ('import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);'
                  'from messenger.store import Store;root=Path(sys.argv[2]);'
                  'store=Store(root/"store",b"s"*32,create=True);'
                  'store.chat_identity().to_file(str(root/"synthetic.identity"));'
                  'print(store.chat_identity().get_public_key().hex());store.close();'
                  '(root/"key").write_bytes(b"s"*32);(root/"key").chmod(0o600)')
    interpreter = os.environ['FC_TEST_SUPPORT_PYTHON']
    public = subprocess.check_output([interpreter, '-I', '-c', initialize, str(installed), str(data)], text=True).strip()
    unit = 'fc-ha-support-replace-test-' + uuid.uuid4().hex + '.service'
    directory = Path(os.environ['XDG_RUNTIME_DIR']) / 'systemd/user'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / unit
    options = ['--store', str(data / 'store'), '--key', str(data / 'key'), '--sender-public', public,
               '--snapshot', str(data / 'unused-snapshot'), '--runtime', str(data / 'runtime'),
               '--socket', str(data / 'worker.sock'), '--snapshot-uid', str(os.getuid())]
    command = [interpreter, '-I', '-B', str(FIXTURE), str(installed), *options]
    path.write_text('[Service]\nType=simple\nRestart=on-failure\nRestartSec=5\nRemainAfterExit=yes\n'
                    'Environment=FC_TEST_PTRACER_ANY=1\n'
                    'TimeoutStopSec=40\nKillMode=control-group\nSendSIGKILL=yes\nUMask=0077\n'
                    'ExecStart=' + ' '.join(command) + '\n')
    manager = replace.Manager(unit, user=True)
    try:
        manager.call('daemon-reload')
        manager.call('start', unit)
        wait_for(lambda: (data / 'worker.sock').exists())
        root = tmp_path / 'replacement'
        plan = replace.prepare(manager, installed, candidate, root, data / 'participant', tmp_path / 'support.pyz',
                               seconds=8, handoff=getattr(request, 'param', False))
        config = root / 'support.conf'
        raw = config.read_bytes().replace(('ExecStart=' + interpreter).encode(),
            ('ExecStart=' + interpreter + ' -I -B ' + str(ROOT / 'tests/fixtures/support_ptracer.py') +
             ' ' + interpreter).encode())
        config.write_bytes(raw)
        plan['dropin_sha256'] = hashlib.sha256(raw).hexdigest()
        (root / 'plan.json').write_text(json.dumps(plan))
        yield manager, plan, root, data
    finally:
        if 'root' in locals():
            for name in ('candidate-wait-observed', 'rollback-intent', 'terminal-failure'):
                if (root / (name + '.json')).exists():
                    print('BOUNDED_REPLACEMENT_DIAGNOSTIC ' + json.dumps(read(root / (name + '.json'))), flush=True)
        (data / 'release').touch()
        manager.call('stop', '--no-block', unit)
        deadline = time.monotonic() + 5
        while manager.state()['MainPID'] != '0' and time.monotonic() < deadline:
            time.sleep(.05)
        if manager.state()['MainPID'] != '0':
            manager.call('kill', '--signal=SIGKILL', unit)
        path.unlink()
        shutil.rmtree(Path(str(path) + '.d'), ignore_errors=True)
        manager.call('daemon-reload')
        subprocess.run([*manager.command, 'reset-failed', unit], capture_output=True)


@pytest.mark.parametrize('service', [True], indirect=True)
def test_handoff_candidate_restart_cannot_reuse_process_start_authority(service):
    manager, plan, root, data = service
    assert eventually(root) == 'ACCEPTED'
    first = manager.state()
    assert first['Restart'] == 'no'
    assert read(Path(plan['start_authority']))['binding']['pid'] == int(first['MainPID'])
    assert not (Path('/proc') / str(plan['old_binding']['pid'])).exists()
    manager.call('restart', manager.unit)
    wait_for(lambda: manager.state()['MainPID'] == '0')
    state = manager.state()
    assert state['ExecMainStatus'] == '78' and state['NRestarts'] == '0'
    with pytest.raises(ValueError):
        replace.Replacement(root).run()
    assert not (root / 'rollback-intent.json').exists()
    assert all((Path(plan['gate']) / 'pending' / name).exists() for name in plan['pending'])
    assert eventually(root, recover=True) == 'ROLLED_BACK'


@pytest.mark.parametrize('service', [True], indirect=True)
def test_start_authority_waits_for_controlled_exec_boundary(service):
    manager, plan, root, data = service
    barrier = data / 'exec-barrier'
    os.mkfifo(barrier, 0o600)
    config = root / 'support.conf'
    config.write_bytes(config.read_bytes().replace(b'support_ptracer.py ',
        ('support_ptracer.py --barrier ' + str(barrier) + ' ').encode()))
    plan['dropin_sha256'] = replace.digest(config)
    (root / 'plan.json').write_text(json.dumps(plan))
    errors = []
    def release_exec():
        try:
            wait_for(lambda: barrier.with_name(barrier.name + '.entered').exists())
            wait_for(lambda: (root / 'candidate-wait-observed.json').exists())
            assert read(root / 'candidate-wait-observed.json')['reason'] == 'LIVE_COMMAND_MISMATCH'
            assert not Path(plan['start_authority']).exists()
            assert not (root / 'rollback-intent.json').exists()
            descriptor = os.open(barrier, os.O_WRONLY | os.O_NONBLOCK)
            try:
                assert os.write(descriptor, b'1') == 1
            finally:
                os.close(descriptor)
        except BaseException as error:
            errors.append(error)
    release = threading.Thread(target=release_exec)
    release.start()
    try:
        assert eventually(root) == 'ACCEPTED'
        release.join(5)
        assert not release.is_alive() and not errors
        assert read(Path(plan['start_authority']))['binding']['command'] == replace.admission.binding(
            int(manager.state()['MainPID']))['command']
    finally:
        release.join(5)


def test_actual_systemd_install_and_code_only_rollback_preserve_uncertainty(service):
    manager, plan, root, data = service
    assert eventually(root) == 'ACCEPTED'
    pid = int(manager.state()['MainPID'])
    assert pid != plan['old_binding']['pid']
    assert replace.argv(pid) == plan['new_argv']
    assert read(root / 'accepted.json')['capture_permitted'] is False
    assert eventually(root) == 'ALREADY_ACCEPTED'
    assert eventually(root, recover=True) == 'ROLLED_BACK'
    assert replace.argv(int(manager.state()['MainPID'])) == plan['old_argv']
    assert not Path(plan['dropin']).exists()
    assert all((Path(plan['gate']) / 'pending' / name).exists() for name in plan['pending'])
    assert eventually(root) == 'ROLLED_BACK'


@pytest.mark.parametrize('name', ['scripts/control_ha_support_exit.py', 'scripts/control_ha_support_replace.py', 'support.conf'])
def test_staged_drift_refuses_without_touching_old_service(service, name):
    manager, plan, root, data = service
    (root / name).write_bytes((root / name).read_bytes() + b'\n')
    with pytest.raises(ValueError):
        replace.Replacement(root).run()
    assert int(manager.state()['MainPID']) == plan['old_binding']['pid']
    assert not Path(plan['dropin']).exists()


def test_foreign_unloaded_dropin_is_not_overwritten_or_reloaded(service):
    manager, plan, root, data = service
    foreign = Path(plan['dropin']).parent / 'unrecognized.conf'
    foreign.parent.mkdir(exist_ok=True)
    foreign.write_text('[Service]\nNice=1\n')
    with pytest.raises(ValueError, match='UNEXPECTED_DISK_DROPIN'):
        replace.Replacement(root).run()
    assert int(manager.state()['MainPID']) == plan['old_binding']['pid']
    assert foreign.read_text() == '[Service]\nNice=1\n'


@pytest.mark.parametrize('phase', ['drain-intent', 'commit-intent', 'old-exited', 'install-intent',
                                  'candidate-start-intent', 'accepted'])
def test_controller_death_resumes_without_repeating_remote_exit(service, phase):
    manager, plan, root, data = service
    code = ('import os,sys;sys.path.insert(0,sys.argv[1]);from scripts import control_ha_support_replace as replacement;'
            'record=replacement.Replacement.record\n'
            'def checkpoint(self,name,**value):\n'
            ' record(self,name,**value)\n'
            ' if name==sys.argv[3]:os._exit(71)\n'
            'replacement.Replacement.record=checkpoint\n'
            'while True:\n'
            ' result=replacement.Replacement(sys.argv[2]).run()\n'
            ' if not result.startswith("WAITING_"):raise SystemExit(72)\n')
    process = subprocess.run([sys.executable, '-I', '-c', code, str(ROOT), str(root), phase],
                             capture_output=True, timeout=15)
    assert process.returncode == 71, process.stderr
    result = eventually(root)
    if phase == 'drain-intent':
        assert result == 'ABORTED'
        assert int(manager.state()['MainPID']) == plan['old_binding']['pid']
    elif phase == 'candidate-start-intent':
        assert result == 'ROLLED_BACK'
    else:
        assert result in ('ACCEPTED', 'ALREADY_ACCEPTED')
    assert len(list((Path(plan['participant']) / 'drain').glob('claimed-exit.json'))) <= 1


def inject(plan, pid, name, code):
    path = Path(plan['participant']) / (name + '.py')
    path.write_text(code)
    sys.remote_exec(pid, str(path))


def write_after_install(plan, pid):
    receipt = Path(plan['participant']) / 'new-write'
    if receipt.exists():
        return
    code = ('import sys;from pathlib import Path\nframe=sys._getframe()\n'
            'while frame is not None:\n'
            ' if frame.f_code.co_name=="main" and "store" in frame.f_locals:break\n'
            ' frame=frame.f_back\n'
            'assert frame is not None\nstore=frame.f_locals["store"]\n'
            'with store.capture_gate.operation(),store._lock,store._db:\n'
            ' store._put("replacement-proof",{"after_install":True})\n'
            f'Path({str(receipt)!r}).touch()\n')
    inject(plan, pid, 'new-write', code)
    wait_for(receipt.exists)


def assert_preserved(data):
    code = ('import json,sqlite3,sys;from cryptography.hazmat.primitives.ciphers.aead import AESGCM;'
            'db=sqlite3.connect(sys.argv[1]);sealed=db.execute("SELECT sealed FROM records WHERE id=?",'
            '("replacement-proof",)).fetchone()[0];assert json.loads(AESGCM(b"s"*32).decrypt('
            'sealed[:12],sealed[12:],b"fc-chat-v1:replacement-proof"))=={"after_install":True}')
    subprocess.run([sys.executable, '-I', '-c', code, str(data / 'store/history.sqlite')],
                   check=True, capture_output=True, timeout=5)


def test_failed_acceptance_rolls_back_without_losing_new_committed_data(service, monkeypatch):
    manager, plan, root, data = service
    original = replace.Replacement.verify

    def reject(self, state):
        original(self, state)
        write_after_install(plan, int(state['MainPID']))
        raise ValueError('SYNTHETIC_READBACK_REJECTION')

    monkeypatch.setattr(replace.Replacement, 'verify', reject)
    assert eventually(root) == 'ROLLED_BACK'
    assert_preserved(data)
    assert replace.argv(int(manager.state()['MainPID'])) == plan['old_argv']


def test_failed_candidate_start_cancels_auto_restart_before_restoring_old_source(service):
    manager, plan, root, data = service
    raw = (root / 'support.conf').read_text()
    raw = '\n'.join('ExecStart=/usr/bin/false' if line.startswith('ExecStart=') and line != 'ExecStart='
                    else line for line in raw.split('\n')).encode()
    (root / 'support.conf').write_bytes(raw)
    plan['dropin_sha256'] = hashlib.sha256(raw).hexdigest()
    (root / 'plan.json').write_text(json.dumps(plan))
    assert eventually(root) == 'ROLLED_BACK'
    assert replace.argv(int(manager.state()['MainPID'])) == plan['old_argv']


def test_rollback_waits_for_native_write_beyond_old_deadline(service):
    manager, plan, root, data = service
    assert eventually(root) == 'ACCEPTED'
    pid = int(manager.state()['MainPID'])
    participant = Path(plan['participant'])
    entered, release = participant / 'writer-entered', participant / 'release'
    code = ('import os,time;from pathlib import Path;import RNS\noriginal=os.replace\n'
            'def replace(source,target,*args,**kwargs):\n'
            ' if str(source).endswith((b"d"*16).hex()+".out"):\n'
            f'  Path({str(entered)!r}).touch()\n'
            f'  while not Path({str(release)!r}).exists():time.sleep(.01)\n'
            ' return original(source,target,*args,**kwargs)\n'
            'os.replace=replace\n'
            'RNS.Identity.remember(b"p"*32,b"d"*16,RNS.Identity().get_public_key(),b"synthetic-probe")\n'
            'RNS.Identity._remember_ratchet(b"d"*16,b"r"*32)\n')
    try:
        inject(plan, pid, 'block-native', code)
        wait_for(entered.exists)
        assert replace.Replacement(root).run(recover=True) == 'WAITING_CANDIDATE_DRAIN'
        time.sleep(41)
        assert replace.Replacement(root).run() == 'WAITING_CANDIDATE_DRAIN'
        assert int(manager.state()['MainPID']) == pid
        assert Path(plan['dropin']).exists()
        release.touch()
        assert eventually(root) == 'ROLLED_BACK'
        code = ('import sys;from pathlib import Path;from RNS.vendor import umsgpack;'
                'assert umsgpack.unpackb(Path(sys.argv[1]).read_bytes())["ratchet"]==b"r"*32')
        subprocess.run([sys.executable, '-I', '-c', code,
                        str(data / 'runtime/storage/ratchets' / (b'd'*16).hex())],
                       check=True, capture_output=True, timeout=5)
    finally:
        release.touch()


@pytest.mark.parametrize('phase', ['old-exited', 'candidate-start-intent'])
def test_independent_systemd_controller_recovers_its_own_death(service, phase):
    manager, plan, root, data = service
    unit = 'fc-ha-support-guard-test-' + uuid.uuid4().hex + '.service'
    code = ('import os,sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);'
            'from scripts import control_ha_support_replace as replacement;record=replacement.Replacement.record\n'
            'def checkpoint(self,name,**value):\n'
            ' record(self,name,**value)\n'
            ' if name==sys.argv[3] and not (self.root/"controller-killed").exists():\n'
            '  (self.root/"controller-killed").touch();os._exit(71)\n'
            'replacement.Replacement.record=checkpoint\n'
            'result=replacement.Replacement(sys.argv[2]).run()\n'
            'raise SystemExit(75 if result.startswith("WAITING_") else 0)\n')
    launcher = root / 'guard.py'
    launcher.write_text(code)
    try:
        subprocess.run(['systemd-run', '--user', '--quiet', '--unit=' + unit,
                        '--property=Restart=on-failure', '--property=RestartSec=.2',
                        '--property=StartLimitIntervalSec=0', '--property=RemainAfterExit=yes',
                        sys.executable, '-I', str(launcher), str(root), str(root), phase],
                       check=True, capture_output=True, timeout=5)
        wait_for(lambda: (root / 'accepted.json').exists() or (root / 'rolled-back.json').exists(), seconds=18)
        assert (root / 'controller-killed').exists()
        assert int(manager.state()['MainPID']) > 1
    finally:
        subprocess.run(['systemctl', '--user', 'stop', unit], check=True, capture_output=True, timeout=5)
