import base64
import copy
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from fleet.bundle import build
from fleet.contracts import FleetError, canonical, digest
from fleet.permit import sign
from fleet.remote import RemoteInstaller, build_agent, bundle_agent, public_hex
from fleet.remote_bootstrap import openssl_verify
from fleet.tests.test_permit import authority


@pytest.fixture
def remote(authority, tmp_path):
    key, authorization, arguments = authority
    root = tmp_path/'inputs'
    root.mkdir()
    content = b'fixture runtime is deliberately not a deployable gateway\n'
    (root/'fixture').write_bytes(content)
    specification = dict(source_commit='a'*40, scope='rehearsal', roles=['awg'], secret_slots=[],
        members=[dict(path='bin/fixture', source='fixture', sha256=digest(content), mode=0o555,
                      restart_group='awg', secret_slots=[])])
    sources = {str(path.relative_to(Path(__file__).parents[2])): path.read_bytes()
               for path in Path(__file__).parents[1].glob('*.py')}
    members = {'runtime/'+name: raw for name, raw in sources.items()}
    members['metadata/agent.json'] = canonical(dict(sha256=digest(build_agent(sources))))
    for name, raw in members.items():
        destination = root/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        specification['members'].append(dict(path=name, source=name, sha256=digest(raw), mode=0o444,
                                             restart_group='awg', secret_slots=[]))
    bundle = tmp_path/'bundle'
    manifest = build(root, specification, key, bundle)
    body = authorization['body']
    body.update(bundle_a=manifest['bundle_id'], agent_sha256=digest(build_agent()),
                bundle_signer_sha256=digest(bytes.fromhex(public_hex(key.public_key()))))
    authorization = sign(body, key, now=1000)
    known_hosts = tmp_path/'known_hosts'
    known_hosts.write_text(body['ipv4']+' ssh-ed25519 public-fixture-key\n')
    known_hosts.chmod(0o600)
    calls = []
    def runner(argv, **options):
        calls.append((argv, options))
        if argv[0] == 'ssh-keygen':
            return SimpleNamespace(returncode=0, stdout='256 '+body['ssh_fingerprint']+' host (ED25519)')
        return SimpleNamespace(returncode=1, stdout='', stderr='sensitive-secret-never-returned')
    adapter = RemoteInstaller(host=body['ipv4'], user='root', known_hosts=known_hosts,
        fingerprint=body['ssh_fingerprint'], authorization=authorization, permit_key=key.public_key(),
        bundle=bundle, bundle_key=key.public_key(), runner=runner, clock=lambda:1001)
    return adapter, calls


def test_agent_deterministic_and_no_private_members():
    import io
    import zipfile
    first = build_agent()
    assert first == build_agent()
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        assert 'fleet/remote_agent.py' in archive.namelist()
        assert all(name.endswith('.py') and not name.startswith('/') and '..' not in name for name in archive.namelist())
        assert archive.namelist() == sorted(archive.namelist())


def test_agent_and_receiver_come_from_verified_bundle_not_operator_tree():
    members = {'fleet/__init__.py': b'', 'fleet/remote_agent.py': b'FROZEN = True\n',
               'fleet/remote_bootstrap.py': b'FROZEN_RECEIVER = True\n'}
    expected = build_agent(members)
    contents = {'runtime/'+name: raw for name, raw in members.items()}
    contents['metadata/agent.json'] = canonical(dict(sha256=digest(expected)))
    agent, receiver = bundle_agent(contents)
    assert agent == expected and agent != build_agent()
    assert receiver == 'FROZEN_RECEIVER = True\n'


@pytest.mark.parametrize('tamper', ['missing', 'hash', 'source', 'path'])
def test_unbound_bundle_agent_rejected(remote, tamper):
    adapter, unused = remote
    contents = dict(adapter.contents)
    if tamper == 'missing':
        del contents['metadata/agent.json']
    elif tamper == 'hash':
        contents['metadata/agent.json'] = canonical(dict(sha256='0'*64))
    elif tamper == 'source':
        contents['runtime/fleet/remote_agent.py'] += b'\nchanged = True\n'
    else:
        contents['runtime/fleet/../outside.py'] = b''
    with pytest.raises(FleetError):
        bundle_agent(contents)


def test_dry_run_no_remote_writes_and_fresh_preflight_required(remote):
    adapter, calls = remote
    for action in adapter.permit['body']['allowed_actions']:
        if action != 'preflight':
            assert adapter.execute(action, 'dry-'+action, dry_run=True)['remote_writes'] == 0
    assert len(calls) == 1
    with pytest.raises(FleetError, match='preflight_required'):
        adapter.execute('stage','stage-one')
    assert len(calls) == 1


