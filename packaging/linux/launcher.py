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

# Fail with a clear message instead of a raw GTK/GI traceback. GTK 4,
# libadwaita and GI are host/system dependencies and are not bundled.
try:
    import gi
    import cairo
    gi.require_foreign('cairo')
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
except (ImportError, ValueError) as exc:
    sys.stderr.write(
        'Family Connect requires GTK 4 / libadwaita system packages.\n'
        'Ubuntu/Debian: sudo apt install python3-gi python3-gi-cairo '
        'gir1.2-gtk-4.0 gir1.2-adw-1\n'
        f'({exc})\n'
    )
    raise SystemExit(2)

app = DESKTOP / 'app.py'
sys.argv[0] = str(app)
runpy.run_path(str(app), run_name='__main__')
