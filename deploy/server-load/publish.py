from pathlib import Path
import subprocess
root=Path('/opt/apps/family_connect/state-product-https/config')
section='''        location = /status/server-load.json {
            alias /etc/fc/server-load/snapshot.json;
            default_type application/json;
            limit_except GET { deny all; }
            add_header Cache-Control "no-store" always;
            add_header X-Content-Type-Options nosniff always;
        }
'''
changed=[]
try:
 for name in ('nginx.conf','nginx-final.conf'):
  p=root/name;s=p.read_text();assert '/status/server-load.json' not in s
  backup=root/(name+'.before-server-load-20260920');assert not backup.exists();backup.write_text(s)
  assert s.count('        location = /invite/ {')==1
  p.write_text(s.replace('        location = /invite/ {',section+'        location = /invite/ {'));changed.append((p,s))
 subprocess.run(['docker','exec','family-connect-product-https','nginx','-t','-c','/etc/fc/nginx.conf'],check=True)
 subprocess.run(['docker','kill','--signal=HUP','family-connect-product-https'],check=True,stdout=subprocess.DEVNULL)
except BaseException:
 for p,s in changed:p.write_text(s)
 subprocess.run(['docker','kill','--signal=HUP','family-connect-product-https'],stdout=subprocess.DEVNULL)
 raise
print('Read-only aggregate load endpoint enabled; existing API/downloads preserved.')
