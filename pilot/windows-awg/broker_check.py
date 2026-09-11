"""Actual LocalSystem AWG broker; synthetic signed grants, scoped routes and UDP data."""
import http.client,http.server
import base64,ctypes,json,os,socket,struct,subprocess,sys,threading,time,uuid,queue,secrets
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
assert sys.platform=='win32' and os.environ.get('GITHUB_ACTIONS')=='true'
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from activate_windows_awg import issue
host=Path(sys.argv[1]).resolve();engine=Path(sys.argv[2]).resolve();out=Path(sys.argv[3]).resolve()
exe=host/'FamilyConnect.exe';root=Path(os.environ['ProgramData'])/'FamilyConnect'
result={'rounds':[],'passed':False};installed=False;peer=None;account=None;other_token=None;tcp_server=None;http_fixture=None
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
  if reply.get('error') and reply['error'] not in ('tcp-reconnecting','auto-switching'):raise RuntimeError('Session failed: '+reply['error'])
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
 assert not (root/'auto-session.json').exists(),'Automatic journal remains'
 assert not ps("Get-NetAdapter -IncludeHidden | Where-Object {$_.Name -like 'fctcp*' -or $_.Name -eq 'fc-native'} | Select-Object -ExpandProperty Name"),'Other transport adapter remains'
 assert not ps("Get-CimInstance Win32_Process -Filter \"Name='xray.exe'\" | Where-Object {$_.ExecutablePath -like '*fc-awg-broker*tcp*xray.exe'} | Select-Object -ExpandProperty ProcessId"),'Client Xray remains'
 assert not ps("Get-Process fc-awg -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"),'AWG worker remains'
 assert not ps("Get-NetAdapter -IncludeHidden | Where-Object {$_.Name -like 'fcawg*'} | Select-Object -ExpandProperty Name"),'AWG adapter remains'
 assert not ps("Get-NetRoute | Where-Object {$_.DestinationPrefix -in @('198.18.0.1/32','fd79:fc::1/128')} | Select-Object -ExpandProperty DestinationPrefix"),'Route remains'
 assert baseline()==before and dns_snapshot()==dns_before and nrpt_snapshot()==nrpt_before,'Network settings changed'
def traffic(row):
 for family,target,source,key in [(socket.AF_INET,'198.18.0.1','198.18.0.2','ipv4'),(socket.AF_INET6,'fd79:fc::1','fd79:fc::2','ipv6')]:
  with socket.socket(family,socket.SOCK_DGRAM) as p:
   p.bind((source,0));p.settimeout(3)
   for _ in range(3):
    row.setdefault('peer_before',dict(result.get('peer_stats',{})));payload=secrets.token_bytes(96);deadline=time.monotonic()+12
    while True:
     p.sendto(payload,(target,18765));row['udp_attempts']=row.get('udp_attempts',0)+1
     try:
      reply,_=p.recvfrom(512)
      if reply!=payload:continue
      row[key]+=1;break
     except socket.timeout:
      if time.monotonic()>=deadline:
       result['failed_status']=call('status')
       result['failed_routes']=ps("Get-NetRoute | Where-Object {$_.DestinationPrefix -in @('198.18.0.1/32','fd79:fc::1/128')} | Select-Object InterfaceAlias,InterfaceIndex,DestinationPrefix,NextHop,State | ConvertTo-Json -Compress")
       result['failed_network']=ps("Get-NetIPAddress | Where-Object {$_.InterfaceAlias -like 'fcawg*'} | Select-Object InterfaceAlias,IPAddress,AddressState | ConvertTo-Json -Compress")
       raise
