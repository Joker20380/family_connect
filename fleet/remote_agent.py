"""Target-side verifier. Only signed rehearsal runtime code can receive dispatch."""

import base64
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .bundle import verify as verify_bundle
from .contracts import canonical, digest, exact, fail, load
from .permit import verify as verify_permit
from .remote_bootstrap import secure_directory
from .rehearsal_state import RehearsalState


def verified_upload(files, key, bundle_id, root):
    expected = {'manifest.json', 'manifest.sig', 'sha256.json', 'fc-gateway-'+bundle_id+'.tar.zst'}
    if type(files) is not dict or set(files) != expected:
        fail('remote_bundle_files')
    for name, encoded in files.items():
        content = base64.b64decode(encoded, validate=True)
        if len(content) > 128*1024*1024:
            fail('remote_bundle_bound')
        (root/name).write_bytes(content)
    return verify_bundle(root, key, bundle_id)


def dispatch(request):
    exact(request, ('permit', 'permit_key', 'bundle_key', 'operation', 'bundle', 'upload_only'))
    body = request['permit']['body']
    operation = request['operation']
    if request['upload_only'] is not False or os.geteuid() != 0:
        fail('remote_execution_contract')
    key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(request['bundle_key']))
    permit_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(request['permit_key']))
    agent = Path(sys.argv[0])
    verify_permit(request['permit'], permit_key, host=body['ipv4'], fingerprint=body['ssh_fingerprint'],
        bundle_id=operation['bundle_id'], action=operation['action'], agent_sha256=digest(agent.read_bytes()),
        bundle_signer_sha256=digest(bytes.fromhex(request['bundle_key'])))
    release = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
    if release.get('ID','').strip('"') != 'ubuntu' or release.get('VERSION_ID','').strip('"') != '24.04':
        fail('unsupported_os')
    import platform
    import stat
    if platform.machine() != 'x86_64':
        fail('unsupported_architecture')
    if not Path('/dev/net/tun').exists() or not stat.S_ISCHR(Path('/dev/net/tun').stat().st_mode):
        fail('missing_tun')
    directory = Path('/var/lib/family-connect-rehearsal')/body['instance_id']
    secure_directory(directory)
    with tempfile.TemporaryDirectory(prefix='verify-', dir=directory) as temporary:
        root = Path(temporary)
        manifest, contents = verified_upload(request['bundle'], key, operation['bundle_id'], root)
        if manifest['scope'] != 'rehearsal' or not {'awg','tcp','mesh'} <= set(manifest['roles']):
            fail('deployable_rehearsal_roles_required')
        if 'runtime/roles.py' not in contents or 'metadata/deployable.json' not in contents:
            fail('UNBOUND_ROLE_ARTIFACT')
        from .provenance import validate
        inventory = validate(load(contents['metadata/deployable.json']))
        if inventory['schema']!=2 or inventory['scope']!='DEPLOYABLE_REHEARSAL':
            fail('deployable_inventory_required')
        if load(contents.get('metadata/agent.json',b'{}'))!=dict(sha256=digest(agent.read_bytes())):
            fail('deployable_agent_binding')
        for artifact in inventory['artifacts']:
            content = contents.get(artifact['path'])
            if content is None or digest(content) != artifact['sha256'] or len(content) != artifact['size']:
                fail('UNBOUND_ROLE_ARTIFACT')
        runtime_path = root/'verified-runtime.py'
        runtime_path.write_bytes(contents['runtime/roles.py'])
        runtime_path.chmod(0o400)
        spec = importlib.util.spec_from_file_location('verified_rehearsal_runtime', runtime_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        runtime = module.Runtime(manifest=manifest, contents=contents, authorization=request['permit'],
                                 authority=permit_key, directory=directory)
        return RehearsalState(directory/'operations', request['permit'], runtime).execute(operation)


def main():
    try:
        request = load(sys.stdin.buffer.read(192*1024*1024))
        print(canonical(dispatch(request)).decode())
    except Exception:
        print('{"error":"remote_agent_rejected"}')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
