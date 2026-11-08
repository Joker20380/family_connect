"""Exact public source fixtures; never an installed APK or runtime qualification."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'bridge95': ('tests/fixtures/accepted_android/bridge95.py.txt',
                 '6dc08e65f7b60d77a1f8a6a4d05afdaadbaad547382a1c7c966365957a517c4b'),
    'bridge96': ('tests/fixtures/accepted_android/bridge96.py.txt',
                 '2c895a3728eb1d93e4121c8c9526960e544a947417738823a4e714c7475e250d'),
    'bridge103': ('clients/rns/fc_rns_transport.py',
                  '70593713d1d915904d10cf0cac0eb21ca41b11b4dedcdb7973d0da236579ada0'),
    'health89': ('tests/fixtures/accepted_android/health89.java.txt',
                 'bbab99f2cfbc527c19e378c37b78f7ec53be96bdafb2bcd2915666ce8013f19b'),
}


def source(name):
    relative, expected = SOURCES[name]
    path = ROOT / relative
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('Accepted Android fixture mismatch: ' + name)
    return path
