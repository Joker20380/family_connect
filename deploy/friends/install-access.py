"""Activate private invite API behind existing HTTPS, preserving enrollment routes."""
import os,subprocess,sys,re,hashlib,base64
from pathlib import Path
ROOT=Path('/opt/apps/family_connect/friends-access');assert os.geteuid()==0
sys.path.insert(0,str(ROOT/'app'))
from control.friends.access import Access
from control.friends.chat import ChatAccess
from control.friends.referrals import Referrals
access=Access(ROOT/'access.db');access.initialize();ChatAccess(access).initialize()
# First installation only: never rotate the campaign key on an existing database.
key=ROOT/'referral.key'
if not key.exists():
 with access.db() as db:
  assert db.execute("SELECT name FROM sqlite_master WHERE name='referral_links'").fetchone() is None
 fd=os.open(key,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(os.urandom(32))
Referrals(access,key.read_bytes()).initialize()
html=(ROOT/'invite/index.html').read_text()
digest=lambda tag:base64.b64encode(hashlib.sha256(re.search('<'+tag+'>(.*?)</'+tag+'>',html,re.S).group(1).encode()).digest()).decode()
csp="default-src 'none'; script-src 'sha256-"+digest('script')+"'; style-src 'sha256-"+digest('style')+"'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
assert not (ROOT/'catalog.json').exists();(ROOT/'catalog.json').write_bytes((ROOT/'catalog-invited.json').read_bytes());(ROOT/'catalog.json').chmod(0o600)
unit=Path('/etc/systemd/system/family-connect-friends-access.service');assert not unit.exists()
unit.write_text('''[Unit]
Description=Family Connect device invitation API
After=network-online.target family-connect-friends-awg.service family-connect-friends-tcp.service
Wants=network-online.target
[Service]
ExecStart=/opt/apps/family_connect/friends-access/venv/bin/python /opt/apps/family_connect/friends-access/access-api.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
ProtectHome=true
ProtectSystem=full
PrivateTmp=true
MemoryMax=256M
TasksMax=128
UMask=0077
StandardOutput=null
StandardError=null
[Install]
WantedBy=multi-user.target
''')
subprocess.run(['systemctl','daemon-reload'],check=True);subprocess.run(['systemctl','enable','--now',unit.name],check=True)
section='''        location = /i/ {
            root /etc/fc;
            try_files /invite.html =404;
            default_type text/html;
            add_header Cache-Control "no-store" always;
            add_header Referrer-Policy "no-referrer" always;
            add_header X-Content-Type-Options "nosniff" always;
            add_header Content-Security-Policy "'''+csp+'''" always;
        }
        location = /invite/ {
            root /etc/fc;
            try_files /invite.html =404;
            default_type text/html;
            add_header Cache-Control "no-store" always;
            add_header Referrer-Policy "no-referrer" always;
            add_header X-Content-Type-Options "nosniff" always;
            add_header Content-Security-Policy "'''+csp+'''" always;
        }
        location ~ ^/friends/(challenge|activate|configuration/(ru|nl)|chat/(challenge|register)|referral/(issue|claim)|device/status|notices/publish)$ {
            if ($request_method != POST) { return 405; }
            proxy_pass http://127.0.0.1:18084;
            proxy_set_header Host 127.0.0.1;
            proxy_set_header Connection "";
            proxy_connect_timeout 2s;
            proxy_send_timeout 5s;
            proxy_read_timeout 20s;
            proxy_max_temp_file_size 0;
        }
'''
root=Path('/opt/apps/family_connect/state-product-https/config');changed=[]
(root/'invite.html').write_text(html);(root/'invite.html').chmod(0o644)
try:
 for name in ('nginx.conf','nginx-final.conf'):
  p=root/name;old=p.read_text();assert '127.0.0.1:18084' not in old
  backup=p.with_suffix(p.suffix+'.before-invites');assert not backup.exists();backup.write_text(old)
  start=old.index('        location = /friends/catalog.json {');end=old.index('        location ~ ^/v2/',start)
  p.write_text(old[:start]+section+old[end:]);changed.append((p,old))
 subprocess.run(['docker','exec','family-connect-product-https','nginx','-t','-c','/etc/fc/nginx.conf'],check=True)
 subprocess.run(['docker','kill','--signal=HUP','family-connect-product-https'],check=True,stdout=subprocess.DEVNULL)
except BaseException:
 for p,old in changed:p.write_text(old)
 raise
print('Invite-only API installed; public credential catalog disabled; product routes retained')
