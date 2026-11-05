import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from mesh_core_stand import CoreStand
from fixtures.mesh_supervisor import request
from online_package_stand import private_file
from scripts import package_online_renewal as package
from test_online_runtime_package import core_driver, online_package
from cryptography import x509
from device_identity.device import DeviceIdentity
from test_friends_access import proof


@pytest.mark.parametrize('raw', [
    b'{"schema":1,"operation":"CREDENTIAL_RENEWAL_RPC","request":{}}',
    b'{"schema":true,"operation":"READ_ONLY_SECURITY_SNAPSHOT"}',
    b'{"schema":1,"schema":1,"operation":"READ_ONLY_SECURITY_SNAPSHOT"}',
    b'{"schema":1,"operation":"READ_ONLY_SECURITY_SNAPSHOT","profile":"override"}',
])
def test_disposable_snapshot_route_is_read_only(tmp_path, raw):
    snapshot = os.environ.get('FC_TEST_SNAPSHOT')
    if not snapshot:
        pytest.skip('explicit frozen read-only snapshot capsule required')
    result = subprocess.run([sys.executable, '-I', '-B', str(package.ROOT/'tests/fixtures/mesh_snapshot.py'),
        snapshot, str(tmp_path/'nonexistent-configuration')], input=raw, capture_output=True,
        env=dict(os.environ, SSH_ORIGINAL_COMMAND='restricted-sync'), timeout=10)
    assert result.returncode != 0 and b'READ_ONLY_SNAPSHOT_REQUIRED' in result.stderr
    assert not list(tmp_path.iterdir())


def test_seed_directory_publisher_preserves_credentials_and_processes(online_package, core_driver, tmp_path):
    from mesh_core_directory import publish_seed_directories
    snapshot = os.environ.get('FC_TEST_SNAPSHOT')
    if not snapshot:
        pytest.skip('explicit frozen read-only snapshot capsule required')
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    try:
        stand.start()
        profiles = {slot: (tmp_path/(slot+'-profile/gateway.json')).read_bytes() for slot in ('NL', 'NL2')}
        processes = {slot: request(dict(command='show', unit='test-'+slot+'.service'))['state'] for slot in profiles}
        receipt = publish_seed_directories(stand, Path(snapshot))
        assert receipt['result']['files_changed'] == 2
        assert receipt['result']['crl_publications'] == receipt['result']['restarts'] == 0
        assert not (tmp_path/'coordinator/transaction.json').exists()
        for slot in profiles:
            assert (tmp_path/(slot+'-profile/gateway.json')).read_bytes() == profiles[slot]
            assert request(dict(command='show', unit='test-'+slot+'.service'))['state'] == processes[slot]
            client = stand.client(slot, 3)
            assert client.wait(timeout=15) == 0
            samples = [json.loads(line) for line in (tmp_path/(slot+'-client.log')).read_text().splitlines()]
            assert any(value.get('tcp') and value.get('dns') and value.get('verified_https') for value in samples)
    finally:
        stand.close()


@pytest.mark.parametrize('field', ['source_commit', 'native_sources', 'scope', 'entrypoint', 'executable_sha256'])
def test_isolated_binding_rejects_foreign_artifacts(online_package, core_driver, tmp_path, field):
    manifest = json.loads((online_package[3]/'source-manifest.json').read_bytes())
    artifact = dict(schema=1, scope='isolated-core-not-production', source_commit=manifest['source_commit'],
        native_sources=manifest['native_sources'], entrypoint='carrier/internal/qualification/cmd/mesh-runtime',
        executable_sha256=package.digest(core_driver.read_bytes()))
    artifact[field] = {} if field == 'native_sources' else 'incorrect'
    path = private_file(tmp_path/'artifact.json', package.encode(artifact))
    probe = ('import sys,json;from pathlib import Path;sys.path.insert(0,sys.argv[1]);'
        'from online_runtime import runtime_binding;'
        'runtime_binding(json.loads(Path(sys.argv[2]).read_bytes()),sys.argv[3])')
    result = subprocess.run([sys.executable, '-I', '-B', '-c', probe, str(online_package[3]/'renewal'),
        str(online_package[3]/'source-manifest.json'), str(path)], capture_output=True, timeout=10)
    assert result.returncode != 0 and b'ONLINE_ISOLATED_ARTIFACT_BINDING' in result.stderr


