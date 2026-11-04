"""Project MESH lifecycle cleanup onto the pinned current private gateway capsule."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from scripts.slow_link_gateway_source import ROOT, committed, digest, inventory
from scripts import slow_link_gateway_source as predecessor


MANIFEST_SHA256 = 'bd4036aa8aa2e0c033b40405d71446330fda97c247ac0318f2f68f1bb3e2d14c'
BASELINE_BINARY_SHA256 = '566cbc96621c348e188aa50ffa54d6cf7bfce6274f8a214d3b0c227e743bb219'
LIFECYCLE_SOURCE = 'f66b533831304136b72f2b9923483090dfcc4c2d'
PATCH = 'deploy/friends/restricted/mesh-cleanup-gateway.patch'
PATCH_SHA256 = '5bfa7380a98b5e892672ae0d36473b83a9cd3d5166989408d0be94db37d3897c'
CHANGED = frozenset(('bootstrap/protocol.go', 'familysession/session.go', 'telemost/session.go'))
TESTS = ('bootstrap/auth_test.go', 'telemost/owned_lifetime_test.go')
TEST_OVERLAY = 'telemost/head_loss_test.go'


def head_loss_constructor(raw):
    replacements = (
        (b'fault string) (*headLossEndpoint, *headLossEndpoint) {\n\ttest.Helper()\n',
         b'fault string, constructors ...func(context.Context, Config) (*Session, error)) (*headLossEndpoint, *headLossEndpoint) {\n'
         b'\ttest.Helper()\n\tconstructor := New\n\tif len(constructors) > 0 {\n\t\tconstructor = constructors[0]\n\t}\n'),
        (b'session, err := New(sessiontrace.With(ctx, trace), Config{RoomURL: "local-test"})',
         b'session, err := constructor(sessiontrace.With(ctx, trace), Config{RoomURL: "local-test"})'),
    )
    for before, after in replacements:
        if raw.count(before) != 1:
            raise ValueError('Accepted head-loss test constructor mismatch')
        raw = raw.replace(before, after)
    return raw


def accepted(source, baseline='secondary', manifest=None):
    if baseline == 'primary':
        if manifest is None:
            raise ValueError('Primary predecessor manifest required')
        return {'carrier/' + name: raw for name, raw in predecessor.accepted(source, manifest).items()}
    if baseline != 'secondary' or manifest is not None:
        raise ValueError('Invalid cleanup predecessor selection')
    files = inventory(source)
    raw = files.pop('source-manifest.json', b'')
    if digest(raw) != MANIFEST_SHA256:
        raise ValueError('Accepted cleanup predecessor manifest mismatch')
    expected = json.loads(raw)['files']
    if {name: digest(content) for name, content in files.items()} != expected:
        raise ValueError('Accepted cleanup predecessor inventory mismatch')
    return files


def project(files, patch):
    if digest(patch) != PATCH_SHA256:
        raise ValueError('Reviewed cleanup patch mismatch')
    with tempfile.TemporaryDirectory(prefix='fc-cleanup-source-') as temporary:
        root = Path(temporary)
        for name, raw in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
        environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
                           GIT_CEILING_DIRECTORIES=str(root.parent))
        for arguments in (['--check'], []):
            subprocess.run(['git', 'apply', *arguments, '-'], input=patch, cwd=root / 'carrier',
                           env=environment, capture_output=True, check=True)
        result = inventory(root)
    changed = {name for name in files.keys() | result.keys() if files.get(name) != result.get(name)}
    if changed != {'carrier/' + name for name in CHANGED}:
        raise ValueError('Cleanup projection crossed the reviewed boundary')
    return result


def materialize(source, output, ref, *, baseline='secondary', manifest=None, repository=ROOT):
    revision = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options',
                                       ref + '^{commit}'], cwd=repository).decode().strip()
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Invalid cleanup source revision')
    files = project(accepted(source, baseline, manifest), committed(repository, revision, PATCH))
    if baseline == 'primary':
        files[predecessor.VECTOR] = committed(repository, predecessor.TRANSPORT_SOURCE, predecessor.VECTOR)
    files['carrier/' + TEST_OVERLAY] = head_loss_constructor(files['carrier/' + TEST_OVERLAY])
    for name in TESTS:
        files['carrier/' + name] = committed(repository, LIFECYCLE_SOURCE, 'carrier/' + name)
    receipt = dict(schema=1, source_commit=revision, lifecycle_source_commit=LIFECYCLE_SOURCE,
                   baseline=baseline,
                   accepted_manifest_sha256=predecessor.MANIFEST_SHA256 if baseline == 'primary' else MANIFEST_SHA256,
                   baseline_binary_sha256=predecessor.BASELINE_BINARY_SHA256 if baseline == 'primary' else BASELINE_BINARY_SHA256,
                   patch_sha256=PATCH_SHA256, changed_members=sorted(CHANGED), test_inputs=list(TESTS),
                   test_overlays=[TEST_OVERLAY],
                   production_configuration='absent', operation_permit=None,
                   files={name: digest(raw) for name, raw in sorted(files.items())})
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    for name, raw in files.items():
        path = output / name
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open('xb') as destination:
            destination.write(raw)
        path.chmod(0o600)
    manifest = output / 'source-manifest.json'
    manifest.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    manifest.chmod(0o600)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accepted-source', type=Path, required=True)
    parser.add_argument('--baseline', choices=('primary', 'secondary'), required=True)
    parser.add_argument('--accepted-manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ref', required=True)
    arguments = parser.parse_args()
    os.umask(0o077)
    receipt = materialize(arguments.accepted_source, arguments.output, arguments.ref,
                          baseline=arguments.baseline, manifest=arguments.accepted_manifest)
    print(json.dumps(dict(source_commit=receipt['source_commit'], files=len(receipt['files']), deployed=False)))


if __name__ == '__main__':
    main()
