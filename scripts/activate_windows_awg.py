"""Issue a signed Windows AWG activation offline from public gateway parameters.
Register the returned device public key/address on the AWG gateway separately.
No device private key is accepted or transferred by this tool.
"""
import argparse,base64,ipaddress,json,os,re,sys,time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'clients/desktop'))
from profile_config import validate_awg,AWG_FIELDS
DOMAIN=b'family-connect/windows-awg-activation/v1\0'
def issue(request,profile,sequence,key,now):
 if not isinstance(request,str) or not re.fullmatch(r'FC1-[0-9A-F]{64}',request) or not any(bytes.fromhex(request[4:])):raise ValueError('device')
 if type(sequence) is not int or not 1<=sequence<=9007199254740991 or type(now) is not int or not 0<=now<253402214399:raise ValueError('sequence/clock')
 def unique(items):
  d={}
  for k,v in items:
   if k in d:raise ValueError('duplicate')
   d[k]=v
  return d
 if len(profile.encode())>8192:raise ValueError('size')
 p=json.loads(profile,object_pairs_hook=unique)
 if not isinstance(p,dict) or set(p)!={'gatewayPublicKey','server','port','number','parameters'}:raise ValueError('fields')
 if type(p['port']) is not int or not 1<=p['port']<=65535 or type(p['number']) is not int or not 4<=p['number']<=254:raise ValueError('address')
 ip=ipaddress.IPv4Address(p['server'])
 if str(ip)!=p['server'] or ip.is_loopback or ip.packed[0]==0 or ip.packed[0]>=224:raise ValueError('endpoint')
 rawkey=base64.b64decode(p['gatewayPublicKey'],validate=True)
 if len(rawkey)!=32 or not any(rawkey) or base64.b64encode(rawkey).decode()!=p['gatewayPublicKey']:raise ValueError('key')
 v=p['parameters']
 if not isinstance(v,dict) or not set(v)<=AWG_FIELDS or not all(isinstance(x,str) for x in v.values()):raise ValueError('parameters')
 validate_awg(v)
 if any(int(v[k])<1 for k in ('Jc','Jmin','Jmax')):raise ValueError('positive junk values required by engine')
 grant=dict(version=1,devicePublicKey=base64.b64encode(bytes.fromhex(request[4:])).decode(),sequence=sequence,expiresAt=now+86400,**p)
 raw=json.dumps(grant,sort_keys=True,separators=(',',':')).encode()
 return dict(payload=base64.b64encode(raw).decode(),signature=base64.b64encode(key.sign(DOMAIN+raw)).decode())
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('key','profile','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--request',required=True);p.add_argument('--sequence',type=int,required=True);a=p.parse_args();os.umask(0o077)
 try:
  with a.profile.open('rb') as f:raw=f.read(8193)
  if len(raw)>8192:raise ValueError('size')
  envelope=issue(a.request,raw.decode(),a.sequence,Ed25519PrivateKey.from_private_bytes(a.key.read_bytes()),int(time.time()))
  with a.output.open('x',encoding='utf-8') as f:json.dump(envelope,f,sort_keys=True)
 except (ValueError,TypeError,OSError,UnicodeError):p.exit(1,'Cannot issue AWG activation; check public parameters and use a new output path.\n')
 print('AWG activation saved. Register device public key/address on the AWG gateway before delivery.')
if __name__=='__main__':main()