def test_production_gateway_has_no_local_provider_mode(online_package):
    binary = online_package[3]/'gateway'
    for arguments in (['-mode', 'relay'], ['-seed-continuous'], ['-seed-rotate-after', '2h']):
        result = subprocess.run([str(binary), *arguments], env=dict(os.environ, FC_LOCAL_CORE='1'),
            capture_output=True, timeout=5)
        assert result.returncode != 0 and b'flag provided but not defined' in result.stderr
    dependencies = subprocess.check_output([os.environ['FC_ONLINE_GO'], 'list', '-deps', './cmd/bootstrap-broker'],
        cwd=online_package[1]/'carrier', text=True)
    assert '/internal/qualification' not in dependencies


@pytest.mark.parametrize('duration,rotation,continuous', [('1h', None, False), ('8h', '2h', True)])
def test_two_gateway_seed_and_verified_traffic_preflight(online_package, core_driver, tmp_path, duration, rotation, continuous):
    assert os.geteuid() == 0 and Path('/.dockerenv').exists() and tmp_path.is_relative_to('/run')
    _, _, archive, extracted, receipt = online_package
    stand = CoreStand(tmp_path, extracted, core_driver, duration=duration, rotation=rotation, continuous=continuous)
    started = time.monotonic()
    try:
        stand.start()
        code, capabilities = stand.run('inspect')
        assert code == 0, capabilities
        code, commit = stand.run('online')
        assert code == 0 and commit['result'] == 'COMMITTED', commit
        clients = {slot: stand.client(slot, 20) for slot in ('NL', 'NL2')}
        for slot, client in clients.items():
            assert client.wait(timeout=65) == 0, (tmp_path/(slot+'-client.log')).read_text()
        observations = {}
        for slot in clients:
            events = [json.loads(line) for line in (tmp_path/(slot+'-client.log')).read_text().splitlines()]
            connected = next(value for value in events if value['event'] == 'connected')
            traffic = [value for value in events if value['event'] == 'traffic']
            assert len(traffic) >= 20 and events[-1]['event'] == 'finished'
            assert all(value['session'] == connected['session'] and value['original']['ID'] == connected['stream']
                and value['tcp'] and value['dns'] and value['verified_https'] for value in traffic)
            assert traffic[-1]['original']['Received'] > traffic[0]['original']['Received'] > 0
            observations[slot] = dict(first=traffic[0], last=traffic[-1], samples=len(traffic))
        code, after = stand.run('inspect')
        assert code == 0, after
        assert time.monotonic()-started > 20
        evidence = dict(scope='isolated-core-preflight-not-G1-G4-acceptance', package=receipt,
            archive_sha256=package.digest(archive.read_bytes()), driver_sha256=package.digest(core_driver.read_bytes()),
            capabilities=capabilities, commit=commit, traffic=observations, echo_connections=stand.accepted)
    finally:
        stand.close()
    assert not any((tmp_path/(slot+'-config/reader.sock')).exists() for slot in ('NL', 'NL2'))
    evidence['cleanup'] = 'processes-waited-and-reader-sockets-absent'
    destination = os.environ.get('FC_CORE_EVIDENCE')
    if destination:
        root = Path(destination)/('preflight-'+duration)
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        private_file(root/'preflight.json', package.encode(evidence))
        for path in tmp_path.glob('*.log'):
            private_file(root/path.name, path.read_bytes())


