"""Isolated AWG3.1 open-test gateway and idempotent public-key registration.

run: service lifetime; register: forced SSH command, one bounded JSON request.
No private key/config/traffic is printed. Existing gateways are never modified.
"""
import base64,fcntl,re,uuid,ipaddress,json,os,signal,sqlite3,subprocess,sys,time
from pathlib import Path
ROOT=Path('/opt/apps/family_connect/friends-awg')
IFACE='fcopen31'

def command(args,check=True):
 r=subprocess.run(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 if check and r.returncode:raise RuntimeError('AWG gateway operation failed')
 return r.returncode

def settings():return json.loads((ROOT/'settings.json').read_text())

def database():
 db=sqlite3.connect(ROOT/'peers.db',timeout=10);db.execute('PRAGMA synchronous=FULL')
 db.execute('CREATE TABLE IF NOT EXISTS peers (id INTEGER PRIMARY KEY AUTOINCREMENT, public TEXT UNIQUE NOT NULL)')
 os.chmod(ROOT/'peers.db',0o600);return db

def address(index):
 network=ipaddress.ip_network(settings()['network']);assert 1<=index<network.num_addresses-2
 return str(network[index+1])+'/32'

def add_peer(public,assigned):command([str(ROOT/'awg'),'set',IFACE,'peer',public,'allowed-ips',assigned])

def tcp_user(device,ident):
 tcp=ROOT.parent/'friends-tcp';path=tcp/'server.json'
 value=json.loads(path.read_text());inbound=next(i for i in value['inbounds'] if i.get('tag')=='friends')
 email=device+'@family.test';clients=inbound['settings']['clients'];existing=[c for c in clients if c.get('email')==email]
 client={'id':ident,'email':email,'flow':'xtls-rprx-vision'}
 if existing:assert existing==[client],'Existing TCP binding differs'
 else:
  assert not any(c['id']==ident for c in clients)
  clients.append(client);temporary=path.with_suffix('.pending');info=path.stat()
  fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o640)
  os.fchmod(fd,0o640)
  with os.fdopen(fd,'w') as f:json.dump(value,f);f.flush();os.fsync(f.fileno())
  os.chown(temporary,info.st_uid,info.st_gid);os.replace(temporary,path)
 payload={'inbounds':[{'tag':'friends','listen':'127.0.0.1','port':inbound['port'],'protocol':'vless','settings':{'clients':[client],'decryption':'none'}}]}
 temporary=tcp/'user-request.json';fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,'w') as f:json.dump(payload,f)
 command([str(tcp/'xray'),'api','adu','--server=127.0.0.1:18085',str(temporary)],False)
 result=subprocess.run([str(tcp/'xray'),'api','inbounduser','--server=127.0.0.1:18085','-tag=friends','-email='+email],capture_output=True,text=True)
 assert result.returncode==0 and ident in result.stdout and email in result.stdout,'TCP user not confirmed'
 temporary.unlink()

def register():
 raw=sys.stdin.buffer.read(1025);assert len(raw)<=1024
 request=json.loads(raw);assert set(request)=={'public_key','tcp_id','device'}
 ident=request['tcp_id'];device=request['device'];assert str(uuid.UUID(ident))==ident and re.fullmatch('[0-9a-f]{32}',device)
 key=request['public_key'];decoded=base64.b64decode(key,validate=True);assert len(decoded)==32 and any(decoded) and base64.b64encode(decoded).decode()==key
 with (ROOT/'registration.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  with database() as db:
   db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT id FROM peers WHERE public=?',(key,)).fetchone()
   if row is None:
    index=db.execute('INSERT INTO peers(public) VALUES (?)',(key,)).lastrowid
   else:index=row[0]
   assigned=address(index);add_peer(key,assigned);tcp_user(device,ident)
  print(json.dumps({'public_key':key,'address':assigned,'transport':'amneziawg-3.1'}))

def run():
 assert Path('/proc/sys/net/ipv4/ip_forward').read_text().strip()=='1','Existing gateway forwarding required'
 config=settings();network=config['network'];external=config['external']
 assert external.replace('-','').replace('_','').isalnum()
 process=subprocess.Popen([str(ROOT/'amneziawg-go'),'-f',IFACE],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env={**os.environ,'GOMAXPROCS':'2'})
 rules=[]
 def stop(*args):raise KeyboardInterrupt()
 signal.signal(signal.SIGTERM,stop)
 try:
  for _ in range(100):
   if command(['ip','link','show',IFACE],False)==0:break
   if process.poll() is not None:raise RuntimeError('Engine failed')
   time.sleep(.05)
  command([str(ROOT/'awg'),'setconf',IFACE,str(ROOT/'server.conf')])
  command(['ip','address','add',config['address'],'dev',IFACE]);command(['ip','link','set','dev',IFACE,'mtu','1280','up'])
  with database() as db:
   for index,public in db.execute('SELECT id,public FROM peers'):add_peer(public,address(index))
  command(['iptables','-N','FCFRIENDS31'],False)
  command(['iptables','-F','FCFRIENDS31'])
  for blocked in ['0.0.0.0/8','10.0.0.0/8','127.0.0.0/8','169.254.0.0/16','172.16.0.0/12','192.168.0.0/16','224.0.0.0/4']:
   command(['iptables','-A','FCFRIENDS31','-d',blocked,'-j','DROP'])
  command(['iptables','-A','FCFRIENDS31','-j','ACCEPT'])
  rules=[['iptables','-I','FORWARD','-i',IFACE,'-j','FCFRIENDS31'],['iptables','-I','FORWARD','-o',IFACE,'-m','conntrack','--ctstate','ESTABLISHED,RELATED','-j','ACCEPT'],['iptables','-t','nat','-A','POSTROUTING','-s',network,'-o',external,'-j','MASQUERADE']]
  for rule in rules:
   check=[("-C" if part in ("-A","-I") else part) for part in rule]
   if command(check,False)!=0:command(rule)
  process.wait()
  raise RuntimeError('Engine exited')
 except KeyboardInterrupt:pass
 finally:
  for rule in reversed(rules):command([('-D' if part in ('-A','-I') else part) for part in rule],False)
  command(['iptables','-F','FCFRIENDS31'],False);command(['iptables','-X','FCFRIENDS31'],False)
  if process.poll() is None:process.terminate();process.wait(timeout=10)
  command(['ip','link','del',IFACE],False)

if __name__=='__main__':
 assert os.geteuid()==0;os.umask(0o077)
 try:
  if sys.argv[1:] == ['run']:run()
  elif sys.argv[1:] == ['register']:register()
  else:raise ValueError('Unknown operation')
 except Exception:print('Open AWG service unavailable',file=sys.stderr);sys.exit(1)
