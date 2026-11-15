"""Prepare the metadata-only overlay on the accepted generation-2 panel image."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'sha256:e44c342383f53feea8414f51033264079b7bfa86247c0b69e8dda2ad2510245d'
REPLACED = {
    'control_plane/apps/console/models.py': '3d9e961254415f20a152d9854d2d87ded5986f11beef4307de62720808eb5a54',
    'control_plane/apps/console/observability_models.py': 'c762210335dd81315d6bd676ce667e52062f69456e4efcd197d19fb1e14aaa00',
    'control_plane/apps/console/objects.py': '9bf4767881040d4ca70b6c698927951a6bf9f17ace836d4270d9549abfbcc674',
    'control_plane/templates/console/object_device.html': '1099912df66ae4681d99a748fe686a9512717235968bb4386b0bdd29192b9ce0',
    'control_plane/templates/console/object_device_table.html': '2f483fef3284b2b6c6ae42e4b3a891a77af75a42d4afa5604e4cec48e312325c',
    'control_plane/templates/console/object_filters.html': '82f05b7427cffc25dacb53e1efa38dccd18c3bcf05635afc01173c48a61fbcd8',
}
PRESERVED = {
    'control_plane/apps/console/management/commands/import_inventory.py': 'd4e4a3b4265d96e801470692315ec5cc6ee932ea25139703a8e81bc5fe32899d',
    'control_plane/apps/console/management/commands/import_subscriptions.py': '0a5d89786c4af7c9ba61e2a8aa3b445c671ed6f7d369a914e5e864bca1c33c7c',
    'control/friends/pseudonyms.py': 'ada9defd475c676e2f27398060ecbbe493a264b030385ae5ef83182b136ab6e9',
}
ADDED = (
    'control/friends/technical_metadata.py',
    'control/friends/geoip.py',
    'control_plane/apps/console/technical_metadata.py',
    'control_plane/apps/console/management/commands/import_technical_metadata.py',
    'control_plane/apps/console/migrations/0014_technical_metadata.py',
    'control_plane/apps/console/migrations/0015_technical_metadata_geoip.py',
    'control_plane/templates/console/technical_metadata.html',
    'control_plane/templates/console/technical_metadata_compact.html',
)
LOG_FORMAT = '%(m)s %(U)s %(s)s %(D)s'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare(baseline, image, output, source=ROOT):
    if image != IMAGE:
        raise ValueError('Unqualified panel image')
    for name, expected in (REPLACED | PRESERVED).items():
        if digest((baseline / name).read_bytes()) != expected:
            raise ValueError('Panel preimage mismatch')
    if any((baseline / name).exists() for name in ADDED):
        raise ValueError('Metadata already present; review a new delta')
    payloads = {name: (source / name).read_bytes() for name in (*REPLACED, *ADDED)}
    for name, raw in payloads.items():
        if name.endswith('.py'):
            compile(raw, name, 'exec')
    output.mkdir(mode=0o700)
    for name, raw in payloads.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    command = ['gunicorn', 'fc_control_plane.wsgi:application', '--bind', '0.0.0.0:8000',
               '--workers', '2', '--access-logformat', LOG_FORMAT]
    dockerfile = [f'FROM {image}', 'USER root']
    dockerfile.extend(f'COPY {name} /app/{name}' for name in payloads)
    dockerfile.extend(['USER console', 'CMD ' + json.dumps(command)])
    (output / 'Dockerfile').write_text('\n'.join(dockerfile) + '\n')
    return dict(schema=1, baseline_image=image, replaced=REPLACED, preserved=PRESERVED,
                installed={name: digest(raw) for name, raw in payloads.items()},
                access_log_format=LOG_FORMAT,
                boundary='Build context only; preserve live settings, aliases mount and data volumes')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.baseline, args.image, args.output), sort_keys=True))


if __name__ == '__main__':
    main()
