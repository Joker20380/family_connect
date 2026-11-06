import hashlib
from pathlib import Path
import zipfile

import pytest

from scripts.package_subscription_overlay import build


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def baseline(tmp_path):
    handler = (ROOT / 'deploy/friends/access-api.py').read_bytes()
    handler = handler.replace(b'from control.friends.subscription import Unsupported as SubscriptionUnsupported\n', b'')
    handler = handler.replace(b",'/friends/device/subscription'", b'')
    handler = handler.replace(b"   elif self.path=='/friends/device/subscription':\n    from control.friends.subscription import request\n    result=request(access,value)\n", b'')
    handler = handler.replace(b"  except SubscriptionUnsupported:self.reply(501,{'error':'subscription-unsupported'})\n", b'')
    access = (ROOT / 'control/friends/access.py').read_bytes().replace(b",'subscription'", b'')
    path = tmp_path / 'serving.pyz'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('friends_http.py', handler)
        archive.writestr('control/friends/access.py', access)
        archive.writestr('control/friends/restricted.py', b'preserve newer serving bootstrap/renewal')
        archive.writestr('control/friends/paid_beta.py', b'preserve accepted paid baseline')
    return path


def test_overlay_preserves_other_members_and_exact_status(baseline, tmp_path):
    output = tmp_path / 'candidate.pyz'
    receipt = build(baseline, hashlib.sha256(baseline.read_bytes()).hexdigest(), output)
    with zipfile.ZipFile(baseline) as before, zipfile.ZipFile(output) as after:
        assert set(after.namelist()) == set(before.namelist()) | {'control/friends/subscription.py'}
        for name in ('control/friends/restricted.py', 'control/friends/paid_beta.py'):
            assert after.read(name) == before.read(name)
        assert after.read('friends_http.py') == (ROOT / 'deploy/friends/access-api.py').read_bytes()
        assert after.read('control/friends/access.py') == (ROOT / 'control/friends/access.py').read_bytes()
    assert receipt['unchanged_members'] == 2
    with pytest.raises(ValueError, match='already present'):
        build(output, receipt['candidate_sha256'], tmp_path / 'duplicate.pyz')


def test_wrong_pin_leaves_no_output(baseline, tmp_path):
    output = tmp_path / 'candidate.pyz'
    with pytest.raises(ValueError, match='pin mismatch'):
        build(baseline, '0' * 64, output)
    assert not output.exists()


def test_unreviewed_handler_fails_closed(baseline, tmp_path):
    with zipfile.ZipFile(baseline, 'a') as archive:
        archive.writestr('control/friends/subscription.py', b'already supported')
    with pytest.raises(ValueError):
        build(baseline, hashlib.sha256(baseline.read_bytes()).hexdigest(), tmp_path / 'candidate.pyz')
