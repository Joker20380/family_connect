"""Disposable Windows LocalSystem broker acceptance; scoped routes/DNS, synthetic VLESS."""
import base64,ctypes,http.client,http.server,json,os,secrets,socket,struct,subprocess,sys,threading,time,uuid
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

assert sys.platform=='win32' and os.environ.get('GITHUB_ACTIONS')=='true'
host=Path(sys.argv[1]).resolve();engine=Path(sys.argv[2]).resolve();out=Path(sys.argv[3]).resolve()
exe=host/'FamilyConnect.exe';root=Path(os.environ['ProgramData'])/'FamilyConnect'
result={'rounds':[],'passed':False}
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
def clean():
 assert not (root/'tcp-session.json').exists(),'Journal remains'
 assert not ps("Get-CimInstance Win32_Process -Filter \"Name='xray.exe'\" | Where-Object {$_.ExecutablePath -like '*tcp\\xray.exe'} | Select-Object -ExpandProperty ProcessId"),'Xray process remains'
 assert not ps("Get-NetAdapter -IncludeHidden | Where-Object {$_.Name -match '^fctcp[0-9a-f]{8}$'} | Select-Object -ExpandProperty Name"),'Adapter remains'
 assert not ps("Get-NetRoute | Where-Object {$_.DestinationPrefix -in @('198.18.0.1/32','fd79:fc::1/128')} | Select-Object -ExpandProperty DestinationPrefix"),'Route remains'
 assert baseline()==before and dns_snapshot()==dns_before and nrpt_snapshot()==nrpt_before,'Network settings changed'

def kill_engine():
 ps("Get-CimInstance Win32_Process -Filter \"Name='xray.exe'\" | Where-Object {$_.ExecutablePath -like '*tcp\\xray.exe'} | ForEach-Object {Stop-Process -Id $_.ProcessId -Force}")
def wait_retry():
 until=time.monotonic()+100
 while time.monotonic()<until:
  reply=call('status')
  if reply.get('error')=='tcp-reconnecting':
   assert reply['state']=='pending' and reply['transport']=='tcp'
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
def traffic(row):
 answer=socket.getaddrinfo(uuid.uuid4().hex+'.fctcp-ci.invalid',fixture.server_port,socket.AF_UNSPEC,socket.SOCK_STREAM)
 assert {'198.18.0.1','fd79:fc::1'}<={a[4][0] for a in answer};row['dns']=True
 row['dns_checks']=row.get('dns_checks',0)+1
 for target,source,counter in [('198.18.0.1','198.18.0.2','http4'),('fd79:fc::1','fd79:fc::2','http6')]:
  for _ in range(3):
   c=http.client.HTTPConnection(target,fixture.server_port,timeout=7,source_address=(source,0))
   try:c.request('GET','/');r=c.getresponse();assert r.status==200 and r.read()==token;row[counter]+=1
   finally:c.close()

