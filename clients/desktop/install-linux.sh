#!/bin/sh
set -eu
python3 -c 'import tkinter'
command -v nmcli >/dev/null
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
install_dir="$HOME/.local/share/family-connect"
mkdir -p "$install_dir" "$HOME/.local/share/applications"
cp "$source_dir/app.py" "$source_dir/backend.py" "$source_dir/profile_config.py" "$install_dir/"
python3 - "$install_dir" <<'PY'
from pathlib import Path
import sys
folder=Path(sys.argv[1])
entry=Path.home()/'.local/share/applications/family-connect.desktop'
command=str(folder/'app.py').replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$')
entry.write_text('[Desktop Entry]\nType=Application\nName=Family Connect\nExec=python3 "'+command+'"\nTerminal=false\nCategories=Network;\nComment=Family VPN client\n')
print('Installed / Установлено:',entry)
PY
