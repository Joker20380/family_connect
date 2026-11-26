"""Disposable user-systemd fixture only; allow its independent test controller."""
import ctypes
import os
from pathlib import Path
import sys

assert os.environ.get('FC_TEST_PTRACER_ANY') == '1'
assert ctypes.CDLL(None, use_errno=True).prctl(0x59616d61, ctypes.c_ulong(-1), 0, 0, 0) == 0
arguments = sys.argv[1:]
if arguments[0] == '--barrier':
    barrier, arguments = arguments[1], arguments[2:]
    Path(barrier + '.entered').touch()
    with open(barrier, 'rb', buffering=0) as source:
        assert source.read(1) == b'1'
os.execv(arguments[0], arguments)
