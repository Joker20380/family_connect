import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time

from mesh_core_stand import CoreStand
from online_package_stand import private_file
from scripts import package_online_renewal as package
from test_mesh_core_soak import bounds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--driver', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
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
    stand = CoreStand(args.root, extracted, driver, duration='4h', rotation='1h', android_tls=True)
    receipt = dict(scope='Android-isolated-core-server-not-G3-acceptance', source=stand.manifest['source_commit'],
                   archive_sha256=package.digest(args.archive.read_bytes()), driver_sha256=package.digest(args.driver.read_bytes()))
    try:
        stand.start()
        code, result = stand.run('online')
        assert code == 0 and result['result'] == 'COMMITTED', result
        program = ('import sys,json;sys.path.insert(0,sys.argv[1]);from control.friends.access import Access;'
                   'access=Access(sys.argv[2]);print(json.dumps([access.invite(),access.invite()]))')
        invitations = json.loads(subprocess.check_output([sys.executable, '-I', '-B', '-c', program,
            str(extracted/'api.pyz'), str(args.root/'access.db')], cwd=args.root, timeout=10))
        import base64
        settings = dict(anchor=base64.b64encode(stand.fleet.service.anchor).decode(),
                        apis={'27': dict(gateway='nl-amsterdam-2', invitation=invitations[0]),
                              '35': dict(gateway='nl-amsterdam-1', invitation=invitations[1])})
        private_file(args.evidence/'android-inputs.json', package.encode(settings))
        private_file(args.evidence/'core-ca.pem', stand.ca.read_bytes())
        retained = bounds(stand)
        due = max(value['leaf'] for value in retained.values()) - 5400 + 2
        receipt.update(state='HTTP_READY', relay=stand.relay, https=stand.https,
                       original_bounds=retained, due=due, started=time.time())
        private_file(args.evidence/'server.json', package.encode(receipt))
        deadline = time.monotonic()+14000
        renewed = False
        while time.monotonic() < deadline and not (args.evidence/'stop').exists():
            if not renewed and time.time() >= due:
                command = stand.command('online')
                command[command.index('--operation')+1] = 'test-android-runtime-renewal'
                result = subprocess.run(command, cwd=args.root, capture_output=True, timeout=180)
                receipt['renewal'] = json.loads(result.stdout)
                assert result.returncode == 0 and receipt['renewal']['result'] == 'COMMITTED', receipt['renewal']
                renewed = True
                receipt.update(state='SUCCESSOR_PUBLISHED', successor_bounds=bounds(stand), published=time.time())
                private_file(args.evidence/'server.json', package.encode(receipt))
            time.sleep(1)
    except BaseException as error:
        receipt.update(state='FAILED', failure_type=type(error).__name__, failure=str(error))
        raise
    finally:
        stand.close()
        receipt['cleanup'] = 'processes-waited'
        private_file(args.evidence/'server.json', package.encode(receipt))
        for path in args.root.glob('*.log'):
            private_file(args.evidence/path.name, path.read_bytes())


if __name__ == '__main__':
    main()
