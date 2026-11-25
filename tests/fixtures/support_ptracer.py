"""Disposable user-systemd fixture only; allow its independent test controller."""
import ctypes
import os
import sys

assert os.environ.get('FC_TEST_PTRACER_ANY') == '1'
assert ctypes.CDLL(None, use_errno=True).prctl(0x59616d61, ctypes.c_ulong(-1), 0, 0, 0) == 0
os.execv(sys.argv[1], sys.argv[1:])
