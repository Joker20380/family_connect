import datetime
import hashlib
import json
import os
from pathlib import Path
import ssl
import subprocess
import time
import urllib.error
import urllib.request

import pytest
from cryptography import x509

from device_identity.device import DeviceIdentity
from fixtures.mesh_supervisor import request
from mesh_core_stand import CoreStand
from mesh_core_budget import delivery_observed, require_delivery_window, require_seed_span
from online_package_stand import private_file
from scripts import package_online_renewal as package
from test_friends_access import proof
from test_mesh_core_faults import kill_at
from test_mesh_core_soak import bounds, generations
from test_online_runtime_package import core_driver, online_package


def lease_evidence(path, session, after):
    tag = hashlib.sha256(b'family-connect/session-diagnostic/v2\x00'+bytes.fromhex(session)).hexdigest()
    events = [value['trace'] for value in map(json.loads, path.read_text().splitlines())
              if value.get('event') == 'session_trace' and value['trace']['session_tag'] == tag]
    original = next(value for value in events if value['stage'] == 'AUTHORIZED')
    applied = [value for value in events if value.get('lease_action') == 'applied']
    assert len(applied) > 2
    assert applied[-1]['lease_deadline_ms']/1000 > after
    assert applied[-1]['timestamp_ms'] > original['lease_deadline_ms']
    assert applied[-1]['lease_deadline_ms'] > original['lease_deadline_ms']
    assert applied[-1]['lease_sequence'] > applied[0].get('lease_sequence', 0)
    assert all(value['lease_deadline_ms'] > value['timestamp_ms'] for value in applied)
    return dict(initial=original, applied=applied)


