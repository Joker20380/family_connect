"""Explicit process boundary for protected Android state, on the CI emulator only."""
import json
import os
from pathlib import Path
import re
import subprocess


def check(root):
    assert os.environ.get('GITHUB_ACTIONS') == 'true', 'CI emulator required'
    assert subprocess.check_output(['adb', 'shell', 'getprop', 'ro.kernel.qemu'], text=True).strip() == '1'
    package = 'com.familyconnect.app'
    pids = []
    for phase in ('prepare', 'recover'):
        subprocess.run(['adb', 'shell', 'am', 'force-stop', package], check=True, timeout=20)
        result = subprocess.run(['adb', 'shell', 'am', 'instrument', '-w', '-r',
            '-e', 'class', package+'.ControlStorageRuntimeTest',
            '-e', 'fc_disposable', 'true', '-e', 'fc_storage_phase', phase,
            package+'.test/androidx.test.runner.AndroidJUnitRunner'],
            capture_output=True, text=True, timeout=120)
        (root/('android-control-storage-'+phase+'.log')).write_text(result.stdout+result.stderr)
        result.check_returncode()
        assert re.search(r'OK \(1 test\)', result.stdout), 'Storage phase failed: '+phase
        assert 'FAILURES' not in result.stdout and 'INSTRUMENTATION_FAILED' not in result.stdout
        ids = re.findall(r'fc_storage_pid=(\d+)', result.stdout)
        assert len(ids) == 1, 'Missing storage process evidence'
        pids.append(int(ids[0]))
    assert pids[0] != pids[1], 'Storage recovery must execute in a new Android process'
    receipt = dict(passed=True, phases=['prepare', 'force-stop', 'recover'],
                   distinct_processes=True, identity_reload=True, atomic_interruption=True,
                   durable_ack=True, clock_regression_refused=True, corrupt_storage_refused=True,
                   vpn_apply_tested=False, live_relay_tested=False)
    (root/'android-control-storage-result.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('Android Keystore/AtomicFile/outbox process restart passed', flush=True)


if __name__ == '__main__':
    check(Path(__file__).resolve().parents[2])
