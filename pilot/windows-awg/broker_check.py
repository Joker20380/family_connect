"""Actual LocalSystem AWG broker; synthetic signed grants, scoped routes and UDP data."""
import base64,ctypes,json,os,socket,struct,subprocess,sys,threading,time,uuid,queue,secrets
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
assert sys.platform=='win32' and os.environ.get('GITHUB_ACTIONS')=='true'
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from activate_windows_awg import issue
host=Path(sys.argv[1]).resolve();engine=Path(sys.argv[2]).resolve();out=Path(sys.argv[3]).resolve()
exe=host/'FamilyConnect.exe';root=Path(os.environ['ProgramData'])/'FamilyConnect'
result={'rounds':[],'passed':False};installed=False;peer=None;account=None;other_token=None
def ps(code):
 p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"$ErrorActionPreference='Stop'; "+code+'; exit 0'],capture_output=True,text=True,timeout=100)
 if p.returncode:raise RuntimeError(p.stderr[-1800:])
 return p.stdout.strip()

def call(action,activation=None):
 # Windows named pipe, same framed JSON protocol as the UI. No credential goes to stdout.
 path=r'\\.\pipe\FamilyConnect.Broker.v1';deadline=time.monotonic()+20
 while True:
  try:f=open(path,'r+b',buffering=0);break
  except OSError:
   if time.monotonic()>deadline:raise
   time.sleep(.15)
 with f:
  raw=json.dumps({'action':action,'activation':activation}).encode();f.write(struct.pack('<i',len(raw))+raw)
  def read(n):
   data=b''
   while len(data)<n:
    chunk=f.read(n-len(data))
    if not chunk:raise RuntimeError('Broker pipe closed')
    data+=chunk
   return data
  size=struct.unpack('<i',read(4))[0];assert 1<=size<=16384
  return json.loads(read(size))

def wait_state(wanted,timeout=100):
 until=time.monotonic()+timeout;reply={}
 while time.monotonic()<until:
  try:reply=call('status')
  except OSError:time.sleep(.2);continue
  if reply['state']==wanted:return reply
  if reply.get('error') and reply['error']!='tcp-reconnecting':raise RuntimeError('Session failed: '+reply['error'])
  time.sleep(.25)
 raise RuntimeError('Session did not reach '+wanted+': '+str(reply))

def baseline():
 return ps("Get-NetRoute | Where-Object { $_.DestinationPrefix -in @('0.0.0.0/0','::/0') } | Sort-Object InterfaceIndex,DestinationPrefix,NextHop | Select-Object InterfaceIndex,DestinationPrefix,NextHop,RouteMetric | ConvertTo-Json -Compress")

def dns_snapshot():
 return ps('Get-DnsClientServerAddress | Where-Object { $_.ServerAddresses.Count -gt 0 } | Sort-Object InterfaceIndex,AddressFamily | Select-Object InterfaceIndex,AddressFamily,ServerAddresses | ConvertTo-Json -Compress')

def nrpt_snapshot():
 return ps('Get-DnsClientNrptRule | Sort-Object Name | Select-Object Name,Namespace,NameServers,DisplayName | ConvertTo-Json -Compress')

def wait_retry():
 until=time.monotonic()+100
 while time.monotonic()<until:
  reply=call('status')
  if reply.get('error')=='tcp-reconnecting':
   assert reply['state']=='pending' and reply['transport']=='awg'
   assert not (root/'tcp-session.json').exists(),'Retry before cleanup'
   assert api.ImpersonateLoggedOnUser(other_token)
   try:
    assert call('status')['state']=='other-user'
    assert call('disconnect')['error']=='other-user'
    assert call('connect-tcp')['error']=='other-user'
   finally:api.RevertToSelf()
   return
  if reply.get('error'):raise RuntimeError('Recovery failed: '+reply['error'])
  time.sleep(.1)
 raise TimeoutError('Recovery did not enter backoff')

def clean():
 assert not (root/'tcp-session.json').exists(),'Journal remains'
 assert not ps("Get-Process fc-awg -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"),'AWG worker remains'
 assert not ps("Get-NetAdapter -IncludeHidden | Where-Object {$_.Name -like 'fcawg*'} | Select-Object -ExpandProperty Name"),'AWG adapter remains'
 assert not ps("Get-NetRoute | Where-Object {$_.DestinationPrefix -in @('198.18.0.1/32','fd79:fc::1/128')} | Select-Object -ExpandProperty DestinationPrefix"),'Route remains'
 assert baseline()==before and dns_snapshot()==dns_before and nrpt_snapshot()==nrpt_before,'Network settings changed'
def traffic(row):
 for family,target,source,key in [(socket.AF_INET,'198.18.0.1','198.18.0.2','ipv4'),(socket.AF_INET6,'fd79:fc::1','fd79:fc::2','ipv6')]:
  with socket.socket(family,socket.SOCK_DGRAM) as p:
   p.bind((source,0));p.settimeout(3)
   for _ in range(3):
    payload=secrets.token_bytes(96);p.sendto(payload,(target,18765));reply,_=p.recvfrom(512);assert reply==payload;row[key]+=1
