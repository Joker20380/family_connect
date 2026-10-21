"""Reuse read-only binary/phone gate; no session control or counters enabled."""
from prepare import ROOT, WORK, APK, GATEWAY, digest
import json
import sys

if len(sys.argv) == 3:
    assert sys.argv.pop() == 'candidate'
    GATEWAY = json.loads((WORK / 'build-result.json').read_text())['binary_sha256']

original = ROOT / 'tests/fixtures/queue_retry/readback.py'
assert digest(original) == '85d5b502f3e46779c3be16bdb064e7068f3240c89a13fece3ce769ae3a3cb2c1'
source = original.read_text().replace('from prepare import APK, GATEWAY, WORK', '')
source = source.replace("phone['code']==90", "phone['code']==96").replace(
    'dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23',
    '66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63')
source = source.replace('profile_sha256=hashlib.sha256(profile.read_bytes()).hexdigest()',
    "profile_sha256=hashlib.sha256(profile.read_bytes()).hexdigest(),operator_profile=Path('/opt/apps/family_connect/friends-restricted/diag67/mux-profile').read_text().strip(),bounded_counters=Path('/opt/apps/family_connect/friends-restricted/diag67/mux-counters').read_text().strip()")
exec(compile(source, str(original), 'exec'), dict(__name__='__main__', __file__=str(original), WORK=WORK, APK=APK, GATEWAY=GATEWAY))
