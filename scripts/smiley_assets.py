"""Verify the frozen Android catalog and copy only its exact GIF bytes."""
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
ANDROID = Path('clients/android/app/src/main')
ASSETS = ANDROID / 'assets/chat/icq-classic'
JAVA = ANDROID / 'java/com/familyconnect/app/ChatSmileys.java'
CATALOG = Path('clients/desktop/smiley_catalog.json')


def android_faces(root=ROOT):
    source = (root / JAVA).read_text()
    records = re.findall(r'new Face\(((?:"(?:\\.|[^"\\])*"\s*,?\s*)+)\)', source)
    faces = []
    for record in records:
        token, label, asset, *aliases = [json.loads(value) for value in re.findall(r'"(?:\\.|[^"\\])*"', record)]
        faces.append(dict(token=token, label=label, asset=asset, aliases=aliases,
                          sha256=hashlib.sha256((root / ASSETS / asset).read_bytes()).hexdigest()))
    return faces


def verify(root=ROOT):
    catalog = json.loads((root / CATALOG).read_text())
    faces = catalog['faces']
    if len(faces) != 49 or faces != android_faces(root):
        raise ValueError('Android smiley catalog parity mismatch')
    expected = {face['asset'] for face in faces} | {'provenance.json'}
    directory = root / ASSETS
    if {path.name for path in directory.iterdir()} != expected:
        raise ValueError('Unexpected smiley asset inventory')
    for face in faces:
        path = directory / face['asset']
        if path.is_symlink() or not path.is_file() or not 1 <= path.stat().st_size <= 32768:
            raise ValueError('Unsafe smiley asset')
    for name, digest in catalog['android_sources'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Android smiley implementation changed')
    return catalog


def copy_assets(destination, root=ROOT):
    catalog = verify(root)
    target = destination / 'clients/desktop/assets/chat/icq-classic'
    target.mkdir(parents=True, exist_ok=True)
    if any(target.iterdir()):
        raise ValueError('Smiley destination must be empty')
    for face in catalog['faces']:
        shutil.copyfile(root / ASSETS / face['asset'], target / face['asset'])
        (target / face['asset']).chmod(0o644)


def verify_bundle(bundle):
    catalog = json.loads((bundle / CATALOG).read_text())
    if catalog != verify():
        raise ValueError('Packaged smiley catalog differs from Android')
    directory = bundle / 'clients/desktop/assets/chat/icq-classic'
    if {path.name for path in directory.iterdir()} != {face['asset'] for face in catalog['faces']}:
        raise ValueError('Packaged smiley inventory mismatch')
    for face in catalog['faces']:
        path = directory / face['asset']
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != face['sha256']:
            raise ValueError('Packaged smiley digest mismatch')
