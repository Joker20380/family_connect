"""Pinned paid policy replacement; preserves every other serving archive member."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MEMBER = 'control/friends/paid_beta.py'


def build(baseline, expected_sha256, expected_paid_sha256, output, source=ROOT):
    digest = lambda raw: hashlib.sha256(raw).hexdigest()
    if digest(baseline.read_bytes()) != expected_sha256:
        raise ValueError('Serving archive pin mismatch')
    with zipfile.ZipFile(baseline) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or any(Path(name).is_absolute() or '..' in Path(name).parts for name in names):
            raise ValueError('Invalid runtime inventory')
        if digest(archive.read(MEMBER)) != expected_paid_sha256:
            raise ValueError('Serving paid module pin mismatch')
        replacement = (source / MEMBER).read_bytes()
        compile(replacement, MEMBER, 'exec')
        before = {name: digest(archive.read(name)) for name in names}
        with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as candidate:
            for entry in archive.infolist():
                candidate.writestr(entry, replacement if entry.filename == MEMBER else archive.read(entry))
    with zipfile.ZipFile(output) as candidate:
        after = {name: digest(candidate.read(name)) for name in candidate.namelist()}
    if set(before) != set(after) or any(before[name] != after[name] for name in before if name != MEMBER):
        raise ValueError('Unexpected runtime delta')
    return dict(schema=1, baseline_sha256=expected_sha256, candidate_sha256=digest(output.read_bytes()),
                before=before, after=after, changed=[name for name in before if before[name] != after[name]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--expected-paid-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.baseline, args.expected_sha256, args.expected_paid_sha256, args.output), sort_keys=True))


if __name__ == '__main__':
    main()
