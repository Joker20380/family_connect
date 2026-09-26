"""Root operator installation; private interface config arrives on stdin."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path('/opt/apps/family_connect/friends-awg');assert os.geteuid()==0 and root.is_dir() and not (root/'server.conf').exists()
for name,digest in [('amneziawg-go','e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f'),('awg','906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278')]:
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest;os.chmod(root/name,0o755)
country=sys.argv[1];assert country in ('ru','nl');prefix='10.84' if country=='ru' else '10.83'
routes=json.loads(subprocess.check_output(['ip','-j','route'],text=True));assert not any(r.get('dst','').startswith(prefix+'.') for r in routes)
external=next(r['dev'] for r in routes if r.get('dst')=='default')
assert subprocess.run(['ip','link','show','fcopen31'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
raw=sys.stdin.read(8193);assert 0<len(raw)<=8192 and '[Peer]' not in raw
os.chmod(root,0o700);os.umask(0o077);(root/'server.conf').write_text(raw)
(root/'settings.json').write_text(json.dumps({'network':prefix+'.0.0/16','address':prefix+'.0.1/16','external':external}))
unit=Path('/etc/systemd/system/family-connect-friends-awg.service');assert not unit.exists()
unit.write_text('''[Unit]
Description=Family Connect open test AWG3.1 gateway
After=network-online.target
Wants=network-online.target
[Service]
UMask=0077
ExecStart=/usr/bin/python3 /opt/apps/family_connect/friends-awg/awg-gateway.py run
Restart=on-failure
RestartSec=3
KillMode=mixed
TimeoutStopSec=90
NoNewPrivileges=true
ProtectHome=true
ProtectSystem=full
PrivateTmp=true
MemoryMax=256M
TasksMax=128
StandardOutput=null
StandardError=journal
[Install]
WantedBy=multi-user.target
''')
subprocess.run(['systemctl','daemon-reload'],check=True);subprocess.run(['systemctl','enable','--now',unit.name],check=True)
print('Separate AWG3.1 service installed; awaiting handshake acceptance')
