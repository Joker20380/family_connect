import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import sys
import time
import uuid

import pytest

from scripts import control_ha_support_replace as replace
from test_control_ha_legacy_support import wait_for
from test_control_ha_support_replace import assert_preserved


REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def system_service():
    if os.geteuid() != 0 or os.environ.get('FC_TEST_SUPPORT_SYSTEM') != '1':
        pytest.skip('requires explicit root qualification of synthetic system services')
    account = pwd.getpwnam('fc-support')
    unit = 'fc-ha-support-replace-fixture-' + uuid.uuid4().hex + '.service'
    root = Path('/run') / unit.removesuffix('.service')
    root.mkdir(mode=0o755)
    source, data = root / 'source', root / 'data'
    data.mkdir(mode=0o700)
    os.chown(data, account.pw_uid, account.pw_gid)
    baseline = json.loads((REPO / replace.SOURCES[-1]).read_bytes())['baseline']
    for name, content in replace.admission.sources('/opt/family-connect-support/app', baseline).items():
        path = source / name
        path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        path.write_bytes(content)
        path.chmod(0o644)
    fixture = root / 'fixture.py'
    shutil.copyfile(REPO / 'tests/fixtures/support_replacement.py', fixture)
    fixture.chmod(0o644)
    interpreter = os.environ['FC_TEST_SUPPORT_PYTHON']
    initialize = ('import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);'
                  'from messenger.store import Store;root=Path(sys.argv[2]);'
                  'store=Store(root/"store",b"s"*32,create=True);'
                  'print(store.chat_identity().get_public_key().hex());store.close();'
                  '(root/"key").write_bytes(b"s"*32);(root/"key").chmod(0o600)')
    public = subprocess.check_output([interpreter, '-I', '-c', initialize, str(source), str(data)],
                                     user=account.pw_uid, group=account.pw_gid, text=True).strip()
    options = ['--store', str(data / 'store'), '--key', str(data / 'key'), '--sender-public', public,
               '--snapshot', str(data / 'unused-snapshot'), '--runtime', str(data / 'runtime'),
               '--socket', str(data / 'worker.sock'), '--snapshot-uid', str(account.pw_uid)]
    path = Path('/run/systemd/system') / unit
    path.write_text('[Service]\nType=simple\nRestart=on-failure\nRestartSec=5\n'
                    'User=fc-support\nGroup=fc-support-ipc\nPrivateTmp=yes\nProtectSystem=strict\n'
                    'ProtectHome=yes\nNoNewPrivileges=yes\nUMask=0077\nReadWritePaths=' + str(data) + '\n'
                    'TimeoutStopSec=40\nKillMode=control-group\nSendSIGKILL=yes\n'
                    'ExecStart=' + ' '.join([interpreter, '-I', '-B', str(fixture), str(source), *options]) + '\n')
    path.chmod(0o644)
    guard = unit.replace('fixture-', 'guard-')
    guard_path = Path('/run/systemd/system') / guard
    manager = replace.Manager(unit)
    try:
        manager.call('daemon-reload')
        manager.call('start', unit)
        wait_for(lambda: (data / 'worker.sock').exists())
        plan = replace.prepare(manager, source, os.environ['FC_TEST_SUPPORT_ARCHIVE'], root / 'controller',
                               data / 'participant', root / 'support.pyz', seconds=15)
        guard_path.write_text(replace.supervisor_unit(plan, interpreter))
        guard_path.chmod(0o644)
        yield manager, plan, root, data, guard_path
    finally:
        if guard_path.exists():
            manager.call('stop', '--no-block', guard)
        (data / 'release').touch()
        manager.call('stop', '--no-block', unit)
        deadline = time.monotonic() + 5
        while manager.state()['MainPID'] != '0' and time.monotonic() < deadline:
            time.sleep(.05)
        if manager.state()['MainPID'] != '0':
            manager.call('kill', '--signal=SIGKILL', unit)
        path.unlink()
        guard_path.unlink(missing_ok=True)
        shutil.rmtree(Path(str(path) + '.d'), ignore_errors=True)
        manager.call('daemon-reload')
        subprocess.run(['systemctl', 'reset-failed', guard, unit], capture_output=True)


@pytest.mark.parametrize('death', [None, 'old-exited'])
def test_independent_root_supervisor_real_uid_sandbox_and_current_data_rollback(system_service, death):
    manager, plan, root, data, guard_path = system_service
    controller = Path(plan['root'])
    if death:
        runner = controller / 'runner.py'
        raw = runner.read_text().replace('from scripts.control_ha_support_replace import main\nmain()',
            'import os\nfrom scripts.control_ha_support_replace import Replacement,main\n'
            'record=Replacement.record\n'
            'def checkpoint(self,name,**value):\n'
            ' record(self,name,**value)\n'
            ' if name=="old-exited" and not (self.root/"death-once").exists():\n'
            '  (self.root/"death-once").touch();os._exit(71)\n'
            'Replacement.record=checkpoint\nmain()')
        runner.write_text(raw)
        plan['sources']['runner.py'] = replace.digest(runner)
        (controller / 'plan.json').write_text(json.dumps(plan))
    manager.call('daemon-reload')
    manager.call('start', guard_path.name)
    wait_for(lambda: (controller / 'accepted.json').exists(), seconds=35)
    accepted = json.loads((controller / 'accepted.json').read_bytes())
    exit_state = json.loads((controller / 'old-exited.json').read_bytes())['state']
    assert exit_state['RemainAfterExit'] == 'no'
    assert exit_state['ExecMainCode'] == '1' and exit_state['ExecMainStatus'] == '0'
    assert accepted['capture_permitted'] is False
    if death:
        assert (controller / 'death-once').exists()
    pid = int(manager.state()['MainPID'])
    participant = Path(plan['participant'])
    receipt = participant / 'new-write-done'
    invoke = participant / 'new-write.py'
    invoke.write_text('import sys\nfrom pathlib import Path\nframe=sys._getframe()\n'
                      'while frame is not None:\n'
                      ' if frame.f_code.co_name=="main" and "store" in frame.f_locals:break\n'
                      ' frame=frame.f_back\nassert frame is not None\nstore=frame.f_locals["store"]\n'
                      'with store.capture_gate.operation(),store._lock,store._db:\n'
                      ' store._put("replacement-proof",{"after_install":True})\n'
                      f'Path({str(receipt)!r}).touch()\n')
    os.chown(invoke, plan['uid'], plan['gid'])
    invoke.chmod(0o600)
    sys.remote_exec(pid, str(invoke))
    wait_for(receipt.exists)
    manager.call('stop', guard_path.name)
    guard_path.write_text(replace.supervisor_unit(plan, os.environ['FC_TEST_SUPPORT_PYTHON']).rstrip() + ' --recover\n')
    manager.call('daemon-reload')
    manager.call('start', guard_path.name)
    wait_for(lambda: (controller / 'rolled-back.json').exists(), seconds=20)
    assert_preserved(data)
    assert replace.argv(int(manager.state()['MainPID'])) == plan['old_argv']
    assert not Path(plan['dropin']).exists()
    assert all((Path(plan['gate']) / 'pending' / name).exists() for name in plan['pending'])
