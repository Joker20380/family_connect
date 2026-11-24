"""Reproducible node/entrypoint/collector bundle; never installs or enables it."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import zipfile

from scripts.package_paid_transport import ROOT, archive, sha
from scripts.package_ru_lifecycle import BASE_SOURCE, BASE_NODE, BASE_GATEWAY

COLLECTORS = ('collector.py', 'transport_collector.py', 'metrics_collector.py',
    'subscription_collector.py', 'technical_metadata_collector.py')
UNITS = ('family-connect-paid-watch.service', 'paid-dependency.conf', 'paid-tcp-preflight.conf')
MODULE = 'control/friends/transport_gateway.py'
POLICY = 'control/friends/transport_policy.py'


def source_bytes(source, revision, path):
    return subprocess.check_output(['git', '-C', str(source), 'show', revision+':'+path])


def build(node, gateway, output, revision, source=ROOT):
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('EXPLICIT_FULL_SOURCE_COMMIT_REQUIRED')
    if sha(node.read_bytes()) != BASE_NODE or sha(gateway.read_bytes()) != BASE_GATEWAY:
        raise ValueError('EXACT_ACCEPTED_RUNTIME_INPUTS_REQUIRED')
    with zipfile.ZipFile(node) as package:
        original = {name: package.read(name) for name in package.namelist()}
        if len(original) != len(package.namelist()):
            raise ValueError('DUPLICATE_ARCHIVE_MEMBER')
    if source_bytes(source, revision, POLICY) != original[POLICY]:
        raise ValueError('POLICY_CHANGE_REQUIRES_NEW_QUALIFICATION')
    current = dict(original)
    current[MODULE] = source_bytes(source, revision, MODULE)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    files, sources = {}, {}

    def save(name, data, source_path=None, source_ref=revision):
        target = output/name
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o600)
        files[name] = dict(sha256=sha(data), mode='0600', bytes=len(data))
        if source_path:
            sources[name] = dict(ref=source_ref, path=source_path, sha256=sha(data))

    archive(output/'paid-transport.pyz', current)
    (output/'paid-transport.pyz').chmod(0o600)
    files['paid-transport.pyz'] = dict(sha256=sha((output/'paid-transport.pyz').read_bytes()),
        mode='0600', bytes=(output/'paid-transport.pyz').stat().st_size)
    save('awg-gateway.py', source_bytes(source, revision, 'deploy/friends/awg-gateway.py'), 'deploy/friends/awg-gateway.py')
    save('legacy/paid-transport.pyz', node.read_bytes())
    save('legacy/awg-gateway.py', gateway.read_bytes(), 'deploy/friends/awg-gateway.py', BASE_SOURCE)
    for name in UNITS:
        path = 'deploy/friends/paid-transport/'+name
        save(name, source_bytes(source, revision, path), path)
        save('legacy/'+name, source_bytes(source, BASE_SOURCE, path), path, BASE_SOURCE)
    for name in COLLECTORS:
        path = 'control_plane/apps/console/'+name
        save('collectors/'+name, source_bytes(source, revision, path), path)
        save('operator/'+path, source_bytes(source, revision, path), path)
    for path in ('control_plane/collect_inventory.py', 'control/friends/pseudonyms.py'):
        save('operator/'+path, source_bytes(source, revision, path), path)
    config = dict(schema=1, profile='paid-transports-v2', node='gateway-ru', enabled=True)
    save('transport-enforcement.legacy.json', (json.dumps(config, sort_keys=True)+'\n').encode())
    save('transport-enforcement.observations-v1.json',
        (json.dumps(dict(config, readback_mode='observations-v1'), sort_keys=True)+'\n').encode())
    manifest = dict(schema=1, kind='transport-readback-coordinated', production='NOT_DEPLOYED',
        builder_sha256=sha(Path(__file__).read_bytes()),
        source=revision, source_tree=subprocess.check_output(['git', '-C', str(source), 'rev-parse', revision+'^{tree}'], text=True).strip(),
        default_mode='legacy', explicit_modes=['legacy', 'observations-v1'], baseline_source=BASE_SOURCE,
        baseline_node=BASE_NODE, baseline_gateway=BASE_GATEWAY, files=files, sources=sources,
        before_modules={name: sha(data) for name, data in original.items()},
        after_modules={name: sha(data) for name, data in current.items()},
        changed_modules=[name for name in current if original.get(name) != current[name]],
        excluded=['authority state', 'keys', 'profiles', 'databases', 'operator HTTP/reconcile archives', 'pressure observer'],
        rollback='stop/fence, retain current authority, replace code and explicit legacy config; never restore state')
    (output/'manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2)+'\n')
    (output/'manifest.json').chmod(0o600)
    return manifest


def verify(root):
    if root.is_symlink() or (root/'manifest.json').is_symlink():
        raise ValueError('BUNDLE_VERIFICATION_FAILED')
    manifest = json.loads((root/'manifest.json').read_text())
    actual = {path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file() or path.is_symlink()}
    if (manifest.get('schema') != 1 or manifest.get('kind') != 'transport-readback-coordinated'
            or actual != set(manifest.get('files', {})) | {'manifest.json'}):
        raise ValueError('BUNDLE_VERIFICATION_FAILED')
    for name, expected in manifest['files'].items():
        path = root/name
        if (Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink()
                or not path.resolve().is_relative_to(root.resolve())
                or not path.is_file() or sha(path.read_bytes()) != expected['sha256']
                or path.stat().st_mode & 0o777 != int(expected['mode'], 8)):
            raise ValueError('BUNDLE_VERIFICATION_FAILED')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', type=Path, required=True)
    parser.add_argument('--gateway', type=Path, required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.node, args.gateway, args.output, args.source), sort_keys=True))


if __name__ == '__main__':
    main()
