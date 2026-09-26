"""Offline referral QR matrix via the system libqrencode (LGPL-2.1-or-later)."""
import ctypes
import ctypes.util
import re


def invitation_matrix(url):
    # Only the existing referral URL is encoded; never keys or VPN profiles.
    if not isinstance(url, str) or not re.fullmatch(r'https://185\.251\.89\.19:8443/(?:invite|i)/#[0-9a-f]{64}', url):
        raise ValueError('Invalid invitation link')
    name = ctypes.util.find_library('qrencode')
    if not name:
        raise RuntimeError('QR support unavailable')
    library = ctypes.CDLL(name)
    class QRcode(ctypes.Structure):
        _fields_ = [('version', ctypes.c_int), ('width', ctypes.c_int),
                    ('data', ctypes.POINTER(ctypes.c_ubyte))]
    library.QRcode_encodeString8bit.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
    library.QRcode_encodeString8bit.restype = ctypes.POINTER(QRcode)
    library.QRcode_free.argtypes = [ctypes.POINTER(QRcode)]
    library.QRcode_free.restype = None
    code = library.QRcode_encodeString8bit(url.encode('ascii'), 0, 1)
    if not code:
        raise RuntimeError('QR encoding failed')
    try:
        width = code.contents.width
        if not 21 <= width <= 177 or not code.contents.data:
            raise RuntimeError('Invalid QR matrix')
        return tuple(tuple(bool(code.contents.data[y*width+x] & 1)
                           for x in range(width)) for y in range(width))
    finally:
        library.QRcode_free(code)
