"""Overlay only support on the exact read-back HTTP artifact; no deployment."""
import hashlib
import json
from pathlib import Path
import zipfile
import difflib

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'state-client-build/support-automation-20261021'


def main():
    parent=WORK/'http-installed.pyz'
    assert hashlib.sha256(parent.read_bytes()).hexdigest()=='e986f98e70ff7f1abc2678566dd360bb6555583f2e1744ea985c63699bcb3ef7'
    with zipfile.ZipFile(parent) as archive:
        original={name:archive.read(name) for name in archive.namelist()}
    updated=dict(original)
    path='control/friends/access.py';text=updated[path].decode()
    old="  if purpose not in ('activate','status','support','ru','nl','refer','notices-role','notices-publish','notices-list','notices-edit'):raise Rejected()"
    new=next(line for line in (ROOT/path).read_text().splitlines() if line.startswith('  if purpose not in'))
    assert text.count(old)==1
    text=text.replace(old,new)
    if 'import re\n' not in text:text='import re\n'+text
    updated[path]=text.encode()
    path='friends_http.py';text=updated[path].decode()
    changes={"'/friends/device/status','/friends/device/support'":"'/friends/device/status','/friends/device/support','/friends/device/diagnostics'",
             "   elif self.path=='/friends/device/support':":"   elif self.path=='/friends/device/diagnostics':\n    from control.friends.diagnostics import request\n    result=request(access,ROOT/'diagnostics.sqlite',value)\n   elif self.path=='/friends/device/support':",
             " ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()":" from control.friends.diagnostics import start_retention\n retention=start_retention(ROOT/'diagnostics.sqlite')\n try:ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()\n finally:retention.set()"}
    for old,new in changes.items():
        assert text.count(old)==1,old
        text=text.replace(old,new)
    updated[path]=text.encode()
    updated['control/friends/diagnostics.py']=(ROOT/'control/friends/diagnostics.py').read_bytes()
    output=WORK/'http';output.mkdir(exist_ok=True)
    target=output/'friends-http.pyz';assert not target.exists()
    patch=''
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,raw in updated.items():
            entry=zipfile.ZipInfo(name,(1980,1,1,0,0,0));entry.external_attr=0o100644<<16;archive.writestr(entry,raw)
            if raw!=original.get(name):
                patch+=''.join(difflib.unified_diff(original.get(name,b'').decode().splitlines(True),raw.decode().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    (output/'support.patch').write_text(patch)
    changed=[name for name in updated if original.get(name)!=updated[name]]
    assert sorted(changed)==['control/friends/access.py','control/friends/diagnostics.py','friends_http.py']
    receipt=dict(parent_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),changed=changed,deployed=False)
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
