"""Offline integrity/capability check; the bundle itself must come from reviewed CI."""
import hashlib
import json
import sys
from pathlib import Path


def check(root):
    root=Path(root)
    record=json.loads((root/'awg31.json').read_text())
    if (record.get('schema')!=1 or
        record.get('engine')!='b5928efb6ca19f0153958460c3d141f04abc5c2e' or
        record.get('tools')!='ee0f0a9aa34ff0a0da4b3433b9512781cfe02843' or
        set(record.get('files',{}))!={'amneziawg-go','awg','awg-quick'}):
        raise ValueError('Pinned AWG 3.1 bundle required')
    for name,digest in record['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('AWG bundle integrity mismatch')

if __name__=='__main__':check(sys.argv[1])
