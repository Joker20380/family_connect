import hashlib
import json
import os
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[3]
BASE = '78a69db8f4e48ee89cf132ea279287dbfc71bdf8d9ae69c205bcaa0e19932a46'
ORIGINAL = '12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed'
MODULE = 'control/friends/owner_handoff.py'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    os.umask(0o077)
    state = ROOT / 'state-client-build/mesh-perf-3b'
    source = state / 'friends-http-owner-candidate.pyz'
    overlay = Path(__file__).with_name('successor_owner_handoff.py').read_bytes()
    assert sha(source.read_bytes()) == BASE
    destination = state / 'successor04'
    destination.mkdir(mode=0o700)
    package = destination / 'friends-http-successor.pyz'
    with zipfile.ZipFile(source) as previous, zipfile.ZipFile(package, 'x') as current:
        assert len(previous.namelist()) == len(set(previous.namelist()))
        for entry in previous.infolist():
            current.writestr(entry, overlay if entry.filename == MODULE else previous.read(entry))
    with zipfile.ZipFile(source) as previous, zipfile.ZipFile(package) as current:
        assert previous.namelist() == current.namelist()
        changed = [name for name in previous.namelist() if previous.read(name) != current.read(name)]
        assert changed == [MODULE]
        restricted = sha(current.read('control/friends/restricted.py'))
    manifest = dict(original_api_sha256=ORIGINAL, sealed_owner_api_sha256=BASE,
        candidate_sha256=sha(package.read_bytes()), overlay_sha256=sha(overlay), changed_members=changed,
        restricted_hook_sha256=restricted, schema_version=2, runtime_applied=False)
    for name in ('successor_migrate.py', 'successor_owner_handoff.py'):
        raw = Path(__file__).with_name(name).read_bytes()
        (destination/name).write_bytes(raw)
        manifest[name+'_sha256'] = sha(raw)
    with (destination/'manifest.json').open('x') as handle:
        json.dump(manifest, handle, indent=2)
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
