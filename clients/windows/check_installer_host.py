"""Verify the actual published PE host does not opt into broken legacy OS CET."""
import struct
import sys
from pathlib import Path


def cet_enabled(data):
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    assert data[pe:pe + 4] == b'PE\0\0'
    sections = struct.unpack_from('<H', data, pe + 6)[0]
    optional_size = struct.unpack_from('<H', data, pe + 20)[0]
    optional = pe + 24
    assert struct.unpack_from('<H', data, optional)[0] == 0x20b, 'Expected x64 PE32+'
    debug_rva, debug_size = struct.unpack_from('<II', data, optional + 112 + 6 * 8)
    if not debug_rva:
        return False
    for i in range(sections):
        section = optional + optional_size + i * 40
        virtual_size, rva, raw_size, raw = struct.unpack_from('<IIII', data, section + 8)
        if rva <= debug_rva < rva + max(virtual_size, raw_size):
            start = raw + debug_rva - rva
            break
    else:
        raise ValueError('Invalid debug directory RVA')
    for pos in range(start, start + debug_size, 28):
        kind, size, _, pointer = struct.unpack_from('<IIII', data, pos + 12)
        if kind == 20:  # IMAGE_DEBUG_TYPE_EX_DLLCHARACTERISTICS
            assert size >= 4
            if struct.unpack_from('<I', data, pointer)[0] & 1:
                return True
    return False


if __name__ == '__main__':
    enabled = cet_enabled(Path(sys.argv[1]).read_bytes())
    assert not enabled, 'Published apphost unexpectedly enables CET'
    print('Published x64 apphost: CET opt-in absent; OS-wide settings unchanged')
