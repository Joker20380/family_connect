"""Guarded support-only update of existing HTTP service; never restarts media gateway."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'state-client-build/support-automation-20261021'


def main():
    receipt=WORK/'http-deploy-2.json'
    assert not receipt.exists(), 'Read back outcome instead of blindly replaying a deployment'
    artifact=WORK/'http/friends-http.pyz'
    sha=hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert sha==json.loads((WORK/'http/receipt.json').read_text())['sha256']
    remote=r"""
import base64,hashlib,json,os,subprocess,time,urllib.request,urllib.error
from pathlib import Path
raw=base64.b64decode(__PAYLOAD__);sha=__SHA__
assert hashlib.sha256(raw).hexdigest()==sha
root=Path('/opt/apps/family_connect/friends-access')
unit='family-connect-friends-http-candidate.service'
before=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
assert before['ActiveState']=='active'
argv=(Path('/proc')/before['MainPID']/'cmdline').read_bytes().split(b'\0')
expected=root/'private-beta-e986f98e70ff7f1abc2678566dd360bb6555583f2e1744ea985c63699bcb3ef7.pyz'
assert str(expected).encode() in argv
assert hashlib.sha256(expected.read_bytes()).hexdigest()=='e986f98e70ff7f1abc2678566dd360bb6555583f2e1744ea985c63699bcb3ef7'
config=Path('/opt/apps/family_connect/state-product-https/config/nginx.conf')
old=config.read_bytes()
assert hashlib.sha256(old).hexdigest()=='128d4cdd3988ee0d187e61009d6e603311a3e7e876ac1d1d9fc8d00e66e44e76'
backup=config.with_name('nginx.conf.before-support-20261021')
drop=Path('/etc/systemd/system')/(unit+'.d')/'zzz-support-diagnostics.conf'
assert not drop.exists()
if backup.exists():assert backup.read_bytes()==old
target=root/('support-'+sha+'.pyz')
if target.exists():assert hashlib.sha256(target.read_bytes()).hexdigest()==sha
def atomic(path,data,mode):
 temp=path.with_name(path.name+'.support-new');fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,mode)
 try:
  with os.fdopen(fd,'wb') as output:output.write(data);output.flush();os.fsync(output.fileno())
  os.replace(temp,path)
 finally:
  if temp.exists():temp.unlink()
if not target.exists():atomic(target,raw,0o600)
subprocess.run([root/'venv/bin/python','-I',target,'--help'],check=True,capture_output=True,timeout=15)
if not backup.exists():backup.write_bytes(old);backup.chmod(0o600)
text=old.decode();needle='        location ~ ^/friends/(challenge|activate|'
assert text.count(needle)==1
addition='''
        location = /friends/device/diagnostics {
            if ($request_method != POST) { return 405; }
            client_max_body_size 8k;
            proxy_pass http://127.0.0.1:18086;
            proxy_set_header Host 127.0.0.1;
            proxy_set_header Connection "";
            proxy_connect_timeout 2s;
            proxy_send_timeout 5s;
            proxy_read_timeout 20s;
            proxy_max_temp_file_size 0;
            proxy_buffering off;
        }
'''
started=False
try:
 atomic(config,text.replace(needle,addition+needle).encode(),0o644)
 subprocess.run(['docker','exec','family-connect-product-https','nginx','-t','-c','/etc/fc/nginx.conf'],check=True,capture_output=True,timeout=15)
 atomic(drop,('[Service]\nExecStart=\nExecStart=/opt/apps/family_connect/friends-access/venv/bin/python -I '+str(target)+' --port 18086\n').encode(),0o644)
 subprocess.run(['systemctl','daemon-reload'],check=True,timeout=20)
 effective=subprocess.check_output(['systemctl','show',unit,'-p','ExecStart','--value'],text=True)
 assert str(target) in effective, 'effective ExecStart must select the new artifact before restart'
 started=True
 subprocess.run(['systemctl','restart',unit],check=True,timeout=30)
 for attempt in range(20):
  try:
   request=urllib.request.Request('http://127.0.0.1:18086/friends/device/diagnostics',data=b'{}',headers={'Content-Type':'application/json'})
   urllib.request.urlopen(request,timeout=2);raise AssertionError('unauthenticated report accepted')
  except urllib.error.HTTPError as error:
   assert error.code==403;break
  except urllib.error.URLError:
   time.sleep(.25)
 else:raise AssertionError('HTTP not ready')
 subprocess.run(['docker','kill','--signal=HUP','family-connect-product-https'],check=True,capture_output=True,timeout=15)
 after=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
 print(json.dumps(dict(status='DEPLOYED_HTTP_ONLY',before=before,after=after,sha256=sha,nginx_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),media_gateway_restart=False,unauthenticated_upload=403,rollback=dict(dropin=str(drop),nginx_backup=str(backup)))))
except Exception:
 atomic(config,old,0o644)
 if drop.exists():drop.unlink()
 subprocess.run(['systemctl','daemon-reload'],check=True,timeout=20)
 if started:subprocess.run(['systemctl','restart',unit],check=True,timeout=30)
 subprocess.run(['docker','kill','--signal=HUP','family-connect-product-https'],check=True,capture_output=True,timeout=15)
 raise
""".replace('__SHA__',repr(sha)).replace('__PAYLOAD__',repr(base64.b64encode(artifact.read_bytes()).decode()))
    compile(remote,'<support-http>','exec')
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','root@185.251.89.19','python3 -B -'],input=remote,text=True,capture_output=True,timeout=120)
    if result.returncode:
        receipt.write_text(json.dumps(dict(status='RECONCILE_REQUIRED',exit=result.returncode,stderr=result.stderr),indent=2))
        raise SystemExit('HTTP deploy failed; read receipt and state before retry')
    value=json.loads(result.stdout);receipt.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
