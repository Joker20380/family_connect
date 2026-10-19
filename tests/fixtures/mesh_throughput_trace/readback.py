"""Read-only exact-source/runtime receipt; no renewal, IPv6 probe or mutation."""

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / 'state-client-build'
OUT = STATE / 'mesh-throughput-trace-20261019'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.umask(0o077)
    OUT.mkdir(mode=0o700, exist_ok=True)
    assert not (OUT / 'baseline.json').exists()
    accepted = STATE / 'transport-write-batching-1'
    manifest = json.loads((accepted / 'gateway-source.json').read_text())
    assert manifest['source_inventory'] == 'aeeb6755bd235160127cfed67da4a870ae340cfebe89fc6d0f937908607d9483'
    assert all(digest(accepted / 'gateway-source/carrier' / name) == value
               for name, value in manifest['files'].items())
    observed = STATE / 'mesh-perf-3/source/carrier'
    files = {str(path.relative_to(observed)): digest(path)
             for path in observed.rglob('*') if path.is_file()}
    inventory = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert inventory == 'bc3721ec8c30c6fb304c478b22398926fe3bfc0c576216c49ed53809d78c3051'
    beta88 = STATE / 'beta87-product-fix-20261019'
    android = json.loads((beta88 / 'android88-build/source-inventory.json').read_text())
    assert all(digest(beta88 / 'android88-source' / name) == value for name, value in android.items())
    result = dict(accepted_inventory=manifest['source_inventory'], observation_inventory=inventory,
                  android_inventory=hashlib.sha256(json.dumps(android, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                  checkpoint=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
    syntax = ast.parse((beta88 / 'preflight.py').read_text())
    remote = next(ast.literal_eval(node.value) for node in syntax.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == 'remote' for target in node.targets))
    for role, host in [('RU', '185.251.89.19'), ('NL', '186.246.45.246')]:
        response = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                                   'root@' + host, 'python3 -B -'], input=remote,
                                  capture_output=True, text=True, timeout=55)
        (OUT / (role + '-readback.stderr')).write_text(response.stderr)
        response.check_returncode()
        result[role] = json.loads(response.stdout)

    def adb(*arguments):
        return subprocess.check_output(['adb', *arguments], text=True, stderr=subprocess.PIPE, timeout=25).strip()

    assert len([line for line in adb('devices').splitlines() if line.endswith('\tdevice')]) == 1
    metadata = adb('shell', 'dumpsys', 'package', 'com.familyconnect.app.friends')
    apk = adb('shell', 'pm', 'path', 'com.familyconnect.app.friends').removeprefix('package:')
    native = adb('shell', 'find', re.search(r'legacyNativeLibraryDir=(\S+)', metadata)[1],
                 '-name', 'libfc_restricted.so')
    result['phone'] = dict(version_code=int(re.search(r'versionCode=(\d+)', metadata)[1]),
                           apk_sha256=adb('shell', 'sha256sum', apk).split()[0],
                           native_sha256=adb('shell', 'sha256sum', native).split()[0])
    with (OUT / 'baseline.json').open('x') as handle:
        json.dump(result, handle, indent=2)
    assert result['phone'] == dict(version_code=88,
        apk_sha256='968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce',
        native_sha256='dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23')
    assert result['NL']['loaded_gateway_sha256'] == '4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7'
    assert result['RU']['directory'] == result['NL']['directory']
    assert result['RU']['source_pins_match'] and result['NL']['source_pins_match']
    print(json.dumps(dict(result='PASS_EXACT_BASELINE', phone=result['phone'],
                          gateway=result['NL']['loaded_gateway_sha256'], validity=result['NL']['validity'],
                          admission=result['RU']['admission_mode'], receipt_sha256=digest(OUT / 'baseline.json'))))


if __name__ == '__main__':
    main()
