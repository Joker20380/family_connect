"""Offline OCI OWNER overlay inspection; no extraction, Docker dispatch or activation."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import stat
import sys
import tarfile
import zlib

from scripts import control_ha_owner_activation_plan as plan

require = plan.require
MANIFEST = 'application/vnd.oci.image.manifest.v1+json'
CONFIG = 'application/vnd.oci.image.config.v1+json'
LAYERS = {'application/vnd.oci.image.layer.v1.tar', 'application/vnd.oci.image.layer.v1.tar+gzip',
          'application/vnd.docker.image.rootfs.diff.tar.gzip'}
LIMIT = 4 * 1024 * 1024
ARCHIVE_LIMIT = 2 * 1024**3
STAT_FIELDS = ('st_dev', 'st_ino', 'st_uid', 'st_gid', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(raw):
    return json.loads(raw, object_pairs_hook=plan.observer.pairs,
                      parse_constant=lambda value: require(False, 'NONFINITE_JSON'))


def image_id(value):
    require(type(value) is str and re.fullmatch(r'sha256:[0-9a-f]{64}', value), 'IMAGE_ID')
    return value.split(':')[1]


def expected_sources(value):
    require(type(value) is dict and set(value) == {'source_commit', 'files'} and
            type(value['source_commit']) is str and re.fullmatch('[0-9a-f]{40}', value['source_commit']), 'SOURCE_COMMIT')
    require(type(value['files']) is dict and set(value['files']) == set(plan.upgrade.source.SOURCES), 'SOURCE_SCOPE')
    for record in value['files'].values():
        require(type(record) is dict and set(record) == {'sha256', 'size'} and
                type(record['sha256']) is str and re.fullmatch('[0-9a-f]{64}', record['sha256']) and
                type(record['size']) is int and 0 < record['size'] <= plan.upgrade.source.FILE_LIMIT, 'SOURCE_RECORD')
    return value['files']


def layer_contents(raw, expected):
    require(0 < len(raw) <= LIMIT and len(raw) % 512 == 0, 'LAYER_BOUNDS')
    files = {'app/' + name: name for name in expected}
    directories = {str(parent) for name in files for parent in PurePosixPath(name).parents if str(parent) != '.'}
    seen, observed, offset = set(), {}, 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for member in archive:
            name = member.name
            require(name in files or name in directories, 'LAYER_MEMBER_SCOPE')
            require(name not in seen and len(seen) < len(files) + len(directories), 'LAYER_DUPLICATE')
            require(member.offset == offset and member.offset_data == offset + 512 and
                    not member.pax_headers and member.sparse is None and not member.linkname and
                    member.uid == member.gid == 0 and member.devmajor == member.devminor == 0, 'LAYER_METADATA')
            seen.add(name)
            if name in directories:
                require(member.isdir() and member.mode == 0o755 and member.size == 0, 'LAYER_DIRECTORY')
            else:
                require(member.isreg() and member.mode == 0o644 and
                        0 < member.size <= plan.upgrade.source.FILE_LIMIT, 'LAYER_SOURCE')
                source = archive.extractfile(member).read(plan.upgrade.source.FILE_LIMIT + 1)
                require(len(source) == member.size, 'LAYER_SOURCE_SIZE')
                observed[files[name]] = dict(sha256=digest(source), size=len(source))
            offset = member.offset_data + ((member.size + 511) // 512) * 512
    require(seen == set(files) | directories and len(raw) - offset >= 1024 and not any(raw[offset:]), 'LAYER_CLOSURE')
    return observed


class OCIArchive:
    def __init__(self, stream):
        self.archive = tarfile.open(fileobj=stream, mode='r:')
        self.members = {}
        try:
            for member in self.archive:
                require(len(self.members) < 4096 and member.name not in self.members, 'OCI_MEMBER_COUNT')
                require((member.isdir() or member.isreg()) and not member.linkname and member.sparse is None and
                        not member.pax_headers and 0 <= member.size <= ARCHIVE_LIMIT and
                        str(PurePosixPath(member.name)) == member.name and not member.name.startswith('/') and
                        '..' not in PurePosixPath(member.name).parts, 'OCI_MEMBER_SHAPE')
                require((member.isdir() and member.name in ('blobs', 'blobs/sha256')) or
                        (member.isreg() and (member.name in ('oci-layout', 'index.json', 'manifest.json') or
                         re.fullmatch('blobs/sha256/[0-9a-f]{64}', member.name))), 'OCI_MEMBER_SCOPE')
                self.members[member.name] = member
        except BaseException:
            self.archive.close()
            raise

    def close(self):
        self.archive.close()

    def read(self, name, limit=LIMIT):
        member = self.members.get(name)
        require(member is not None and member.isreg() and 0 < member.size <= limit, 'OCI_BLOB')
        raw = self.archive.extractfile(member).read(limit + 1)
        require(len(raw) == member.size, 'OCI_BLOB_SIZE')
        return raw

    def blob(self, descriptor, media):
        require(type(descriptor) is dict and descriptor.get('mediaType') in media and
                type(descriptor.get('size')) is int and 0 < descriptor['size'] <= LIMIT and
                not any(field in descriptor for field in ('urls', 'data')), 'OCI_DESCRIPTOR')
        expected = image_id(descriptor['digest'])
        raw = self.read('blobs/sha256/' + expected)
        require(len(raw) == descriptor['size'] and digest(raw) == expected, 'OCI_BLOB_PIN')
        return raw

    def image(self, selected):
        expected = image_id(selected)
        raw = self.read('blobs/sha256/' + expected)
        require(digest(raw) == expected, 'OCI_MANIFEST_PIN')
        manifest = parse(raw)
        require(type(manifest) is dict and manifest.get('schemaVersion') == 2 and
                manifest.get('mediaType') == MANIFEST and type(manifest.get('layers')) is list and
                0 < len(manifest['layers']) <= 128, 'OCI_MANIFEST')
        config = parse(self.blob(manifest['config'], {CONFIG}))
        require(type(config) is dict and type(config.get('config')) is dict and
                config['rootfs']['type'] == 'layers' and type(config['rootfs']['diff_ids']) is list and
                len(config['rootfs']['diff_ids']) == len(manifest['layers']), 'OCI_CONFIG')
        for identifier in config['rootfs']['diff_ids']:
            image_id(identifier)
        return manifest, config


def inspect(stream, role, candidate, expectation):
    expected = expected_sources(expectation)
    require(role in plan.upgrade.ROLES and candidate not in plan.upgrade.ROLES.values(), 'ROLE_CANDIDATE')
    baseline = plan.upgrade.ROLES[role]
    archive = OCIArchive(stream)
    try:
        require(parse(archive.read('oci-layout')) == {'imageLayoutVersion': '1.0.0'}, 'OCI_LAYOUT')
        index = parse(archive.read('index.json'))
        require(type(index) is dict and index.get('schemaVersion') == 2 and
                type(index.get('manifests')) is list and 0 < len(index['manifests']) <= 8, 'OCI_INDEX')
        descriptors = {item['digest']: item for item in index['manifests']}
        require(len(descriptors) == len(index['manifests']) and {baseline, candidate} <= descriptors.keys(), 'OCI_INDEX_SCOPE')
        for identifier in (baseline, candidate):
            archive.blob(descriptors[identifier], {MANIFEST})
        original_manifest, original = archive.image(baseline)
        candidate_manifest, updated = archive.image(candidate)
        require(original['config'] == updated['config'] and
                all(original.get(field) == updated.get(field) for field in ('os', 'architecture', 'variant')), 'OCI_RUNTIME_CHANGED')
        layers = candidate_manifest['layers']
        require(layers[:-1] == original_manifest['layers'] and len(layers) == len(original_manifest['layers']) + 1 and
                updated['rootfs']['diff_ids'][:-1] == original['rootfs']['diff_ids'], 'OCI_BASE_CHANGED')
        compressed = archive.blob(layers[-1], LAYERS)
        if layers[-1]['mediaType'].endswith(('gzip', '+gzip')):
            with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as decoder:
                raw = decoder.read(LIMIT + 1)
        else:
            raw = compressed
        require(len(raw) <= LIMIT and 'sha256:' + digest(raw) == updated['rootfs']['diff_ids'][-1], 'OCI_DIFF_PIN')
        observed = layer_contents(raw, expected)
    finally:
        archive.close()
    changed = sorted(name for name in expected if expected[name] != observed[name])
    return dict(status='OWNER_OVERLAY_SOURCE_MISMATCH' if changed else 'OWNER_OVERLAY_SOURCE_MATCH', role=role,
                baseline_image=baseline, candidate_image=candidate, source_commit=expectation['source_commit'],
                expected_sources_sha256=digest(json.dumps(expectation, sort_keys=True).encode()),
                layer_sha256=layers[-1]['digest'], diff_id=updated['rootfs']['diff_ids'][-1],
                layer_content_closed=True, source_matches=not changed, changed_sources=changed, observed_sources=observed,
                independent_approval=False, runtime_qualified=False, capture_permitted=False, deployed=False)


def inspect_private(path, expected_sha, role, candidate, expectation):
    require(type(expected_sha) is str and re.fullmatch('[0-9a-f]{64}', expected_sha), 'ARCHIVE_PIN')
    path = plan.private_path(path)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and stat.S_IMODE(before.st_mode) == 0o600 and
                before.st_uid == os.geteuid() and before.st_nlink == 1 and
                0 < before.st_size <= ARCHIVE_LIMIT, 'PRIVATE_ARCHIVE')
        require(hashlib.file_digest(stream, 'sha256').hexdigest() == expected_sha, 'ARCHIVE_PIN')
        stream.seek(0)
        receipt = inspect(stream, role, candidate, expectation)
        after = os.fstat(stream.fileno())
        require(all(getattr(before, field) == getattr(after, field) for field in STAT_FIELDS), 'ARCHIVE_CHANGED')
    receipt['archive_sha256'] = expected_sha
    return receipt


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--archive-sha256', required=True)
    parser.add_argument('--sources', required=True, type=Path)
    parser.add_argument('--sources-sha256', required=True)
    parser.add_argument('--role', required=True, choices=plan.upgrade.ROLES)
    parser.add_argument('--candidate', required=True)
    arguments = parser.parse_args()
    try:
        expectation = plan.read_private(arguments.sources, arguments.sources_sha256)
        receipt = inspect_private(arguments.archive, arguments.archive_sha256, arguments.role, arguments.candidate, expectation)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, EOFError, RecursionError, tarfile.TarError, zlib.error):
        print('OWNER_OVERLAY_REFUSED', file=sys.stderr)
        return 1
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt['source_matches'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
