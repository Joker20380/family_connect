#!/usr/bin/env bash
set -euo pipefail

environment="${1:?Usage: ci_desktop_env.sh VENV_PATH}"
/usr/bin/python3 -c 'import sys; print("System:", sys.executable, sys.version); assert sys.version_info[:2] == (3, 12)'
sudo apt-get update
sudo apt-get install -y curl python3-venv python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
/usr/bin/python3 -m venv --system-site-packages "$environment"
"$environment/bin/python" -m pip install -r control/requirements.lock -r provisioning/requirements.lock -r device_identity/requirements.lock
"$environment/bin/python" -m pip install --no-deps --require-hashes -r messenger/requirements.lock
"$environment/bin/python" - <<'PY'
from importlib.metadata import version
from pathlib import Path
import sys

print("Desktop tests:", sys.executable, sys.version, flush=True)
assert sys.version_info[:2] == (3, 12)
assert sys.prefix != sys.base_prefix

import httpx
import LXMF
import RNS
import gi

for namespace, required in (("Gio", "2.0"), ("GLib", "2.0"), ("Gtk", "4.0"), ("Adw", "1")):
    gi.require_version(namespace, required)
from gi.repository import Gio, GLib, Gtk, Adw

sys.path.insert(0, str(Path("clients/desktop").resolve()))
from provisioning.chat_owner import ChatOwner
from provisioning.chat_bridge import ChatBridge
import chat_daemon

for package in ("pytest", "httpx", "lxmf", "rns", "cryptography", "PyGObject"):
    print(f"{package}=={version(package)}")
for module in (httpx, LXMF, RNS, gi, chat_daemon):
    print(f"{module.__name__}: {module.__file__}")
for namespace in (Gio, GLib, Gtk, Adw):
    print(f"{namespace.__name__}: {namespace._version}")
print("ChatOwner:", ChatOwner.__module__, "ChatBridge:", ChatBridge.__module__)
print("Real desktop imports: PASS")
PY
