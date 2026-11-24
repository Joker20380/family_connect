from copy import deepcopy
import gzip
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from scripts import control_ha_owner_images as images
from scripts import control_ha_owner_image_bootstrap as cold
from scripts import control_ha_owner_runtime as owner


def tar_bytes(files, extra=None):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:') as archive:
        for name, raw in files.items():
            info = tarfile.TarInfo(name); info.size = len(raw)
            archive.addfile(info, io.BytesIO(raw))
        if extra:
            archive.addfile(extra, io.BytesIO(b'x' * extra.size) if extra.isfile() else None)
    return stream.getvalue()


def fixture_archive(monkeypatch, *, platform='amd64', bad_diff=False, ambiguous=False, missing_selected=False):
    files, roots, saved, pins = {}, [], [], {}

    def put(raw, media):
        identifier = 'sha256:' + images.digest(raw)
        files[images.blob_name(identifier)] = raw
        return dict(digest=identifier, size=len(raw), mediaType=media)

    for role in ('console', 'postgres', 'system_publisher'):
        expanded = tar_bytes({'fixture': role.encode()})
        layer = put(gzip.compress(expanded, mtime=0), images.OCI_LAYER + '+gzip')
        config = put(images.encoded(dict(os='linux', architecture=platform, config={}, rootfs=dict(type='layers',
            diff_ids=['sha256:' + ('0' * 64 if bad_diff else images.digest(expanded))]))), images.OCI_CONFIG)
        manifest = put(images.encoded(dict(schemaVersion=2, mediaType=images.OCI_MANIFEST, config=config, layers=[layer])), images.OCI_MANIFEST)
        saved.append(dict(Config=images.blob_name(config['digest']), Layers=[images.blob_name(layer['digest'])], RepoTags=None))
        root = manifest
        if role == 'postgres':
            child = manifest | {'platform': dict(os='linux', architecture='amd64')}
            children = [child, dict(digest='sha256:' + 'a'*64, size=1, mediaType=images.OCI_MANIFEST,
                                   platform=dict(os='linux', architecture='arm64'))]
            if ambiguous: children.append(deepcopy(child))
            root = put(images.encoded(dict(schemaVersion=2, mediaType=images.OCI_INDEX, manifests=children)), images.OCI_INDEX)
            if missing_selected: del files[images.blob_name(manifest['digest'])]
        roots.append(root); pins[role] = root['digest']
    files['index.json'] = images.encoded(dict(schemaVersion=2, mediaType=images.OCI_INDEX, manifests=roots))
    files['oci-layout'] = images.encoded(dict(imageLayoutVersion='1.0.0'))
    files['manifest.json'] = images.encoded(saved)
    monkeypatch.setattr(images, 'IMAGES', pins)
    return files


def test_source_image_pins_agree_with_existing_owner_custody():
    assert images.IMAGES == owner.IMAGES


def test_closed_multiarchitecture_archive_selects_only_present_amd64(monkeypatch):
    checked = images.validate(tar_bytes(fixture_archive(monkeypatch)))
    assert checked['summary']['roles'] == 3
    assert checked['summary']['unique_layers'] == checked['summary']['layer_references'] == 3
    assert checked['summary']['platform'] == 'linux/amd64'
    assert checked['summary']['activation'] is checked['summary']['full_recovery'] is False


@pytest.mark.parametrize('kind', ('platform', 'diff', 'ambiguous', 'missing_selected'))
def test_archive_refuses_wrong_runtime_bindings(monkeypatch, kind):
    files = fixture_archive(monkeypatch, platform='arm64' if kind == 'platform' else 'amd64',
                            bad_diff=kind == 'diff', ambiguous=kind == 'ambiguous', missing_selected=kind == 'missing_selected')
    with pytest.raises(ValueError): images.validate(tar_bytes(files))


@pytest.mark.parametrize('kind', ('blob', 'missing', 'extra', 'compatibility', 'root', 'duplicate_json', 'gzip_bomb'))
def test_archive_refuses_corruption_and_incomplete_graph(monkeypatch, kind):
    files = fixture_archive(monkeypatch)
    blob = next(name for name in files if name.startswith('blobs/'))
    if kind == 'blob': files[blob] += b'x'
    elif kind == 'missing': del files[blob]
    elif kind == 'extra': files['blobs/sha256/' + images.digest(b'extra')] = b'extra'
    elif kind == 'compatibility':
        saved = json.loads(files['manifest.json']); saved[0]['Layers'] = saved[1]['Layers']
        files['manifest.json'] = images.encoded(saved)
    elif kind == 'root':
        roots = json.loads(files['index.json']); roots['manifests'].pop(); files['index.json'] = images.encoded(roots)
    elif kind == 'duplicate_json': files['oci-layout'] = b'{"imageLayoutVersion":"1.0.0","imageLayoutVersion":"1.0.0"}'
    else: monkeypatch.setattr(images, 'LAYER_LIMIT', 100)
    with pytest.raises((ValueError, KeyError)): images.validate(tar_bytes(files))


