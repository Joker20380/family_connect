"""Publish HTTPS Android discovery after APK signature/device acceptance, preserving rollback."""
import argparse,base64,hashlib,json,os,re,subprocess,time
from pathlib import Path

ROOT=Path('/opt/apps/family_connect/state-product-https/config')
BASE='https://185.251.89.19:8443'

def verify_signed(raw, legacy, previous=None):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if len(raw)>16384:raise ValueError('signed manifest size')
    envelope=json.loads(raw);payload=base64.b64decode(envelope['payload'],validate=True)
    anchor=base64.b64decode('0NdiJ/7kjveUMEEFNr7or8tMZNQHHzNq4rrfzp6/6i0=')
    Ed25519PublicKey.from_public_bytes(anchor).verify(base64.b64decode(envelope['signature'],validate=True),b'family-connect/android-update/v1\0'+payload)
    data=json.loads(payload);now=int(time.time())
    if any(data.get(key)!=legacy[key] for key in ('schema','package','abi','version_code','version','url','size','sha256')):raise ValueError('legacy/signed mismatch')
    if data['channel']!='android-field' or data['signer_fingerprint']!='67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a':raise ValueError('signed identity')
    if not data['issued_at']<=now<data['expires_at']<=data['issued_at']+90*86400:raise ValueError('signed lease')
    if not 1<=data['minimum_supported_version']<=data['version_code'] or data['mandatory_after']!=0 and not data['issued_at']<=data['mandatory_after']<data['expires_at']:raise ValueError('signed policy')
    if not 1<=data['sequence']<10**15:raise ValueError('signed sequence')
    if previous is not None:
        old=json.loads(base64.b64decode(json.loads(previous)['payload'],validate=True))
        if data['sequence']<old['sequence'] or data['sequence']==old['sequence'] and raw!=previous:raise ValueError('signed rollback/conflict')
    return data

def main():
    parser=argparse.ArgumentParser();parser.add_argument('manifest',type=Path);parser.add_argument('--signed-catalog',type=Path);args=parser.parse_args()
    raw=args.manifest.read_bytes();assert len(raw)<=8192
    data=json.loads(raw);assert data['schema']==1 and data['package']=='com.familyconnect.app.friends' and data['abi']=='arm64-v8a'
    code=data['version_code'];assert type(code) is int and code>0
    version=data['version'];assert re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+-beta[0-9]+',version)
    name=f'FamilyConnect-Test-{version}.apk';assert data['url']==f'{BASE}/downloads/{name}'
    apk=ROOT/'downloads'/name;assert apk.stat().st_size==data['size'] and hashlib.sha256(apk.read_bytes()).hexdigest()==data['sha256']
    target=ROOT/'android-friends-update.json';previous=target.read_bytes() if target.exists() else None
    signed_target=ROOT/'android-friends-update-v2.json';signed_previous=signed_target.read_bytes() if signed_target.exists() else None
    signed_raw=args.signed_catalog.read_bytes() if args.signed_catalog else None
    if code>=59 and signed_raw is None:raise ValueError('FIELD requires signed discovery')
    if signed_raw is not None:verify_signed(signed_raw,data,signed_previous)
    if previous is not None:
        old=json.loads(previous);assert code>=old['version_code']
        if code==old['version_code']:assert data==old,'Refuse replacing an existing version'
    suffix=f'.before-android-update-{code}';changed=[]
    location='''        location = /updates/android-friends.json {
            alias /etc/fc/android-friends-update.json;
            default_type application/json;
            limit_except GET { deny all; }
            add_header Cache-Control "no-store" always;
            add_header X-Content-Type-Options nosniff always;
        }
'''
    try:
        for name in ['nginx.conf','nginx-final.conf']:
            path=ROOT/name;text=path.read_text()
            locations=location if 'location = /updates/android-friends.json {' not in text else ''
            if signed_raw is not None and 'location = /updates/android-friends-v2.json {' not in text:
                locations+=location.replace('/updates/android-friends.json','/updates/android-friends-v2.json').replace('/etc/fc/android-friends-update.json','/etc/fc/android-friends-update-v2.json')
            if not locations:continue
            assert text.count('        location = /invite/ {')==1
            backup=ROOT/(name+suffix);assert not backup.exists();backup.write_text(text)
            path.write_text(text.replace('        location = /invite/ {',locations+'        location = /invite/ {',1));changed.append((path,text))
        if previous is not None and raw!=previous:
            backup=ROOT/('android-friends-update.json'+suffix);assert not backup.exists();backup.write_bytes(previous)
        temporary=target.with_suffix('.pending');temporary.write_bytes(raw);temporary.chmod(0o644);os.replace(temporary,target)
        if signed_raw is not None:
            if signed_previous is not None and signed_raw!=signed_previous:
                backup=ROOT/('android-friends-update-v2.json'+suffix);assert not backup.exists();backup.write_bytes(signed_previous)
            temporary=signed_target.with_suffix('.pending');temporary.write_bytes(signed_raw);temporary.chmod(0o644);os.replace(temporary,signed_target)
        subprocess.run(['docker','exec','family-connect-product-https','nginx','-t','-c','/etc/fc/nginx.conf'],check=True)
        if changed:subprocess.run(['docker','kill','--signal=HUP','family-connect-product-https'],check=True,stdout=subprocess.DEVNULL)
    except BaseException:
        for path,text in changed:path.write_text(text)
        if previous is not None:target.write_bytes(previous)
        else:target.unlink(missing_ok=True)
        if signed_previous is not None:signed_target.write_bytes(signed_previous)
        else:signed_target.unlink(missing_ok=True)
        raise
    print(f'Android discovery published: {version}, code {code}; APK size/hash verified')

if __name__=='__main__':main()
