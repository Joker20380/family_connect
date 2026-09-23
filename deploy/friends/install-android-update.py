"""Publish HTTPS Android discovery after APK signature/device acceptance, preserving rollback."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path

ROOT=Path('/opt/apps/family_connect/state-product-https/config')
BASE='https://185.251.89.19:8443'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('manifest',type=Path);args=parser.parse_args()
    raw=args.manifest.read_bytes();assert len(raw)<=8192
    data=json.loads(raw);assert data['schema']==1 and data['package']=='com.familyconnect.app.friends' and data['abi']=='arm64-v8a'
    code=data['version_code'];assert type(code) is int and code>0
    version=data['version'];assert re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+-beta[0-9]+',version)
    name=f'FamilyConnect-Test-{version}.apk';assert data['url']==f'{BASE}/downloads/{name}'
    apk=ROOT/'downloads'/name;assert apk.stat().st_size==data['size'] and hashlib.sha256(apk.read_bytes()).hexdigest()==data['sha256']
    target=ROOT/'android-friends-update.json';previous=target.read_bytes() if target.exists() else None
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
            if 'location = /updates/android-friends.json {' in text:continue
            assert text.count('        location = /invite/ {')==1
            backup=ROOT/(name+suffix);assert not backup.exists();backup.write_text(text)
            path.write_text(text.replace('        location = /invite/ {',location+'        location = /invite/ {',1));changed.append((path,text))
        if previous is not None and raw!=previous:
            backup=ROOT/('android-friends-update.json'+suffix);assert not backup.exists();backup.write_bytes(previous)
        temporary=target.with_suffix('.pending');temporary.write_bytes(raw);temporary.chmod(0o644);os.replace(temporary,target)
        subprocess.run(['docker','exec','family-connect-product-https','nginx','-t','-c','/etc/fc/nginx.conf'],check=True)
        if changed:subprocess.run(['docker','kill','--signal=HUP','family-connect-product-https'],check=True,stdout=subprocess.DEVNULL)
    except BaseException:
        for path,text in changed:path.write_text(text)
        if previous is not None:target.write_bytes(previous)
        else:target.unlink(missing_ok=True)
        raise
    print(f'Android discovery published: {version}, code {code}; APK size/hash verified')

if __name__=='__main__':main()