try:
 assert not root.exists(),'Existing store';assert not ps('Get-Service FamilyConnectBroker -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name'),'Existing service'
 before=baseline();dns_before=dns_snapshot();nrpt_before=nrpt_snapshot()
 signing=Ed25519PrivateKey.generate();(host/'activation.pub').write_text(base64.b64encode(signing.public_key().public_bytes_raw()).decode())
 installed=True;subprocess.run([str(exe),'/install-service'],check=True,timeout=60)
 # A second local account exercises actual pipe SID ownership while TCP is active.
 from ctypes import wintypes
 candidate='fctcpci'+uuid.uuid4().hex[:6];password=secrets.token_urlsafe(24)+'aA1!'
 class UserInfo(ctypes.Structure):
  _fields_=[('name',wintypes.LPWSTR),('password',wintypes.LPWSTR),('age',wintypes.DWORD),('privilege',wintypes.DWORD),('home',wintypes.LPWSTR),('comment',wintypes.LPWSTR),('flags',wintypes.DWORD),('script',wintypes.LPWSTR)]
 net=ctypes.WinDLL('netapi32');net.NetUserAdd.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,ctypes.c_void_p,ctypes.POINTER(wintypes.DWORD)]
 info=UserInfo(candidate,password,0,1,None,None,0x10201,None);parameter=wintypes.DWORD()
 code=net.NetUserAdd(None,1,ctypes.byref(info),ctypes.byref(parameter));assert code==0,'Test account creation code='+str(code)
 account=candidate
 net.NetLocalGroupAddMembers.argtypes=[wintypes.LPCWSTR,wintypes.LPCWSTR,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD]
 member=ctypes.c_wchar_p(account);code=net.NetLocalGroupAddMembers(None,'Users',3,ctypes.byref(member),1)
 assert code in (0,1378),'Test account group code='+str(code)
 api=ctypes.WinDLL('advapi32',use_last_error=True);other_token=wintypes.HANDLE()
 api.LogonUserW.argtypes=[wintypes.LPCWSTR,wintypes.LPCWSTR,wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(wintypes.HANDLE)]
 api.ImpersonateLoggedOnUser.argtypes=[wintypes.HANDLE]
 assert api.LogonUserW(account,'.',password,2,0,ctypes.byref(other_token)), 'Test account logon code='+str(ctypes.get_last_error())

 code=call('request')['code'];device_public=bytes.fromhex(code[4:]).hex();gateway=X25519PrivateKey.generate()
 with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as p:p.bind(('127.0.0.1',0));port=p.getsockname()[1]
 params=dict(Jc='3',Jmin='40',Jmax='80',S1='17',S2='29',S3='3',S4='9',H1='1001-1010',H2='2001-2010',H3='3001-3010',H4='4001-4010',I1='<b 0x11223344><r 16>')
 config='private_key='+gateway.private_bytes_raw().hex()+'\nlisten_port='+str(port)+'\n'+''.join(k.lower()+'='+v+'\n' for k,v in params.items())+'public_key='+device_public+'\nallowed_ip=198.18.0.2/32\nallowed_ip=fd79:fc::2/128\n\n'
 peer=subprocess.Popen([str(engine/'peer-fixture.exe')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True);peer.stdin.write(json.dumps({'config':config}));peer.stdin.close()
 q=queue.Queue();threading.Thread(target=lambda:q.put(peer.stdout.readline().strip()),daemon=True).start();assert q.get(timeout=30)=='ready'
 profile=dict(gatewayPublicKey=base64.b64encode(gateway.public_key().public_bytes_raw()).decode(),server='192.0.2.10',port=port,number=4,parameters=params)
 def activation(sequence=1,change=None):return json.dumps(issue(code,json.dumps(profile|(change or {})),sequence,signing,int(time.time())))
 envelope=activation();assert call('activate-awg',envelope)['ok'];assert call('status')['awgReady']
 assert not call('activate-awg',activation(change={'number':5}))['ok'],'Same sequence replacement accepted'
 envelope=activation(2);assert call('activate-awg',envelope)['ok']
 assert not call('activate-awg',activation(1))['ok'],'Rollback accepted'
 result['profile_replacement_checked']=True
 for mode in ('disconnect','engine-crash','broker-crash','cancel-start'):
  row={'mode':mode,'ipv4':0,'ipv6':0,'clean':False};result['rounds'].append(row)
  reply=call('connect-awg');assert reply['ok'] and reply['state']=='pending' and reply['transport']=='awg'
  if mode=='cancel-start':
   assert call('disconnect')['ok'];wait_state('inactive');clean();row['clean']=True;continue
  assert wait_state('on')['transport']=='awg'
  assert call('connect-tcp')['error']=='busy' and call('connect')['error']=='busy','Simultaneous transports accepted'
  assert call('activate-awg',envelope)['error']=='disconnect-first','Active profile replaced'
  assert api.ImpersonateLoggedOnUser(other_token)
  try:
   assert call('status')['state']=='other-user';assert call('disconnect')['error']=='other-user';assert call('connect-awg')['error']=='other-user'
   row['other_user_denied']=True
  finally:api.RevertToSelf()
  traffic(row)
  if mode=='engine-crash':
   ps('Get-Process fc-awg | Stop-Process -Force');wait_retry();assert wait_state('on')['transport']=='awg';traffic(row);row['recovered']=True
  if mode=='broker-crash':
   ps("$s=Get-CimInstance Win32_Service -Filter \"Name='FamilyConnectBroker'\"; Stop-Process -Id $s.ProcessId -Force");time.sleep(2);wait_state('inactive')
  else:assert call('disconnect')['ok'];wait_state('inactive')
  clean();row['clean']=True
 result['passed']=all(x['clean'] and (x['mode']=='cancel-start' or x['ipv4']>=3 and x['ipv6']>=3 and x['other_user_denied']) for x in result['rounds']);assert result['passed']
except Exception as e:
 import traceback
 result.update(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc());raise
finally:
 try:
  if installed:subprocess.run([str(exe),'/remove-service'],check=True,timeout=180)
 finally:
  if other_token and other_token.value:ctypes.windll.kernel32.CloseHandle(other_token)
  if account:
   net.NetUserDel.argtypes=[wintypes.LPCWSTR,wintypes.LPCWSTR];assert net.NetUserDel(None,account)==0
  if peer and peer.poll() is None:peer.kill();peer.wait(timeout=10)
  out.write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
