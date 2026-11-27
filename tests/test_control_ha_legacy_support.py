import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

import pytest

from scripts import control_ha_legacy_support as bridge


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/legacy_support.py'
INTERPRETER = os.environ.get('FC_TEST_SUPPORT_PYTHON', sys.executable)


def wait_for(predicate, seconds=8):
    deadline = time.monotonic() + seconds
    while not predicate():
        assert time.monotonic() < deadline, 'bounded fixture wait'
        time.sleep(.01)


def read(path):
    return json.loads(path.read_bytes())


@pytest.fixture
def installed(tmp_path):
    selected = os.environ.get('FC_TEST_SUPPORT_BASELINE')
    if selected is None:
        pytest.skip('requires exact installed source-only support baseline')
    expected = read(ROOT / 'deploy/support-chat/support-capture-v1.json')['baseline']
    content = bridge.sources(selected, expected)
    source = tmp_path / 'source'
    for name, raw in content.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return source


def install_collector_sources(baseline, *, mandatory=False):
    commit = 'b7f4cbd2b96750cb9c97eee61f27a9881d5b4bdb' if mandatory else '192343eb7433a98eb8ec3f92c0d0c78f8b49f845'
    pins = bridge.MANDATORY_COLLECTOR_SOURCES if mandatory else bridge.COLLECTOR_SOURCES
    for name, expected in pins.items():
        raw = subprocess.check_output(['git', 'show', commit + ':' + name], cwd=ROOT)
        assert bridge.digest(raw) == expected
        target = baseline / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)


def test_installed_collectors_require_explicit_exact_closed_source_variant(installed):
    expected = read(ROOT / 'deploy/support-chat/support-capture-v1.json')['baseline']
    original = dict(expected)
    install_collector_sources(installed)
    with pytest.raises(ValueError, match='SOURCE_CLOSURE'):
        bridge.sources(installed, expected)
    observed = bridge.sources(installed, expected, installed_collectors=True)
    assert set(observed) == expected.keys() | bridge.COLLECTOR_SOURCES.keys()
    assert expected == original
    assert all(bridge.digest(raw) == (expected | bridge.COLLECTOR_SOURCES)[name] for name, raw in observed.items())


@pytest.mark.parametrize('damage', ['extra', 'missing', 'changed-collector', 'changed-support', 'symlink', 'pins'])
@pytest.mark.parametrize('mandatory', [False, True])
def test_installed_collector_variant_never_accepts_unreviewed_source(installed, damage, mandatory):
    expected = read(ROOT / 'deploy/support-chat/support-capture-v1.json')['baseline']
    install_collector_sources(installed, mandatory=mandatory)
    collector = installed / 'provisioning/owner_capture.py'
    if damage == 'extra':
        (installed / 'extra.py').write_text('value = True\n')
    elif damage == 'missing':
        collector.unlink()
    elif damage == 'changed-collector':
        collector.write_text('value = True\n')
    elif damage == 'changed-support':
        other = next(name for name in expected if name not in bridge.COLLECTOR_SOURCES)
        (installed / other).write_text('value = True\n')
    elif damage == 'symlink':
        saved = collector.with_suffix('.saved')
        collector.rename(saved)
        collector.symlink_to(saved)
    else:
        expected['provisioning/support_bindings.py'] = bridge.COLLECTOR_SOURCES['provisioning/support_bindings.py']
    with pytest.raises(ValueError):
        bridge.sources(installed, expected, baseline_variant=(bridge.MANDATORY_COLLECTOR_BASELINE
                                                             if mandatory else bridge.COLLECTOR_BASELINE))


def test_mandatory_baseline_has_independent_meaning_and_exact_pins(installed):
    expected = read(ROOT / 'deploy/support-chat/support-capture-v1.json')['baseline']
    install_collector_sources(installed, mandatory=True)
    with pytest.raises(ValueError, match='SOURCE_PIN'):
        bridge.sources(installed, expected, installed_collectors=True)
    with pytest.raises(ValueError, match='BASELINE_VARIANT'):
        bridge.sources(installed, expected, baseline_variant='unreviewed')
    with pytest.raises(ValueError, match='BASELINE_VARIANT_CONFLICT'):
        bridge.sources(installed, expected, installed_collectors=True,
                       baseline_variant=bridge.MANDATORY_COLLECTOR_BASELINE)
    observed = bridge.sources(installed, expected, baseline_variant=bridge.MANDATORY_COLLECTOR_BASELINE)
    assert all(bridge.digest(raw) == (expected | bridge.MANDATORY_COLLECTOR_SOURCES)[name]
               for name, raw in observed.items())


