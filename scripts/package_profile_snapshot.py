"""Deterministic canonical snapshot source capsule without production configuration."""
import argparse
import json
from pathlib import Path

from scripts.package_paid_canary_crl import ROOT, SOURCES as HELPER_SOURCES
from scripts.package_restricted_maintenance import build_capsule

SOURCES = (*HELPER_SOURCES, 'control/friends/profile_store.py', 'control/friends/profile_snapshot.py')


def build(output, ref, *, repository=ROOT):
    return build_capsule(output, ref, sources=SOURCES, entrypoint='control.friends.profile_snapshot', repository=repository)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.ref), sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
