"""Provision the fixed native fixture; never a working-host maintenance command."""
import argparse
import base64
import io
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ('deploy/control-ha/Dockerfile.maintenance-fixture', 'control/requirements.lock',
          'provisioning/requirements.lock', 'device_identity/requirements.lock',
          'deploy/control-ha/requirements.lock', 'messenger/requirements.lock')
HELPER = Path('/opt/fc-ci-maintenance-source/scripts/ci_maintenance_fixture.py')


def context():
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w') as archive:
        for name in INPUTS:
            path = ROOT / name
            if path.is_symlink() or not path.is_file():
                raise ValueError('FIXTURE_INPUT_SHAPE')
            raw = path.read_bytes()
            entry = tarfile.TarInfo(name)
            entry.size, entry.mode = len(raw), 0o644
            archive.addfile(entry, io.BytesIO(raw))
    return output.getvalue()


def build():
    with tempfile.TemporaryDirectory(prefix='fc-maintenance-build-') as temporary:
        image_file = Path(temporary) / 'image.id'
        subprocess.run(['docker', '--host', 'unix:///var/run/docker.sock', 'build',
                        '--file', INPUTS[0], '--iidfile', str(image_file), '-'],
                       input=context(), check=True, stdout=sys.stderr)
        image = image_file.read_text().strip()
    if re.fullmatch('sha256:[0-9a-f]{64}', image) is None:
        raise ValueError('FIXTURE_IMAGE_ID')
    print('FC_TEST_MAINTENANCE_IMAGE=' + image)


def validate_root():
    if (os.geteuid() != 0 or Path(__file__) != HELPER or
            {path.name for path in Path('/sys/class/net').iterdir()} != {'lo'}):
        raise ValueError('NETWORKLESS_BUILD_CONTAINER_REQUIRED')
    if any(path.stat().st_uid != 0 or path.stat().st_mode & 0o022
           for path in (HELPER, *HELPER.parents)):
        raise ValueError('ROOT_OWNED_FIXTURE_SOURCE_REQUIRED')


def root_fixture():
    validate_root()
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    sys.path.insert(0, str(ROOT))
    from scripts.control_ha_maintenance_fixture import root_fixture as capture
    from scripts.control_ha_recovery_bundle import parse
    raw = sys.stdin.buffer.read(131073)
    if len(raw) > 131072:
        raise ValueError('FIXTURE_INPUT_LIMIT')
    issuer = {name: base64.b64decode(value, validate=True) for name, value in parse(raw).items()}
    with tempfile.TemporaryDirectory(prefix='fc-maintenance-root-', dir='/run') as temporary:
        lab = Path(temporary)
        lab.chmod(0o755)
        print(json.dumps(capture(issuer, lab=lab), sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', action='store_true')
    args = parser.parse_args()
    root_fixture() if args.root else build()
