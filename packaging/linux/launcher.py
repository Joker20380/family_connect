"""Bundled Linux launcher: isolate pinned deps, then run the GTK client.

The Debian package and AppImage share this launcher so behaviour is identical.
State stays under $HOME; nothing here reads or writes package-local identity.
"""
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / 'vendor'
DESKTOP = ROOT / 'clients' / 'desktop'

# Pinned vendor first, then the bundle layout used by the paired preview.
if VENDOR.is_dir():
    sys.path.insert(0, str(VENDOR))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(DESKTOP))

app = DESKTOP / 'app.py'
sys.argv[0] = str(app)
runpy.run_path(str(app), run_name='__main__')
