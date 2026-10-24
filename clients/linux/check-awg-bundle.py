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


def adapt_quick(raw):
    text = raw.decode()
    old='[[ $proto == -4 ]] && cmd sysctl -q net.ipv4.conf.all.src_valid_mark=1'
    new='if [[ $proto == -4 && $(sysctl -n net.ipv4.conf.all.src_valid_mark) != 1 ]]; then cmd sysctl -q net.ipv4.conf.all.src_valid_mark=1; fi'
    if text.count(old)!=1:raise ValueError('Unexpected awg-quick source')
    text=text.replace(old,new)
    old='\n\tlocal ret\n\tif ! cmd ip link add "$INTERFACE" type amneziawg; then\n\t\tret=$?\n\t\t[[ -e /sys/module/amneziawg ]] || ! command -v "${WG_QUICK_USERSPACE_IMPLEMENTATION:-amneziawg-go}" >/dev/null && exit $ret\n\t\techo "[!] Missing WireGuard (Amnezia VPN) kernel module. Falling back to slow userspace implementation." >&2\n\t\tcmd "${WG_QUICK_USERSPACE_IMPLEMENTATION:-amneziawg-go}" "$INTERFACE"\n\tfi'
    new='\n\tcmd "${WG_QUICK_USERSPACE_IMPLEMENTATION:-amneziawg-go}" "$INTERFACE"'
    if text.count(old)!=1:raise ValueError('Unexpected awg-quick interface creation')
    text=text.replace(old,new)
    return text.encode()


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--adapt':
        path = Path(sys.argv[2])
        path.write_bytes(adapt_quick(path.read_bytes()))
    else:
        check(sys.argv[1])
