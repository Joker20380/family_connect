"""Patch only the metadata HTTP boundary over a pinned serving archive."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXISTING = {'friends_http.py': 'deploy/friends/access-api.py', 'control/friends/access.py': 'control/friends/access.py'}
ADDED = ('control/friends/technical_metadata.py', 'control/friends/geoip.py')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def build(baseline, expected_sha256, output, source=ROOT):
    raw = Path(baseline).read_bytes()
    if digest(raw) != expected_sha256:
        raise ValueError('Serving archive pin mismatch')
    delta = source / 'deploy/friends/technical-metadata-runtime.patch'
    with zipfile.ZipFile(baseline) as archive, tempfile.TemporaryDirectory() as directory:
        names = archive.namelist()
        if len(set(names)) != len(names) or any(Path(name).is_absolute() or '..' in Path(name).parts for name in names):
            raise ValueError('Invalid runtime inventory')
        if any(name in names for name in ADDED):
            raise ValueError('Metadata already installed; require a new reviewed delta')
        stage = Path(directory)
        before = {name: digest(archive.read(name)) for name in names}
        for member, path in EXISTING.items():
            target = stage / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
        subprocess.run(['git', 'apply', '--check', str(delta)], cwd=stage, check=True, capture_output=True)
        subprocess.run(['git', 'apply', str(delta)], cwd=stage, check=True, capture_output=True)
        if {str(path.relative_to(stage)) for path in stage.rglob('*') if path.is_file()} != set(EXISTING.values()):
            raise ValueError('Unexpected overlay member')
        replacements = {member: (stage / path).read_bytes() for member, path in EXISTING.items()}
        replacements.update({name: (source / name).read_bytes() for name in ADDED})
        for name, content in replacements.items():
            compile(content, name, 'exec')
        with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as candidate:
            for entry in archive.infolist():
                candidate.writestr(entry, replacements.get(entry.filename, archive.read(entry)))
            for name in ADDED:
                entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                candidate.writestr(entry, replacements[name])
    with zipfile.ZipFile(output) as candidate:
        after = {name: digest(candidate.read(name)) for name in candidate.namelist()}
    changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
    if set(changed) != set(EXISTING) | set(ADDED):
        raise ValueError('Unexpected runtime delta')
    return dict(schema=1, baseline_sha256=expected_sha256, candidate_sha256=digest(Path(output).read_bytes()),
                patch_sha256=digest(delta.read_bytes()), before=before, after=after, changed=changed,
                boundary='Source overlay only; not payment-policy, deployment or acceptance')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.baseline, args.expected_sha256, args.output), sort_keys=True))


if __name__ == '__main__':
    main()
