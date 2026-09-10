#!/bin/sh
set -eu
if ! python3 -c 'import gi, cryptography; gi.require_version("Gtk", "4.0"); gi.require_version("Adw", "1")'; then
    echo 'Install Python GI, GTK 4 and libadwaita first. Ubuntu/Debian: sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-cryptography' >&2
    exit 1
fi
command -v nmcli >/dev/null
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 - "$source_dir" <<'PY'
import ast
import base64
import os
from pathlib import Path
import secrets
import shutil
import sys
source=Path(sys.argv[1])
version=next(node.value.value for node in ast.parse((source/'app.py').read_text()).body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='APP_VERSION' for t in node.targets))
root=Path.home()/'.local/share/family-connect';root.mkdir(parents=True,exist_ok=True)
if root.is_symlink():raise ValueError('Unsafe application directory')
releases=root/'releases';releases.mkdir(mode=0o700,exist_ok=True)
if releases.is_symlink():raise ValueError('Unsafe release directory')
release=releases/(version+'-'+secrets.token_hex(6));release.mkdir(mode=0o700)
for name in ('app.py','backend.py','profile_config.py','updates.py','update.pub','install-linux.sh'):
    shutil.copyfile(source/name,release/name);(release/name).chmod(0o600)
if (root/'current').is_symlink():
    previous=root/('.previous-'+secrets.token_hex(6));previous.symlink_to(os.readlink(root/'current'));os.replace(previous,root/'previous')
link=root/('.current-'+secrets.token_hex(6));link.symlink_to(release.relative_to(root));os.replace(link,root/'current')
icon_data=next(node.value.value for node in ast.parse((source/'app.py').read_text()).body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ICON_PNG' for t in node.targets))
(root/'app.png').write_bytes(base64.b64decode(icon_data))
folder=Path.home()/'.local/share/applications';folder.mkdir(parents=True,exist_ok=True)
command=str(root/'current/app.py').replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$')
(folder/'family-connect.desktop').write_text('[Desktop Entry]\nType=Application\nName=Family Connect\nExec=python3 "'+command+'"\nIcon='+str(root/'app.png')+'\nStartupWMClass=com.familyconnect.Client\nTerminal=false\nCategories=Network;\nComment=Family VPN client\n')
entry=folder/'family-connect.desktop'
(folder/'com.familyconnect.Client.desktop').write_text(entry.read_text()+'NoDisplay=true\n')
print('Installed Family Connect',version)
PY