def test_gateway_restart_after_commit_needs_approved_emergency(online_package, core_driver, tmp_path):
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    process = None
    results = []
    try:
        stand.start()
        process = subprocess.Popen(stand.command('online'), cwd=tmp_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        journal = tmp_path/'coordinator/transaction.json'
        deadline = time.monotonic()+40
        while True:
            record = json.loads(journal.read_bytes()) if journal.exists() else {}
            if record.get('state') == 'ONLINE_COMMIT_DECIDED':
                process.kill()
                process.wait(timeout=5)
                break
            assert process.poll() is None and time.monotonic() < deadline, record.get('state')
            time.sleep(.001)
        origin = json.loads(journal.read_bytes())
        before = request(dict(command='show', unit='test-NL2.service'))['state']
        request(dict(command='kill', unit='test-NL2.service'))
        assert not (tmp_path/'NL2-config/reader.sock').exists()
        after = request(dict(command='start', unit='test-NL2.service'))['state']
        assert before['MainPID'] != after['MainPID'] and before['InvocationID'] != after['InvocationID']
        deadline = time.monotonic()+5
        while not (tmp_path/'NL2-config/reader.sock').exists():
            assert time.monotonic() < deadline
            time.sleep(.02)
        code, result = stand.run('resume')
        results.append(result)
        assert code == 75 and result['result'] == 'ONLINE_EMERGENCY_REQUIRED', result
        emergency_fence = json.loads(journal.read_bytes())['fence']
        assert emergency_fence > origin['fence']
        code, required = stand.run('emergency')
        results.append(required)
        assert code == 75 and required['result'] == 'EMERGENCY_APPROVAL_REQUIRED', required
        for slot in ('NL', 'NL2'):
            assert request(dict(command='show', unit='test-'+slot+'.service'))['state']['MainPID'] == '0'
            assert not (tmp_path/(slot+'-config/reader.sock')).exists()
        for kind in ('denied', 'expired'):
            now = int(time.time())
            approval = dict(operation_id='test-packaged-ssh-controller', expected_state_sha256=required['request']['expected_state_sha256'],
                approved_at=now if kind == 'denied' else now-901, expires_at=now+300 if kind == 'denied' else now-1,
                approval='DENIED' if kind == 'denied' else 'OPERATOR_APPROVED_OUTAGE')
            path = private_file(tmp_path/(kind+'.json'), package.encode(approval))
            code, result = stand.run('emergency', path)
            results.append(result)
            assert code == 75 and result['result'] == 'EMERGENCY_BLOCKED' and result['cause'].startswith('MAINTENANCE_APPROVAL_'), result
        now = int(time.time())
        approval = private_file(tmp_path/'approved.json', package.encode(dict(operation_id='test-packaged-ssh-controller',
            expected_state_sha256=required['request']['expected_state_sha256'], approved_at=now, expires_at=now+900,
            approval='OPERATOR_APPROVED_OUTAGE')))
        request(dict(command='lose-start-response', unit='test-NL.service'))
        code, result = stand.run('emergency', approval)
        results.append(result)
        assert code == 75 and result['result'] == 'EMERGENCY_BLOCKED', result
        intent = (stand.fleet.nodes['NL'].state/'start-intent-0.json').read_bytes()
        started = request(dict(command='show', unit='test-NL.service'))['state']
        assert started['MainPID'] != '0'
        code, result = stand.run('emergency', approval)
        results.append(result)
        assert code == 0 and result['result'] == 'EMERGENCY_RECOVERED', result
        assert request(dict(command='show', unit='test-NL.service'))['state'] == started
        assert (stand.fleet.nodes['NL'].state/'archive/test-packaged-ssh-controller/start-intent-0.json').read_bytes() == intent
        clients = {slot: stand.client(slot, 3) for slot in ('NL', 'NL2')}
        for slot, client in clients.items():
            assert client.wait(timeout=35) == 0, (tmp_path/(slot+'-client.log')).read_text()
        code, replay = stand.run('emergency')
        results.append(replay)
        assert code == 0 and replay['replay'], replay
        final = json.loads(journal.read_bytes())
        assert final['online_parent']['decision'] == 'COMMIT' and final['online_parent']['fence'] == emergency_fence
        assert package.digest(package.encode(final['online_parent']['plan'])) == origin['plan_sha256']
    finally:
        if process and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        stand.close()
        if os.environ.get('FC_CORE_EVIDENCE'):
            root = Path(os.environ['FC_CORE_EVIDENCE'])
            private_file(root/'gateway-restart-emergency.json', package.encode(dict(results=results,
                scope='gateway-replacement-approval-start-intent-not-revocation-G1')))


def test_revocation_after_commit_and_after_approval_recovers_without_rollback(online_package, core_driver, tmp_path):
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    process, results, probes = None, [], []
    lifecycle = {}
    revoked, late = DeviceIdentity.generate(), DeviceIdentity.generate()
    access = stand.fleet.service.access
    for device in (revoked, late):
        access.complete(proof(access, device, access.invite()), 'activate')
    try:
        stand.start()
        credentials = {}
        for label, device in (('revoked', revoked), ('late', late)):
            for slot in ('NL', 'NL2'):
                profile = stand.issue_probe(slot, device, label+'-'+slot)
                credentials[label, slot] = profile
                result = stand.probe(slot, profile)
                assert result.returncode == 0 and b'admission_allowed' in result.stdout, result.stderr.decode()
                probes.append(dict(identity=label, slot=slot, phase='before-commit', result='ALLOWED'))
        before = {slot: request(dict(command='show', unit='test-'+slot+'.service'))['state'] for slot in ('NL', 'NL2')}
        lifecycle['before'] = before
        process = subprocess.Popen(stand.command('online'), cwd=tmp_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        journal = tmp_path/'coordinator/transaction.json'
        deadline = time.monotonic()+60
        while True:
            record = json.loads(journal.read_bytes()) if journal.exists() else {}
            if record.get('state') == 'ONLINE_COMMIT_DECIDED':
                process.kill()
                process.wait(timeout=5)
                break
            assert process.poll() is None and time.monotonic() < deadline, record.get('state')
            time.sleep(.001)
        origin = json.loads(journal.read_bytes())
        assert stand.revoke(revoked).returncode == 0
        code, result = stand.run('resume')
        results.append(result)
        assert code == 75 and result['result'] == 'ONLINE_EMERGENCY_REQUIRED', result
        assert result['decision'] == 'COMMIT'
        fence = json.loads(journal.read_bytes())['fence']
        assert fence > origin['fence']
        code, required = stand.run('emergency')
        results.append(required)
        assert code == 75 and required['result'] == 'EMERGENCY_APPROVAL_REQUIRED', required
        for slot in before:
            assert request(dict(command='show', unit='test-'+slot+'.service'))['state']['MainPID'] == '0'
            assert not (tmp_path/(slot+'-config/reader.sock')).exists()

        def approval(kind, current):
            now = int(time.time())
            return private_file(tmp_path/(kind+'.json'), package.encode(dict(operation_id=origin['operation_id'],
                expected_state_sha256=current['request']['expected_state_sha256'],
                approved_at=now-901 if kind == 'expired' else now,
                expires_at=now-1 if kind == 'expired' else now+900,
                approval='DENIED' if kind == 'denied' else 'OPERATOR_APPROVED_OUTAGE')))

        for kind in ('denied', 'expired'):
            code, result = stand.run('emergency', approval(kind, required))
            results.append(result)
            assert code == 75 and result['result'] == 'EMERGENCY_BLOCKED' and result['cause'].startswith('MAINTENANCE_APPROVAL_'), result
        stale = approval('approved-before-late-revoke', required)
        assert stand.revoke(late).returncode == 0
        code, result = stand.run('emergency', stale)
        results.append(result)
        assert code == 75 and result['result'] == 'EMERGENCY_BLOCKED' and result['cause'] == 'MAINTENANCE_APPROVAL_BINDING', result
        code, updated = stand.run('emergency')
        results.append(updated)
        assert code == 75 and updated['result'] == 'EMERGENCY_APPROVAL_REQUIRED', updated
        assert updated['request']['expected_state_sha256'] != required['request']['expected_state_sha256']
        approved = approval('approved-current-state', updated)
        request(dict(command='lose-start-response', unit='test-NL.service'))
        code, result = stand.run('emergency', approved)
        results.append(result)
        assert code == 75 and result['result'] == 'EMERGENCY_BLOCKED', result
        started = request(dict(command='show', unit='test-NL.service'))['state']
        assert started['MainPID'] != '0'
        intent = (stand.fleet.nodes['NL'].state/'start-intent-0.json').read_bytes()
        lifecycle['start_intent_sha256'] = package.digest(intent)
        code, result = stand.run('emergency', approved)
        results.append(result)
        assert code == 0 and result['result'] == 'EMERGENCY_RECOVERED', result
        assert request(dict(command='show', unit='test-NL.service'))['state'] == started
        assert (stand.fleet.nodes['NL'].state/'archive'/origin['operation_id']/'start-intent-0.json').read_bytes() == intent
        for slot in before:
            after = request(dict(command='show', unit='test-'+slot+'.service'))['state']
            assert before[slot]['MainPID'] != after['MainPID'] and before[slot]['InvocationID'] != after['InvocationID']
            lifecycle[slot+'-after'] = after
        for (label, slot), profile in credentials.items():
            prior = json.loads(profile.read_bytes())
            certificate = x509.load_pem_x509_certificate(prior['certificate'].encode())
            serial = certificate.serial_number
            assert time.time() < certificate.not_valid_after_utc.timestamp()
            assert time.time() < x509.load_pem_x509_crl(prior['revocations'].encode()).next_update_utc.timestamp()
            current = json.loads((tmp_path/(slot+'-profile/gateway.json')).read_bytes())
            crl = x509.load_pem_x509_crl(current['revocations'].encode())
            assert crl.get_revoked_certificate_by_serial_number(serial) is not None
            assert current['minimum_crl'] > prior['minimum_crl']
            gateway_log = tmp_path/('test-'+slot+'.service.log')
            offset = gateway_log.stat().st_size
            result = stand.probe(slot, profile)
            assert result.returncode != 0 and b'admission_allowed' not in result.stdout, result.stdout.decode()
            assert b'bootstrap_protocol_rejected' in result.stderr, result.stderr.decode()
            deadline = time.monotonic()+5
            while True:
                events = [json.loads(line)['event'] for line in gateway_log.read_bytes()[offset:].splitlines()]
                if 'family_open:unknown' in events or time.monotonic() >= deadline:
                    break
                time.sleep(.01)
            assert 'bootstrap_admission_rejected' in events and 'family_open:unknown' in events, events
            assert 'bootstrap_family_auth' not in events and 'CLIENT_ISSUED:' not in events, events
            probes.append(dict(identity=label, slot=slot, phase='after-recovery', result='TLS_DENIED',
                               cause=result.stderr.decode().strip(), server_events=events,
                               revoked_serial_present=True, minimum_crl=current['minimum_crl']))
        clients = {slot: stand.client(slot, 3) for slot in before}
        for slot, client in clients.items():
            assert client.wait(timeout=40) == 0, (tmp_path/(slot+'-client.log')).read_text()
        for label, device in (('revoked', revoked), ('late', late)):
            client = stand.client('NL', 1, device, name=label)
            assert client.wait(timeout=15) != 0
            assert 'readiness HTTP 403' in (tmp_path/(label+'-client.log')).read_text()
        code, replay = stand.run('emergency')
        results.append(replay)
        assert code == 0 and replay['replay'], replay
        assert request(dict(command='show', unit='test-NL.service'))['state'] == started
        final = json.loads(journal.read_bytes())
        assert final['online_parent']['decision'] == 'COMMIT' and final['online_parent']['fence'] == fence
        assert package.digest(package.encode(final['online_parent']['plan'])) == origin['plan_sha256']
        lifecycle.update(origin_plan_sha256=origin['plan_sha256'], original_fence=origin['fence'],
                         resumed_fence=fence, origin_decision=final['online_parent']['decision'])
    finally:
        if process and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        stand.close()
        if os.environ.get('FC_CORE_EVIDENCE'):
            root = Path(os.environ['FC_CORE_EVIDENCE'])/'revoke'
            root.mkdir(mode=0o700, parents=True, exist_ok=True)
            private_file(root/'recovery.json', package.encode(dict(results=results, probes=probes, lifecycle=lifecycle,
                package=online_package[4], driver_sha256=package.digest(core_driver.read_bytes()),
                scope='packaged-operator-revoke-real-TLS-emergency-not-Android-or-Telemost')))
            for path in tmp_path.glob('*.log'):
                private_file(root/path.name, path.read_bytes())
