"""Reproducible standalone TCP updater setup, with an explicit first-trust boundary."""
import argparse,gzip,hashlib,io,json,re,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES=('clients/linux/install-tcp-updater.py','clients/linux/tcp-update-broker.py','scripts/tcp_delivery.py','clients/desktop/updates.py','clients/desktop/update.pub')
def build(output,version='0.1.0'):
    if not re.fullmatch(r'(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})',version):raise ValueError('Invalid setup version')
    files={n:(ROOT/n).read_bytes() for n in SOURCES}
    files['install.py']=(ROOT/'clients/linux/install-tcp-setup.py').read_bytes()
    files['README.txt']=b'''Family Connect TCP updater setup - Debian 12 / Ubuntu, Linux amd64 pilot
No Git checkout, VPN profile or private signing key is included or required.
First trust: obtain this setup from an authenticated publisher channel and compare
its SHA256 with an independently trusted expected value BEFORE executing it as root.
The included manifest detects corruption; it is NOT an independent signature.
The included public key is a trust anchor only after you have authenticated this setup.
Dependencies (Debian 12): python3 python3-cryptography iproute2 procps curl
systemd systemd-resolved pkexec ca-certificates. A booted systemd and /dev/net/tun
are required. Configure normal system DNS/resolved for your machine first.
Extract as a normal user into an empty directory, then: sudo python3 -I install.py
This installs only the root-owned TCP updater; it does not start VPN or import profiles.
Then use Install / update TCP in the Linux pilot, or:
pkexec /usr/local/lib/family-connect-tcp-updater/broker install
The broker downloads the fixed published TCP catalog and verifies its Ed25519 signature.
It never trusts caller-provided URLs, profiles, keys or executable paths.
Backups: /var/backups/family-connect/tcp-updater-*/restore.json.
For rollback, stop updater work, hold /run/family-connect-tcp-updater.lock,
restore previous_modes files to /usr/local/lib/family-connect-tcp-updater and remove
only new_files. Do not delete profiles or update floors. See publisher runbook.
This setup is a pilot artifact; it is not a new desktop release or unattended update.
'''
    manifest={'format':1,'version':version,'architecture':'amd64','sha256':{n:hashlib.sha256(v).hexdigest() for n,v in sorted(files.items())}}
    files['manifest.json']=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()
    with output.open('xb') as out,gzip.GzipFile(fileobj=out,filename='',mode='wb',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w') as archive:
        for name,raw in sorted(files.items()):
            info=tarfile.TarInfo(f'FamilyConnect-TCP-Setup-{version}/'+name);info.size=len(raw);info.mode=0o755 if name=='install.py' else 0o644
            archive.addfile(info,io.BytesIO(raw))
    return hashlib.sha256(output.read_bytes()).hexdigest()
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--version',default='0.1.0');a=p.parse_args();print(build(a.output,a.version))
