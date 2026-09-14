"""Offline-only signing of perpetual invited-test gateway templates.

Templates contain placeholders for device credentials and addresses. Never include
personal profiles or server private keys. Does not sign application updates.
"""
import argparse,base64,json,os,stat
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from clients.desktop.profile_config import parse_tcp, parse

DOMAIN=b'family-connect/invited-test/v1\0'

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--key',type=Path,required=True);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 args=p.parse_args();raw=args.input.read_bytes();assert len(raw)<=8192
 value=json.loads(raw);assert set(value)=={'schema','sequence','access','gateways'}
 assert value['schema']==2 and type(value['sequence']) is int and value['sequence']>0 and value['access']=='invite-test'
 assert len(value['gateways'])==2 and {g['country'] for g in value['gateways']}=={'ru','nl'}
 for gateway in value['gateways']:
  assert set(gateway)=={'country','tcp','awg'};tcp=dict(gateway['tcp']);assert tcp['id']=='DEVICE_CREDENTIAL';tcp['id']='11111111-1111-4111-8111-111111111111';parse_tcp(json.dumps(tcp))
  template=gateway['awg'];assert template.count('LOCAL_DEVICE_KEY')==1 and template.count('ASSIGNED_ADDRESS')==1
  assert '\nPrivateKey = LOCAL_DEVICE_KEY\n' in template and '\nAddress = ASSIGNED_ADDRESS\n' in template
  assert 'HeaderProtectionKey = ' in template and 'ContentPaddingAddition = ' in template
  # Validate added 3.1 parameters separately; never loosen the managed schema2 parser.
  import re
  header=re.findall(r'^HeaderProtectionKey = (.+)$',template,re.M);assert len(header)==1
  decoded=base64.b64decode(header[0],validate=True);assert len(decoded)==32 and any(decoded)
  padding=re.findall(r'^ContentPaddingAddition = (.+)$',template,re.M);assert padding==['0-32']
  for index in range(1,5):
   assert re.findall(r'^H'+str(index)+r' = (.+)$',template,re.M)==[str(index)]
   widths=re.findall(r'^S'+str(index)+r' = (.+)$',template,re.M);assert len(widths)==1 and widths[0].isdigit() and 12<=int(widths[0])<=256
  legacy=re.sub(r'^(HeaderProtectionKey|ContentPaddingAddition) = .+\n','',template,flags=re.M)
  for index in range(1,5):legacy=legacy.replace('H'+str(index)+' = '+str(index)+'\n','H'+str(index)+' = '+str(100+index)+'\n')
  parse(legacy.replace('LOCAL_DEVICE_KEY',base64.b64encode(bytes([1])*32).decode()).replace('ASSIGNED_ADDRESS','10.83.0.2/32'),allow_awg=True)
 fd=os.open(args.key,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  info=os.fstat(fd);assert stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1 and stat.S_IMODE(info.st_mode)==0o600
  key=Ed25519PrivateKey.from_private_bytes(os.read(fd,33))
 finally:os.close(fd)
 envelope=json.dumps({'payload':base64.b64encode(raw).decode(),'signature':base64.b64encode(key.sign(DOMAIN+raw)).decode()},separators=(',',':')).encode()
 fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as output:output.write(envelope);output.flush();os.fsync(output.fileno())
 print('Invited-test templates signed offline; sequence',value['sequence'])

if __name__=='__main__':main()
