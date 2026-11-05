import json
import os
from pathlib import Path
import time

import pytest
from cryptography import x509

from fixtures.mesh_supervisor import request
from mesh_core_stand import CoreStand
from online_package_stand import private_file
from scripts import package_online_renewal as package
from test_mesh_core_faults import kill_at
from test_online_runtime_package import core_driver, online_package


def test_successor_recovery_after_real_expiry(online_package, core_driver, tmp_path):
    if os.environ.get('FC_CORE_EXPIRY') != '1':
        pytest.skip('explicit four-hour successor expiry qualification required')
    assert os.environ.get('FC_TEST_ONLINE_PACKAGE'), 'immutable archive required'
    destination = Path(os.environ['FC_CORE_EVIDENCE'])/'successor-expiry'
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    stand = CoreStand(tmp_path, online_package[3], core_driver, duration='5h', rotation='1h')
    receipt = dict(scope='actual-successor-expiry-after-controller-death', package=online_package[4],
                   driver_sha256=package.digest(core_driver.read_bytes()), started=time.time(), results=[])
    def save():
        private_file(destination/'progress.json', package.encode(receipt))
    try:
        stand.start()
        origin = kill_at(stand, 'online', 'ONLINE_COMMIT_DECIDED')
        assert origin['decision'] == 'COMMIT'
        plan = json.loads((tmp_path/'coordinator/plan.json').read_bytes())
        assert package.digest(package.encode(plan)) == origin['plan_sha256']
        candidate = plan['candidate']
        deadlines = [x509.load_pem_x509_crl(candidate['crl'].encode()).next_update_utc.timestamp()]
        for slot in ('NL', 'NL2'):
            selected = plan if slot == 'NL' else plan['secondary']
            deadlines.append(x509.load_pem_x509_certificate(selected['candidate']['certificate'].encode()).not_valid_after_utc.timestamp())
        due = max(deadlines)+2
        assert 14000 < due-time.time() < 14500
        receipt.update(state='WAITING_FOR_SUCCESSOR_EXPIRY', due=due, deadlines=deadlines,
                       origin_plan_sha256=origin['plan_sha256'], origin_fence=origin['fence'], decision='COMMIT')
        journal_before = (tmp_path/'coordinator/transaction.json').read_bytes()
        profile_paths = {}
        for slot in ('NL', 'NL2'):
            config = json.loads(stand.configs[slot].read_bytes())
            locator = json.loads(Path(config['profile_locator']).read_bytes())
            profile_paths[slot] = Path(locator['profile'])
        profiles_before = {slot: path.read_bytes() for slot, path in profile_paths.items()}
        processes_before = {slot: request(dict(command='show', unit='test-'+slot+'.service'))['state'] for slot in ('NL', 'NL2')}
        save()
        while time.time() <= due:
            time.sleep(min(30, max(.1, due-time.time())))
        for attempt in range(2):
            code, result = stand.run('resume')
            record = json.loads((tmp_path/'coordinator/transaction.json').read_bytes())
            receipt['results'].append(dict(attempt=attempt+1, exit_code=code, result=result, observed=time.time()))
            save()
            assert code != 0, result
            cause = result.get('last_cause')
            if result['result'] == 'FAIL_CLOSED':
                assert result == dict(result='FAIL_CLOSED', cause='ONLINE_RUNTIME_RECEIPT', automatic_retry=False)
                assert (tmp_path/'coordinator/transaction.json').read_bytes() == journal_before
                for slot, profile in profiles_before.items():
                    assert profile_paths[slot].read_bytes() == profile
                    assert request(dict(command='show', unit='test-'+slot+'.service'))['state'] == processes_before[slot]
                    material = json.loads(profile)
                    assert x509.load_pem_x509_certificate(material['certificate'].encode()).not_valid_after_utc.timestamp() < time.time()
                    assert x509.load_pem_x509_crl(material['revocations'].encode()).next_update_utc.timestamp() < time.time()
                cause = result['cause']
            else:
                assert result['result'] in ('ONLINE_EMERGENCY_REQUIRED', 'ONLINE_RECOVERY_REQUIRED'), result
            assert record['decision'] == 'COMMIT' and record['plan_sha256'] == origin['plan_sha256']
            assert record['fence'] >= origin['fence'] and cause
            receipt['results'][-1]['cause'] = cause
            save()
        assert receipt['results'][0]['cause'] == receipt['results'][1]['cause']
        receipt.update(state='EXPIRED_SUCCESSOR_BLOCKED_SAME_COMMIT', finished=time.time(),
                       processes={slot: request(dict(command='show', unit='test-'+slot+'.service'))['state'] for slot in ('NL', 'NL2')})
        save()
    except BaseException as error:
        receipt.update(state='FAILED', failed_at=time.time(), failure_type=type(error).__name__, failure=str(error))
        save()
        raise
    finally:
        stand.close()
        receipt['cleanup'] = 'processes-waited-and-reader-sockets-absent'
        assert not any((tmp_path/(slot+'-config/reader.sock')).exists() for slot in ('NL', 'NL2'))
        save()
        for path in tmp_path.glob('*.log'):
            private_file(destination/path.name, path.read_bytes())
