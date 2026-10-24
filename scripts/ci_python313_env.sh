#!/usr/bin/env bash
set -euo pipefail

environment="${1:?Usage: ci_python313_env.sh VENV_PATH}"
python -c 'import sys; print("Bootstrap:", sys.executable, sys.version); assert sys.version_info[:2] == (3, 13)'
python -m venv "$environment"
export PATH="$environment/bin:$PATH"
"$environment/bin/python" -m pip install -r control/requirements.lock -r provisioning/requirements.lock -r device_identity/requirements.lock
"$environment/bin/python" -m pip install --no-deps --require-hashes -r messenger/requirements.lock
"$environment/bin/python" -m pip install meson==1.7.0 meson-python==0.17.1 pyproject-metadata==0.9.1 ninja==1.11.1.3
"$environment/bin/python" -m pip install --no-build-isolation pycairo==1.27.0
"$environment/bin/python" -m pip install --no-build-isolation PyGObject==3.50.0
"$environment/bin/python" - <<'PY'
from importlib.metadata import version
from pathlib import Path
import sys

print("Full-suite tests:", sys.executable, sys.version, flush=True)
assert sys.version_info[:2] == (3, 13)
assert sys.prefix != sys.base_prefix

import httpx
import LXMF
import RNS
import cairo
import gi
import gi._gi

for namespace, required in (("Gio", "2.0"), ("GLib", "2.0"), ("Gtk", "4.0"), ("Adw", "1")):
    gi.require_version(namespace, required)
from gi.repository import Gio, GLib, Gtk, Adw

sys.path.insert(0, str(Path("clients/desktop").resolve()))
from provisioning.chat_owner import ChatOwner
from provisioning.chat_bridge import ChatBridge
import chat_daemon
import messenger.codec

for package in ("pytest", "httpx", "lxmf", "rns", "cryptography", "PyGObject", "pycairo",
                "meson", "meson-python", "pyproject-metadata", "ninja"):
    print(f"{package}=={version(package)}")
for module in (httpx, LXMF, RNS, cairo, gi, gi._gi, chat_daemon, messenger.codec,
               sys.modules[ChatOwner.__module__], sys.modules[ChatBridge.__module__]):
    print(f"{module.__name__}: {module.__file__}")
for namespace in (Gio, GLib, Gtk, Adw):
    print(f"{namespace.__name__}: {namespace._version}")
print("Real Python 3.13 imports: PASS")
PY
