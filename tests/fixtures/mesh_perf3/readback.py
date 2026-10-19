import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

os.umask(0o077)
out = Path(__file__).resolve().parents[3] / 'state-client-build/mesh-perf-3/receipts'
target = out / (sys.argv[1] + '.json')
assert not target.exists()


def run(args):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE, timeout=35)


remote = r'''
import datetime,hashlib,json,subprocess
from pathlib import Path
from cryptography import x509
root=Path('/opt/apps/family_connect/friends-restricted')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','family-connect-restricted-bootstrap.service','--property=MainPID,InvocationID,ActiveState,SubState,NRestarts'],text=True).splitlines())
profile=json.loads((root/'gateway.json').read_bytes())
ca=x509.load_pem_x509_certificate(profile['authority'].encode());leaf=x509.load_pem_x509_certificate(profile['certificate'].encode());crl=x509.load_pem_x509_crl(profile['revocations'].encode())
leaf.verify_directly_issued_by(ca);assert crl.is_signature_valid(ca.public_key())
now=datetime.datetime.now(datetime.timezone.utc)
valid=all(start<=now<end for start,end in [(ca.not_valid_before_utc,ca.not_valid_after_utc),(leaf.not_valid_before_utc,leaf.not_valid_after_utc),(crl.last_update_utc,crl.next_update_utc)])
print(json.dumps(dict(utc=now.isoformat(),state=state,loaded_sha256=sha(Path('/proc')/state['MainPID']/'exe') if state['MainPID']!='0' else None,profile_sha256=sha(root/'gateway.json'),valid=valid,leaf_expiry=leaf.not_valid_after_utc.isoformat(),ca_expiry=ca.not_valid_after_utc.isoformat(),crl_expiry=crl.next_update_utc.isoformat(),crl_number=crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number)))
'''
result = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
result['nl'] = json.loads(run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'root@186.246.45.246', 'python3 - <<\'PY\'\n' + remote + '\nPY']))
try:
    attached = [line.split()[0] for line in run(['adb', 'devices']).splitlines()[1:] if line.endswith('\tdevice')]
    assert len(attached) == 1
    package = run(['adb', 'shell', 'dumpsys', 'package', 'com.familyconnect.app.friends'])
    apk = run(['adb', 'shell', 'pm', 'path', 'com.familyconnect.app.friends']).strip().removeprefix('package:')
    native_dir = re.search(r'legacyNativeLibraryDir=(\S+)', package).group(1)
    native, = run(['adb', 'shell', 'find', native_dir, '-name', 'libfc_restricted.so']).splitlines()
    connectivity = run(['adb', 'shell', 'dumpsys', 'connectivity'])
    result['phone'] = dict(apk_sha256=run(['adb', 'shell', 'sha256sum', apk]).split()[0], native_sha256=run(['adb', 'shell', 'sha256sum', native]).split()[0], process=run(['adb', 'shell', 'pidof', 'com.familyconnect.app.friends']).strip(), vpn_present=any('ni{VPN' in line and 'OwnerUid: 10283' in line for line in connectivity.splitlines()))
except Exception as failure:
    result['phone'] = dict(error_type=type(failure).__name__)
with target.open('x') as handle:
    json.dump(result, handle, indent=2)
print(json.dumps(result, indent=2))