server=None;fixture=None;udp=None;installed=False;dns_stop=threading.Event();account=None;other_token=None
try:
 assert not ps('Get-Service FamilyConnectBroker -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name'),'Refuse existing service'
 assert not root.exists(),'Refuse existing store'
 before=baseline();dns_before=dns_snapshot();nrpt_before=nrpt_snapshot()
 token=secrets.token_hex(16).encode()
 class Handler(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
   self.send_response(200);self.send_header('Content-Length',str(len(token)));self.end_headers();self.wfile.write(token)
  def log_message(self,*args):pass
 fixture=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
 threading.Thread(target=fixture.serve_forever,daemon=True).start()
 udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);udp.bind(('127.0.0.1',fixture.server_port));udp.settimeout(.3)
 def dns_loop():
  while not dns_stop.is_set():
   try:data,addr=udp.recvfrom(4096)
   except socket.timeout:continue
   except OSError:return
   try:
    pos=12
    while data[pos]:pos+=data[pos]+1
    pos+=1;kind=struct.unpack('!H',data[pos:pos+2])[0];question=data[12:pos+4]
    value=socket.inet_pton(socket.AF_INET,'198.18.0.1') if kind==1 else socket.inet_pton(socket.AF_INET6,'fd79:fc::1') if kind==28 else None
    answer=b'' if value is None else b'\xc0\x0c'+struct.pack('!HHIH',kind,1,0,len(value))+value
    udp.sendto(data[:2]+struct.pack('!HHHHH',0x8180,1,int(value is not None),0,0)+question+answer,addr)
   except (IndexError,struct.error):continue
 threading.Thread(target=dns_loop,daemon=True).start()
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 ident=str(uuid.uuid4());config={'log':{'loglevel':'none'},'inbounds':[{'listen':'127.0.0.1','port':port,'protocol':'vless','settings':{'clients':[{'id':ident}],'decryption':'none'}}],'outbounds':[{'protocol':'freedom','settings':{'redirect':'127.0.0.1:'+str(fixture.server_port)}}]}
 server=subprocess.Popen([str(engine/'xray.exe'),'run','-config','stdin:'],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 server.stdin.write(json.dumps(config).encode());server.stdin.close()
 key=Ed25519PrivateKey.generate();(host/'activation.pub').write_text(base64.b64encode(key.public_key().public_bytes_raw()).decode())
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
 device=base64.b64encode(bytes.fromhex(call('request')['code'][4:])).decode()
 grant=dict(version=1,devicePublicKey=device,sequence=1,expiresAt=int(time.time())+3600,server='192.0.2.10',port=port,id=ident,publicKey=base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('='),serverName='example.com',shortId='0123456789abcdef')
 raw=json.dumps(grant,separators=(',',':')).encode();envelope=json.dumps(dict(payload=base64.b64encode(raw).decode(),signature=base64.b64encode(key.sign(b'family-connect/windows-tcp-activation/v1\0'+raw)).decode()))
 assert call('activate-tcp',envelope)['ok']
 for mode in ('disconnect','engine-crash','broker-crash','service-stop','cancel-start','cancel-recovery','service-stop-recovery','recovery-exhaustion'):
  row={'mode':mode,'http4':0,'http6':0,'dns':False,'clean':False};result['rounds'].append(row)
  reply=call('connect-tcp');assert reply['ok'] and reply['state']=='pending'
  if mode=='cancel-start':
   assert call('disconnect')['ok'];wait_state('inactive');clean();row['clean']=True;continue
  reply=wait_state('on');assert reply['transport']=='tcp'
  assert not call('activate-tcp',envelope)['ok'],'Active profile replaced'
  assert not call('connect')['ok'],'WG started over TCP'
  assert api.ImpersonateLoggedOnUser(other_token),'Test account impersonation failed'
  try:
   assert call('status')['state']=='other-user','Owner hidden from second account'
   assert call('disconnect')['error']=='other-user','Other account stopped session'
   assert call('connect-tcp')['error']=='other-user','Other account replaced session'
   row['other_user_denied']=True
  finally:api.RevertToSelf()
  traffic(row)
  if mode=='disconnect':assert call('disconnect')['ok'];wait_state('inactive')
  elif mode=='engine-crash':
   old=json.loads((root/'tcp-session.json').read_text())['adapter'];kill_engine();wait_retry()
   wait_state('on');assert json.loads((root/'tcp-session.json').read_text())['adapter']!=old
   traffic(row);row['recovered']=True
   assert call('disconnect')['ok'];wait_state('inactive')
  elif mode in ('cancel-recovery','service-stop-recovery'):
   kill_engine();wait_retry()
   if mode=='cancel-recovery':assert call('disconnect')['ok'];wait_state('inactive')
   else:ps('Stop-Service FamilyConnectBroker');ps('Start-Service FamilyConnectBroker');wait_state('inactive')
   time.sleep(20);assert call('status')['state']=='inactive','Cancelled recovery restarted'
   row['retry_cancelled']=True
  elif mode=='recovery-exhaustion':
   row['restarts']=0;row['recovery_seconds']=[]
   for attempt in range(4):
    kill_engine()
    if attempt<3:
     started=time.monotonic();wait_retry();wait_state('on',timeout=150)
     elapsed=time.monotonic()-started;assert elapsed>=15*(2**attempt),'Backoff shorter than policy'
     row['recovery_seconds'].append(round(elapsed,2))
     traffic(row);row['restarts']+=1
    else:
     reply=wait_state('inactive');assert reply.get('error')=='tcp-recovery-exhausted'
   time.sleep(20);assert call('status')['state']=='inactive','Retry budget reset'
  elif mode=='broker-crash':
   ps("$s=Get-CimInstance Win32_Service -Filter \"Name='FamilyConnectBroker'\"; Stop-Process -Id $s.ProcessId -Force")
   time.sleep(2);wait_state('inactive')
  else:
   ps('Stop-Service FamilyConnectBroker');clean();ps('Start-Service FamilyConnectBroker');wait_state('inactive')
  clean();row['clean']=True
 result['passed']=all(x['clean'] and (x['mode']=='cancel-start' or x['http4']>=3 and x['http6']>=3 and x['dns'] and x['other_user_denied']) for x in result['rounds'])
except Exception as error:
 import traceback
 result.update(error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc());raise
finally:
 try:
  if installed:subprocess.run([str(exe),'/remove-service'],check=True,timeout=180)
 finally:
  if other_token and other_token.value:
   ctypes.windll.kernel32.CloseHandle(other_token)
  if account:
   net.NetUserDel.argtypes=[wintypes.LPCWSTR,wintypes.LPCWSTR]
   assert net.NetUserDel(None,account)==0,'Test account deletion failed'
  if server and server.poll() is None:server.kill();server.wait(timeout=10)
  dns_stop.set()
  if udp:udp.close()
  if fixture:fixture.shutdown();fixture.server_close()
  out.write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
