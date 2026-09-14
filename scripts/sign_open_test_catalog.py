"""Offline-only signing of an explicitly public, perpetual TCP test catalog.

Client credentials in this catalog are intentionally shared by all testers. Never
use personal profiles or server private keys. Does not sign application updates.
"""
import argparse,base64,json,os,stat
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from clients.desktop.profile_config import parse_tcp

DOMAIN=b'family-connect/open-test/v1\0'

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--key',type=Path,required=True);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 args=p.parse_args();raw=args.input.read_bytes();assert len(raw)<=8192
 value=json.loads(raw);assert set(value)=={'schema','sequence','access','gateways'}
 assert value['schema']==1 and type(value['sequence']) is int and value['sequence']>0 and value['access']=='open-test'
 assert len(value['gateways'])==2 and {g['country'] for g in value['gateways']}=={'ru','nl'}
 for gateway in value['gateways']:
  assert set(gateway)=={'country','profile'};parse_tcp(json.dumps(gateway['profile']))
 fd=os.open(args.key,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  info=os.fstat(fd);assert stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1 and stat.S_IMODE(info.st_mode)==0o600
  key=Ed25519PrivateKey.from_private_bytes(os.read(fd,33))
 finally:os.close(fd)
 envelope=json.dumps({'payload':base64.b64encode(raw).decode(),'signature':base64.b64encode(key.sign(DOMAIN+raw)).decode()},separators=(',',':')).encode()
 fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as output:output.write(envelope);output.flush();os.fsync(output.fileno())
 print('Open-test catalog signed offline; sequence',value['sequence'])

if __name__=='__main__':main()
