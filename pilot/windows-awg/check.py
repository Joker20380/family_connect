"""AWG 2 encrypted UDP echo, real Wintun, synthetic keys, no external gateway."""
import json,os,socket,subprocess,sys,time,uuid,secrets,hashlib,threading,queue
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
assert sys.platform=='win32' and os.environ.get('GITHUB_ACTIONS')=='true'
folder=Path(sys.argv[1]).resolve();owner_exe=Path(sys.argv[2]).resolve();output=Path(sys.argv[3]).resolve()
result={'rounds':[],'passed':False};peer=None;owner=None;child_pid=None;alias=None
params='jc=3\njmin=40\njmax=80\ns1=17\ns2=29\ns3=3\ns4=9\nh1=1001-1010\nh2=2001-2010\nh3=3001-3010\nh4=4001-4010\ni1=<b 0x11223344><r 16>\n'
def ps(code):
 p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"$ErrorActionPreference='Stop'; "+code+'; exit 0'],capture_output=True,text=True,timeout=60)
 if p.returncode:raise RuntimeError(p.stderr[-1200:])
 return p.stdout.strip()
def line(p):
 q=queue.Queue();threading.Thread(target=lambda:q.put(p.stdout.readline().strip()),daemon=True).start()
 try:return q.get(timeout=30)
 except queue.Empty:raise TimeoutError('Child readiness')
def baseline():
 return ps("Get-NetRoute | Where-Object {$_.DestinationPrefix -in @('0.0.0.0/0','::/0')} | Sort-Object InterfaceIndex,DestinationPrefix,NextHop | Select-Object InterfaceIndex,DestinationPrefix,NextHop,RouteMetric | ConvertTo-Json -Compress")
def dns():
 return ps('Get-DnsClientServerAddress | Where-Object {$_.ServerAddresses.Count -gt 0} | Sort-Object InterfaceIndex,AddressFamily | Select-Object InterfaceIndex,AddressFamily,ServerAddresses | ConvertTo-Json -Compress')
def clean():
 until=time.monotonic()+30
 while ps(f"Get-NetAdapter -Name '{alias}' -IncludeHidden -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name"):
  assert time.monotonic()<until,'AWG adapter remained';time.sleep(.3)
 assert not ps("Get-NetRoute | Where-Object {$_.DestinationPrefix -in @('198.19.0.1/32','fd78:fccc::1/128')} | Select-Object -ExpandProperty DestinationPrefix"),'Test routes remained'
 assert baseline()==before and dns()==dns_before,'Defaults/DNS changed'
 assert not ps("Get-Process fc-awg -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"),'Worker remained'
def stop(mode):
 global owner,child_pid
 if mode=='owner-crash':owner.kill();owner.wait(timeout=10)
 else:
  ps(f'Stop-Process -Id {child_pid} -Force');owner.wait(timeout=10)
 owner=None;child_pid=None;clean()
