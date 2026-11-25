import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from scripts import control_ha_legacy_support as admission
from scripts import control_ha_support_quiesce as probe
from test_control_ha_legacy_support import installed, running, read, wait_for, ipc, assert_restored


ROOT = Path(__file__).resolve().parents[1]


def invoke(root, installed, process, *, seconds=8, hold=.25, change=None):
    output = root / 'quiesce'
    launcher = probe.prepare(process.pid, installed, output, seconds=seconds, hold=hold)
    if change is not None:
        request = read(output / 'request.json')
        change(request)
        (output / 'request.json').write_text(json.dumps(request))
    sys.remote_exec(process.pid, str(launcher))
    wait_for(lambda: (output / 'entered.json').exists() or (output / 'error.json').exists())
    return output


def check_hooks(root, process):
    receipt = root / 'hooks.json'
    code = (f'import importlib,json,threading,time;from pathlib import Path\n'
            f'assert time.monotonic() < {time.monotonic() + 5!r}\n'
            'import RNS\n'
            'assert importlib.import_module("RNS.Reticulum").time is time\n'
            'assert importlib.import_module("RNS.Transport").time is time\n'
            'assert importlib.import_module("RNS.Transport").sleep is time.sleep\n'
            'assert "wait" not in vars(RNS.Transport.inbound_queues._cond)\n'
            'assert RNS.log.__module__=="RNS"\n'
            'assert threading.excepthook is threading.__excepthook__\n'
            f'Path({str(receipt)!r}).write_text(json.dumps(dict(threads=len(threading.enumerate()))))\n')
    launcher = root / 'check-hooks.py'
    launcher.write_text(code)
    sys.remote_exec(process.pid, str(launcher))
    wait_for(receipt.exists)
    assert read(receipt)['threads'] == 6


def test_running_jobs_and_queue_pause_together_then_resume_same_process(running, installed):
    root, process, _ = running('rns-idle')
    binding = admission.binding(process.pid)
    output = invoke(root, installed, process, hold=.5)
    wait_for(lambda: (output / 'quiesced.json').exists())
    with ipc(root) as connection:
        connection.settimeout(.1)
        with pytest.raises(TimeoutError):
            connection.recv(1)
        connection.settimeout(3)
        assert json.loads(connection.recv(16384))['ok'] is False
    assert_restored(root, process, output)
    assert not (output / 'error.json').exists()
    assert read(output / 'quiesced.json') == dict(application_drained=True, rns_idle_paused=True,
        producers=3, queues=1, exit_persisted=False, external_settlement_proven=False, capture_permitted=False)
    assert admission.binding(process.pid) == binding
    check_hooks(root, process)


@pytest.mark.parametrize('mode', ['rns-queue', 'rns-descendant', 'rns-async'])
def test_pending_queue_and_native_async_writes_are_not_interrupted(running, installed, mode):
    root, process, _ = running(mode)
    wait_for(lambda: (root / 'writer-entered').exists())
    output = invoke(root, installed, process)
    time.sleep(.3)
    assert not (output / 'quiesced.json').exists()
    (root / 'release').touch()
    assert_restored(root, process, output)
    assert (output / 'quiesced.json').exists() and not (output / 'error.json').exists()
    if mode == 'rns-descendant':
        assert (root / 'packet-second').exists()
    command = ('from pathlib import Path;from RNS.vendor import umsgpack;import sys;'
               'record=umsgpack.unpackb(Path(sys.argv[1]).read_bytes());assert record["ratchet"]==b"r"*32')
    interpreter = os.environ['FC_TEST_SUPPORT_PYTHON']
    subprocess.run([interpreter, '-I', '-c', command,
                    str(root / 'runtime/storage/ratchets' / (b'd' * 16).hex())],
                   check=True, capture_output=True, timeout=5)
    check_hooks(root, process)


@pytest.mark.parametrize('mode', ['rns-queue', 'rns-async', 'rns-unknown', 'rns-sleep'])
def test_deadline_restores_hooks_without_aborting_work_or_waking_old_sleep(running, installed, mode):
    root, process, _ = running(mode)
    output = invoke(root, installed, process, seconds=2.2, hold=0)
    assert_restored(root, process, output)
    assert not (output / 'quiesced.json').exists()
    assert read(output / 'error.json')['reason'] == 'PROBE_EXPIRED'
    (root / 'release').touch()
    time.sleep(.3)
    check_hooks(root, process)


