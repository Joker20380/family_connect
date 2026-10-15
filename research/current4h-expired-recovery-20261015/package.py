import argparse
import hashlib
import json
from pathlib import Path


MODULES = ('credential_renewal.py', 'grant_cutover.py', 'maintenance_policy.py', 'offline_handoff.py',
    'production_node.py', 'production_transport.py', 'production_controller.py', 'renewal_cli.py',
    'node.py', 'scheduled_evaluate.py', 'renewal_health.py', 'runtime_controller.py', 'expired_recovery.py')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def build(source, output):
    expected = json.loads((Path(__file__).resolve().parent/'source-manifest.json').read_bytes())['management_sources']
    actual = {name:hashlib.sha256((source/'controller'/name).read_bytes()).hexdigest() for name in MODULES}
    assert actual == expected, 'management source differs from verified derivative'
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    manifest = {}
    for name in MODULES:
        raw = (source/'controller'/name).read_bytes()
        manifest[name] = hashlib.sha256(raw).hexdigest()
        (output/name).write_bytes(raw)
        (output/name).chmod(0o600)
    identity = hashlib.sha256(canonical(manifest)).hexdigest()
    (output/'manifest.json').write_bytes(canonical(dict(schema=1, version='expired-recovery-v1',
        source_files=manifest, source_sha256=identity, offline_signer_in_package=False,
        gateway_executable_changed=False, api_and_receiver_unchanged=True)))
    return identity


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(build(args.source, args.out))


if __name__ == '__main__':
    main()
