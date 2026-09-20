"""Signed Friends catalog -> native AWG 3.1 /16 -> journal v2 recovery, CI only."""
import base64
import hashlib
import json
import os
from pathlib import Path
import queue
import secrets
import socket
import subprocess
import sys
import threading
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

assert sys.platform=='win32' and os.environ.get('GITHUB_ACTIONS')=='true'
host,engine,out=map(Path,sys.argv[1:4]);exe=host/'FamilyConnect.exe'
root=Path(os.environ['ProgramData'])/'FamilyConnect';journal=root/'tcp-session.json'
peer=None;session=None;result={'passed':False,'rounds':[]}
def ps(code):
 p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"$ErrorActionPreference='Stop'; "+code],capture_output=True,text=True,timeout=60)
 if p.returncode:raise RuntimeError('Network assertion failed')
 return p.stdout.strip()
def line(p):
 q=queue.Queue();threading.Thread(target=lambda:q.put(p.stdout.readline().strip()),daemon=True).start()
 return q.get(timeout=90)
def b64(b):return base64.b64encode(b).decode()
def network():
 return ps("Get-NetRoute | Where-Object {$_.DestinationPrefix -in @('0.0.0.0/0','::/0')} | Sort-Object InterfaceIndex,DestinationPrefix | Select-Object InterfaceIndex,DestinationPrefix,NextHop | ConvertTo-Json -Compress"),ps('Get-DnsClientServerAddress | Where-Object {$_.ServerAddresses.Count -gt 0} | Sort-Object InterfaceIndex,AddressFamily | Select-Object InterfaceIndex,AddressFamily,ServerAddresses | ConvertTo-Json -Compress'),ps('Get-DnsClientNrptRule | Sort-Object Name | Select-Object Name,Namespace,NameServers,DisplayName | ConvertTo-Json -Compress')
def clean():
 assert not journal.exists()
 assert not ps("Get-NetAdapter -IncludeHidden | Where-Object {$_.Name -like 'fcawg*'} | Select-Object -ExpandProperty Name")
 assert not ps("Get-NetRoute | Where-Object {$_.DestinationPrefix -in @('198.18.0.1/32','fd79:fc::1/128')} | Select-Object -ExpandProperty DestinationPrefix")
 assert network()==before
try:
 assert not root.exists(),'Existing store';before=network()
 client=X25519PrivateKey.generate();server=X25519PrivateKey.generate();signer=Ed25519PrivateKey.generate()
 hpk=secrets.token_bytes(32);address='10.83.42.254'
 with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 params='jc=3\njmin=40\njmax=80\n'+''.join(f's{i}=32\nh{i}={i}\n' for i in range(1,5))+'header_protection_key='+hpk.hex()+'\ncontent_padding_addition=0-64\nrandom_trailers=true\ndisable_cookies=false\n'
 config='private_key='+server.private_bytes_raw().hex()+f'\nlisten_port={port}\n'+params+'public_key='+client.public_key().public_bytes_raw().hex()+f'\nallowed_ip={address}/32\nallowed_ip=fd79:fc::2/128\n\n'
 peer=subprocess.Popen([str(engine/'peer-fixture.exe')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
 peer.stdin.write(json.dumps({'config':config}));peer.stdin.close();assert line(peer)=='ready'
 template='[Interface]\nPrivateKey = LOCAL_DEVICE_KEY\nAddress = ASSIGNED_ADDRESS\nDNS = 1.1.1.1\nMTU = 1280\nJc = 3\nJmin = 40\nJmax = 80\n'+''.join(f'S{i} = 32\nH{i} = {i}\n' for i in range(1,5))+'HeaderProtectionKey = '+b64(hpk)+'\nContentPaddingAddition = 0-64\nRandomTrailers = true\nDisableCookies = false\n[Peer]\nPublicKey = '+b64(server.public_key().public_bytes_raw())+f'\nEndpoint = 192.0.2.1:{port}\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n'
 tcp=dict(type='vless-reality-v1',server='192.0.2.1',port=443,id='DEVICE_CREDENTIAL',public_key=base64.urlsafe_b64encode(bytes(range(32))).decode().rstrip('='),server_name='example.com',short_id='abcd')
 catalog=dict(schema=2,sequence=2,access='invite-test',gateways=[dict(country=c,tcp=tcp,awg=template) for c in ('ru','nl')])
 raw=json.dumps(catalog,separators=(',',':')).encode();device='a'*64
 reply=dict(device=device,country='nl',address=address+'/32',tcp_id='11111111-1111-4111-8111-111111111111',catalog=dict(payload=b64(raw),signature=b64(signer.sign(b'family-connect/invited-test/v1\0'+raw))))
 request=dict(reply=reply,anchor=b64(signer.public_key().public_bytes_raw()),device=device,key=b64(client.private_bytes_raw()))
 for mode in ('disconnect','process-crash'):
  session=subprocess.Popen([str(exe),'/friends-awg-session'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
  session.stdin.write(json.dumps(request)+'\n');session.stdin.flush();assert line(session)=='ready','Friends session not ready'
  record=json.loads(journal.read_text());assert record['version']==2 and record['address']==address
  alias=record['adapter'];assert ps(f"(Get-NetIPAddress -InterfaceAlias '{alias}' -AddressFamily IPv4).IPAddress")==address
  with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
   s.bind((address,0));s.settimeout(5);payload=secrets.token_bytes(64);s.sendto(payload,('198.18.0.1',18765));assert s.recv(128)==payload
  if mode=='disconnect':
   session.stdin.write('stop\n');session.stdin.flush();assert line(session)=='clean';assert session.wait(timeout=30)==0
  else:
   session.kill();session.wait(timeout=10);assert journal.exists()
   p=subprocess.run([str(exe),'/recover-friends-session'],capture_output=True,text=True,timeout=60)
   assert p.returncode==0 and p.stdout.strip()=='clean','Journal recovery failed'
  session=None;clean();result['rounds'].append(dict(mode=mode,address=address,journal=2,clean=True))
 # This test created only the journal directory. Restore the clean-install
 # precondition for the following LocalSystem test; refuse to remove contents.
 root.rmdir()
 result['passed']=True
finally:
 if session and session.poll() is None:session.kill();session.wait(timeout=10)
 if journal.exists():subprocess.run([str(exe),'/recover-friends-session'],capture_output=True,timeout=60)
 if peer and peer.poll() is None:peer.kill();peer.wait(timeout=10)
 out.write_text(json.dumps(result,indent=2));print(json.dumps(result))
