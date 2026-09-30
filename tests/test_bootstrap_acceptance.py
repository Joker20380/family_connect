import copy
import importlib.util
import io
import json
from pathlib import Path

import pytest


path = Path(__file__).resolve().parents[1] / 'pilot/android-telemost/bootstrap_acceptance.py'
spec = importlib.util.spec_from_file_location('bootstrap_acceptance', path)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def evidence():
    prepared = [{'event': 'bootstrap_cache_stored'}, {'event': 'android_exit', 'code': 0}]
    recovered = [{'event': name} for name in [
        'android_start', 'bootstrap_normal_control_unavailable', 'bootstrap_cache_loaded',
        'bootstrap_carrier_connected', 'bootstrap_family_auth', 'bootstrap_descriptor_received',
        'bootstrap_closed_before_dedicated', 'start', 'connected', 'family_auth', 'mux_open']]
    recovered[0].update(network='cellular', android='12', abi='arm64-v8a', model='Redmi Note 9 Pro')
    next(row for row in recovered if row['event'] == 'start')['room_method'] = 'cached bootstrap Telemost rendezvous'
    next(row for row in recovered if row['event'] == 'family_auth')['accepted'] = True
    recovered += [{'event': 'mux_https', 'passed': True, 'end_site_tls_verified': True, 'http_status': 200, 'stream_id': index} for index in range(4)]
    recovered += [{'event': 'mux_dns', 'passed': True, 'query_type': query, 'rcode': code, 'nxdomain': code == 3} for query, code in [(1, 0), (28, 0), (1, 3)]]
    recovered += [{'event': 'mux_result', 'status': 'PASS'}, {'event': 'android_exit', 'code': 0, 'cancelled': False}]
    gateway = [{'event': name} for name in ['bootstrap_seed_ready', 'bootstrap_family_auth', 'CREATING', 'CREATED', 'GATEWAY_JOINING', 'READY', 'CLIENT_ISSUED', 'bootstrap_handoff', 'family_auth', 'ACTIVE', 'dedicated_resources_closed']]
    return prepared, recovered, gateway


def test_acceptance_requires_complete_evidence():
    assert runner.validate(*evidence(), restarted=True)['bootstrap'] == 'PASS'
    with pytest.raises(RuntimeError):
        runner.validate(*evidence(), restarted=False)


@pytest.mark.parametrize('event', [
    'bootstrap_normal_control_unavailable', 'bootstrap_cache_loaded', 'bootstrap_carrier_connected',
    'bootstrap_family_auth', 'bootstrap_descriptor_received', 'bootstrap_closed_before_dedicated',
    'connected', 'family_auth', 'mux_result', 'android_exit'])
def test_missing_recovery_proof_is_not_pass(event):
    prepared, recovered, gateway = evidence()
    recovered = [row for row in recovered if row['event'] != event]
    with pytest.raises(RuntimeError):
        runner.validate(prepared, recovered, gateway, restarted=True)


@pytest.mark.parametrize('event', ['bootstrap_seed_ready', 'bootstrap_family_auth', 'READY', 'ACTIVE', 'dedicated_resources_closed'])
def test_gateway_proof_required(event):
    prepared, recovered, gateway = evidence()
    gateway = [row for row in gateway if row['event'] != event]
    with pytest.raises(RuntimeError):
        runner.validate(prepared, recovered, gateway, restarted=True)


def test_order_ordinary_control_manual_room_and_failed_dns_rejected():
    original = evidence()
    for fault in ['order', 'refresh', 'manual', 'dns', 'https', 'wifi']:
        prepared, recovered, gateway = copy.deepcopy(original)
        if fault == 'order': gateway[5], gateway[6] = gateway[6], gateway[5]
        if fault == 'refresh': recovered.append({'event': 'bootstrap_cache_stored'})
        if fault == 'manual': next(row for row in recovered if row['event'] == 'start')['room_method'] = 'operator-provided disposable room'
        if fault == 'dns': recovered = [row for row in recovered if row.get('query_type') != 28]
        if fault == 'https': next(row for row in recovered if row['event'] == 'mux_https')['passed'] = False
        if fault == 'wifi': recovered[0]['network'] = 'wifi'
        with pytest.raises(RuntimeError): runner.validate(prepared, recovered, gateway, restarted=True)


@pytest.mark.parametrize('outcome', ['closed_on_shutdown', 'missing_close', 'cleanup_failed'])
def test_main_validates_final_gateway_evidence_after_cleanup(tmp_path, monkeypatch, outcome):
    prepared, recovered, gateway = evidence()
    output = tmp_path / 'evidence'
    profiles = tmp_path / 'profiles'
    profiles.mkdir()
    for name in ['gateway.json', 'valid.json']:
        (profiles / name).write_text('{}')
    binary = tmp_path / 'broker'
    apk = tmp_path / 'diagnostic.apk'
    binary.write_bytes(b'test binary')
    apk.write_bytes(b'test apk')
    monkeypatch.setenv('YANDEX_TELEMOST_OAUTH_TOKEN', 'disposable-test-token')
    monkeypatch.delenv('FC_TELEMOST_ROOM', raising=False)
    monkeypatch.setattr('sys.argv', ['bootstrap_acceptance', '--adb', 'test-adb',
                                   '--binary', str(binary), '--apk', str(apk),
                                   '--family-dir', str(profiles), '--out', str(output)])
    state = {'mode': None, 'cleaned': False}

    def encode(rows):
        return ''.join(json.dumps(row) + '\n' for row in rows).encode()

    class Remote:
        def __init__(self, command, **options):
            self.stdin = io.BytesIO()
            self.log = options['stdout']
            self.log.write(encode(gateway[:-1]))
            self.log.flush()
            state['remote'] = self

        def poll(self):
            return None

        def wait(self, **options):
            assert state['cleaned']
            return 0

    def run(command, **options):
        if command[0] == 'test-adb':
            if command[-1] == 'wifi_on':
                return b'0\n'
            if command[-1] == 'mobile_data':
                return b'1\n'
            if 'cat > files/bootstrap.input' in command[-1]:
                state['mode'] = options['input'].decode()
            if 'head -c 4194305 files/evidence.jsonl' in command[-1]:
                return encode(prepared if state['mode'] == 'refresh' else recovered)
        elif 'shutil.rmtree(root)' in command[-1]:
            state['cleaned'] = True
            if outcome == 'cleanup_failed':
                raise RuntimeError('test cleanup failed')
            if outcome == 'closed_on_shutdown':
                state['remote'].log.write(encode(gateway[-1:]))
                state['remote'].log.flush()
        return b''

    monkeypatch.setattr(runner, 'run', run)
    monkeypatch.setattr(runner.subprocess, 'Popen', Remote)
    if outcome == 'closed_on_shutdown':
        runner.main()
        assert json.loads((output / 'evidence.json').read_text())['bootstrap'] == 'PASS'
    else:
        with pytest.raises(RuntimeError):
            runner.main()
        assert not (output / 'evidence.json').exists()
    assert state['cleaned']
    cleanup = json.loads((output / 'cleanup.json').read_text())
    assert cleanup['errors'] == (['gateway'] if outcome == 'cleanup_failed' else [])