try:
 before=baseline();dns_before=dns()
 assert not ps("Get-NetAdapter -IncludeHidden | Where-Object {$_.Name -like 'fcawg*'} | Select-Object -ExpandProperty Name"),'Existing AWG adapter'
 assert not ps("Get-NetRoute | Where-Object {$_.DestinationPrefix -in @('198.19.0.1/32','fd78:fccc::1/128')} | Select-Object -ExpandProperty DestinationPrefix"),'Conflicting test routes'
 manifest=json.loads((folder/'build.json').read_text(encoding='utf-8-sig'))
 for name,h in manifest['files'].items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==h
 client_key=X25519PrivateKey.generate();server_key=X25519PrivateKey.generate()
 client_public=client_key.public_key().public_bytes_raw().hex();server_public=server_key.public_key().public_bytes_raw().hex()
 with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as p:p.bind(('127.0.0.1',0));port=p.getsockname()[1]
 server_config=f'private_key={server_key.private_bytes_raw().hex()}\nlisten_port={port}\n'+params+f'public_key={client_public}\nallowed_ip=198.19.0.2/32\nallowed_ip=fd78:fccc::2/128\n\n'
 peer=subprocess.Popen([str(folder/'peer-fixture.exe')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
 peer.stdin.write(json.dumps({'config':server_config}));peer.stdin.close();assert line(peer)=='ready'
 uplink=ps("(Get-NetIPAddress -IPAddress '127.0.0.1' -AddressFamily IPv4).InterfaceAlias")
 for mode in ('engine-stop','owner-crash','wrong-header','wrong-key'):
  alias='fcawg'+uuid.uuid4().hex[:8]
  obfuscation=params.replace('h1=1001-1010','h1=9001-9010') if mode=='wrong-header' else params
  public=X25519PrivateKey.generate().public_key().public_bytes_raw().hex() if mode=='wrong-key' else server_public
  cfg=f'private_key={client_key.private_bytes_raw().hex()}\n'+obfuscation+f'public_key={public}\nendpoint=127.0.0.1:{port}\nallowed_ip=0.0.0.0/0\nallowed_ip=::/0\npersistent_keepalive_interval=1\n\n'
  owner=subprocess.Popen([str(owner_exe),str(folder/'fc-awg.exe')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
  owner.stdin.write(json.dumps({'adapter':alias,'uplink':uplink,'config':cfg}));owner.stdin.close();child_pid=int(line(owner))
  try:
   f=open('\\\\.\\pipe\\ProtectedPrefix\\Administrators\\AmneziaWG\\'+alias,'r+b',buffering=0);f.close();raise AssertionError('Unexpected UAPI pipe')
  except FileNotFoundError:pass
  ps(f"$i=(Get-NetAdapter -Name '{alias}').ifIndex; Set-NetIPInterface -InterfaceIndex $i -AddressFamily IPv4 -Dhcp Disabled -InterfaceMetric 5000; Set-NetIPInterface -InterfaceIndex $i -AddressFamily IPv6 -InterfaceMetric 5000; New-NetIPAddress -InterfaceIndex $i -IPAddress '198.19.0.2' -PrefixLength 32 -PolicyStore ActiveStore | Out-Null; New-NetIPAddress -InterfaceIndex $i -IPAddress 'fd78:fccc::2' -PrefixLength 128 -PolicyStore ActiveStore | Out-Null; New-NetRoute -InterfaceIndex $i -DestinationPrefix '198.19.0.1/32' -NextHop '0.0.0.0' -PolicyStore ActiveStore | Out-Null; New-NetRoute -InterfaceIndex $i -DestinationPrefix 'fd78:fccc::1/128' -NextHop '::' -PolicyStore ActiveStore | Out-Null")
  until=time.monotonic()+20
  while ps(f"@(Get-NetIPAddress -InterfaceAlias '{alias}' | Where-Object {{$_.IPAddress -in @('198.19.0.2','fd78:fccc::2') -and $_.AddressState -eq 'Preferred'}}).Count")!='2':
   assert time.monotonic()<until;time.sleep(.3)
  row={'mode':mode,'ipv4':0,'ipv6':0,'rejected':0,'clean':False};result['rounds'].append(row)
  for family,target,source,key in [(socket.AF_INET,'198.19.0.1','198.19.0.2','ipv4'),(socket.AF_INET6,'fd78:fccc::1','fd78:fccc::2','ipv6')]:
   with socket.socket(family,socket.SOCK_DGRAM) as p:
    p.bind((source,0));p.settimeout(3)
    for _ in range(3 if mode in ('engine-stop','owner-crash') else 1):
     payload=secrets.token_bytes(96);p.sendto(payload,(target,18765))
     try:reply,_=p.recvfrom(512)
     except socket.timeout:
      assert mode in ('wrong-header','wrong-key'),'AWG echo timed out';row['rejected']+=1;continue
     assert mode in ('engine-stop','owner-crash') and reply==payload,'Unauthorized or corrupt echo';row[key]+=1
  stop(mode);row['clean']=True
 # Invalid input must not create any adapter or public control interface.
 for raw in ('{}','{"adapter":"bad","uplink":"x","config":"x"}',json.dumps({'adapter':'fcawg12345678','uplink':uplink,'config':'private_key=invalid\n\n'})):
  p=subprocess.run([str(folder/'fc-awg.exe')],input=raw,text=True,capture_output=True,timeout=15);assert p.returncode!=0
 alias='fcawg12345678';clean();result['invalid_inputs_rejected']=3
 result['passed']=all(x['clean'] and (x['ipv4']==3 and x['ipv6']==3 if x['mode'] in ('engine-stop','owner-crash') else x['rejected']==2) for x in result['rounds'])
 assert result['passed']
except Exception as e:
 import traceback
 result.update(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc());raise
finally:
 if owner and owner.poll() is None:owner.kill();owner.wait(timeout=10)
 if peer and peer.poll() is None:peer.kill();peer.wait(timeout=10)
 output.write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
