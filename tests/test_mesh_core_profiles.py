import json
from types import SimpleNamespace

import pytest

from test_mesh_core_soak import canonical_profile


def profile_stand(tmp_path):
    live = tmp_path/'live'
    live.mkdir()
    (live/'gateway.json').write_text(json.dumps(dict(minimum_crl=1)))
    profile = tmp_path/'canonical.json'
    locator = tmp_path/'locator.json'
    locator.write_text(json.dumps(dict(profile=str(profile))))
    config = tmp_path/'node.json'
    config.write_text(json.dumps(dict(profile_locator=str(locator))))
    stand = SimpleNamespace(configs={'NL': config}, fleet=SimpleNamespace(
        nodes={'NL': SimpleNamespace(live=live)}))
    return stand, profile


def test_revocation_evidence_reads_canonical_profile_not_initial_fixture(tmp_path):
    stand, profile = profile_stand(tmp_path)
    profile.write_text(json.dumps(dict(minimum_crl=6)))
    assert canonical_profile(stand, 'NL') == dict(minimum_crl=6)
    profile.write_text(json.dumps(dict(minimum_crl=7)))
    assert canonical_profile(stand, 'NL') == dict(minimum_crl=7)


def test_missing_canonical_profile_does_not_fall_back_to_initial_fixture(tmp_path):
    stand, profile = profile_stand(tmp_path)
    assert not profile.exists()
    with pytest.raises(FileNotFoundError):
        canonical_profile(stand, 'NL')