try:
 assert not root.exists(),'Existing store';assert not ps('Get-Service FamilyConnectBroker -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name'),'Existing service'
 before=baseline();dns_before=dns_snapshot();nrpt_before=nrpt_snapshot()
 signing=Ed25519PrivateKey.generate();(host/'activation.pub').write_text(base64.b64encode(signing.public_key().public_bytes_raw()).decode())
 installed=True;subprocess.run([str(exe),'/install-service'],check=True,timeout=60)
 # A second local account exercises actual pipe SID ownership while AWG is active.
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
 def peer_stats():
  for line in peer.stdout:
   try:result['peer_stats']=json.loads(line)
   except ValueError:pass
 threading.Thread(target=peer_stats,daemon=True).start()
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
   ps('Get-Process fc-awg | Stop-Process -Force');wait_retry();assert wait_state('on')['transport']=='awg';row['recovery_peer_before']=dict(result.get('peer_stats',{}));traffic(row);row['recovered']=True
  if mode=='broker-crash':
   ps("$s=Get-CimInstance Win32_Service -Filter \"Name='FamilyConnectBroker'\"; Stop-Process -Id $s.ProcessId -Force");time.sleep(2);wait_state('inactive')
  else:assert call('disconnect')['ok'];wait_state('inactive')
  clean();row['clean']=True
 # Automatic mode: real encrypted AWG -> real VLESS/TUN TCP; unavailable WG service first.
 from activate_windows import issue as issue_wg
 wg_envelope,_=issue_wg(code,4,profile['gatewayPublicKey'],'192.0.2.10:51820',signing,int(time.time()))
 assert call('activate',json.dumps(wg_envelope))['ok']
 class Handler(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
   self.send_response(204 if self.path.startswith('/health/') else 200);self.end_headers()
   if not self.path.startswith('/health/'):self.wfile.write(b'auto-flow')
  def log_message(self,*args):pass
 http_fixture=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
 threading.Thread(target=http_fixture.serve_forever,daemon=True).start()
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));tcp_port=sock.getsockname()[1]
 ident=str(uuid.uuid4());tcp_config={'log':{'loglevel':'none'},'inbounds':[{'listen':'127.0.0.1','port':tcp_port,'protocol':'vless','settings':{'clients':[{'id':ident}],'decryption':'none'}}],'outbounds':[{'protocol':'freedom','settings':{'redirect':'127.0.0.1:'+str(http_fixture.server_port)}}]}
 tcp_server=subprocess.Popen([str(Path(sys.argv[4])/'xray.exe'),'run','-config','stdin:'],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 tcp_server.stdin.write(json.dumps(tcp_config).encode());tcp_server.stdin.close()
 grant=dict(version=1,devicePublicKey=base64.b64encode(bytes.fromhex(code[4:])).decode(),sequence=1,expiresAt=int(time.time())+86400,server='192.0.2.10',port=tcp_port,id=ident,publicKey=base64.urlsafe_b64encode(bytes(range(1,33))).decode().rstrip('='),serverName='example.com',shortId='01')
 raw=json.dumps(grant,separators=(',',':')).encode();activation_tcp=json.dumps(dict(payload=base64.b64encode(raw).decode(),signature=base64.b64encode(signing.sign(b'family-connect/windows-tcp-activation/v1\0'+raw)).decode()))
 assert call('activate-tcp',activation_tcp)['ok']
 result['automatic']=[]
 def auto_wait(transport,state='on',timeout=150):
  until=time.monotonic()+timeout
  while time.monotonic()<until:
   reply=call('status')
   if reply['state']==state and reply['transport']==transport and reply['automatic']:return reply
   if reply.get('error') not in (None,'auto-switching'):raise RuntimeError('Automatic connection: '+reply['error'])
   time.sleep(.2)
  raise TimeoutError('Automatic transport did not reach '+transport)
 def own_check():
  assert api.ImpersonateLoggedOnUser(other_token)
  try:
   assert call('status')['state']=='other-user';assert call('disconnect')['error']=='other-user';assert call('connect-auto')['error']=='other-user'
  finally:api.RevertToSelf()
 row={'mode':'auto-fallback-restart','ipv4':0,'ipv6':0,'http':0,'clean':False};result['automatic'].append(row)
 assert call('connect-auto')['automatic'];own_check();auto_wait('awg');traffic(row);own_check()
 peer.kill();peer.wait(timeout=10);auto_wait('tcp');own_check()
 for target,source in [('198.18.0.1','198.18.0.2'),('fd79:fc::1','fd79:fc::2')]:
  for _ in range(3):
   c=http.client.HTTPConnection(target,http_fixture.server_port,timeout=7,source_address=(source,0))
   try:c.request('GET','/');reply=c.getresponse();assert reply.status==200 and reply.read()==b'auto-flow';row['http']+=1
   finally:c.close()
 assert not ps("Get-Process fc-awg -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id")
 ps("$s=Get-CimInstance Win32_Service -Filter \"Name='FamilyConnectBroker'\"; Stop-Process -Id $s.ProcessId -Force")
 time.sleep(2);wait_state('off');clean();row['clean']=True
 row={'mode':'auto-exhaustion','clean':False};result['automatic'].append(row)
 assert call('connect-auto')['automatic'];auto_wait('tcp');tcp_server.kill();tcp_server.wait(timeout=10)
 reply=wait_state('off',timeout=150);assert reply['error']=='auto-exhausted';clean();row['clean']=True
 row={'mode':'auto-cancel','clean':False};result['automatic'].append(row)
 assert call('connect-auto')['automatic'];assert call('disconnect')['ok'];wait_state('off');clean();row['clean']=True
 row={'mode':'auto-cancel-probe','clean':False};result['automatic'].append(row)
 assert call('connect-auto')['automatic'];auto_wait('awg',state='pending');assert call('disconnect')['ok'];wait_state('off');clean();row['clean']=True
 result['automatic_passed']=all(x['clean'] for x in result['automatic']);assert result['automatic_passed']
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
  if tcp_server and tcp_server.poll() is None:tcp_server.kill();tcp_server.wait(timeout=10)
  if http_fixture:http_fixture.shutdown();http_fixture.server_close()
  out.write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
