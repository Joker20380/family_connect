"""Closed, private OWNER image custody; standalone verifier, not deployment authority."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tarfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PURPOSE = 'family-connect/owner-image-custody/v1/linux-amd64/offline-only'
MAGIC = b'FCOIMG1\x00'
LIMIT = 512 * 1024 * 1024
LAYER_LIMIT = 1024 * 1024 * 1024
PLATFORM = 'linux/amd64'
IMAGES = {
    'console': 'sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a',
    'postgres': 'sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73',
    'system_publisher': 'sha256:50de6f25a04c1127b127b3278314619c69eddeec229d0d4ad9b7e67c1d2ffeab',
}
TOOL_SHA = 'fa84af91f6ca20630bf1aa83392423a59b54ff5e95bcab9ba3aff13d5ef666b2'
TOOL_BINARY_SHA = '4796f71e1dc93959b5d5c33066ee5a51542a16879df92a21fc0d6227a62d89d6'
SOURCES = ('control_ha_owner_images.py', 'control_ha_owner_image_bootstrap.py')
FRAMES = (('docker-save.tar', LIMIT), ('umoci.deb', 4 * 1024 * 1024),
          *((name, 128 * 1024) for name in SOURCES))
OCI_MANIFEST = 'application/vnd.oci.image.manifest.v1+json'
OCI_INDEX = 'application/vnd.oci.image.index.v1+json'
OCI_CONFIG = 'application/vnd.oci.image.config.v1+json'
OCI_LAYER = 'application/vnd.oci.image.layer.v1.tar'
MANIFEST_TYPES = {OCI_MANIFEST, 'application/vnd.docker.distribution.manifest.v2+json'}
INDEX_TYPES = {OCI_INDEX, 'application/vnd.docker.distribution.manifest.list.v2+json'}
LAYER_TYPES = {OCI_LAYER, OCI_LAYER + '+gzip', 'application/vnd.docker.image.rootfs.diff.tar.gzip'}


def require(condition, code):
    if not condition:
        raise ValueError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def document(raw):
    require(len(raw) <= 1024 * 1024, 'JSON_BOUNDS')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda value: require(False, 'NONFINITE_JSON'))


def blob_name(identifier):
    require(type(identifier) is str and re.fullmatch('sha256:[a-f0-9]{64}', identifier), 'BLOB_ID')
    return 'blobs/sha256/' + identifier[7:]


def validate(raw):
    require(type(raw) is bytes and 0 < len(raw) <= LIMIT, 'IMAGE_ARCHIVE_BOUNDS')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        members = archive.getmembers()
        require(0 < len(members) <= 256 and len({member.name for member in members}) == len(members), 'ARCHIVE_MEMBERS')
        for member in members:
            require(not member.pax_headers and member.sparse is None, 'ARCHIVE_EXTENSION')
            if member.isdir():
                require(member.name in ('blobs', 'blobs/sha256'), 'ARCHIVE_DIRECTORY')
                continue
            require(member.isfile() and 0 < member.size <= LIMIT and
                    (member.name in ('index.json', 'oci-layout', 'manifest.json') or
                     re.fullmatch('blobs/sha256/[a-f0-9]{64}', member.name)), 'ARCHIVE_MEMBER')
            files[member.name] = archive.extractfile(member).read()
    require(all(name in files for name in ('index.json', 'oci-layout', 'manifest.json')), 'ARCHIVE_LAYOUT')
    require(document(files['oci-layout']) == {'imageLayoutVersion': '1.0.0'}, 'OCI_LAYOUT')
    blobs = {name: body for name, body in files.items() if name.startswith('blobs/')}
    require(all(digest(body) == name.rsplit('/', 1)[1] for name, body in blobs.items()), 'BLOB_DIGEST')
    roots = document(files['index.json'])
    require(roots.get('schemaVersion') == 2 and roots.get('mediaType') == OCI_INDEX and
            len(roots.get('manifests', [])) == 3 and
            {item['digest'] for item in roots['manifests']} == set(IMAGES.values()), 'IMAGE_ROOT_COVERAGE')
    reachable = set()

    def descriptor(item):
        name = blob_name(item['digest'])
        require(name in blobs and type(item['size']) is int and item['size'] == len(blobs[name]), 'DESCRIPTOR_BINDING')
        reachable.add(name)
        return blobs[name]

    def walk(item, depth=0):
        require(depth <= 4, 'GRAPH_DEPTH')
        body = descriptor(item)
        if item['mediaType'] in INDEX_TYPES:
            node = document(body)
            require(node.get('schemaVersion') == 2, 'INDEX_VERSION')
            for child in node['manifests']:
                if blob_name(child['digest']) in blobs:
                    walk(child, depth + 1)
        elif item['mediaType'] in MANIFEST_TYPES:
            node = document(body)
            require(node.get('schemaVersion') == 2, 'MANIFEST_VERSION')
            descriptor(node['config'])
            for layer in node['layers']:
                descriptor(layer)

    roles, compatibility, checked_layers = {}, {}, {}
    for root in roots['manifests']:
        walk(root)
        role = next(role for role, identifier in IMAGES.items() if identifier == root['digest'])
        selected = root
        if root['mediaType'] in INDEX_TYPES:
            children = document(descriptor(root))['manifests']
            candidates = [item for item in children if item.get('platform') == {'os': 'linux', 'architecture': 'amd64'}]
            require(len(candidates) == 1, 'AMD64_MANIFEST_REQUIRED')
            selected = candidates[0]
        require(selected['mediaType'] in MANIFEST_TYPES, 'RUNTIME_MANIFEST_TYPE')
        manifest = document(descriptor(selected))
        config = document(descriptor(manifest['config']))
        require(config.get('os') == 'linux' and config.get('architecture') == 'amd64' and
                config.get('rootfs', {}).get('type') == 'layers', 'RUNTIME_PLATFORM')
        layers, diffs = manifest['layers'], config['rootfs']['diff_ids']
        require(0 < len(layers) == len(diffs) <= 100, 'LAYER_COVERAGE')
        for layer, expected in zip(layers, diffs):
            require(layer['mediaType'] in LAYER_TYPES, 'LAYER_TYPE')
            body = descriptor(layer)
            if layer['digest'] not in checked_layers:
                stream = gzip.GzipFile(fileobj=io.BytesIO(body)) if layer['mediaType'] != OCI_LAYER else io.BytesIO(body)
                checksum, size = hashlib.sha256(), 0
                with stream:
                    while chunk := stream.read(1024 * 1024):
                        size += len(chunk)
                        require(size <= LAYER_LIMIT, 'LAYER_EXPANSION_BOUNDS')
                        checksum.update(chunk)
                checked_layers[layer['digest']] = ('sha256:' + checksum.hexdigest(), size)
                require(sum(value[1] for value in checked_layers.values()) <= 2 * LAYER_LIMIT, 'TOTAL_EXPANSION_BOUNDS')
            require(checked_layers[layer['digest']][0] == expected, 'LAYER_DIFF_ID')
        roles[role] = dict(root=root['digest'], selected=selected, manifest=manifest)
        compatibility[blob_name(manifest['config']['digest'])] = dict(Config=blob_name(manifest['config']['digest']),
            Layers=[blob_name(item['digest']) for item in layers], RepoTags=None)
    saved = document(files['manifest.json'])
    require(type(saved) is list and len(saved) == 3 and
            {item['Config']: item for item in saved} == compatibility, 'DOCKER_MANIFEST_BINDING')
    require(reachable == set(blobs), 'UNREFERENCED_BLOB')
    require(sum(value[1] for value in checked_layers.values()) <= 2 * LAYER_LIMIT, 'TOTAL_EXPANSION_BOUNDS')
    return dict(roles=roles, blobs=blobs, summary=dict(images=dict(IMAGES), platform=PLATFORM, roles=len(roles),
        blobs=len(blobs), unique_layers=len(checked_layers), layer_references=sum(len(value['manifest']['layers']) for value in roles.values()),
        uncompressed_bytes=sum(value[1] for value in checked_layers.values()), archive_sha256=digest(raw),
        activation=False, full_recovery=False))


def seal(archive, tool, key):
    validate(archive)
    require(type(key) is bytes and len(key) == 32 and digest(tool) == TOOL_SHA, 'CUSTODY_KEY_OR_TOOL')
    files = {'docker-save.tar': archive, 'umoci.deb': tool}
    files.update({name: Path(__file__).with_name(name).read_bytes() for name in SOURCES})
    require(all(0 < len(files[name]) <= limit for name, limit in FRAMES), 'CUSTODY_FRAME_BOUNDS')
    plaintext = b''.join(len(files[name]).to_bytes(8, 'big') + files[name] for name, _ in FRAMES)
    nonce = os.urandom(12)
    capsule = MAGIC + nonce + AESGCM(key).encrypt(nonce, plaintext, PURPOSE.encode())
    checkpoint = dict(purpose=PURPOSE, images=dict(IMAGES), platform=PLATFORM, ciphertext_sha256=digest(capsule),
        archive_sha256=digest(archive), tool_sha256=TOOL_SHA, sources={name: digest(files[name]) for name in SOURCES})
    return capsule, checkpoint


def unseal(capsule, key, checkpoint):
    require(type(checkpoint) is dict and set(checkpoint) == {'purpose', 'images', 'platform', 'ciphertext_sha256',
            'archive_sha256', 'tool_sha256', 'sources'} and checkpoint['purpose'] == PURPOSE and
            checkpoint['images'] == IMAGES and checkpoint['platform'] == PLATFORM and
            checkpoint['tool_sha256'] == TOOL_SHA and set(checkpoint['sources']) == set(SOURCES), 'CUSTODY_CHECKPOINT')
    require(type(capsule) is bytes and len(MAGIC) + 28 < len(capsule) <= sum(limit + 8 for _, limit in FRAMES) + 64 and
            capsule.startswith(MAGIC) and digest(capsule) == checkpoint['ciphertext_sha256'] and
            type(key) is bytes and len(key) == 32, 'CUSTODY_PIN')
    offset = len(MAGIC)
    plaintext = AESGCM(key).decrypt(capsule[offset:offset+12], capsule[offset+12:], PURPOSE.encode())
    files, offset = {}, 0
    for name, limit in FRAMES:
        require(offset + 8 <= len(plaintext), 'CUSTODY_TRUNCATED')
        size = int.from_bytes(plaintext[offset:offset+8], 'big'); offset += 8
        require(0 < size <= limit and offset + size <= len(plaintext), 'CUSTODY_FRAME_BOUNDS')
        files[name] = plaintext[offset:offset+size]; offset += size
    require(offset == len(plaintext), 'CUSTODY_TRAILING_DATA')
    require(digest(files['docker-save.tar']) == checkpoint['archive_sha256'] and digest(files['umoci.deb']) == TOOL_SHA and
            all(digest(files[name]) == checkpoint['sources'][name] for name in SOURCES), 'CUSTODY_CONTENT_PIN')
    validate(files['docker-save.tar'])
    return files


def private_file(path, raw):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())


def restore(files, destination):
    require(set(files) == {name for name, _ in FRAMES}, 'RESTORE_FILE_COVERAGE')
    destination = Path(destination)
    require(destination.is_absolute() and '..' not in destination.parts and
            not any(parent.is_symlink() for parent in (destination, *destination.parents)), 'RESTORE_PATH')
    destination.mkdir(mode=0o700)
    for name, _ in FRAMES:
        private_file(destination / name, files[name])