def test_two_renewals_then_linked_emergency_on_original_sessions(online_package, core_driver, tmp_path):
    if os.environ.get('FC_CORE_ACCEPTANCE') != '1':
        pytest.skip('explicit eight-hour full core qualification required')
    assert os.environ.get('FC_TEST_ONLINE_PACKAGE'), 'immutable archive required'
    assert all(line.split()[1] != '00000000' for line in Path('/proc/net/route').read_text().splitlines()[1:])
    require_seed_span(8*3600, 4*3600, 2*3600, continuous=True)
    destination = Path(os.environ['FC_CORE_EVIDENCE'])/'full-core'
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    stand = CoreStand(tmp_path, online_package[3], core_driver, duration='8h', rotation='2h', continuous=True, android_tls=True)
    clients = {}
    receipt = dict(scope='isolated-core-full-path-not-Telemost-systemd-or-Android', package=online_package[4],
                   driver_sha256=package.digest(core_driver.read_bytes()), started=time.time(), renewals=[])
    def save():
        private_file(destination/'progress.json', package.encode(receipt))
    def processes():
        return {slot: request(dict(command='show', unit='test-'+slot+'.service'))['state'] for slot in ('NL', 'NL2')}
    def alive():
        assert all(client.poll() is None for client in clients.values()), 'original client exited'
        assert processes() == receipt['processes'], 'gateway process changed before emergency'
    def wait(until, state):
        receipt.update(state=state, due=until)
        save()
        while time.time() < until:
            alive()
            time.sleep(min(30, max(.1, until-time.time())))
    def invoke(mode, operation, approval=None):
        command = stand.command(mode)
        command[command.index('--operation')+1] = operation
        if approval is not None:
            command += ['--outage-approval', str(approval)]
        result = subprocess.run(command, cwd=tmp_path, capture_output=True, timeout=180)
        return result.returncode, json.loads(result.stdout)
    try:
        stand.start()
        receipt.update(state='WAITING_FOR_ISOLATED_PUBLIC_ROUTE', https=stand.https)
        save()
        deadline = time.monotonic()+600
        trust = ssl.create_default_context(cafile=stand.ca)
        while True:
            try:
                with urllib.request.urlopen('https://185.251.89.19:8443/', context=trust, timeout=5) as response:
                    assert response.read() == b'verified-isolated-origin'
                break
            except (OSError, urllib.error.URLError):
                assert time.monotonic() < deadline, 'isolated route did not become usable'
                time.sleep(1)
        code, setup = stand.run('online')
        assert code == 0 and setup['result'] == 'COMMITTED', setup
        receipt.update(setup=setup, processes=processes(), initial_bounds=bounds(stand))
        clients = {slot: stand.client(slot, 28800, https_address='185.251.89.19:8443') for slot in ('NL', 'NL2')}
        retained = receipt['initial_bounds']
        for ordinal in (1, 2):
            due = max(value['leaf'] for value in retained.values())-5400+2
            assert 0 < due-time.time() < 9100
            wait(due, 'WAITING_FOR_RENEWAL_'+str(ordinal))
            code, result = invoke('online', 'test-core-complete-renewal-'+str(ordinal))
            assert code == 0 and result['result'] == 'COMMITTED', result
            record = json.loads((tmp_path/'coordinator/transaction.json').read_bytes())
            retained = bounds(stand)
            receipt['renewals'].append(dict(ordinal=ordinal, completed=time.time(), result=result, bounds=retained,
                plan_sha256=record['plan_sha256'], fence=record['fence'], published=record['published']))
            alive()
            save()
            delivery_deadline = time.monotonic()+120
            while True:
                observed = {slot: generations(tmp_path/(slot+'-client.log')) for slot in clients}
                if delivery_observed(observed, ordinal):
                    break
                alive()
                assert time.monotonic() < delivery_deadline, 'actual client commit was not observed'
                time.sleep(1)
            require_delivery_window(observed, max(value['leaf'] for value in retained.values())-5400+2)
        crossed = max(bound for values in receipt['renewals'][0]['bounds'].values() for bound in values.values())
        wait(crossed+3, 'WAITING_FOR_CRYPTO_BOUND')
        receipt['traffic'] = {slot: generations(tmp_path/(slot+'-client.log')) for slot in clients}
        receipt['leases'] = {}
        for slot, observations in receipt['traffic'].items():
            assert observations['last']['generation'] >= observations['first']['generation']+2
            assert observations['committed'] >= 2 and observations['samples'] > 20000
            assert datetime.datetime.fromisoformat(observations['last']['at']).timestamp() > crossed
            receipt['leases'][slot] = lease_evidence(tmp_path/('test-'+slot+'.service.log'), observations['first']['session'], crossed)
        retained_sockets = [value for value in stand.accepted if not value['closed'] and value['received'] > 10000]
        assert len(retained_sockets) == 2
        receipt['original_sockets_before_emergency'] = [dict(value) for value in retained_sockets]
        receipt['state'] = 'TWO_RENEWALS_AND_CRYPTO_LEASE_BOUNDS_CROSSED'
        save()
        wait(max(value['leaf'] for value in retained.values())-5400+2, 'WAITING_FOR_EMERGENCY_OPERATION_DUE')
        revoked = DeviceIdentity.generate()
        access = stand.fleet.service.access
        access.complete(proof(access, revoked, access.invite()), 'activate')
        profiles = {slot: stand.issue_probe(slot, revoked, 'revoked-'+slot) for slot in clients}
        for slot, profile in profiles.items():
            assert stand.probe(slot, profile).returncode == 0
        operation = 'test-core-complete-emergency'
        origin = kill_at(stand, 'online', 'ONLINE_COMMIT_DECIDED', operation=operation)
        assert origin['decision'] == 'COMMIT' and stand.revoke(revoked).returncode == 0
        code, emergency = invoke('resume', operation)
        assert code == 75 and emergency['result'] == 'ONLINE_EMERGENCY_REQUIRED', emergency
        code, approval_required = invoke('emergency', operation)
        assert code == 75 and approval_required['result'] == 'EMERGENCY_APPROVAL_REQUIRED', approval_required
        for slot, client in clients.items():
            assert client.wait(timeout=30) != 0, 'old connection was not closed by emergency'
            assert processes()[slot]['MainPID'] == '0'
            assert not (tmp_path/(slot+'-config/reader.sock')).exists()
        assert all(value['closed'] for value in retained_sockets)
        receipt['old_connections'] = 'closed-by-emergency-not-reused'
        receipt['original_sockets_after_emergency'] = [dict(value) for value in retained_sockets]
        now = int(time.time())
        approval = private_file(tmp_path/'approved-outage.json', package.encode(dict(operation_id=operation,
            expected_state_sha256=approval_required['request']['expected_state_sha256'], approved_at=now,
            expires_at=now+900, approval='OPERATOR_APPROVED_OUTAGE')))
        request(dict(command='lose-start-response', unit='test-NL.service'))
        code, lost = invoke('emergency', operation, approval)
        assert code == 75 and lost['result'] == 'EMERGENCY_BLOCKED', lost
        started = processes()['NL']
        intent = (stand.fleet.nodes['NL'].state/'start-intent-0.json').read_bytes()
        code, recovered = invoke('emergency', operation, approval)
        assert code == 0 and recovered['result'] == 'EMERGENCY_RECOVERED', recovered
        after = processes()
        assert after['NL'] == started
        assert (stand.fleet.nodes['NL'].state/'archive'/operation/'start-intent-0.json').read_bytes() == intent
        assert all(after[slot]['MainPID'] != receipt['processes'][slot]['MainPID'] and
                   after[slot]['InvocationID'] != receipt['processes'][slot]['InvocationID'] for slot in after)
        revocations = {}
        for slot, profile in profiles.items():
            rejected = stand.probe(slot, profile)
            assert rejected.returncode != 0 and b'admission_allowed' not in rejected.stdout
            assert b'bootstrap_protocol_rejected' in rejected.stderr
            old = json.loads(profile.read_bytes())
            current = json.loads((stand.fleet.nodes[slot].live/'gateway.json').read_bytes())
            serial = x509.load_pem_x509_certificate(old['certificate'].encode()).serial_number
            assert x509.load_pem_x509_crl(current['revocations'].encode()).get_revoked_certificate_by_serial_number(serial) is not None
            assert current['minimum_crl'] > old['minimum_crl']
            revocations[slot] = dict(denial='TLS_DENIED', revoked_serial_present=True, minimum_crl=current['minimum_crl'])
        fresh = {slot: stand.client(slot, 5, name=slot+'-recovered', https_address='185.251.89.19:8443') for slot in after}
        assert all(client.wait(timeout=40) == 0 for client in fresh.values())
        code, replay = invoke('emergency', operation)
        assert code == 0 and replay['replay'] and processes() == after
        final = json.loads((tmp_path/'coordinator/transaction.json').read_bytes())
        assert final['online_parent']['decision'] == 'COMMIT'
        assert package.digest(package.encode(final['online_parent']['plan'])) == origin['plan_sha256']
        receipt.update(state='FULL_CORE_PATH_PASS', finished=time.time(), emergency=dict(result=emergency,
            approval_required=approval_required, lost_start=lost, recovered=recovered, replay=replay, after=after,
            original_plan_sha256=origin['plan_sha256'], start_intent_sha256=package.digest(intent), revocations=revocations),
            fresh_traffic={slot: generations(tmp_path/(slot+'-recovered-client.log')) for slot in after})
        save()
    except BaseException as error:
        receipt.update(state='FAILED', failed_at=time.time(), failure_type=type(error).__name__, failure=str(error))
        save()
        raise
    finally:
        for client in clients.values():
            if client.poll() is None:
                client.terminate()
                client.wait(timeout=15)
        stand.close()
        receipt['cleanup'] = 'processes-waited-and-reader-sockets-absent'
        assert not any((tmp_path/(slot+'-config/reader.sock')).exists() for slot in ('NL', 'NL2'))
        save()
        for path in tmp_path.glob('*.log'):
            private_file(destination/path.name, path.read_bytes())
