"""Closed support commissioning kit; no identities, credentials, state or deployment."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

from scripts.package_friends_http import build as build_http

ROOT = Path(__file__).resolve().parents[1]
MESSENGER = ('__init__', 'chat', 'codec', 'delivery', 'mailbox', 'notices', 'routed',
             'store', 'subscription_view', 'support')
PROVISIONING = ('__init__', 'chat_transport', 'chat_bridge_protocol', 'support_worker', 'support_bindings')
UNITS = ('family-connect-support.service', 'family-connect-support-bindings.service',
         'family-connect-support-bindings.timer')


def build(output, source=ROOT):
    inputs = {'app/messenger/' + name + '.py': 'messenger/' + name + '.py' for name in MESSENGER}
    inputs.update({'app/provisioning/' + name + '.py': 'provisioning/' + name + '.py' for name in PROVISIONING})
    inputs.update({'units/' + name: 'deploy/support-chat/' + name for name in UNITS})
    inputs.update({'provisioning.lock': 'provisioning/requirements.lock', 'messenger.lock': 'messenger/requirements.lock',
                   'panel.override.yaml': 'deploy/support-chat/panel.override.yaml',
                   'registry/chat-sync.py': 'deploy/friends/chat-sync.py',
                   'registry/support-bindings-read.py': 'deploy/friends/support-bindings-read.py'})
    for relative in inputs.values():
        path = source / relative
        if not path.is_file() or any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError('Missing or unsafe commissioning source: ' + relative)
    output.mkdir(parents=True, exist_ok=False)
    for destination, relative in inputs.items():
        path = output / destination
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, path)
    build_http(output / 'registry/http', source)
    hashes = {path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted(output.rglob('*')) if path.is_file()}
    (output / 'sha256.json').write_text(json.dumps(hashes, sort_keys=True, indent=2) + '\n')
    return hashes


def archive(directory, destination):
    with destination.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as target:
            for path in sorted(directory.rglob('*')):
                if not path.is_file() or path.is_symlink():
                    continue
                info = tarfile.TarInfo(path.relative_to(directory).as_posix())
                info.size = path.stat().st_size
                info.mode = 0o644
                with path.open('rb') as stream:
                    target.addfile(info, stream)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    hashes = build(args.output)
    destination = args.output.with_suffix('.tar.gz')
    archive(args.output, destination)
    print(json.dumps(dict(files=len(hashes), archive=str(destination),
                          sha256=hashlib.sha256(destination.read_bytes()).hexdigest(), deployed=False)))


if __name__ == '__main__':
    main()
