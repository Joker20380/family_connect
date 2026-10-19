"""Private beta89 signing with the existing GUI vault workflow and certificate pin."""

import ast
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import tarfile
from types import SimpleNamespace
import zipfile

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'
TOOLS = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
SIGNER = '67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata(path, code, signed):
    sdk = TOOLS / 'android/build-tools/35.0.0'
    output = subprocess.check_output([sdk / 'aapt', 'dump', 'badging', path], text=True, timeout=30)
    package = re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", output)
    assert package and package[1] == 'com.familyconnect.app.friends' and package[2] == str(code)
    assert re.search(r"sdkVersion:'(\d+)'", output)[1] == '31'
    assert re.search(r"native-code: (.+)", output)[1] == "'arm64-v8a'"
    subprocess.run([sdk / 'zipalign', '-c', '-P', '16', '4', path], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    if signed:
        output = subprocess.check_output([TOOLS / 'jdk/bin/java', '-jar', sdk / 'lib/apksigner.jar',
                                         'verify', '--verbose', '--print-certs', path], text=True, timeout=30)
        assert re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-f]{64})', output) == [SIGNER]
    return dict(package=package[1], version_code=code, version=package[3], sha256=sha(path),
                alignment_16k=True, signer_sha256=SIGNER if signed else None)


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    receipt = json.loads((WORK / 'build/receipt.json').read_text())
    assert receipt['result'] == 'PASS_LOCAL_BUILD_JVM' and receipt['tests'] >= 169
    inventory = json.loads((WORK / 'build/source-inventory.json').read_text())
    assert all(sha(WORK / 'android-source' / name) == digest for name, digest in inventory.items())
    unsigned = WORK / 'build/android/app/outputs/apk/privateBeta/app-privateBeta-unsigned.apk'
    baseline = ROOT / 'state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk'
    assert sha(unsigned) == receipt['apk_sha256']
    assert sha(baseline) == '968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce'
    before, candidate = metadata(baseline, 88, True), metadata(unsigned, 89, False)
    with zipfile.ZipFile(baseline) as old, zipfile.ZipFile(unsigned) as new:
        libraries = {name for name in old.namelist() if name.startswith('lib/')}
        assert len(libraries) == 12 and libraries == {name for name in new.namelist() if name.startswith('lib/')}
        assert [name for name in sorted(libraries) if old.read(name) != new.read(name)] == ['lib/arm64-v8a/libfc_restricted.so']
        manifest = json.loads(new.read('assets/restricted-build.json'))
        assert manifest['build_tags'] == ['fc_perf_diagnostic'] and manifest['owner_diagnostic_fault_schema'] == 0
        assert manifest['binary_sha256'] == receipt['native_sha256']
        for name in new.namelist():
            if name.endswith('.dex'):
                assert b'Lcom/familyconnect/app/ProvisioningWindow;' not in new.read(name)
                assert b'RESEARCH_CONTRACT' not in new.read(name)
    signed = WORK / 'delivery/FamilyConnect-0.1.18-beta89-mesh-trace.apk'
    if signed.exists():
        print(json.dumps(metadata(signed, 89, True)))
        return
    if '--check-only' in sys.argv:
        print(json.dumps(dict(result='VERIFIED_UNSIGNED_OBSERVATION_ONLY', candidate=candidate, baseline=before)))
        return
    signed.parent.mkdir(mode=0o700, exist_ok=True)
    sys.path.insert(0, str(ROOT))
    from scripts import sign_android_vault, signing_key
    helper = ROOT / 'state-client-build/bootstrap-cause-owner-1-owner-research2/tools/vault_sign_once.py'
    assert sha(helper) == 'f4f5bfb02f67ef76700ad2dd29163a8eab5a267fdb2045e072c51a18a70896df'
    definitions = [node for node in ast.parse(helper.read_text()).body if isinstance(node, ast.FunctionDef)
                   and node.name in ('choose', 'discovery_run')]
    original_run = subprocess.run
    namespace = dict(subprocess=subprocess, original_run=original_run)
    exec(compile(ast.Module(body=definitions, type_ignores=[]), '<existing-vault-workflow>', 'exec'), namespace)
    vault = Path(namespace['choose']('Family Connect: existing Android signer vault',
        sorted(str(path) for path in Path('/home/joker/.local/share/family-connect-vault').glob('*.kdbx'))))
    subprocess.run = namespace['discovery_run']
    try:
        raw = signing_key.vault_archive(SimpleNamespace(vault=vault, vault_entry='resolved-in-memory-before-export', vault_password_dialog=True))
    finally:
        subprocess.run = original_run
    names, total, count = [], 0, 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r|gz') as archive:
        for member in archive:
            total += member.size
            count += 1
            assert 0 <= member.size and total <= signing_key.LIMIT and count <= 1024
            if member.isfile():
                names.append(member.name)
    member = namespace['choose']('Family Connect: existing Android PKCS12', [name for name in names if Path(name).suffix.lower() in ('.p12', '.pfx')])
    password_member = namespace['choose']('Family Connect: existing password member',
        [name for name in names if Path(name).parent == Path(member).parent and 'pass' in Path(name).name.lower()])
    store, password = sign_android_vault.credentials(raw, member, password_member, SIGNER)
    raw = None
    checksum = sign_android_vault.sign(store, password, SimpleNamespace(apk=unsigned, apk_sha256=sha(unsigned), output=signed,
        java=TOOLS / 'jdk/bin/java', apksigner_jar=TOOLS / 'android/build-tools/35.0.0/lib/apksigner.jar', certificate_sha256=SIGNER))
    store = password = None
    actual = metadata(signed, 89, True)
    assert actual['sha256'] == checksum
    with zipfile.ZipFile(unsigned) as old, zipfile.ZipFile(signed) as new:
        assert all(old.read(name) == new.read(name) for name in old.namelist() if not name.startswith('META-INF/'))
    result = dict(result='SIGNED_PRIVATE_OBSERVATION_NOT_SPEED_FIX', signed=actual, unsigned=candidate, baseline=before,
                  native_sha256=receipt['native_sha256'], installed=False, distributed=False, private_key_exported=False)
    with (signed.parent / 'signing-receipt.json').open('x') as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('SIGNING_STOPPED_NO_SECRET_OUTPUT')
        raise SystemExit(1) from None