@pytest.mark.parametrize('kind', ('traversal', 'absolute', 'symlink', 'hardlink', 'duplicate', 'directory', 'pax'))
def test_archive_never_extracts_untrusted_members(monkeypatch, kind, tmp_path):
    files = fixture_archive(monkeypatch)
    extra = tarfile.TarInfo('unexpected')
    if kind == 'traversal': extra.name = '../escape'
    elif kind == 'absolute': extra.name = '/escape'
    elif kind == 'symlink': extra.type = tarfile.SYMTYPE; extra.linkname = '/escape'
    elif kind == 'hardlink': extra.type = tarfile.LNKTYPE; extra.linkname = 'index.json'
    elif kind == 'duplicate': extra.name = 'index.json'; extra.size = 1
    elif kind == 'directory': extra.type = tarfile.DIRTYPE
    elif kind == 'pax': extra.pax_headers = {'comment': 'untrusted'}
    with pytest.raises(ValueError): images.validate(tar_bytes(files, extra))
    assert not list(tmp_path.iterdir())


@pytest.fixture
def capsule(monkeypatch):
    archive = tar_bytes(fixture_archive(monkeypatch))
    tool = b'fixture tool, never executed'
    monkeypatch.setattr(images, 'TOOL_SHA', images.digest(tool))
    key = os.urandom(32)
    raw, checkpoint = images.seal(archive, tool, key)
    return raw, key, checkpoint


def test_capsule_exact_private_restore_and_no_overwrite(capsule, tmp_path):
    files = images.unseal(*capsule)
    destination = tmp_path / 'restored'
    images.restore(files, destination)
    assert {path.name: path.read_bytes() for path in destination.iterdir()} == files
    assert destination.stat().st_mode & 0o777 == 0o700
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in destination.iterdir())
    with pytest.raises(FileExistsError): images.restore(files, destination)


def test_returned_checkpoint_cannot_change_trusted_image_pins(capsule):
    checkpoint = capsule[2]
    original = images.IMAGES['console']
    checkpoint['images']['console'] = 'changed'
    assert images.IMAGES['console'] == original


@pytest.mark.parametrize('kind', ('key', 'cipher', 'archive', 'tool', 'sources', 'scope', 'platform', 'images'))
def test_capsule_requires_separate_exact_pins(capsule, kind):
    raw, key, checkpoint = capsule; checkpoint = deepcopy(checkpoint)
    if kind == 'key': key = b'x' * 32
    elif kind == 'cipher': raw = raw[:-1] + bytes([raw[-1] ^ 1])
    elif kind == 'archive': checkpoint['archive_sha256'] = '0' * 64
    elif kind == 'tool': checkpoint['tool_sha256'] = '0' * 64
    elif kind == 'sources': checkpoint['sources'][images.SOURCES[0]] = '0' * 64
    elif kind == 'scope': checkpoint['purpose'] = 'deploy'
    elif kind == 'platform': checkpoint['platform'] = 'linux/arm64'
    else: checkpoint['images']['console'] = 'sha256:' + '0' * 64
    with pytest.raises(Exception): images.unseal(raw, key, checkpoint)


@pytest.mark.parametrize('kind', ('truncated', 'trailing', 'oversized'))
def test_authenticated_frame_structure_is_closed(capsule, kind):
    raw, key, checkpoint = capsule; checkpoint = deepcopy(checkpoint)
    nonce = raw[len(images.MAGIC):len(images.MAGIC)+12]
    plaintext = AESGCM(key).decrypt(nonce, raw[len(images.MAGIC)+12:], images.PURPOSE.encode())
    if kind == 'truncated': plaintext = plaintext[:-1]
    elif kind == 'trailing': plaintext += b'x'
    else: plaintext = (images.LIMIT + 1).to_bytes(8, 'big') + plaintext[8:]
    raw = images.MAGIC + nonce + AESGCM(key).encrypt(nonce, plaintext, images.PURPOSE.encode())
    checkpoint['ciphertext_sha256'] = images.digest(raw)
    with pytest.raises(ValueError): images.unseal(raw, key, checkpoint)


def test_restore_refuses_symlink_parent(capsule, tmp_path):
    files = images.unseal(*capsule)
    (tmp_path / 'link').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='RESTORE_PATH'): images.restore(files, tmp_path / 'link/out')


@pytest.mark.parametrize('role', ('console', 'postgres', 'system_publisher'))
def test_cold_probe_has_no_host_runtime_docker_or_source_mount(role):
    command = cold.native_command(Path('/private/rootfs'), Path('/private/scratch'), role)
    assert all(flag in command for flag in ('--unshare-all', '--die-with-parent', '--new-session', '--clearenv', '--cap-drop'))
    assert command[command.index('--ro-bind')+1:command.index('--ro-bind')+3] == ['/private/rootfs', '/']
    assert command[command.index('--bind')+1:command.index('--bind')+3] == ['/private/scratch', '/tmp/fc-work']
    assert all(value not in command for value in ('/var/run/docker.sock', '/home', '/usr', '--share-net'))
    assert not any('entrypoint.sh' in value or 'gunicorn' in value for value in command)


def test_bootstrap_deadline_reports_no_private_command(monkeypatch, tmp_path):
    def timeout(*args, **kwargs): raise subprocess.TimeoutExpired('private', 240)
    monkeypatch.setattr(cold.subprocess, 'run', timeout)
    with pytest.raises(ValueError, match='^COLD_BOOTSTRAP_DEADLINE$'): cold.run(['private'], tmp_path, 'fixture')
