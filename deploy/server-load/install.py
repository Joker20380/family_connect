"""Install only Family Connect read-only sampling; no VPN service restart."""
import argparse
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess

ROOT=Path('/opt/apps/family_connect/server-load')
def run(*args):return subprocess.run(args,check=True,capture_output=True,text=True)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('country',choices=['ru','nl']);args=parser.parse_args()
    assert os.geteuid()==0
    try:user=pwd.getpwnam('fc-load')
    except KeyError:
        run('useradd','--system','--no-create-home','--shell','/usr/sbin/nologin','fc-load');user=pwd.getpwnam('fc-load')
    ROOT.mkdir(mode=0o755,exist_ok=True)
    state=ROOT/'state';state.mkdir(mode=0o700,exist_ok=True);os.chown(state,user.pw_uid,user.pw_gid)
    public=ROOT/'snapshot';public.mkdir(mode=0o755,exist_ok=True);os.chown(public,user.pw_uid,user.pw_gid)
    source=Path(__file__).with_name('monitor.py');target=ROOT/'monitor.py'
    shutil.copyfile(source,target);target.chmod(0o644)
    interface=json.loads((ROOT.parent/'friends-awg/settings.json').read_text())['external']
    assert interface.replace('-','').replace('_','').isalnum()
    config=dict(country=args.country,interface=interface,capacity_mbps=None,snapshot=str(public/'snapshot.json'))
    paths=[str(public)]
    if args.country=='ru':
        key=state/'read-nl'
        if not key.exists():run('ssh-keygen','-q','-t','ed25519','-N','','-C','fc-server-load-readonly','-f',str(key))
        for name in (key,key.with_suffix('.pub')):os.chown(name,user.pw_uid,user.pw_gid)
        key.chmod(0o600)
        known=state/'known_hosts';shutil.copyfile(ROOT.parent/'friends-awg/known_hosts',known);known.chmod(0o600);os.chown(known,user.pw_uid,user.pw_gid)
        output=ROOT.parent/'state-product-https/config/server-load';output.mkdir(mode=0o755,exist_ok=True);os.chown(output,user.pw_uid,user.pw_gid)
        config.update(key=str(key),known_hosts=str(known),public=str(output/'snapshot.json'));paths.append(str(output))
    path=ROOT/'config.json'
    # Capacity is operator-provided. Never guess or overwrite a configured value.
    if path.exists():config['capacity_mbps']=json.loads(path.read_text()).get('capacity_mbps')
    path.write_text(json.dumps(config,indent=2)+'\n');path.chmod(0o644)
    unit=Path('/etc/systemd/system/family-connect-server-load.service')
    unit.write_text('''[Unit]
Description=Family Connect read-only server utilization
After=network-online.target
[Service]
Type=simple
User=fc-load
Group=fc-load
ExecStart=/usr/bin/python3 /opt/apps/family_connect/server-load/monitor.py /opt/apps/family_connect/server-load/config.json
Restart=on-failure
RestartSec=10
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictSUIDSGID=true
CapabilityBoundingSet=
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
MemoryMax=96M
CPUQuota=5%
ReadWritePaths='''+' '.join(paths)+'''
[Install]
WantedBy=multi-user.target
''')
    run('systemctl','daemon-reload');run('systemctl','enable','--now','family-connect-server-load.service')
    print(args.country+': read-only monitor installed; capacity remains unconfigured')
if __name__=='__main__':main()
