"""Bundled Linux launcher: isolate pinned deps, then run the GTK client.

The Debian package and AppImage share this launcher so behaviour is identical.
State stays under $HOME; nothing here reads or writes package-local identity.
"""
from pathlib import Path
import json
import os
import runpy
import sys
import sysconfig

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / 'vendor'
DESKTOP = ROOT / 'clients' / 'desktop'

sys.dont_write_bytecode = True
if (ROOT / 'candidate.json').is_file():
    library = sysconfig.get_path('stdlib')
    sys.path[:] = [str(DESKTOP), str(ROOT), str(VENDOR), library,
                   str(Path(library) / 'lib-dynload'), '/usr/lib/python3/dist-packages']
    import candidate_runtime
    candidate = candidate_runtime.verify()
    if os.geteuid() == 0:
        raise SystemExit('Launch the internal candidate as an ordinary desktop user, never root')
    import backend
    backend.CANDIDATE_GUARD = candidate_runtime.installed_guard
    backend.CANDIDATE_SETUP = candidate_runtime.setup
    backend.CANDIDATE_VERSION = candidate['internal_version']
    if sys.argv[1:] == ['--setup-system']:
        print(json.dumps(candidate_runtime.setup()))
        raise SystemExit(0)
    if sys.argv[1:] == ['--candidate-check']:
        print(json.dumps(candidate_runtime.check_imports()))
        raise SystemExit(0)
    if sys.argv[1:] == ['--candidate-status']:
        print(json.dumps({'candidate': candidate['build_id'], 'system': backend.system_component_status()}))
        raise SystemExit(0)
    if sys.argv[1:] == ['--prepare-chat']:
        print(json.dumps(backend.prepare_chat_services()))
        raise SystemExit(0)
    if sys.argv[1:] == ['--remove-integration']:
        print(json.dumps(candidate_runtime.remove_integration()))
        raise SystemExit(0)
    if sys.argv[1:] == ['--chat-service'] and backend.system_component_status() != 'READY':
        raise SystemExit('Matching system runtime required before starting the candidate chat owner')
    if any(argument.startswith('--setup-system') for argument in sys.argv[1:]):
        raise SystemExit('System setup accepts no paths or additional arguments')
elif any(argument in ('--setup-system', '--candidate-check', '--candidate-status', '--prepare-chat') for argument in sys.argv[1:]):
    raise SystemExit('This package has no internal candidate contract')

# Pinned vendor first, then the bundle layout used by the paired preview.
if VENDOR.is_dir():
    sys.path.insert(0, str(VENDOR))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(DESKTOP))

if sys.argv[1:] == ['--chat-service']:
    runpy.run_path(str(DESKTOP / 'chat_daemon.py'), run_name='__main__')
    raise SystemExit(0)

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
        'gir1.2-gtk-4.0 gir1.2-adw-1 librsvg2-common\n'
        f'({exc})\n'
    )
    raise SystemExit(2)

app = DESKTOP / 'app.py'
sys.argv[0] = str(app)
runpy.run_path(str(app), run_name='__main__')
