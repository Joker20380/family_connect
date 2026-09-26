"""Install a verified paired preview and its invitation URL handler for this user.

Run using the persistent Python environment prepared for run_control_preview.py.
This does not install privileged VPN helpers or change an existing identity.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def install(source, python, data, applications):
    manifest=json.loads((source/'manifest.json').read_text())
    files=manifest['files'];bundle=manifest['bundle_id']
    digest=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
    if digest!=bundle or len(bundle)!=64:raise ValueError('Invalid bundle')
    for name,expected in files.items():
        path=source/name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('Invalid source file')
    target=data/'control-previews'/bundle[:16]/'FamilyConnect-Control-preview'
    target.mkdir(mode=0o700,parents=True,exist_ok=True)
    for name in (*files,'manifest.json'):
        dest=target/name;raw=(source/name).read_bytes()
        if dest.is_symlink():raise ValueError('Unsafe installation path')
        if dest.exists():
            if dest.read_bytes()!=raw:raise ValueError('Installed bundle differs')
        else:
            dest.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            with dest.open('xb') as stream:stream.write(raw)
            dest.chmod(0o600)
    def quote(value):
        value=str(value)
        if '\n' in value or '\r' in value:raise ValueError('Invalid desktop path')
        return '"'+value.replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')+'"'
    command=quote(python)+' '+quote(target/'scripts/run_control_preview.py')+' gui %u'
    entry='[Desktop Entry]\nType=Application\nName=family_connect\nExec='+command+'\nTerminal=false\nCategories=Network;\nStartupWMClass=com.familyconnect.Client\nMimeType=x-scheme-handler/familyconnect;\n'
    applications.mkdir(parents=True,exist_ok=True)
    path=applications/'family-connect.desktop'
    if path.is_symlink():raise ValueError('Unsafe launcher')
    pending=path.with_suffix('.pending');pending.write_text(entry);pending.replace(path)
    return target


def main():
    source=Path(__file__).resolve().parents[1]
    data=Path.home()/'.local/share'
    target=install(source,Path(sys.executable).absolute(),data/'family-connect',data/'applications')
    if shutil.which('update-desktop-database'):subprocess.run(['update-desktop-database',str(data/'applications')],check=True)
    subprocess.run(['xdg-mime','default','family-connect.desktop','x-scheme-handler/familyconnect'],check=True)
    print('Installed family_connect invitation handler:',target)


if __name__=='__main__':main()
