import json
import os
from pathlib import Path
import subprocess
import time

import pytest
from cryptography import x509

from fixtures.mesh_supervisor import request
from mesh_core_stand import CoreStand
from mesh_core_budget import require_seed_span
from online_package_stand import private_file
from scripts import package_online_renewal as package
from test_online_runtime_package import core_driver, online_package


def bounds(stand):
    result = {}
    for slot in ('NL', 'NL2'):
        config = json.loads(stand.configs[slot].read_bytes())
        locator = json.loads(Path(config['profile_locator']).read_bytes())
        profile = json.loads(Path(locator['profile']).read_bytes())
        result[slot] = dict(leaf=x509.load_pem_x509_certificate(profile['certificate'].encode()).not_valid_after_utc.timestamp(),
                           crl=x509.load_pem_x509_crl(profile['revocations'].encode()).next_update_utc.timestamp())
    return result


def generations(path):
    first, last, count, committed = None, None, 0, 0
    with path.open() as source:
        for line in source:
            value = json.loads(line)
            if value['event'] == 'credentials_committed':
                committed += 1
            if value['event'] != 'traffic':
                continue
            first = first or value
            assert value['session'] == first['session'] and value['original']['ID'] == first['original']['ID']
            assert value['tcp'] and value['dns'] and value['verified_https']
            if last is not None:
                assert value['original']['Received'] > last['original']['Received']
                assert value['generation'] >= last['generation']
            last, count = value, count + 1
    assert first is not None and count > 1
    return dict(first=first, last=last, samples=count, committed=committed)


def test_two_online_renewals_cross_real_crypto_bounds(online_package, core_driver, tmp_path):
    if os.environ.get('FC_CORE_SOAK') != '1':
        pytest.skip('explicit seven-hour isolated core wall-clock qualification required')
    assert os.environ.get('FC_TEST_ONLINE_PACKAGE'), 'immutable archive required'
    destination = Path(os.environ['FC_CORE_EVIDENCE'])/'soak'
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    require_seed_span(7*3600, 4*3600, 2*3600, continuous=True)
    stand = CoreStand(tmp_path, online_package[3], core_driver, duration='7h', rotation='2h', continuous=True)
    clients = {}
    receipt = dict(scope='two-renewal-wall-clock-core-not-complete-G4', package=online_package[4],
                   driver_sha256=package.digest(core_driver.read_bytes()), started=time.time(), renewals=[])
    def save():
        private_file(destination/'progress.json', package.encode(receipt))
    def processes():
        return {slot: request(dict(command='show', unit='test-'+slot+'.service'))['state'] for slot in ('NL', 'NL2')}
    def alive():
        assert all(client.poll() is None for client in clients.values()), 'original client exited'
        current = processes()
        assert all(all(current[slot][field] == receipt['processes'][slot][field]
                       for field in ('MainPID', 'InvocationID', 'NRestarts')) for slot in current), 'gateway changed'
    try:
        stand.start()
        code, setup = stand.run('online')
        assert code == 0 and setup['result'] == 'COMMITTED', setup
        receipt.update(setup=setup, processes=processes(), original_bounds=bounds(stand), state='TRAFFIC_STARTING')
        clients = {slot: stand.client(slot, 24000) for slot in ('NL', 'NL2')}
        save()
        retained = receipt['original_bounds']
        for ordinal in (1, 2):
            due = max(value['leaf'] for value in retained.values()) - 5400 + 2
            assert due > time.time() and due - time.time() < 9100
            receipt.update(state='WAITING_FOR_RENEWAL_'+str(ordinal), due=due)
            save()
            while time.time() < due:
                alive()
                time.sleep(min(30, max(.1, due-time.time())))
            alive()
            command = stand.command('online')
            command[command.index('--operation')+1] = 'test-core-soak-renewal-'+str(ordinal)
            result = subprocess.run(command, cwd=tmp_path, capture_output=True, timeout=180)
            committed = json.loads(result.stdout)
            assert result.returncode == 0 and committed['result'] == 'COMMITTED', committed
            record = json.loads((tmp_path/'coordinator/transaction.json').read_bytes())
            assert record['decision'] == 'COMMIT' and record['state'] == 'COMMITTED'
            retained = bounds(stand)
            receipt['renewals'].append(dict(ordinal=ordinal, completed=time.time(), result=committed,
                bounds=retained, plan_sha256=record['plan_sha256'], fence=record['fence']))
            receipt['state'] = 'RENEWAL_'+str(ordinal)+'_COMMITTED'
            alive()
            save()
        crossed = max(bound for values in receipt['renewals'][0]['bounds'].values() for bound in values.values())
        receipt.update(state='WAITING_FOR_CRYPTO_BOUND', crossed_bound=crossed)
        save()
        while time.time() <= crossed + 3:
            alive()
            time.sleep(30)
        for slot, client in clients.items():
            assert client.wait(timeout=900) == 0, 'original session failed on '+slot
        receipt['traffic'] = {slot: generations(tmp_path/(slot+'-client.log')) for slot in clients}
        for observations in receipt['traffic'].values():
            assert observations['last']['generation'] >= observations['first']['generation'] + 2
            assert observations['committed'] >= 2 and observations['samples'] >= 24000
        assert processes() == receipt['processes']
        receipt.update(state='CORE_TWO_RENEWAL_PASS', finished=time.time(), emergency='NOT_RUN_IN_THIS_SOAK')
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
