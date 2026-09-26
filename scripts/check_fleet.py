"""Validate an operator fleet inventory without changing servers or clients."""
import argparse
import json
from pathlib import Path

from control.fleet import MAX_REGISTRY_BYTES, load_registry, validate_update


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('registry', type=Path)
    parser.add_argument('--previous', type=Path)
    args = parser.parse_args()
    try:
        with args.registry.open('rb') as stream:
            registry = load_registry(stream.read(MAX_REGISTRY_BYTES + 1))
        if args.previous:
            with args.previous.open('rb') as stream:
                validate_update(load_registry(stream.read(MAX_REGISTRY_BYTES + 1)), registry)
    except (OSError, ValueError, RecursionError):
        parser.exit(1, 'Invalid fleet registry\n')
    print(json.dumps(dict(schema_version=registry.schema_version, revision=registry.revision,
                         gateways=len(registry.gateways), control_ingresses=len(registry.control_ingresses))))


if __name__ == '__main__':
    main()
