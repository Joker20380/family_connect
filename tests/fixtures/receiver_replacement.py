import ctypes
from pathlib import Path
import sqlite3
import sys

assert ctypes.CDLL(None, use_errno=True).prctl(0x59616d61, ctypes.c_ulong(-1), 0, 0, 0) == 0
archive = sys.argv.pop(1)
sys.path.insert(0, archive)
root = Path(sys.argv[sys.argv.index('--root') + 1])
candidate = '--capture-gate' in sys.argv
if candidate:
    with sqlite3.connect(root / 'preserved.sqlite') as database:
        database.execute('INSERT INTO history VALUES(2)')
    if (root / 'fail-candidate').exists():
        raise SystemExit(23)
    if (root / 'ignore-gate').exists():
        index = sys.argv.index('--capture-gate')
        del sys.argv[index:index + 2]

import friends_http

friends_http.main()
