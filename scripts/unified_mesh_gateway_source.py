"""Materialize one reviewed MESH runtime for both pinned canonical gateways."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from scripts.slow_link_gateway_source import ROOT, committed, digest, inventory


MANIFESTS = {
    'primary': 'e60e31cf7b0a6e8384f1eaefde7d258b84966326db501f1ff21bfec5d0b8530a',
    'secondary': '4cf6b1464216e720d7f9014a2f9a39184759ae4c7095b9b19afb6019d96ad343',
}
BINARIES = {
    'primary': '8769eadfa88850c41fc0d90a9dcc4749f2e949de36dfd95bb606c32c404b3c30',
    'secondary': '5bcb32ea138325fbe3c788e2500d5054073ffc8df589e1cd1e83ed31c0946638',
}
IDLE_SOURCE = '2bc42584fbcba6ad0fafa24de2975a5154dce0b3'
PATCH = 'deploy/friends/restricted/mesh-idle-gateway.patch'
PATCH_SHA256 = '2b896c7dbc49eb6edef4ed32e8b11b88f0f815c60234da1f9a2c7a7591f829b4'
PROMOTED = frozenset('carrier/' + name for name in (
    'reliablestream/engine.go', 'reliablestream/performance.go', 'reliablestream/stream.go',
    'telemost/rtp.go', 'telemost/session.go', 'telemost/signaling.go', 'telemost/trace.go'))
CHANGED = frozenset(('carrier/reliablestream/engine.go', 'carrier/sessiontrace/trace.go'))
TESTS = tuple('carrier/' + name for name in (
    'reliablestream/idle_timeout_test.go', 'reliablestream/head_loss_test.go',
    'familysession/idle_timeout_test.go', 'roombroker/idle_cleanup_test.go'))


def accepted(source, role):
    if role not in MANIFESTS:
        raise ValueError('Unknown canonical predecessor')
    files = inventory(source)
    raw = files.pop('source-manifest.json', b'')
    if digest(raw) != MANIFESTS[role]:
        raise ValueError('Canonical predecessor manifest mismatch')
    expected = json.loads(raw)['files']
    if {name: digest(content) for name, content in files.items()} != expected:
        raise ValueError('Canonical predecessor inventory mismatch')
    return files


def reconcile(primary, secondary):
    differences = {name for name in primary.keys() | secondary.keys()
                   if primary.get(name) != secondary.get(name)}
    production = {name for name in differences if not name.endswith('_test.go')}
    if production != PROMOTED:
        raise ValueError('Unreviewed difference between canonical gateways')
    if not primary.keys() <= secondary.keys():
        raise ValueError('Shared source would discard predecessor members')
    return dict(secondary), sorted(differences)


def project(files, patch):
    if digest(patch) != PATCH_SHA256:
        raise ValueError('Reviewed idle patch mismatch')
    with tempfile.TemporaryDirectory(prefix='fc-unified-mesh-') as temporary:
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
    if changed != CHANGED:
        raise ValueError('Idle projection changed an unreviewed source boundary')
    return result


def materialize(primary, secondary, output, ref, *, repository=ROOT):
    if any(output.resolve().is_relative_to(source.resolve()) for source in (primary, secondary)):
        raise ValueError('Output cannot modify a predecessor')
    revision = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options',
                                       ref + '^{commit}'], cwd=repository).decode().strip()
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Invalid unified MESH source revision')
    files, differences = reconcile(accepted(primary, 'primary'), accepted(secondary, 'secondary'))
    files = project(files, committed(repository, revision, PATCH))
    for name in TESTS:
        files[name] = committed(repository, IDLE_SOURCE, name)
    receipt = dict(schema=1, source_commit=revision, idle_source_commit=IDLE_SOURCE,
                   predecessor_manifests=MANIFESTS, predecessor_binaries=BINARIES,
                   selected_base='secondary', reconciled_members=differences,
                   promoted_production=sorted(PROMOTED), patch_sha256=PATCH_SHA256,
                   idle_changed_members=sorted(CHANGED), test_inputs=list(TESTS),
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
    parser.add_argument('--primary', type=Path, required=True)
    parser.add_argument('--secondary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ref', required=True)
    arguments = parser.parse_args()
    os.umask(0o077)
    receipt = materialize(arguments.primary, arguments.secondary, arguments.output, arguments.ref)
    print(json.dumps(dict(source_commit=receipt['source_commit'], files=len(receipt['files']),
                          shared_gateway_source=True, deployed=False)))


if __name__ == '__main__':
    main()
