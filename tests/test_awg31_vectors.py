"""Shared signed vectors: explicit support versus unchanged legacy refusal."""
import hashlib
import json
from pathlib import Path

import pytest
from provisioning.configuration import ConfigError, ConfigVerifier
from test_control_vectors import device

ROOT = Path(__file__).parent/'vectors/control-awg31-v1'
MANIFEST = json.loads((ROOT/'manifest.json').read_text())


def test_integrity():
    assert MANIFEST['test_only'] is True
    assert set(p.name for p in ROOT.iterdir()) == set(MANIFEST['files'])|{'manifest.json'}
    for name, expected in MANIFEST['files'].items():
        raw = (ROOT/name).read_bytes()
        assert len(raw) == expected['size']
        assert hashlib.sha256(raw).hexdigest() == expected['sha256']
    _, anchor = device(ROOT)
    import base64
    assert anchor != base64.b64decode((ROOT.parents[2]/'clients/desktop/update.pub').read_text().strip())


@pytest.mark.parametrize('case', MANIFEST['configurations'], ids=lambda case: case['id'])
@pytest.mark.parametrize('supported', [False, True])
def test_vector(case, supported):
    d, anchor = device(ROOT)
    verifier = ConfigVerifier(anchor=anchor, device=d, client_version=case['client_version'],
                              supports_awg31=supported)
    expected = case['expected'] if supported else case['legacy_expected']
    raw = (ROOT/case['input']).read_bytes()
    if expected == 'ACCEPT':
        assert verifier.verify(raw, now=case['now']).state.model_dump(mode='json') == case['payload']
    else:
        with pytest.raises(ConfigError) as error:
            verifier.verify(raw, now=case['now'])
        assert error.value.category == expected
