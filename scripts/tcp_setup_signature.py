"""Offline TCP Setup release signatures; verification never executes the archive."""
import argparse,base64,hashlib,json,os,re
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

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
def key_loader():
    # Verification is also shipped standalone; import operator dependencies only for signing.
    if __package__:
        from . import signing_key
    else:
        # Also support importlib loading by operator/test harnesses, which do not
        # automatically add this script's directory to sys.path.
        import importlib.util
        spec=importlib.util.spec_from_file_location('_fc_signing_key',Path(__file__).with_name('signing_key.py'))
        signing_key=importlib.util.module_from_spec(spec);spec.loader.exec_module(signing_key)
    return signing_key

def sign(archive,release_version,key_path,output,*,private_key=None):
    key=private_key
    if key is None:
        a=argparse.Namespace(key=key_path,vault=None,vault_entry=None,vault_member=None,
                             vault_public_key=None,vault_password_dialog=False)
        key=key_loader().load(a)
    payload=json.dumps(metadata(archive,release_version),sort_keys=True,separators=(',',':')).encode()
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
        if operation=='sign':
            source=p.add_mutually_exclusive_group(required=True)
            source.add_argument('--key',type=Path);source.add_argument('--vault',type=Path)
            p.add_argument('--vault-entry');p.add_argument('--vault-member')
            p.add_argument('--vault-public-key',type=Path);p.add_argument('--vault-password-dialog',action='store_true')
            p.add_argument('--output',type=Path,required=True)
        else:p.add_argument('--signature',type=Path,required=True);p.add_argument('--anchor',type=Path,required=True,help='Previously trusted base64 Ed25519 public key; never trust the key inside the downloaded setup')
    a=parser.parse_args()
    if a.operation=='sign':sign(a.archive,a.version,None,a.output,private_key=key_loader().load(a));print('Setup signature written; private key remains local.')
    else:print(json.dumps(verify(a.archive,a.signature,a.anchor,a.version),sort_keys=True))
if __name__=='__main__':main()
