"""Project reviewed slow-link changes onto the exact accepted production gateway."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SHA256 = '27b54a9dd167c3b6af639bb03864f4d7d121c0e8b96c90eccb45a198c936f117'
BASELINE_BINARY_SHA256 = 'f8ff517804c8cc425b172c821630274ce39ccfa9a3e79328db3e8a626f45ebef'
TRANSPORT_SOURCE = '142ee464f12cd93f3aa82c2f6b1a5a912f196481'
PATCH = 'deploy/friends/restricted/slow-link-gateway.patch'
PATCH_SHA256 = 'cd6405673580bcccf251b2a7b56389269083a77f81b787f82648ac68b84002dd'
CHANGED = frozenset(('reliablestream/engine.go', 'reliablestream/performance.go',
                     'reliablestream/performance_test.go', 'reliablestream/stream.go',
                     'telemost/rtp.go', 'telemost/session.go', 'telemost/signaling.go',
                     'telemost/trace.go'))
TESTS = ('reliablestream/adaptive_retry_test.go', 'reliablestream/engine_test.go',
         'reliablestream/slow_link_test.go', 'reliablestream/stream_test.go',
         'reliablestream/trace_test.go', 'reliablestream/throughput_comparison_test.go',
         'telemost/ice_recovery_runtime_test.go', 'telemost/reliable_framing_test.go',
         'telemost/trace_test.go', 'telemost/transient_disconnect_test.go',
         'telemost/receive_stall_test.go', 'telemost/local_process_test.go',
         'familysession/process_link_test.go', 'tcpforward/mesh_performance_test.go')
CORRECTION_TESTS = {
    'reliablestream/close_write_test.go': 'bd67843f980ede602cf3aeeefa5f31e23ac6711a',
    'reliablestream/close_delivery_test.go': 'bd67843f980ede602cf3aeeefa5f31e23ac6711a',
    'telemost/rtp_idle_test.go': '36ce71365e3393419073430eebf6824baed140be',
}
VECTOR = 'tests/vectors/bootstrap-timestamps.json'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def inventory(source):
    if source.is_symlink() or not source.is_dir():
        raise ValueError('Gateway source must be a real directory')
    files = {}
    for path in sorted(source.rglob('*')):
        metadata = path.lstat()
        if stat.S_ISDIR(metadata.st_mode):
            continue
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError('Gateway source contains a non-regular or linked member')
        files[path.relative_to(source).as_posix()] = path.read_bytes()
    return files


def accepted(source, manifest):
    raw = manifest.read_bytes()
    if digest(raw) != MANIFEST_SHA256:
        raise ValueError('Accepted gateway manifest mismatch')
    value = json.loads(raw)
    expected = value['files']
    if not expected or any(not isinstance(name, str) or PurePosixPath(name).is_absolute()
                           or '..' in PurePosixPath(name).parts for name in expected):
        raise ValueError('Invalid gateway inventory')
    files = inventory(source)
    if {name: digest(content) for name, content in files.items()} != expected:
        raise ValueError('Accepted gateway source mismatch')
    return files


def project(files, patch):
    if digest(patch) != PATCH_SHA256:
        raise ValueError('Reviewed gateway patch mismatch')
    with tempfile.TemporaryDirectory(prefix='fc-gateway-source-') as temporary:
        source = Path(temporary)
        for name, raw in files.items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
        environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
                           GIT_CEILING_DIRECTORIES=str(source.parent))
        for arguments in (['--check'], []):
            subprocess.run(['git', 'apply', *arguments, '-'], input=patch, cwd=source,
                           env=environment, capture_output=True, check=True)
        projected = inventory(source)
    changed = {name for name in files.keys() | projected.keys() if files.get(name) != projected.get(name)}
    if changed != CHANGED:
        raise ValueError('Gateway projection changed an unreviewed source boundary')
    return projected


def committed(repository, revision, name):
    entry = subprocess.check_output(['git', 'ls-tree', revision, '--', name], cwd=repository).decode()
    if not entry.startswith(('100644 blob ', '100755 blob ')):
        raise ValueError('Missing committed gateway input')
    return subprocess.check_output(['git', 'show', revision + ':' + name], cwd=repository)


def materialize(source, manifest, output, ref, *, repository=ROOT):
    revision = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options',
                                        ref + '^{commit}'], cwd=repository).decode().strip()
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Invalid source revision')
    files = project(accepted(source, manifest), committed(repository, revision, PATCH))
    for name in TESTS:
        files[name] = committed(repository, TRANSPORT_SOURCE, 'carrier/' + name)
    for name, test_revision in CORRECTION_TESTS.items():
        files[name] = committed(repository, test_revision, 'carrier/' + name)
    content = {'carrier/' + name: raw for name, raw in files.items()}
    content[VECTOR] = committed(repository, TRANSPORT_SOURCE, VECTOR)
    receipt = dict(schema=1, source_commit=revision, transport_source_commit=TRANSPORT_SOURCE,
                   accepted_manifest_sha256=MANIFEST_SHA256, baseline_binary_sha256=BASELINE_BINARY_SHA256,
                   patch_sha256=PATCH_SHA256, changed_members=sorted(CHANGED),
                   test_inputs=list(TESTS) + list(CORRECTION_TESTS) + [VECTOR],
                   correction_test_sources=dict(CORRECTION_TESTS), production_configuration='absent',
                   operation_permit=None, files={name: digest(raw) for name, raw in sorted(content.items())})
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    for name, raw in content.items():
        path = output / name
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open('xb') as destination:
            destination.write(raw)
        path.chmod(0o600)
    receipt_path = output / 'source-manifest.json'
    receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    receipt_path.chmod(0o600)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accepted-source', required=True, type=Path)
    parser.add_argument('--accepted-manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--ref', required=True)
    arguments = parser.parse_args()
    os.umask(0o077)
    receipt = materialize(arguments.accepted_source, arguments.accepted_manifest,
                          arguments.output, arguments.ref)
    print(json.dumps({'source_commit': receipt['source_commit'], 'files': len(receipt['files']),
                      'deployed': False}))


if __name__ == '__main__':
    main()
