import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('restricted_ci', ROOT / 'pilot/android-restricted/package_ci.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_retained_native_source_requires_equal_dependency_tree(tmp_path):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=tmp_path, text=True).strip()
    git('init', '-q')
    git('config', 'user.name', 'Disposable Test')
    git('config', 'user.email', 'test@example.invalid')
    for name in ('carrier/coldprovision/channel.go', 'carrier/cmd/entry/main.go', 'clients/android/version'):
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('one')
    git('add', '.')
    git('commit', '-qm', 'base')
    native = git('rev-parse', 'HEAD')
    (tmp_path/'clients/android/version').write_text('two')
    (tmp_path/'carrier/cmd/entry/main.go').write_text('two')
    git('commit', '-qam', 'delivery only')
    module.verify_native_source(native, git('rev-parse', 'HEAD'), tmp_path)
    (tmp_path/'carrier/coldprovision/channel.go').write_text('changed native dependency')
    git('commit', '-qam', 'native delta')
    with pytest.raises(subprocess.CalledProcessError):
        module.verify_native_source(native, git('rev-parse', 'HEAD'), tmp_path)


@pytest.mark.parametrize('fault', ['', 'native', 'manifest', 'source', 'dex', 'revision', 'tags', 'producer', 'patch',
                                   'local-core-tag', 'local-core-provider', 'local-core-diagnostic', 'local-core-abi'])
def test_exact_native_and_diagnostic_contract(tmp_path, fault):
    native = tmp_path / 'native.so'
    native.write_bytes(b'synthetic native')
    revision = 'a' * 40
    manifest = dict(binary_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),
                    xray_revision='d2758a023cd7f4174a5a5fa4ff66e487d4342ba0',
                    metadata_schema=2, source_revision=revision, source_tree='b' * 40,
                    provider='telemost', abi='arm64-v8a', build_tags=[], diagnostic_only=False,
                    owner_diagnostic_fault_schema=0,
                    builder_sha256=module.digest((ROOT / 'pilot/android-restricted/build.py').read_bytes()),
                    patch_sha256=module.digest((ROOT / 'pilot/android-restricted/xray-packet-boundary.patch').read_bytes()))
    if fault == 'revision':
        manifest['source_revision'] = 'c' * 40
    if fault == 'tags':
        manifest['build_tags'] = ['fc_owner_diagnostic']
    if fault == 'local-core-tag':
        manifest['build_tags'] = ['fc_local_core']
    if fault == 'local-core-provider':
        manifest['provider'] = 'isolated-local-core'
    if fault == 'local-core-diagnostic':
        manifest['diagnostic_only'] = True
    if fault == 'local-core-abi':
        manifest['abi'] = 'x86_64'
    if fault == 'producer':
        manifest['builder_sha256'] = '0' * 64
    if fault == 'patch':
        manifest['patch_sha256'] = '0' * 64
    if fault == 'source':
        manifest['xray_revision'] = 'foreign'
    metadata = tmp_path / 'build.json'
    metadata.write_text(json.dumps(manifest))
    apk = tmp_path / 'test.apk'
    with zipfile.ZipFile(apk, 'w') as archive:
        archive.writestr('lib/arm64-v8a/libfc_restricted.so', b'stale native' if fault == 'native' else native.read_bytes())
        archive.writestr('assets/restricted-build.json', '{}' if fault == 'manifest' else metadata.read_bytes())
        archive.writestr('classes.dex', b'old contract' if fault == 'dex' else b'restricted_session')
    if fault:
        with pytest.raises(ValueError):
            module.inspect(apk, native, metadata, revision)
    else:
        assert module.inspect(apk, native, metadata, revision) == manifest