def test_logged_native_write_failure_refuses_success_but_restores_service(running, installed):
    root, process, _ = running('rns-uncertain')
    wait_for(lambda: (root / 'writer-entered').exists())
    output = invoke(root, installed, process)
    (root / 'release').touch()
    assert_restored(root, process, output)
    assert read(output / 'error.json')['reason'] == 'RNS_WORK_UNCERTAIN'
    assert not (output / 'quiesced.json').exists()
    check_hooks(root, process)


def test_admitted_delivery_commits_before_runtime_pause_without_cancellation(running, installed):
    root, process, _ = running('rns-exchange')
    wait_for(lambda: (root / 'exchange-entered').exists())
    output = invoke(root, installed, process)
    time.sleep(.2)
    assert not (output / 'quiesced.json').exists()
    (root / 'release').touch()
    assert_restored(root, process, output)
    assert (output / 'quiesced.json').exists() and (root / 'committed').exists()
    assert not (output / 'error.json').exists()
    check_hooks(root, process)


def test_receipt_failure_restores_application_and_runtime(running, installed):
    root, process, _ = running('rns-idle')
    output = invoke(root, installed, process,
                    change=lambda _: (root / 'quiesce/quiesced.json').mkdir())
    assert_restored(root, process, output)
    assert read(output / 'error.json')['reason'] == 'PROBE_FAILURE'
    check_hooks(root, process)


def test_source_code_drift_refuses_before_runtime_hooks(running, installed):
    root, process, _ = running('rns-drift')
    output = invoke(root, installed, process)
    assert_restored(root, process, output)
    assert read(output / 'error.json')['reason'] == 'RNS_LOADED_CODE'
    assert not (output / 'quiesced.json').exists()
    check_hooks(root, process)


@pytest.mark.parametrize('change', [lambda request: request.update(deadline=time.monotonic() - 1),
                                   lambda request: request['binding'].update(start='different'),
                                   lambda request: request['hashes'].update({'runtime.py': '0' * 64})])
def test_untrusted_request_refused_before_application_pause(running, installed, change):
    root, process, _ = running('rns-idle')
    output = invoke(root, installed, process, change=change)
    assert (output / 'error.json').exists() and not (output / 'entered.json').exists()
    check_hooks(root, process)


@pytest.mark.parametrize('seconds,hold', [(0, 0), (361, 0), (float('nan'), 0), (5, 11), (1, 1)])
def test_bad_budget_refused_before_staging(installed, tmp_path, seconds, hold):
    with pytest.raises(ValueError, match='REQUEST_TIME'):
        probe.prepare(os.getpid(), installed, tmp_path / 'probe', seconds=seconds, hold=hold)
    assert not (tmp_path / 'probe').exists()


def test_controller_death_still_restores_admission_and_all_runtime_hooks(running, installed):
    root, process, _ = running('rns-idle')
    output = root / 'quiesce'
    controller = subprocess.Popen([sys.executable, '-m', 'scripts.control_ha_support_quiesce',
        '--pid', str(process.pid), '--root', str(installed), '--output', str(output),
        '--seconds', '4', '--hold', '1'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        wait_for(lambda: (output / 'quiesced.json').exists() or controller.poll() is not None)
        assert controller.poll() is None, controller.stderr.read().decode() if controller.poll() is not None else ''
        controller.kill()
        controller.wait(5)
        assert_restored(root, process, output)
        assert not (output / 'error.json').exists()
        check_hooks(root, process)
    finally:
        if controller.poll() is None:
            controller.kill()
        controller.wait(5)
        controller.stderr.close()


def test_independent_controller_verifies_process_sources_and_restoration(running, installed):
    root, process, _ = running('rns-idle')
    output = root / 'quiesce'
    result = subprocess.run([sys.executable, '-m', 'scripts.control_ha_support_quiesce',
        '--pid', str(process.pid), '--root', str(installed), '--output', str(output),
        '--seconds', '8', '--hold', '.25'], cwd=ROOT, capture_output=True, text=True, timeout=12)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'REVERSIBLE_RNS_IDLE_PROBE_PASS_NO_CAPTURE'
    assert read(output / 'completed.json') == dict(binding=admission.binding(process.pid),
                    same_process_and_sources=True, capture_permitted=False)
    assert_restored(root, process, output)
    check_hooks(root, process)
