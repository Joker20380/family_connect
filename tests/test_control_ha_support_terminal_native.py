import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from scripts import control_ha_support_replace as replace
from test_control_ha_legacy_support import installed, read, wait_for
from test_control_ha_support_replace import service


def test_systemd_terminal_failure_preserves_parked_old_process_without_restart(service):
    manager, plan, root, data = service
    replacement = replace.Replacement(root)
    assert not replacement.old_exit(commit=False)
    wait_for(lambda: (replacement.drain / 'ready.json').exists())
    injected = data / 'fault-applied'
    launcher = data / 'inject-final-failure.py'
    launcher.write_text('from pathlib import Path\nimport RNS\n'
                        'def fail():\n    raise ValueError("SYNTHETIC_FINAL_FAILURE")\n'
                        'RNS.Reticulum.exit_handler=staticmethod(fail)\n'
                        f'Path({str(injected)!r}).touch()\n')
    sys.remote_exec(plan['old_binding']['pid'], str(launcher))
    wait_for(injected.exists)
    unit = 'fc-ha-support-guard-test-' + uuid.uuid4().hex + '.service'
    path = Path(os.environ['XDG_RUNTIME_DIR']) / 'systemd/user' / unit
    path.write_text(replace.supervisor_unit(plan, os.environ['FC_TEST_SUPPORT_PYTHON']))
    try:
        manager.call('daemon-reload')
        manager.call('start', unit)
        wait_for(lambda: replacement.has('terminal-failure'))
        receipt = read(root / 'terminal-failure.json')
        assert receipt['reason'] == 'SYNTHETIC_FINAL_FAILURE'
        assert receipt['irreversible'] is True
        def state():
            result = subprocess.check_output([*manager.command, 'show', unit,
                                              '-pMainPID', '-pExecMainStatus', '-pNRestarts'], text=True)
            return dict(line.split('=', 1) for line in result.splitlines())
        wait_for(lambda: state()['MainPID'] == '0')
        assert state() == dict(MainPID='0', ExecMainStatus='78', NRestarts='0')
        assert replace.admission.binding(plan['old_binding']['pid']) == plan['old_binding']
        assert replacement.run(recover=True) == 'MANUAL_RECONCILIATION_REQUIRED'
        assert replacement.rollback() == 'MANUAL_RECONCILIATION_REQUIRED'
        assert not replacement.has('accepted') and not replacement.has('handoff-reserved')
        assert not replacement.has('rollback-intent') and not replacement.dropin.exists()
        assert not (replacement.drain / 'exited.json').exists()
        assert not (replacement.drain / 'restored.json').exists()
        assert all((Path(plan['gate']) / 'pending' / name).exists() for name in plan['pending'])
    finally:
        manager.call('stop', unit)
        path.unlink()
        manager.call('daemon-reload')
        subprocess.run([*manager.command, 'reset-failed', unit], capture_output=True)
