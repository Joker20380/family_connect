"""Deterministic signed gateway archives; verify before extracting anything."""

import argparse
import base64
import io
import os
from pathlib import Path, PurePosixPath
import re
import resource
import stat
import subprocess
import tarfile
import tempfile

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .contracts import FleetError, ROLES, canonical, digest, exact, fail, load, typed

LIMIT = 128 * 1024 * 1024
MEMBER_LIMIT = 32 * 1024 * 1024
MEMBER_FIELDS = ('path', 'sha256', 'size', 'target', 'mode', 'owner', 'group', 'restart_group', 'secret_slots')
CORE_FIELDS = ('schema', 'source_commit', 'scope', 'supported_os', 'architecture', 'roles', 'secret_slots', 'members')
FORBIDDEN = ('.key', '.pem', '.sqlite', '.sqlite3', '.db', '.env', '.journal')


def safe_path(value):
    if (type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_./-]{1,100}', value)
            or value.startswith('/') or any(part in ('', '.', '..') for part in value.split('/'))
            or str(PurePosixPath(value)) != value):
        fail('unsafe_member_path')
    return value


def nonsecret(path, content):
    if (path.endswith(FORBIDDEN) or any(part in ('secrets', 'state', 'journals', 'credentials') for part in path.split('/'))
            or len(content) in (32, 64) or b'PRIVATE KEY' in content
            or re.search(rb'(?i)(?:password|private_key|token)\s*[=:]\s*["\']?[A-Za-z0-9+/]{16}', content)):
        fail('secret_or_state_member')


def check_core(core):
    exact(core, CORE_FIELDS)
    if (type(core['schema']) is not int or core['schema'] != 1 or not typed(core['source_commit'], 'commit')
            or core['scope'] not in ('synthetic', 'candidate') or core['supported_os'] != ['ubuntu-24.04']
            or core['architecture'] != 'x86_64' or not typed(core['roles'], 'roles') or not core['roles']
            or not typed(core['secret_slots'], 'ids')):
        fail('manifest_contract')
    members = core['members']
    if type(members) is not list or not 1 <= len(members) <= 1024:
        fail('member_count')
    paths = []
    total = 0
    for member in members:
        exact(member, MEMBER_FIELDS)
        path = safe_path(member['path'])
        if (member['target'] != 'RELEASE/' + path or not typed(member['sha256'], 'hash')
                or type(member['size']) is not int or not 0 <= member['size'] <= MEMBER_LIMIT
                or type(member['mode']) is not int or member['mode'] not in (0o444, 0o555)
                or member['owner'] != 'root' or member['group'] != 'root'
                or member['restart_group'] not in core['roles']
                or not typed(member['secret_slots'], 'ids')
                or not set(member['secret_slots']) <= set(core['secret_slots'])):
            fail('member_contract')
        if path in paths or any(path.startswith(previous + '/') or previous.startswith(path + '/') for previous in paths):
            fail('duplicate_or_overlapping_path')
        paths.append(path)
        total += member['size']
    if paths != sorted(paths) or total > LIMIT:
        fail('member_order_or_bound')


def tar_bytes(members, contents):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for member in members:
            info = tarfile.TarInfo(member['path'])
            info.size = member['size']
            info.mode = member['mode']
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = 'root'
            archive.addfile(info, io.BytesIO(contents[info.name]))
    return output.getvalue()


def codec(data, decompress=False):
    if len(data) > LIMIT:
        fail('archive_bound')
    def limits():
        resource.setrlimit(resource.RLIMIT_FSIZE, (LIMIT + 1024 * 1024, LIMIT + 1024 * 1024))
    with tempfile.TemporaryFile() as output:
        try:
            result = subprocess.run(['zstd', '-q', '-T1', '--no-progress', '-d' if decompress else '-19', '-c'],
                input=data, stdout=output, stderr=subprocess.PIPE, timeout=60, preexec_fn=limits)
            if result.returncode or output.tell() > LIMIT:
                fail('archive_codec')
            output.seek(0)
            return output.read(LIMIT + 1)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise FleetError('archive_codec') from error


def source_bytes(root, relative):
    safe_path(relative)
    path = root
    for component in relative.split('/'):
        path = path / component
        if path.is_symlink():
            fail('source_symlink')
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_size > MEMBER_LIMIT:
        fail('source_type_or_bound')
    return path.read_bytes()