@pytest.fixture
def running(tmp_path, installed):
    processes, peers = [], []

    def launch(mode='idle'):
        root = tmp_path / mode
        root.mkdir()
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen()
        peer = socket.create_connection(listener.getsockname())
        reader, _ = listener.accept()
        listener.close()
        peers.append(peer)
        with (root / 'output').open('wb') as output:
            process = subprocess.Popen([INTERPRETER, '-I', '-B', str(FIXTURE), str(root),
                                        str(installed), mode, str(reader.fileno())],
                                       pass_fds=(reader.fileno(),), stdout=output, stderr=subprocess.STDOUT,
                                       start_new_session=True)
        reader.close()
        processes.append((root, process))
        wait_for(lambda: (root / 'ready').exists() or process.poll() is not None)
        assert process.poll() is None, (root / 'output').read_text()
        return root, process, peer

    yield launch
    for peer in peers:
        peer.close()
    for root, process in processes:
        (root / 'release').touch()
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(8)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(5)


def invoke(root, installed, process, *, seconds=5, hold=0, change=None):
    output = root / 'probe'
    launcher = bridge.prepare(process.pid, installed, output, seconds=seconds, hold=hold)
    if change is not None:
        request = read(output / 'request.json')
        change(request)
        (output / 'request.json').write_text(json.dumps(request))
    sys.remote_exec(process.pid, str(launcher))
    wait_for(lambda: (output / 'entered.json').exists() or (output / 'error.json').exists())
    return output


def ipc(root):
    connection = socket.socket(socket.AF_UNIX)
    connection.settimeout(3)
    connection.connect(str(root / 'worker.sock'))
    connection.sendall(b'{"operation":"unknown"}\n')
    return connection


def assert_restored(root, process, output):
    wait_for(lambda: (output / 'restored.json').exists())
    assert read(output / 'restored.json')['delivery_online'] is True
    assert process.poll() is None
    with ipc(root) as connection:
        assert json.loads(connection.recv(16384))['ok'] is False


@pytest.mark.parametrize('mode', ['idle', 'module'])
def test_idle_pause_is_reversible_and_never_permits_capture(running, installed, mode):
    root, process, _ = running(mode)
    if mode == 'module':
        assert (root / 'module-shape').exists()
    before = bridge.binding(process.pid)
    output = invoke(root, installed, process, hold=.5)
    wait_for(lambda: (output / 'drained.json').exists())
    with ipc(root) as connection:
        connection.settimeout(.1)
        with pytest.raises(TimeoutError):
            connection.recv(1)
        connection.settimeout(3)
        assert json.loads(connection.recv(16384))['ok'] is False
    assert_restored(root, process, output)
    result = read(output / 'drained.json')
    assert result == dict(application_drained=True, runtime_drained=False, runtime_threads=4,
                          external_settlement_proven=False, capture_permitted=False)
    assert not (output / 'error.json').exists()
    assert bridge.binding(process.pid) == before


@pytest.mark.parametrize('mode', ['exchange', 'failure', 'child'])
def test_admitted_delivery_finishes_without_cancellation_or_lost_commit(running, installed, mode):
    root, process, _ = running(mode)
    wait_for(lambda: (root / 'exchange-entered').exists())
    output = invoke(root, installed, process)
    assert not (output / 'drained.json').exists()
    assert read(output / 'entered.json')['cancellation_requested'] is False
    (root / 'release').touch()
    assert_restored(root, process, output)
    assert (root / 'committed').exists() and (output / 'drained.json').exists()
    if mode == 'child':
        assert (root / 'child-finished').exists()
    process.terminate()
    assert process.wait(5) == 0
    code = ('import sys;sys.path.insert(0,sys.argv[1]);from messenger.store import Store;'
            'store=Store(sys.argv[2],b"s"*32,create=False);'
            'assert store._get("bridge-synthetic")=={"completed":True};store.close()')
    subprocess.run([INTERPRETER, '-I', '-B', '-c', code, str(installed), str(root / 'store')],
                   capture_output=True, check=True, timeout=5)