def test_fixed_ssh_argv_and_redacted_errors(remote):
    adapter, calls = remote
    argv = adapter.ssh.argv
    for setting in ('StrictHostKeyChecking=yes','ForwardAgent=no','ClearAllForwardings=yes',
                    'PasswordAuthentication=no','KbdInteractiveAuthentication=no','BatchMode=yes'):
        assert setting in argv
    assert argv[argv.index('-F')+1] == '/dev/null'
    adapter.preflight_at = 1001
    with pytest.raises(FleetError, match='remote_transport_failure') as failure:
        adapter.execute('stage','stage-one')
    assert 'secret' not in str(failure.value)
    command, options = calls[-1]
    assert command[:-1] == argv
    assert 'shell' not in options
    assert options['timeout'] == 660
    assert '"operation_id":"stage-one"' in options['input']


def test_known_hosts_cannot_change_after_initial_pin(remote):
    adapter, calls = remote
    adapter.preflight_at = 1001
    adapter.known_hosts.write_text('8.8.8.8 ssh-ed25519 changed-key\n')
    with pytest.raises(FleetError, match='pin_changed'):
        adapter.execute('stage','stage-pin-changed')
    assert len(calls) == 1


@pytest.mark.parametrize('operation', ['../escape', 'id;id', 'id\nshutdown', '--force-live'])
def test_operation_injection_rejected(remote, operation):
    adapter, calls = remote
    with pytest.raises(FleetError):
        adapter.execute('stage', operation, dry_run=True)
    assert len(calls) == 1


def test_openssl_readonly_signature_verification():
    key = Ed25519PrivateKey.generate()
    public = bytes.fromhex(public_hex(key.public_key()))
    payload = b'bounded disposable permit fixture'
    openssl_verify(public, key.sign(payload), payload)
    with pytest.raises(ValueError, match='signature'):
        openssl_verify(public, key.sign(payload), payload+b'changed')


def test_receiver_rejects_before_any_upload(authority, monkeypatch):
    from fleet import remote_bootstrap
    key, authorization, arguments = authority
    monkeypatch.setattr(remote_bootstrap.time, 'time', lambda:1001)
    touched = []
    monkeypatch.setattr(remote_bootstrap, 'secure_directory', lambda path:touched.append(path))
    authorization['signature'] = base64.b64encode(bytes(64)).decode()
    request = dict(permit=authorization, permit_key=public_hex(key.public_key()))
    with pytest.raises(ValueError, match='signature'):
        remote_bootstrap.receive(request)
    assert not touched


@pytest.mark.parametrize('tamper', [None, 'archive', 'signature', 'extra'])
def test_target_reverifies_uploaded_bundle(remote, tmp_path, tamper):
    from fleet.remote_agent import verified_upload
    adapter, calls = remote
    files = {path.name:base64.b64encode(path.read_bytes()).decode() for path in adapter.bundle.iterdir()}
    if tamper == 'archive':
        name = 'fc-gateway-'+adapter.manifest['bundle_id']+'.tar.zst'
        files[name] = base64.b64encode(b'changed archive').decode()
    if tamper == 'signature':
        files['manifest.sig'] = base64.b64encode(base64.b64encode(bytes(64))).decode()
    if tamper == 'extra':
        files['../outside'] = base64.b64encode(b'extra').decode()
    root = tmp_path/'target'
    root.mkdir()
    if tamper:
        with pytest.raises(FleetError):
            verified_upload(files, adapter.bundle_key, adapter.manifest['bundle_id'], root)
    else:
        assert verified_upload(files, adapter.bundle_key, adapter.manifest['bundle_id'], root)[0] == adapter.manifest


def test_bootstrap_verifies_members_before_package_install(remote):
    from fleet.remote_bootstrap import verify_bundle_payload
    adapter, calls = remote
    request = dict(operation=dict(bundle_id=adapter.manifest['bundle_id']), bundle_key=public_hex(adapter.bundle_key),
        bundle={path.name:base64.b64encode(path.read_bytes()).decode() for path in adapter.bundle.iterdir()})
    verify_bundle_payload(request)
    request['bundle']['fc-gateway-'+adapter.manifest['bundle_id']+'.tar.zst'] = base64.b64encode(b'changed').decode()
    with pytest.raises(ValueError, match='archive_hash'):
        verify_bundle_payload(request)
