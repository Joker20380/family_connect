"""Final executable/APK/native and operator policy readback; no mutation."""

import json
import sys
from prepare import ROOT, WORK, digest

original=ROOT/'tests/fixtures/queue_retry/readback.py'
assert digest(original)=='85d5b502f3e46779c3be16bdb064e7068f3240c89a13fece3ce769ae3a3cb2c1'
signing=json.loads((WORK/'delivery/signing-receipt.json').read_text())
gateway=json.loads((WORK/'negotiated-build.json').read_text())
source=original.read_text().replace('from prepare import APK, GATEWAY, WORK','')
source=source.replace("phone['code']==90","phone['code']==95").replace('dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23',signing['native_sha256'])
source=source.replace('profile_sha256=hashlib.sha256(profile.read_bytes()).hexdigest()', "profile_sha256=hashlib.sha256(profile.read_bytes()).hexdigest(),operator_profile=Path('/opt/apps/family_connect/friends-restricted/diag67/mux-profile').read_text().strip(),bounded_counters=Path('/opt/apps/family_connect/friends-restricted/diag67/mux-counters').read_text().strip(),resources=subprocess.check_output(['systemctl','show',unit,'-p','MemoryCurrent,MemoryPeak,MemoryMax,MemoryHigh,TasksCurrent,TasksMax'],text=True).splitlines()")
exec(compile(source,str(original),'exec'),dict(__name__='__main__',__file__=str(original),WORK=WORK,APK=signing['signed']['sha256'],GATEWAY=gateway['sha256']))
