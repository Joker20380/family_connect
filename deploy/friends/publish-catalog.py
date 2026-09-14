"""Install already-signed public test catalog on the existing Family Connect HTTPS ingress."""
import json,os,subprocess,sys
from pathlib import Path
root=Path('/opt/apps/family_connect/state-product-https')
assert os.geteuid()==0
raw=sys.stdin.buffer.read(16385);assert 0<len(raw)<=16384
assert set(json.loads(raw))=={'payload','signature'}
public=root/'webroot/friends';public.mkdir(mode=0o755,exist_ok=True)
path=public/'catalog.json';assert not path.exists(),'Immutable first catalog already exists'
path.write_bytes(raw);path.chmod(0o644)
section='''        location = /friends/catalog.json {
            limit_except GET { deny all; }
            alias /var/www/acme/friends/catalog.json;
            default_type application/json;
        }
'''
changed=[]
try:
 for name in ['nginx.conf','nginx-final.conf']:
  p=root/'config'/name;old=p.read_text();assert '/friends/catalog.json' not in old
  backup=p.with_suffix(p.suffix+'.before-friends');assert not backup.exists();backup.write_text(old)
  new=old.replace('        location ~ ^/v2/',section+'        location ~ ^/v2/');assert new!=old
  p.write_text(new);changed.append((p,old))
 subprocess.run(['docker','exec','family-connect-product-https','nginx','-t','-c','/etc/fc/nginx.conf'],check=True)
 subprocess.run(['docker','kill','--signal=HUP','family-connect-product-https'],check=True,stdout=subprocess.DEVNULL)
except BaseException:
 for p,old in changed:p.write_text(old)
 raise
print('Signed open-test catalog published; registration routes and VPN services retained')
