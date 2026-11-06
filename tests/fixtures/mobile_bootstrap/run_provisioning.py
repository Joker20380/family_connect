"""Offline, bounded source integration; no AVD, production endpoints or APK build."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tools', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--image', default='fc-online-runtime-tests:20261105')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output, tools = args.output.resolve(), args.tools.resolve()
    output.relative_to(root / 'state-client-build')
    output.mkdir(parents=True, exist_ok=False)
    image = subprocess.check_output(['docker', 'image', 'inspect', '--format={{.Id}}', args.image], text=True).strip()
    def inventory():
        paths = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '--',
                                         'carrier', 'control', 'device_identity', 'provisioning', 'deploy/friends/access-api.py',
                                         'clients/android/app/src', 'pilot/android-restricted', 'tests/fixtures/mobile_bootstrap'], cwd=root, text=True).splitlines()
        return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sorted(set(paths)) if (root / name).is_file()}
    inputs = inventory()
    source_inventory = json.dumps(inputs, sort_keys=True, indent=2) + '\n'
    (output / 'source-inventory.json').write_text(source_inventory)
    receipt = dict(source=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
                   diff_sha256=hashlib.sha256(subprocess.check_output(['git', 'diff', 'HEAD'], cwd=root)).hexdigest(), image=image,
                   inventory_sha256=hashlib.sha256(source_inventory.encode()).hexdigest(), checks=[])
    environment = os.environ | dict(GOMAXPROCS='2', GOMEMLIMIT='384MiB', GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off',
                                    GOCACHE=str(tools / 'go-cache'), GOMODCACHE=str(tools / 'go-mod'), CGO_ENABLED='0')
    def run(name, command):
        with (output / (name + '.log')).open('xb') as log:
            completed = subprocess.run(command, cwd=root, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        receipt['checks'].append(dict(name=name, command=command, exit=completed.returncode,
                                      log_sha256=hashlib.sha256((output / (name + '.log')).read_bytes()).hexdigest()))
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(name, completed.returncode, flush=True)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    run('jvm', [sys.executable, str(Path(__file__).with_name('check_provisioning.py')), '--pipeline', '--tools', str(tools), '--output', str(output / 'jvm')])
    binary = output / 'integration.test'
    run('compile', ['nice', '-n', '10', str(tools / 'go/bin/go'), 'test', '-C', 'carrier', '-p', '1', '-c', './internal/qualification', '-o', str(binary)])
    receipt['integration_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
    classpath = '/repo/' + str((output / 'jvm/classes').relative_to(root))
    for name in ('gson-2.13.2.jar', 'junit-4.13.2.jar', 'hamcrest-core-1.3.jar', 'bcprov-jdk18on-1.85.2.jar'):
        classpath += ':/tools/' + str(next((tools / 'gradle-home/caches').rglob(name)).relative_to(tools))
    run('runtime', ['docker', 'run', '--rm', '--network', 'none', '--cpus', '1', '--memory', '640m', '--read-only', '--tmpfs', '/tmp:rw,size=64m',
                    '--mount', f'type=bind,src={root},dst=/repo,readonly', '--mount', f'type=bind,src={tools},dst=/tools,readonly',
                    '-w', '/repo/carrier/internal/qualification', '-e', 'FC_COLD_PROVISION_PYTHON=/usr/local/bin/python', '-e', 'GOMAXPROCS=1',
                    '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'FC_COLD_JAVA=/tools/jdk/bin/java', '-e', 'FC_COLD_CLASSPATH=' + classpath,
                    '--entrypoint', '/repo/' + str(binary.relative_to(root)), image,
                    '-test.run', '^TestColdProvisionRealAuthorityAndNativeTraffic$', '-test.count=1', '-test.timeout=60s', '-test.v'])
    if inputs != inventory():
        raise RuntimeError('Source changed during the run; receipt is not a frozen acceptance')


if __name__ == '__main__':
    main()
