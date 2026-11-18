import json
import pytest

from scripts import package_transport_readback as package


def test_packaging_rejects_unpinned_runtime(tmp_path):
    node, gateway = tmp_path/'node', tmp_path/'gateway'
    node.write_bytes(b'unqualified')
    gateway.write_bytes(b'unqualified')
    with pytest.raises(ValueError, match='EXACT_ACCEPTED_RUNTIME_INPUTS_REQUIRED'):
        package.build(node, gateway, tmp_path/'output', 'a'*40)
    assert not (tmp_path/'output').exists()


def test_packaging_requires_exact_source(tmp_path):
    with pytest.raises(ValueError, match='EXPLICIT_FULL_SOURCE_COMMIT_REQUIRED'):
        package.build(tmp_path/'absent', tmp_path/'absent', tmp_path/'output', 'HEAD')


@pytest.mark.parametrize('name', ['/outside', '../outside', 'payload'])
def test_manifest_rejects_unsafe_or_changed_payload(tmp_path, name):
    (tmp_path/'manifest.json').write_text(json.dumps(dict(files={name: dict(sha256='0'*64, mode='0600')})))
    with pytest.raises(ValueError, match='BUNDLE_VERIFICATION_FAILED'):
        package.verify(tmp_path)


def test_reproducible_closed_bundle_and_tamper_detection(tmp_path, monkeypatch):
    node, gateway = tmp_path/'node', tmp_path/'gateway'
    original = {package.POLICY: b'unchanged policy', package.MODULE: b'legacy module'}
    package.archive(node, original)
    gateway.write_bytes(b'legacy entrypoint')
    monkeypatch.setattr(package, 'BASE_NODE', package.sha(node.read_bytes()))
    monkeypatch.setattr(package, 'BASE_GATEWAY', package.sha(gateway.read_bytes()))
    monkeypatch.setattr(package, 'source_bytes', lambda source, revision, path:
        original[package.POLICY] if path == package.POLICY else (revision+':'+path).encode())
    monkeypatch.setattr(package.subprocess, 'check_output', lambda *args, **kwargs: 'b'*40+'\n')
    first, second = tmp_path/'first', tmp_path/'second'
    first_manifest = package.build(node, gateway, first, 'a'*40)
    assert package.build(node, gateway, second, 'a'*40) == first_manifest
    assert package.verify(first) == first_manifest
    assert first_manifest['changed_modules'] == [package.MODULE]
    assert first_manifest['default_mode'] == 'legacy'
    assert (first/'manifest.json').read_bytes() == (second/'manifest.json').read_bytes()
    (first/'unlisted.py').write_bytes(b'unexpected code')
    with pytest.raises(ValueError, match='BUNDLE_VERIFICATION_FAILED'):
        package.verify(first)
    (second/'awg-gateway.py').chmod(0o644)
    with pytest.raises(ValueError, match='BUNDLE_VERIFICATION_FAILED'):
        package.verify(second)
