import json
from pathlib import Path

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