def build(root, specification, signing_key, output):
    exact(specification, ('source_commit', 'scope', 'roles', 'secret_slots', 'members'))
    contents = {}
    members = []
    for entry in specification['members']:
        exact(entry, ('path', 'source', 'sha256', 'mode', 'restart_group', 'secret_slots'))
        content = source_bytes(Path(root).resolve(), entry['source'])
        path = safe_path(entry['path'])
        nonsecret(path, content)
        if path in contents or digest(content) != entry['sha256']:
            fail('source_hash_or_duplicate')
        contents[path] = content
        members.append(dict(path=path, sha256=digest(content), size=len(content), target='RELEASE/' + path,
            mode=entry['mode'], owner='root', group='root', restart_group=entry['restart_group'], secret_slots=entry['secret_slots']))
    core = dict(schema=1, source_commit=specification['source_commit'], scope=specification['scope'],
        supported_os=['ubuntu-24.04'], architecture='x86_64', roles=specification['roles'],
        secret_slots=specification['secret_slots'], members=sorted(members, key=lambda member: member['path']))
    check_core(core)
    bundle_id = 'gw-' + digest(canonical(core))[:32]
    archive = codec(tar_bytes(core['members'], contents))
    manifest = dict(core, bundle_id=bundle_id, archive_sha256=digest(archive))
    payload = canonical(manifest)
    signature = base64.b64encode(signing_key.sign(payload))
    output = Path(output)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    files = {'fc-gateway-' + bundle_id + '.tar.zst': archive, 'manifest.json': payload, 'manifest.sig': signature}
    hashes = {name: digest(content) for name, content in files.items()}
    files['sha256.json'] = canonical(hashes)
    for name, content in files.items():
        (output / name).write_bytes(content)
    return manifest


def verify(directory, public_key, expected_bundle=None):
    directory = Path(directory)
    payload = source_bytes(directory, 'manifest.json')
    signature = source_bytes(directory, 'manifest.sig')
    try:
        public_key.verify(base64.b64decode(signature, validate=True), payload)
    except (ValueError, InvalidSignature) as error:
        raise FleetError('signature_invalid') from error
    manifest = load(payload)
    exact(manifest, CORE_FIELDS + ('bundle_id', 'archive_sha256'))
    core = {key: manifest[key] for key in CORE_FIELDS}
    check_core(core)
    if (payload != canonical(manifest) or manifest['bundle_id'] != 'gw-' + digest(canonical(core))[:32]
            or expected_bundle is not None and expected_bundle != manifest['bundle_id']):
        fail('bundle_binding')
    archive_name = 'fc-gateway-' + manifest['bundle_id'] + '.tar.zst'
    archive_path = directory / archive_name
    if archive_path.is_symlink() or not archive_path.is_file() or archive_path.stat().st_size > LIMIT:
        fail('archive_file')
    archive = archive_path.read_bytes()
    if digest(archive) != manifest['archive_sha256']:
        fail('archive_hash')
    hashes = load(source_bytes(directory, 'sha256.json'))
    if hashes != {archive_name: digest(archive), 'manifest.json': digest(payload), 'manifest.sig': digest(signature)}:
        fail('hash_inventory')
    raw = codec(archive, decompress=True)
    contents = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as stream:
            for info in stream:
                safe_path(info.name)
                if not info.isreg() or info.name in contents or info.size > MEMBER_LIMIT or len(contents) >= 1024:
                    fail('archive_member_type')
                contents[info.name] = stream.extractfile(info).read(MEMBER_LIMIT + 1)
        if set(contents) != {member['path'] for member in core['members']}:
            fail('archive_member_set')
        for member in core['members']:
            content = contents[member['path']]
            nonsecret(member['path'], content)
            if len(content) != member['size'] or digest(content) != member['sha256']:
                fail('member_hash')
        if raw != tar_bytes(core['members'], contents):
            fail('archive_metadata')
    except (tarfile.TarError, OSError) as error:
        raise FleetError('archive_invalid') from error
    return manifest, contents


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'verify'])
    parser.add_argument('--directory', required=True)
    parser.add_argument('--key', required=True, help='External raw Ed25519 key file; never echoed')
    parser.add_argument('--spec')
    parser.add_argument('--source-root')
    arguments = parser.parse_args()
    try:
        key = Path(arguments.key).read_bytes()
        if arguments.action == 'build':
            result = build(arguments.source_root, load(Path(arguments.spec).read_bytes()), Ed25519PrivateKey.from_private_bytes(key), arguments.directory)
        else:
            result, contents = verify(arguments.directory, Ed25519PublicKey.from_public_bytes(key))
        print(canonical(dict(result='PASS', bundle_id=result['bundle_id'], archive_sha256=result['archive_sha256'])).decode())
    except (FleetError, OSError, ValueError, TypeError) as error:
        print(canonical(dict(result='FAIL', code=str(error) if isinstance(error, FleetError) else 'invalid_input')).decode())
        raise SystemExit(1)


if __name__ == '__main__':
    main()
