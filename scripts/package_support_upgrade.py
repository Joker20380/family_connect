"""Support-only overlay of the observed HTTP runtime; preserve later VPN fixes."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA256 = 'a59956c40af36d6172e5f35f1804fe3c7bc93993c21f5f4cc1030820383e8ec1'
REPLACE = {
    'friends_http.py': ('fb049818aa1e515d7c682e30dba56b7e1a92fac4e74e980ce6bede63f1d5b32b', 'deploy/friends/access-api.py'),
    'control/friends/chat.py': ('6401c061aab650416e733c4433ce9a3a4f12742bcb0acd136248ab344736eda7', 'control/friends/chat.py'),
}
ADD = ('control/friends/chat_service.py', 'control/friends/support.py', 'messenger/support.py')


def build(base, output, source=ROOT):
    if hashlib.sha256(base.read_bytes()).hexdigest() != BASE_SHA256:
        raise ValueError('Runtime changed: review the new base before overlay')
    with zipfile.ZipFile(base) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or any(Path(name).is_absolute() or '..' in Path(name).parts for name in names):
            raise ValueError('Unsafe base archive')
        entries = {name: archive.read(name) for name in names}
    if any(name in entries for name in ADD):
        raise ValueError('Support already present; do not overwrite it')
    for name, (expected, path) in REPLACE.items():
        if hashlib.sha256(entries[name]).hexdigest() != expected:
            raise ValueError('Unreviewed replacement source')
        entries[name] = (source / path).read_bytes()
    for name in ADD:
        entries[name] = (source / name).read_bytes()
    for name, raw in entries.items():
        if name.endswith('.py'):
            compile(raw, name, 'exec')
    with output.open('xb') as stream, zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (2026, 11, 11, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, raw)
    return dict(base_sha256=BASE_SHA256, sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                replaced=sorted(REPLACE), added=list(ADD), preserved=len(names) - len(REPLACE),
                files={name: hashlib.sha256(raw).hexdigest() for name, raw in entries.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    receipt = build(args.base, args.output)
    args.output.with_suffix('.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({key: value for key, value in receipt.items() if key != 'files'}))


if __name__ == '__main__':
    main()
