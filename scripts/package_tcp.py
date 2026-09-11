"""Deterministic amd64 TCP component archive; separate from the desktop updater."""
import argparse,gzip,hashlib,io,json,struct,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
XRAY_REV='d2758a023cd7f4174a5a5fa4ff66e487d4342ba0'
def build(binary,output):
    raw=binary.read_bytes()
    if raw[:6]!=b'\x7fELF\x02\x01' or len(raw)<64 or struct.unpack('<H',raw[18:20])[0]!=62:
        raise ValueError('Expected Linux amd64 ELF binary')
    sources={'lib/helper':'clients/linux/tcp-helper.py','lib/backend.py':'clients/desktop/backend.py',
        'lib/profile_config.py':'clients/desktop/profile_config.py','lib/LICENSE':'pilot/tcp/LICENSE-Xray',
        'systemd/family-connect-tcp@.service':'clients/linux/family-connect-tcp@.service',
        'install.py':'clients/linux/install-tcp-bundle.py'}
    files={name:(ROOT/src).read_bytes() for name,src in sources.items()};files['bin/xray']=raw
    files['README.txt']=b'''Family Connect TCP components (Linux amd64 pilot)
Requires Python 3, iproute2, procps, curl, systemd + systemd-resolved, pkexec, /dev/net/tun.
On Debian 12: apt install python3 iproute2 procps curl systemd systemd-resolved pkexec
Use only a trusted archive; manifest hashes detect corruption, NOT authenticity.
Extract as a normal user, then: sudo python3 -I install.py
Installer refuses active TCP, preserves backups, never imports keys or starts VPN.
Existing profiles stay in /etc/family-connect/tcp. Desktop updater remains separate.
Backup location is printed; restore.json describes old files/modes and newly added files.
Before manual rollback stop TCP and finish routing cleanup; restore only listed component files.
This local pilot archive is not a signed release. Do not replace a published version.
'''
    manifest={'format':1,'architecture':'amd64','xray_source_revision':XRAY_REV,
        'provenance':'Binary supplied by operator; build using pinned pilot/tcp/Dockerfile',
        'sha256':{n:hashlib.sha256(v).hexdigest() for n,v in sorted(files.items())}}
    files['manifest.json']=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()
    with output.open('xb') as out,gzip.GzipFile(fileobj=out,filename='',mode='wb',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w') as archive:
        for name,data in sorted(files.items()):
            info=tarfile.TarInfo('FamilyConnect-TCP-amd64/'+name);info.size=len(data);info.mode=0o755 if name in ('bin/xray','lib/helper','install.py') else 0o644
            archive.addfile(info,io.BytesIO(data))
    return hashlib.sha256(output.read_bytes()).hexdigest()
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--xray',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    print(build(args.xray,args.output))
