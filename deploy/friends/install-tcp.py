"""Operator-only isolated open-test TCP gateway; read private server config on stdin."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path('/opt/apps/family_connect/friends-tcp')
BINARY_SHA='4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940'
assert os.geteuid()==0
config=json.load(sys.stdin);port=config['inbounds'][0]['port']
assert port in (443,8446)
assert ROOT.is_dir() and not (ROOT/'server.json').exists()
assert hashlib.sha256((ROOT/'xray').read_bytes()).hexdigest()==BINARY_SHA
assert not any(line.split()[3].rsplit(':',1)[-1]==str(port) for line in subprocess.check_output(['ss','-H','-lnt'],text=True).splitlines())
if subprocess.run(['id','fc-friends'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['useradd','--system','--no-create-home','--shell','/usr/sbin/nologin','fc-friends'],check=True)
import pwd
gid=pwd.getpwnam('fc-friends').pw_gid
os.chmod(ROOT,0o750);os.chown(ROOT,0,gid)
p=ROOT/'server.json';fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o640)
with os.fdopen(fd,'w') as f:json.dump(config,f)
os.chown(p,0,gid);os.chmod(ROOT/'xray',0o755)
result=subprocess.run(['runuser','-u','fc-friends','--',str(ROOT/'xray'),'run','-test','-config',str(p)],capture_output=True)
assert result.returncode==0,'Xray config validation failed (private output withheld)'
unit=Path('/etc/systemd/system/family-connect-friends-tcp.service');assert not unit.exists()
unit.write_text('''[Unit]
Description=Family Connect open test TCP gateway
After=network-online.target
Wants=network-online.target
[Service]
User=fc-friends
Group=fc-friends
ExecStart=/opt/apps/family_connect/friends-tcp/xray run -config /opt/apps/family_connect/friends-tcp/server.json
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
MemoryMax=256M
TasksMax=128
StandardOutput=null
StandardError=null
[Install]
WantedBy=multi-user.target
''')
subprocess.run(['systemctl','daemon-reload'],check=True)
subprocess.run(['systemctl','enable','--now',unit.name],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['systemctl','is-active',unit.name],check=True)
print('Separate open-test TCP service installed; existing services unchanged')
