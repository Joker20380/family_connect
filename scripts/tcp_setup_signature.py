"""Offline TCP Setup release signatures; verification never executes the archive."""
import argparse,base64,hashlib,json,os,re,stat
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey

DOMAIN=b'family-connect/tcp-setup-release/v1\x00'
MAX_SIZE=1024*1024
def unique(pairs):
    out={}
    for key,value in pairs:
        if key in out:raise ValueError('Duplicate signature field')
        out[key]=value
    return out
def version(value):
    if not isinstance(value,str) or not re.fullmatch(r'(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})',value):raise ValueError('Invalid setup version')
    return value
def archive_bytes(path):
    with path.open('rb') as f:raw=f.read(MAX_SIZE+1)
    if not 1<=len(raw)<=MAX_SIZE:raise ValueError('Setup size limit')
    return raw
def metadata(archive,release_version):
    raw=archive_bytes(archive)
    return dict(schema=1,component='tcp-setup',architecture='amd64',version=version(release_version),size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def sign(archive,release_version,key_path,output):
    info=key_path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600:raise ValueError('Unsafe signing key')
    payload=json.dumps(metadata(archive,release_version),sort_keys=True,separators=(',',':')).encode()
    key=Ed25519PrivateKey.from_private_bytes(key_path.read_bytes())
    envelope=json.dumps(dict(payload=base64.b64encode(payload).decode(),signature=base64.b64encode(key.sign(DOMAIN+payload)).decode()),sort_keys=True,separators=(',',':'))+'\n'
    with output.open('x') as f:f.write(envelope)
def verify(archive,signature,anchor,expected_version):
    version(expected_version)
    with signature.open('rb') as f:raw=f.read(65537)
    if len(raw)>65536:raise ValueError('Signature size limit')
    outer=json.loads(raw,object_pairs_hook=unique)
    if type(outer) is not dict or set(outer)!={'payload','signature'}:raise ValueError('Invalid signature envelope')
    payload=base64.b64decode(outer['payload'],validate=True)
    public=base64.b64decode(anchor.read_text().strip(),validate=True)
    Ed25519PublicKey.from_public_bytes(public).verify(base64.b64decode(outer['signature'],validate=True),DOMAIN+payload)
    data=json.loads(payload,object_pairs_hook=unique)
    if type(data) is not dict or set(data)!={'schema','component','architecture','version','size','sha256'} or type(data['schema']) is not int or type(data['size']) is not int:raise ValueError('Invalid setup metadata')
    if data!=metadata(archive,expected_version):raise ValueError('Setup version/hash/size mismatch')
    return data
def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='operation',required=True)
    for operation in ('sign','verify'):
        p=sub.add_parser(operation);p.add_argument('--archive',type=Path,required=True);p.add_argument('--version',required=True)
        if operation=='sign':p.add_argument('--key',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
        else:p.add_argument('--signature',type=Path,required=True);p.add_argument('--anchor',type=Path,required=True,help='Previously trusted base64 Ed25519 public key; never trust the key inside the downloaded setup')
    a=parser.parse_args()
    if a.operation=='sign':sign(a.archive,a.version,a.key,a.output);print('Setup signature written; private key remains local.')
    else:print(json.dumps(verify(a.archive,a.signature,a.anchor,a.version),sort_keys=True))
if __name__=='__main__':main()
