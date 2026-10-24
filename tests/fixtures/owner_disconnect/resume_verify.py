"""Read-only beta105 artifact reconciliation; never signs, installs or probes traffic."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/owner-pressure105-20261022'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def members(path):
    with zipfile.ZipFile(path) as archive:
        return {name: hashlib.sha256(archive.read(name)).hexdigest()
                for name in archive.namelist() if not name.startswith('META-INF/')}


def main():
    os.umask(0o077)
    destination = Path(sys.argv[1]).resolve()
    assert destination.is_relative_to((ROOT / 'state-client-build').resolve())
    destination.mkdir(parents=True, exist_ok=False)
    helper = runpy.run_path(str(ROOT / 'tests/fixtures/mesh_throughput_trace/sign.py'))
    metadata = helper['metadata']
    signed = WORK / 'delivery/FamilyConnect-0.1.18-beta105-recovery.apk'
    unsigned = WORK / 'build/android/app/outputs/apk/privateBeta/app-privateBeta-unsigned.apk'
    signing = json.loads((WORK / 'delivery/signing-receipt.json').read_text())
    build = json.loads((WORK / 'build/receipt.json').read_text())
    install = json.loads((WORK / 'install-receipt.json').read_text())
    observed = metadata(signed, 105, True)
    assert observed == signing['signed']
    assert digest(unsigned) == build['apk_sha256'] == signing['unsigned']['sha256']
    assert members(signed) == members(unsigned)
    native = {name: value for name, value in members(signed).items() if name.startswith('lib/')}
    assert len(native) == 12
    assert native['lib/arm64-v8a/libfc_restricted.so'] == build['native_sha256'] == signing['native_sha256']
    inventory_path = WORK / 'build/complete-source-inventory.json'
    inventory = json.loads(inventory_path.read_text())
    assert all(digest(WORK / 'android-source' / name) == value for name, value in inventory.items())
    build_inventory = WORK / 'build/source-inventory.json'
    source_hash = hashlib.sha256(json.dumps(json.loads(build_inventory.read_text()),
                                           sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert source_hash == build['source_inventory']
    with zipfile.ZipFile(signed) as archive:
        native_manifest = json.loads(archive.read('assets/restricted-build.json'))
    assert native_manifest['binary_sha256'] == build['native_sha256']
    assert native_manifest['source_delta_sha256'] == source_hash
    assert native_manifest['build_tags'] == []
    wrapper = ROOT / 'tests/fixtures/owner_disconnect/pressure.py'
    assert native_manifest['actual_runner_sha256'] == digest(wrapper)
    syntax = ast.parse(wrapper.read_text())
    execute = next(node for node in syntax.body if isinstance(node, ast.FunctionDef) and node.name == 'execute')
    reconstruction = []
    for node in execute.body:
        if isinstance(node, ast.If):
            break
        assert isinstance(node, ast.Assign)
        reconstruction.append(node)
    namespace = dict(FIXTURE=wrapper.parent)
    exec(compile(ast.Module(body=reconstruction, type_ignores=[]), str(wrapper), 'exec'), namespace)
    assert namespace['source'] == (WORK / 'executed-build-runner.py').read_text()
    assert all(digest(WORK / 'android-source' / name) == value
               for name, value in json.loads(build_inventory.read_text()).items())
    delta = json.loads((WORK / 'source-delta-final.json').read_text())
    parent = ROOT / 'state-client-build/owner-reorder104-20261022'
    parent_inventory = json.loads((WORK / 'parent-inventory.json').read_text())
    assert all(digest(parent / 'android-source' / name) == value for name, value in parent_inventory.items())
    actual_delta = {name: dict(before=parent_inventory.get(name), after=value)
                    for name, value in inventory.items() if parent_inventory.get(name) != value}
    assert set(parent_inventory) == set(inventory)
    assert actual_delta == delta
    assert set(delta) == {'carrier/telemost/rtp.go', 'carrier/telemost/owner_late_frame_test.go',
                          'clients/android/app/build.gradle'}
    original = parent / 'delivery/FamilyConnect-0.1.18-beta104-recovery.apk'
    old_native = {name: value for name, value in members(original).items() if name.startswith('lib/')}
    assert set(old_native) == set(native)
    assert [name for name in native if native[name] != old_native[name]] == ['lib/arm64-v8a/libfc_restricted.so']
    assert install['exit'] == 0 and install['stdout'].strip().endswith('Success')
    assert install['before']['code'] == 104 and install['after']['code'] == 105
    assert install['before']['uid'] == install['after']['uid'] == 10283
    assert install['after']['apk_sha256'] == observed['sha256']
    assert install['after']['native_sha256'] == build['native_sha256']
    reports = sorted((WORK / 'build/android/app/test-results/testPrivateBetaUnitTest').glob('TEST-*.xml'))
    suites = [ET.parse(path).getroot().attrib for path in reports]
    assert suites and sum(int(suite['tests']) for suite in suites) == build['tests'] == 213
    assert all(int(suite[field]) == 0 for suite in suites for field in ('failures', 'errors', 'skipped'))
    upgrades = []
    for code, path in [(88, ROOT / 'state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk'),
                       (94, ROOT / 'state-client-build/rtp-deadline-20261020/normal94/delivery/FamilyConnect-0.1.18-beta94-stability.apk'),
                       (104, original)]:
        if not path.is_file():
            upgrades.append(dict(version_code=code, status='ARTIFACT_PATH_NOT_FOUND_NOT_VERIFIED'))
            continue
        old = metadata(path, code, True)
        assert old['package'] == observed['package'] and old['signer_sha256'] == observed['signer_sha256']
        assert old['version_code'] < observed['version_code']
        upgrades.append(dict(artifact=str(path.relative_to(ROOT)), metadata=old,
                             status='STATIC_PACKAGE_SIGNER_CODE_MATCH',
                             physical_upgrade='RETAINED_RECEIPT' if code == 104 else 'NOT_RUN'))
    receipt = dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   result='VERIFIED_EXISTING_SIGNED_APK_NOT_PRIVATE_FIELD_READY',
                   artifact=str(signed.relative_to(ROOT)), metadata=observed, android_min_api=31,
                   abi='arm64-v8a', native=native, signed_unsigned_payload_identical=True,
                   complete_source_count=len(inventory), complete_source_inventory_sha256=digest(inventory_path),
                   source_inventory_sha256=digest(build_inventory), delta=delta,
                   native_manifest=native_manifest,
                   runner_wrapper_sha256=digest(wrapper),
                   generated_runner_sha256=digest(WORK / 'executed-build-runner.py'),
                   generated_runner_reconstructed=True,
                   signing_receipt_sha256=digest(WORK / 'delivery/signing-receipt.json'),
                   build_receipt_sha256=digest(WORK / 'build/receipt.json'),
                   install_receipt_sha256=digest(WORK / 'install-receipt.json'),
                   historical_install=install, current_phone_readback='NOT_REQUESTED_BY_ARTIFACT_VERIFIER',
                   support_id_after_105='UNVERIFIED', upgrades=upgrades,
                   jvm=dict(tests=213, scope='RETAINED_BUILD_REPORTS_NOT_FRESH_RUN',
                            xml_sha256={path.name: digest(path) for path in reports}),
                   signed_apk_ready=True, owner_wifi_acceptance='NOT_ASSESSED_BY_ARTIFACT_VERIFIER',
                   recovery_acceptance='NOT_ASSESSED_BY_ARTIFACT_VERIFIER',
                   tester_p1_policy_ready='NOT_ASSESSED_BY_ARTIFACT_VERIFIER', field_whitelist_validation='NOT_RUN',
                   application_traffic_bytes=0, new_build=False, new_signing=False, install_performed=False)
    target = destination / 'artifact-readback.json'
    target.write_text(json.dumps(receipt, indent=2) + '\n')
    target.chmod(0o400)
    print(json.dumps(dict(result=receipt['result'], receipt=str(target), sha256=digest(target),
                          artifact=observed, source_files=len(inventory), native_libraries=len(native))))


if __name__ == '__main__':
    main()
