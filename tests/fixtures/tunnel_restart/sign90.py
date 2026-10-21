"""Use the existing protected vault dialog, never export signing secrets."""

import ast
import io
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tarfile
from types import SimpleNamespace
import zipfile

from preserve import ROOT, WORK, digest


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    assert digest(ROOT / 'tests/fixtures/mesh_throughput_trace/sign.py') == 'e9d703553ab073ce25a0e76312827a5b650c6cb5ce2a2ab854f1f5d672ab56e3'
    sys.path.insert(0, str(ROOT / 'tests/fixtures/mesh_throughput_trace'))
    from sign import metadata, SIGNER, TOOLS
    output = WORK / 'android-build'
    receipt = json.loads((output / 'receipt.json').read_text())
    assert receipt['result'] == 'PASS_LOCAL_BUILD_JVM' and receipt['tests'] == 169
    assert receipt['java_equal_beta88'] and receipt['all_12_native_libraries_equal_beta88']
    unsigned = output / 'android/app/outputs/apk/privateBeta/app-privateBeta-unsigned.apk'
    assert digest(unsigned) == receipt['apk_sha256']
    inventory = json.loads((output / 'source-inventory.json').read_text())
    assert all(digest(WORK / 'android-source' / name) == value for name, value in inventory.items())
    baseline = ROOT / 'state-client-build/mesh-throughput-trace-20261019/delivery/FamilyConnect-0.1.18-beta89-mesh-trace.apk'
    before, candidate = metadata(baseline, 89, True), metadata(unsigned, 90, False)
    signed = WORK / 'delivery/FamilyConnect-0.1.18-beta90-stability.apk'
    assert not signed.exists(), 'Do not overwrite signed artifacts'
    if '--check-only' in sys.argv:
        print(json.dumps(dict(candidate=candidate, baseline=before, extended_trace=False)))
        return
    signed.parent.mkdir(mode=0o700, exist_ok=True)
    sys.path.insert(0, str(ROOT))
    from scripts import sign_android_vault, signing_key
    helper = ROOT / 'state-client-build/bootstrap-cause-owner-1-owner-research2/tools/vault_sign_once.py'
    assert digest(helper) == 'f4f5bfb02f67ef76700ad2dd29163a8eab5a267fdb2045e072c51a18a70896df'
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
            if member.isfile(): names.append(member.name)
    member = namespace['choose']('Family Connect: existing Android PKCS12', [name for name in names if Path(name).suffix.lower() in ('.p12', '.pfx')])
    password_member = namespace['choose']('Family Connect: existing password member',
        [name for name in names if Path(name).parent == Path(member).parent and 'pass' in Path(name).name.lower()])
    store, password = sign_android_vault.credentials(raw, member, password_member, SIGNER)
    raw = None
    checksum = sign_android_vault.sign(store, password, SimpleNamespace(apk=unsigned, apk_sha256=digest(unsigned), output=signed,
        java=TOOLS / 'jdk/bin/java', apksigner_jar=TOOLS / 'android/build-tools/35.0.0/lib/apksigner.jar', certificate_sha256=SIGNER))
    store = password = None
    actual = metadata(signed, 90, True)
    assert checksum == actual['sha256']
    with zipfile.ZipFile(unsigned) as old, zipfile.ZipFile(signed) as new:
        assert all(old.read(name) == new.read(name) for name in old.namelist() if not name.startswith('META-INF/'))
    result = dict(result='SIGNED_PRIVATE_TRACE_REMOVAL_NOT_CLIENT_RESTART_FIX', signed=actual, unsigned=candidate,
                  baseline=before, native_sha256=receipt['native_sha256'], installed=False, distributed=False)
    (signed.parent / 'signing-receipt.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('SIGNING_STOPPED_NO_SECRET_OUTPUT')
        raise SystemExit(1) from None