def test_delivery_timeout_restores_without_claiming_drain(running, installed):
    root, process, _ = running('exchange')
    wait_for(lambda: (root / 'exchange-entered').exists())
    output = invoke(root, installed, process, seconds=2)
    wait_for(lambda: (output / 'restored.json').exists())
    assert read(output / 'error.json')['reason'] == 'DELIVERY_UNFINISHED'
    assert not (output / 'drained.json').exists()
    (root / 'release').touch()
    wait_for(lambda: (root / 'committed').exists())
    assert_restored(root, process, output)


@pytest.mark.parametrize('release', [True, False])
def test_old_detached_reader_must_finish_before_application_drain(running, installed, release):
    root, process, peer = running('reader')
    wait_for(lambda: (root / 'reader-entered').exists())
    output = invoke(root, installed, process, seconds=2)
    assert not (output / 'drained.json').exists()
    if release:
        peer.close()
    assert_restored(root, process, output)
    assert (output / 'drained.json').exists() is release
    if not release:
        assert read(output / 'error.json')['reason'] == 'READERS_UNFINISHED'


@pytest.mark.parametrize('mode,reason', [('unknown-thread', 'UNKNOWN_THREAD'),
                                      ('changed-code', 'LOADED_CODE'),
                                      ('orphan-child', 'CHILDREN_UNFINISHED')])
def test_unrecognized_work_and_loaded_code_refuse(running, installed, mode, reason):
    root, process, _ = running(mode)
    output = invoke(root, installed, process)
    wait_for(lambda: (output / 'error.json').exists())
    assert read(output / 'error.json')['reason'] == reason
    assert not (output / 'drained.json').exists()
    if mode != 'changed-code':
        assert_restored(root, process, output)
    assert process.poll() is None


def test_inflight_serial_ipc_refuses_before_mutating_delivery(running, installed):
    root, process, _ = running('ipc')
    with ipc(root) as connection:
        wait_for(lambda: (root / 'ipc-entered').exists())
        output = invoke(root, installed, process)
        assert read(output / 'error.json')['reason'] == 'PARTIAL_ACCEPT_REFUSED'
        assert not (output / 'entered.json').exists() and not (output / 'restored.json').exists()
        (root / 'release').touch()
        assert json.loads(connection.recv(16384))['ok'] is False


@pytest.mark.parametrize('mutation,reason', [
    ('expired', 'EXPIRED_REQUEST'), ('binding', 'PROCESS_BINDING'), ('source', 'BRIDGE_PIN'),
    ('baseline', 'BASELINE_PIN'), ('unknown', 'REQUEST_FIELDS'), ('nan', 'EXPIRED_REQUEST')])
def test_request_drift_is_rejected_without_mutating_service(running, installed, mutation, reason):
    root, process, _ = running()

    def change(value):
        if mutation == 'expired':
            value['deadline'] = 0
        elif mutation == 'binding':
            value['binding']['start'] = 'wrong'
        elif mutation == 'source':
            value['source_sha256'] = '0' * 64
        elif mutation == 'baseline':
            value['baseline']['provisioning/support_worker.py'] = '0' * 64
        elif mutation == 'nan':
            value['hold'] = float('nan')
        else:
            value['stop'] = True

    output = invoke(root, installed, process, change=change)
    assert read(output / 'error.json')['reason'] == reason
    assert not (output / 'entered.json').exists()
    assert process.poll() is None


def test_replay_and_existing_output_refuse(running, installed):
    root, process, _ = running()
    output = invoke(root, installed, process)
    assert_restored(root, process, output)
    first = read(output / 'restored.json')
    sys.remote_exec(process.pid, str(output / 'invoke.py'))
    wait_for(lambda: (output / 'error.json').exists())
    assert read(output / 'restored.json') == first
    with pytest.raises(FileExistsError):
        bridge.prepare(process.pid, installed, output)


def test_controller_exit_does_not_leave_admission_paused(running, installed):
    root, process, _ = running()
    output = root / 'probe'
    launcher = bridge.prepare(process.pid, installed, output, hold=.5)
    code = 'import sys;sys.remote_exec(int(sys.argv[1]),sys.argv[2])'
    subprocess.run([sys.executable, '-I', '-c', code, str(process.pid), str(launcher)],
                   capture_output=True, check=True, timeout=3)
    assert_restored(root, process, output)
    assert (output / 'drained.json').exists()


def test_receipt_failure_restores_admission(running, installed):
    root, process, _ = running()
    output = root / 'probe'
    launcher = bridge.prepare(process.pid, installed, output)
    (output / 'drained.json').write_text('preserved')
    sys.remote_exec(process.pid, str(launcher))
    assert_restored(root, process, output)
    assert read(output / 'error.json')['reason'] == 'BRIDGE_FAILURE'
    assert (output / 'drained.json').read_text() == 'preserved'


