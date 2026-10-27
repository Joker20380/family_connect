"""Stage an allowlisted local build context without traversing repository state."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import tempfile

BASE = Path(__file__).resolve().parent
REPOSITORY = BASE.parent


def source_paths():
    paths = [BASE / name for name in ('manage.py', 'pyproject.toml', 'requirements.lock')]
    for directory in ('fc_control_plane', 'apps', 'tests'):
        paths.extend((BASE / directory).rglob('*.py'))
    paths.extend((BASE / 'templates').rglob('*.html'))
    paths.extend((BASE / 'static').rglob('*.css'))
    paths.extend((REPOSITORY / 'control/friends').glob('*.py'))
    paths.extend((REPOSITORY / 'device_identity').glob('*.py'))
    return sorted(paths)


def prepare():
    local = BASE / '.local'
    if any(parent.is_symlink() for parent in (local, *local.parents)):
        raise ValueError('Unsafe local build directory')
    local.mkdir(mode=0o700, exist_ok=True)
    env = BASE / '.env'
    if not env.exists():
        descriptor = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as handle:
            handle.write('CONTROL_PLANE_MODE=synthetic\nDJANGO_SECRET_KEY=' + secrets.token_hex(32) +
                         '\nPOSTGRES_PASSWORD=' + secrets.token_hex(24) + '\n')
    destination = local / 'build-context'
    if destination.exists():
        marker = destination / 'source-manifest.json'
        if destination.is_symlink() or not marker.is_file():
            raise ValueError('Unrecognized build context; preserve it for review')
        previous = json.loads(marker.read_text())
        allowed = set(previous) | {'source-manifest.json'}
        if any(path.is_symlink() or str(path.relative_to(destination)) not in allowed
               for path in destination.rglob('*') if not path.is_dir()):
            raise ValueError('Unexpected build context contents; preserve them for review')
        shutil.rmtree(destination)
    temporary = Path(tempfile.mkdtemp(prefix='context-', dir=local))
    manifest = {}
    try:
        for source in source_paths() + [BASE / 'Dockerfile']:
            if any(parent.is_symlink() for parent in (source, *source.parents)):
                raise ValueError('Symlink source rejected')
            relative = 'Dockerfile' if source == BASE / 'Dockerfile' else str(source.relative_to(REPOSITORY))
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = source.read_bytes()
            target.write_bytes(raw)
            target.chmod(0o644)
            manifest[relative] = hashlib.sha256(raw).hexdigest()
        (temporary / 'source-manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
        (temporary / 'source-manifest.json').chmod(0o644)
        for directory in temporary.rglob('*'):
            if directory.is_dir():
                directory.chmod(0o755)
        temporary.chmod(0o755)
        temporary.rename(destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    print(f'Prepared {len(manifest)} source files. Private .env stays outside the build context.')


if __name__ == '__main__':
    prepare()
