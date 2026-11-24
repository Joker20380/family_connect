"""Source-only opt-in scheduler archives; never overlays or deploys a serving artifact."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

from scripts.package_friends_http import ARCHIVE, ROOT, build as build_http

DISPATCHERS = {
    'chat-sync': ('friends_chat_sync.py', 'deploy/friends/chat-sync.py', 'friends_chat_sync'),
    'paid-reconcile': ('control/friends/transport_reconcile.py', 'control/friends/transport_reconcile.py',
                       'control.friends.transport_reconcile'),
}


def build(output, dispatcher, source=ROOT):
    if dispatcher not in DISPATCHERS:
        raise ValueError('UNKNOWN_DISPATCHER')
    name, relative, module = DISPATCHERS[dispatcher]
    path = source / relative
    if not path.is_file() or any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError('UNSAFE_DISPATCHER_SOURCE')
    with tempfile.TemporaryDirectory(prefix='fc-capture-dispatcher-') as directory:
        temporary = Path(directory) / 'http'
        build_http(temporary, source)
        with zipfile.ZipFile(temporary / ARCHIVE) as archive:
            contents = {entry: archive.read(entry) for entry in archive.namelist()}
    contents[name] = path.read_bytes()
    contents['__main__.py'] = f'from {module} import main\nraise SystemExit(main())\n'.encode()
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for entry, raw in sorted(contents.items()):
            info = zipfile.ZipInfo(entry, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o40755 if entry.endswith('/') else 0o100644) << 16
            archive.writestr(info, raw)
    return dict(dispatcher=dispatcher, sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                files={entry: hashlib.sha256(raw).hexdigest() for entry, raw in contents.items()},
                deployed=False, capture_permitted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispatcher', choices=sorted(DISPATCHERS), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.dispatcher), sort_keys=True))


if __name__ == '__main__':
    main()