def test_partial_ipc_header_refuses_without_accepting_more_work(running, installed):
    root, process, _ = running()
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(3)
        connection.connect(str(root / 'worker.sock'))
        connection.sendall(b'{"operation":')
        time.sleep(.1)
        output = invoke(root, installed, process, seconds=8)
        assert read(output / 'error.json')['reason'] == 'PARTIAL_ACCEPT_REFUSED'
        assert not (output / 'entered.json').exists()
        assert json.loads(connection.recv(16384))['ok'] is False
    with ipc(root) as connection:
        assert json.loads(connection.recv(16384))['ok'] is False


@pytest.mark.parametrize('mutation,reason', [('bytes', 'SOURCE_PIN'), ('extra', 'SOURCE_CLOSURE'),
                                           ('symlink', 'INPUT_SYMLINK')])
def test_installed_sources_must_still_match_at_execution(running, installed, mutation, reason):
    root, process, _ = running()
    output = root / 'probe'
    launcher = bridge.prepare(process.pid, installed, output)
    source = installed / 'provisioning/support_worker.py'
    if mutation == 'bytes':
        source.write_bytes(source.read_bytes() + b'\n')
    elif mutation == 'extra':
        (installed / 'unexpected.py').write_text('pass\n')
    else:
        source.rename(source.with_suffix('.saved'))
        source.symlink_to(source.with_suffix('.saved'))
    sys.remote_exec(process.pid, str(launcher))
    wait_for(lambda: (output / 'error.json').exists())
    assert read(output / 'error.json')['reason'] == reason
    assert not (output / 'entered.json').exists()


@pytest.mark.parametrize('seconds,hold', [(True, 0), (float('nan'), 0), (16, 0), (1, 1), (1, -1), (1, True)])
def test_invalid_budget_refuses_before_staging(tmp_path, seconds, hold):
    with pytest.raises(ValueError, match='REQUEST_TIME'):
        bridge.prepare(os.getpid(), tmp_path, tmp_path / 'probe', seconds=seconds, hold=hold)
    assert not (tmp_path / 'probe').exists()


def test_module_main_globals_must_match_running_frame(running, installed):
    root, process, _ = running('module-globals')
    output = invoke(root, installed, process)
    assert read(output / 'error.json')['reason'] == 'RUNTIME_BINDING'
    assert not (output / 'entered.json').exists()
    with ipc(root) as connection:
        assert json.loads(connection.recv(16384))['ok'] is False


def test_inactive_import_with_identical_code_does_not_replace_active_main(running, installed):
    root, process, _ = running('module-ambiguous')
    output = invoke(root, installed, process)
    assert_restored(root, process, output)
    assert not (output / 'error.json').exists()


@pytest.mark.parametrize('missing', [False, True])
def test_namespace_check_rejects_different_or_missing_paths(tmp_path, monkeypatch, missing):
    actual = Path.stat
    target = Path('/proc') / str(os.getpid()) / 'root' / tmp_path.relative_to('/')
    other = tmp_path / 'other'
    other.mkdir()

    def stat_path(path, *args, **kwargs):
        if path == target:
            if missing:
                raise FileNotFoundError()
            return actual(other)
        return actual(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'stat', stat_path)
    with pytest.raises(ValueError, match='OUTPUT_NAMESPACE'):
        bridge.visible_to(os.getpid(), tmp_path)


@pytest.mark.parametrize('changed', ['namespace', 'process'])
def test_prepare_rechecks_staged_files_and_process(installed, tmp_path, monkeypatch, changed):
    observed = bridge.binding(os.getpid())
    real_write = bridge.write

    def write(path, value):
        real_write(path, value)
        if path.name == 'prepared.json':
            if changed == 'process':
                monkeypatch.setattr(bridge, 'binding', lambda pid: dict(observed, start='changed'))
            else:
                monkeypatch.setattr(bridge, 'visible_to', lambda pid, path: bridge.require(False, 'OUTPUT_NAMESPACE'))

    monkeypatch.setattr(bridge, 'write', write)
    with pytest.raises(ValueError, match='PID_CHANGED' if changed == 'process' else 'OUTPUT_NAMESPACE'):
        bridge.prepare(os.getpid(), installed, tmp_path / 'probe')
