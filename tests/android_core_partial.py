import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import threading
import time

from mesh_core_stand import CoreStand
from mesh_core_directory import publish_seed_directories
from online_package_stand import private_file
from scripts import package_online_renewal as package
from test_mesh_core_soak import bounds


def readiness_metadata(raw):
    envelope = json.loads(raw)
    response = envelope.get('response', envelope)
    return dict(ready=response.get('ready'), gateway=envelope.get('gateway_id', 'nl-amsterdam-1'),
                expires=response.get('expires_at'), crl=response.get('minimum_crl'), sha256=package.digest(raw))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--driver', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--api', type=int, choices=(27, 35), required=True)
    parser.add_argument('--scenario', choices=('partial', 'owner-race', 'partial-connect', 'late-closed-owner', 'legacy'), default='partial')
    parser.add_argument('--legacy-manifest', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    args.root.mkdir(mode=0o700)
    args.evidence.mkdir(mode=0o700)
    extracted = args.root/'package'
    extracted.mkdir(mode=0o700)
    with tarfile.open(args.archive) as archive:
        archive.extractall(extracted, filter='data')
    driver = args.root/'mesh-runtime'
    shutil.copyfile(args.driver, driver)
    driver.chmod(0o755)
    assert package.digest(driver.read_bytes()) == package.digest(args.driver.read_bytes())
    stand = CoreStand(args.root, extracted, driver, duration='45m', rotation='15m', android_tls=True)
    lock = threading.RLock()
    connected, released = set(), set()
    release_response = threading.Event()
    receipt = dict(scope='actual-Android-'+args.scenario+'-not-full-G3', source=stand.manifest['source_commit'],
                   archive_sha256=package.digest(args.archive.read_bytes()), driver_sha256=package.digest(driver.read_bytes()),
                   state='STARTING', requests=[], connected=[], released=[])
    if args.scenario == 'legacy':
        assert args.legacy_manifest is not None
        legacy = json.loads(args.legacy_manifest.read_bytes())
        assert legacy['scope'] == 'legacy-peer-compatibility-fixture-not-online-runtime-acceptance'
        assert legacy['source_commit'] == stand.manifest['source_commit']
        assert legacy['source_path'] == 'carrier/roombroker/authorization.go'
        assert legacy['original_sha256'] == stand.manifest['native_sources'][legacy['source_path']]
        assert legacy['driver_sha256'] == receipt['driver_sha256']
        assert legacy['driver_sha256'] != legacy['normal_driver_sha256']
        assert legacy['credential_exchange'] is False and legacy['lease_renewal'] is True
        receipt['legacy_peer'] = legacy
    else:
        assert args.legacy_manifest is None

    def save():
        with lock:
            private_file(args.evidence/'server.json', package.encode(receipt))

    def control(action):
        with lock:
            if action == 'connected'+str(args.api):
                connected.add(action[-2:])
                receipt['connected'] = sorted(connected)
            elif action == 'release'+str(args.api):
                assert receipt['state'] == 'PARTIAL'
                assert args.scenario == 'partial-connect' or time.time()-receipt['partial_at'] >= 305
                released.add(action[-2:])
                receipt['released'] = sorted(released)
            elif action == 'response'+str(args.api):
                assert args.scenario in ('owner-race', 'late-closed-owner') and receipt['state'] == 'READINESS_HELD'
                release_response.set()
            else:
                assert action == 'state'
            save()
            return dict(state=receipt['state'], requests=len(receipt['requests']), wall=time.time())

    def observe(path, status, raw):
        if path != '/friends/restricted-readiness':
            return
        metadata = readiness_metadata(raw)
        hold = False
        with lock:
            receipt['requests'].append(dict(wall=time.time(), state=receipt['state'], status=status, **metadata))
            if args.scenario in ('owner-race', 'late-closed-owner') and receipt['state'] == 'SUCCESSOR_PUBLISHED' and metadata['gateway'] == 'nl-amsterdam-2':
                assert status == 200 and metadata['expires'] is not None
                receipt.update(state='READINESS_HELD', response_held_at=time.time())
                hold = True
            save()
        if hold:
            assert release_response.wait(10), 'Android must acquire its real cache lock before releasing HTTP'
            with lock:
                receipt.update(state='HTTP_RELEASED', response_released_at=time.time())
                save()

    stand.http_control, stand.http_observer = control, observe
    try:
        stand.start()
        receipt['directory_publication'] = publish_seed_directories(stand, args.snapshot)
        program = ('import sys,json;sys.path.insert(0,sys.argv[1]);from control.friends.access import Access;'
                   'access=Access(sys.argv[2]);print(json.dumps(access.invite()))')
        invitations = json.loads(subprocess.check_output([sys.executable, '-I', '-B', '-c', program,
            str(extracted/'api.pyz'), str(args.root/'access.db')], cwd=args.root, timeout=10))
        settings = dict(anchor=base64.b64encode(stand.fleet.service.anchor).decode(), scenario=args.scenario,
                        apis={str(args.api): dict(gateway='nl-amsterdam-2', invitation=invitations)})
        private_file(args.evidence/'android-inputs.json', package.encode(settings))
        private_file(args.evidence/'core-ca.pem', stand.ca.read_bytes())
        receipt.update(state='HTTP_READY', relay=stand.relay, https=stand.https, original_bounds=bounds(stand), started=time.time())
        save()
        deadline = time.monotonic()+2400
        while time.monotonic() < deadline and not (args.evidence/'stop').exists():
            with lock:
                begin = receipt['state'] == 'HTTP_READY' and connected == {str(args.api)}
                resume = receipt['state'] == 'PARTIAL' and released == {str(args.api)}
            if begin:
                if args.scenario in ('partial', 'partial-connect'):
                    stand.rpc_fault('NL2', 'publish', 'drop-before')
                code, result = stand.run('online')
                journal = json.loads((args.root/'coordinator/transaction.json').read_bytes())
                assert journal['decision'] == 'COMMIT', result
                with lock:
                    if args.scenario in ('partial', 'partial-connect'):
                        assert code != 0 and not journal['published'], result
                        receipt.update(state='PARTIAL', partial_at=time.time(), blocked=result,
                                       plan_sha256=journal['plan_sha256'], published=journal['published'])
                    else:
                        assert code == 0 and result['result'] == 'COMMITTED', result
                        receipt.update(state='SUCCESSOR_PUBLISHED', result=result, published_at=time.time(),
                                       plan_sha256=journal['plan_sha256'], successor_bounds=bounds(stand))
                    save()
            if resume:
                code, result = stand.run('resume')
                journal = json.loads((args.root/'coordinator/transaction.json').read_bytes())
                assert code == 0 and result['result'] == 'COMMITTED', result
                assert journal['decision'] == 'COMMIT' and journal['plan_sha256'] == receipt['plan_sha256']
                with lock:
                    assert any(value['state'] == 'PARTIAL' for value in receipt['requests'])
                    receipt.update(state='SUCCESSOR_PUBLISHED', result=result, published_at=time.time(), successor_bounds=bounds(stand))
                    save()
            time.sleep(.2)
    except BaseException as error:
        receipt.update(state='FAILED', failure_type=type(error).__name__, failure=str(error))
        raise
    finally:
        release_response.set()
        stand.close()
        receipt['cleanup'] = 'processes-waited'
        save()
        for path in args.root.glob('*.log'):
            private_file(args.evidence/path.name, path.read_bytes())


if __name__ == '__main__':
    main()
