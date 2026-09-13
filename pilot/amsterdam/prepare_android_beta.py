from pathlib import Path
import base64,json,os,shlex,subprocess,hashlib
import argparse
p=argparse.ArgumentParser(description='Provision reserved Amsterdam Android beta01 peer; private state required')
p.add_argument('--state',type=Path,required=True)
p.add_argument('--wg',required=True)
a=p.parse_args()
state=a.state;state.mkdir(mode=0o700,exist_ok=True);os.chmod(state,0o700)
wg=a.wg
key=state/'client.key'
if not key.exists():
 with key.open('xb') as f:os.fchmod(f.fileno(),0o600);f.write(subprocess.check_output([wg,'genkey']))
pub=subprocess.check_output([wg,'pubkey'],input=key.read_bytes()).decode().strip()
assert len(base64.b64decode(pub))==32
remote=r'''
import base64,fcntl,json,os,subprocess,sys,tempfile
from pathlib import Path
pub=json.load(sys.stdin)['public_key']
assert len(base64.b64decode(pub,validate=True))==32
allowed={'10.79.0.4/32','fd79:92::4/128'}
def run(args):return subprocess.run(args,capture_output=True,text=True,check=True,timeout=10).stdout.strip()
def peers():return {x.split()[0]:set(x.split()[1:]) for x in run(['wg','show','fcams','allowed-ips']).replace(',',' ').splitlines()}
def write_atomic(path,data):
 fd,name=tempfile.mkstemp(prefix='.fc-peer-',dir=path.parent)
 try:
  os.fchmod(fd,0o600)
  with os.fdopen(fd,'w') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(name,path)
 finally:
  if os.path.exists(name):os.unlink(name)
with open('/run/lock/fc-ams-peers.lock','a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 config=Path('/etc/wireguard/fcams.conf');old=config.read_text();before=peers()
 assert all(not (ips&allowed) for k,ips in before.items() if k!=pub),'Address occupied'
 assert pub not in before or before[pub]==allowed,'Peer address conflict'
 if pub in before:
  assert pub in old,'Peer not persisted'
 else:
  assert pub not in old and '10.79.0.4/' not in old and 'fd79:92::4/' not in old,'Persistent config conflict'
  backup=Path('/opt/apps/family_connect/amsterdam/before-android-beta-01.conf')
  if not backup.exists():
   with backup.open('x') as f:os.fchmod(f.fileno(),0o600);f.write(old)
  new=old.rstrip()+'\n\n# Android beta 01 - separately revocable pilot\n[Peer]\nPublicKey = '+pub+'\nAllowedIPs = 10.79.0.4/32, fd79:92::4/128\n'
  assert config.read_text()==old
  write_atomic(config,new)
  try:
   run(['wg','set','fcams','peer',pub,'allowed-ips',','.join(sorted(allowed))])
   after=peers();assert after.get(pub)==allowed and all(after.get(k)==v for k,v in before.items())
  except Exception:
   subprocess.run(['wg','set','fcams','peer',pub,'remove'],capture_output=True,timeout=10)
   write_atomic(config,old)
   raise
 print(json.dumps({'server_public_key':run(['wg','show','fcams','public-key']),'peer_public_key':pub,'allowed_ips':sorted(allowed),'previous_peers_preserved':True,'persisted':True,'server_restarted':False}))
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','root@186.246.45.246','python3 -c '+shlex.quote(remote)],input=json.dumps({'public_key':pub}),text=True,capture_output=True,timeout=35)
if p.returncode:raise SystemExit('Peer provisioning failed; remote details retained in memory only')
r=json.loads(p.stdout);server=r['server_public_key'];assert len(base64.b64decode(server))==32
profile='[Interface]\nPrivateKey = '+key.read_text().strip()+'\nAddress = 10.79.0.4/32, fd79:92::4/128\nDNS = 1.1.1.1\nMTU = 1280\n[Peer]\nPublicKey = '+server+'\nEndpoint = 186.246.45.246:51820\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n'
for name,data in [('Amsterdam-Android-beta-01.conf',profile),('client-uapi.conf','\n'.join(x for x in profile.splitlines() if not x.startswith(('Address =','DNS =','MTU =')))+'\n'),('client.pub',pub+'\n')]:
 path=state/name;path.write_text(data);os.chmod(path,0o600)
import shutil
shutil.copyfile(wg,state/'wg');os.chmod(state/'wg',0o755)
(state/'peer-receipt.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r))
