"""Guarded in-place beta88->89 update. No Disconnect, enrollment or data clearing."""

import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'
PACKAGE = 'com.familyconnect.app.friends'


def adb(*args, timeout=25):
    return subprocess.check_output(['adb', *args], text=True, stderr=subprocess.PIPE, timeout=timeout).strip()


def snapshot():
    devices = [line for line in adb('devices').splitlines() if line.endswith('\tdevice')]
    assert len(devices) == 1
    raw = adb('shell', 'dumpsys', 'package', PACKAGE)
    path = adb('shell', 'pm', 'path', PACKAGE).removeprefix('package:')
    native = adb('shell', 'find', re.search(r'legacyNativeLibraryDir=(\S+)', raw)[1], '-name', 'libfc_restricted.so')
    connectivity = adb('shell', 'dumpsys', 'connectivity')
    services = adb('shell', 'dumpsys', 'activity', 'services', PACKAGE)
    return dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), uid=int(re.search(r'userId=(\d+)', raw)[1]),
        code=int(re.search(r'versionCode=(\d+)', raw)[1]), apk_sha256=adb('shell', 'sha256sum', path).split()[0],
        native_sha256=adb('shell', 'sha256sum', native).split()[0],
        vpn=any('Transports:' in line and re.search(r'\bVPN\b', line) for line in connectivity.splitlines()),
        vpn_service=any('ServiceRecord{' in line and any(name in line for name in ('.ConnectionService', '.TcpVpnService', 'GoBackend$VpnService')) for line in services.splitlines()))


def identity(label):
    previous = ROOT / 'state-client-build/beta87-product-fix-20261019/identity_readback88.py'
    syntax = ast.parse(previous.read_text())
    remote = next(ast.literal_eval(node.value) for node in syntax.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == 'remote' for target in node.targets))
    if label == 'after':
        remote = remote.replace("version_code')=88", "version_code')=89").replace('beta88_readiness', 'beta89_readiness')
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', 'root@185.251.89.19',
                             'python3 -B -'], input=remote, text=True, capture_output=True, timeout=30)
    result.check_returncode()
    record = json.loads(result.stdout)
    reference = json.loads((previous.parent / 'identity-before88.json').read_text())
    assert all(record[key] == reference[key] for key in ('identity_bindings_sha256', 'support_id_sha256', 'owner_record_count'))
    assert not record['owner_revoked']
    with (WORK / ('identity-' + label + '.json')).open('x') as handle:
        json.dump(record, handle, indent=2)
    return record


def main():
    os.umask(0o077)
    mode = sys.argv[1]
    assert mode in ('check', 'install', 'identity-after')
    if mode == 'identity-after':
        record = identity('after')
        print(json.dumps(dict(identity_preserved=True, ready=record.get('beta89_readiness', {}).get('result'))))
        return
    current = snapshot()
    if mode == 'check':
        print(json.dumps(current))
        return
    signing = json.loads((WORK / 'delivery/signing-receipt.json').read_text())
    assert current['code'] == 88 and current['apk_sha256'] == signing['baseline']['sha256']
    assert current['native_sha256'] == 'dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23'
    assert not (WORK / 'upgrade-intent.json').exists(), 'Reconcile prior installation first'
    if current['vpn'] or current['vpn_service']:
        print(json.dumps(dict(result='WAIT_FOR_ORDINARY_DISCONNECT', changed=False)))
        return
    identity('before')
    apk = WORK / 'delivery/FamilyConnect-0.1.18-beta89-mesh-trace.apk'
    assert hashlib.sha256(apk.read_bytes()).hexdigest() == signing['signed']['sha256']
    with (WORK / 'upgrade-intent.json').open('x') as handle:
        json.dump(dict(before=current, signed=signing['signed'], method='adb install -r'), handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    result = subprocess.run(['adb', 'install', '-r', str(apk)], text=True, capture_output=True, timeout=180)
    after = snapshot()
    with (WORK / 'upgrade-receipt.json').open('x') as handle:
        json.dump(dict(exit=result.returncode, stdout=result.stdout, stderr=result.stderr, before=current, after=after,
                       uninstall=False, data_cleared=False, identity_proof_pending=True), handle, indent=2)
    assert result.returncode == 0 and result.stdout.strip().endswith('Success')
    assert after['uid'] == current['uid'] and after['code'] == 89
    assert after['apk_sha256'] == signing['signed']['sha256'] and after['native_sha256'] == signing['native_sha256']
    print(json.dumps(dict(result='IN_PLACE_UPDATE_VERIFIED', after=after)))


if __name__ == '__main__':
    main()
