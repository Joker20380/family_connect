"""Native root-only maintenance fixture in an owned networkless disposable container."""
import base64
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import uuid

import cryptography
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.x509.oid import NameOID

from control.friends import profile_store, restricted, restricted_maintenance as maintenance
from control.friends.transport_policy import NODES
from scripts.control_ha_import import encoded, digest
from scripts.control_ha_maintenance_v1 import PURPOSE
from scripts.control_ha_receiver_fixture import artifacts_for_receivers
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_rehearsal import private_file, require
from scripts.referral_postgres_rehearsal import NOW

ROOT = Path(__file__).resolve().parents[1]
LABEL = 'family-connect.ha-maintenance-fixture'


def packed(raw):
    return base64.b64encode(raw).decode()


def create_node(root, node, issuer):
    root.mkdir(mode=0o755)
    material = root / 'profile'
    material.mkdir(mode=0o750)
    os.chown(material, 0, 41003)
    control = root / 'control'
    control.mkdir(mode=0o700)
    operations = control / 'operations'
    operations.mkdir(mode=0o700)
    lock = control / 'profile.lock'
    private_file(lock, b'')
    publisher = root / 'publisher'
    publisher.mkdir(mode=0o1770)
    os.chown(publisher, 0, 41002)
    publisher.chmod(0o1770)
    directory = publisher / 'directory.json'
    private_file(directory, issuer['directory'])
    os.chown(directory, 41001, 41002)
    executable = control / 'publisher-contract'
    private_file(executable, b'synthetic-publisher-identity/not-executable')
    port = profile_store.DirectoryPort(directory, dict(uid=41001, gid=41002, mode=0o600),
        dict(path=str(publisher), **profile_store.metadata(publisher.stat()), device=publisher.stat().st_dev,
             inode=publisher.stat().st_ino),
        ((str(executable), digest(executable.read_bytes()), profile_store.metadata(executable.stat())),))
    trust = parse(base64.b64decode(parse(issuer['delegation'])['payload'], validate=True))
    authority = x509.load_pem_x509_certificate(trust['authority'].encode())
    signing = Ed25519PrivateKey.from_private_bytes(issuer['runtime-key'])
    private = Ed25519PrivateKey.generate()
    leaf = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, node)]))
        .issuer_name(authority.subject).public_key(private.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(restricted.utc(NOW - 1)).not_valid_after(restricted.utc(NOW + 3599))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), True)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(signing.public_key()), False).sign(signing, None))
    profile = material / 'profile.json'
    exact_crl = node == 'nl-amsterdam-1'
    previous_crl = ((x509.CertificateRevocationListBuilder().issuer_name(authority.subject)
        .last_update(restricted.utc(NOW - 2)).next_update(restricted.utc(NOW + 3598))
        .add_extension(x509.CRLNumber(0), False).sign(signing, None).public_bytes(Encoding.PEM))
        if exact_crl else issuer['crl'])
    before = encoded(dict(authority=trust['authority'], family=trust['family'], gateway=trust['gateway'],
        minimum_revision=trust['minimum_revision'], revocations=previous_crl.decode(), minimum_crl=0,
        certificate=leaf.public_bytes(Encoding.PEM).decode(),
        private_key=private.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode()))
    private_file(profile, before)
    os.chown(profile, 0, 41003)
    profile.chmod(0o640)
    locator = profile_store.Locator(profile, lock, operations, 41003, port)
    locator_document = dict(schema=1, lock_version=1, profile=str(profile), lock=str(lock), operations=str(operations),
        reader_gid=41003, directory=dict(path=str(directory), metadata=port.expected,
            publisher_parent=port.publisher_parent, publisher_contract=port.publisher_contract))
    locator_path = control / 'locator.json'
    private_file(locator_path, encoded(locator_document))
    loaded = profile_store.Locator.load(locator_path)
    config = maintenance.CanonicalConfiguration(profile_store.ProfileStore(loaded, clock=lambda: NOW), secrets.token_bytes(32))
    request = encoded(dict(revocations=issuer['crl'].decode()))
    number = x509.load_pem_x509_crl(issuer['crl']).extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
    permit = dict(schema=1, operation_id='restricted_maintenance_' + secrets.token_hex(16),
        action='apply_exact_crl' if exact_crl else 'reconcile_current_floor',
        expected_profile_sha256=digest(before), expected_directory_sha256=digest(issuer['directory']),
        expected_embedded_crl_sha256=digest(previous_crl), expected_embedded_crl_number=0 if exact_crl else number,
        expected_minimum_crl=0,
        request_sha256=digest(request), target_crl_sha256=digest(issuer['crl']), target_crl_number=number,
        target_minimum_crl=number, not_before=NOW, not_after=NOW + 300)
    operation = maintenance.Operation(config, permit, clock=lambda: NOW)
    config.validate()
    with config.lock():
        operation._prepare(request)
    def capture():
        require(sorted(path.name for path in operations.iterdir()) == [permit['operation_id']], 'FIXTURE_OPERATION_CENSUS')
        return dict(schema=1, node=node, locator=locator_document, contract=config.contract(), metadata=config.material_snapshot(),
            files={name: packed(raw) for name, raw in dict(profile=profile.read_bytes(), directory=directory.read_bytes(),
                lock=lock.read_bytes(), publisher=executable.read_bytes(), **{'journal-key': config.journal_key}).items()},
            operations={permit['operation_id']: {path.name: packed(path.read_bytes()) for path in operation.root.iterdir()}},
            renewal=dict(format='none-declared/v1', coordinator=[], node=[]))
    pending = capture()
    first = operation.execute(request)
    settled = capture()
    duplicate = operation.execute(request)
    require(first['result'] == 'PASS' and duplicate['result'] == 'IDEMPOTENT' and
            first['applied_at'] == duplicate['applied_at'] and first['profile_sha256'] == duplicate['profile_sha256'],
            'NATIVE_MAINTENANCE_REPLAY')
    def refused(call):
        try:
            call()
        except (maintenance.MaintenanceError, profile_store.ProfileError, OSError):
            return
        raise ValueError('NATIVE_MAINTENANCE_UNSAFE_ACCEPTANCE')
    profile.chmod(0o666)
    refused(lambda: operation.execute(request))
    profile.chmod(0o640)
    os.chown(profile, 41001, 41003)
    refused(lambda: operation.execute(request))
    os.chown(profile, 0, 41003)
    retained = control / 'old.lock'
    lock.rename(retained)
    private_file(lock, b'')
    refused(lambda: operation.execute(request))
    lock.unlink()
    retained.rename(lock)
    retained = material / 'retained.json'
    profile.rename(retained)
    profile.symlink_to(retained)
    refused(lambda: operation.execute(request))
    profile.unlink()
    retained.rename(profile)
    journal = operation.root / 'journal.json'
    retained_journal = journal.read_bytes()
    journal.unlink()
    refused(lambda: operation.execute(request))
    private_file(journal, retained_journal)
    old_operations = control / 'retained-operations'
    operations.rename(old_operations)
    shutil.copytree(old_operations, operations)
    refused(lambda: operation.execute(request))
    shutil.rmtree(operations)
    old_operations.rename(operations)
    refused(lambda: maintenance.Operation(config, permit, clock=lambda: NOW + 4000).execute(request))
    require(operation.execute(request)['profile_sha256'] == first['profile_sha256'], 'NATIVE_PROFILE_CHANGED')
    return settled, pending


def root_fixture(issuer):
    manifest = parse((ROOT / 'deploy/control-ha/rehearsal-maintenance.json').read_bytes())
    require(os.geteuid() == 0 and Path('/.dockerenv').exists() and Path('/lab').is_dir(), 'ISOLATED_ROOT_REQUIRED')
    require(sys.version.split()[0] == manifest['python'] and cryptography.__version__ == manifest['cryptography'],
            'ROOT_FIXTURE_VERSION')
    settled, pending = {}, {}
    capture = encoded(dict(schema=1, purpose=PURPOSE, captured_at=NOW, nodes=sorted(NODES)))
    settled['capture.json'] = packed(capture)
    pending['capture.json'] = packed(capture)
    for node in NODES:
        complete, unfinished = create_node(Path('/lab') / node, node, issuer)
        settled[node + '.json'] = packed(encoded(complete))
        pending[node + '.json'] = packed(encoded(unfinished if node == 'gateway-ru' else complete))
    return dict(settled=settled, pending=pending, behavior=dict(native_prepare=True, native_commit=True,
        native_floor_reconcile=True, native_exact_crl=True,
        exact_retry=True, owner_mode_refused=True, replaced_lock_refused=True, symlink_refused=True,
        missing_journal_refused=True, relocated_operations_refused=True, expired_directory_refused=True,
        unchanged_profile=True))


def retain_evidence(recovered, root):
    from scripts.control_ha_maintenance_v1 import inspect_maintenance
    root.mkdir(mode=0o700)
    parts = recovered.artifacts['maintenance_state']
    for name, raw in parts.items():
        private_file(root / name, raw)
    retained = {name: (root / name).read_bytes() for name in parts}
    require(retained == parts, 'MAINTENANCE_EVIDENCE_CHANGED')
    result = inspect_maintenance(retained, recovered.artifacts['issuer_material'], now=NOW)
    require(result['settled'], 'MAINTENANCE_EVIDENCE_UNSETTLED')
    return dict(exact_private_evidence=True, native_activation=False, **result)


def source_snapshot(destination):
    selected = subprocess.run(['git', 'ls-files', '-z', '--', '*.py', 'deploy/control-ha/*.json'],
                              cwd=ROOT, capture_output=True, timeout=15, check=True).stdout
    names = {name.decode() for name in selected.split(b'\x00') if name}
    names.update(('scripts/control_ha_maintenance_fixture.py', 'scripts/control_ha_maintenance_v1.py',
                  'deploy/control-ha/rehearsal-maintenance.json'))
    for name in sorted(names):
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts and
                not relative.parts[0].startswith(('state', 'backup')) and
                not any(parent.is_symlink() for parent in (ROOT / relative, *(ROOT / relative).parents)),
                'ROOT_FIXTURE_UNSAFE_SOURCE')
        target = destination / relative
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        private_file(target, (ROOT / relative).read_bytes())


def native_capture(issuer):
    with tempfile.TemporaryDirectory(prefix='fc-ha-maintenance-source-') as temporary:
        source = Path(temporary)
        source_snapshot(source)
        return capture_container(issuer, source)


def capture_container(issuer, source):
    manifest = parse((ROOT / 'deploy/control-ha/rehearsal-maintenance.json').read_bytes())
    token = uuid.uuid4().hex
    name = 'fc-ha-maintenance-' + token
    environment = {key: value for key, value in os.environ.items() if not key.startswith(('DOCKER_', 'PG', 'FC_HA_'))}
    docker = ['docker', '--host', 'unix:///var/run/docker.sock']
    arguments = [*docker, 'run', '-i', '--name', name, '--label', LABEL + '=' + token, '--network', 'none', '--read-only',
        '--cap-drop', 'ALL', '--cap-add', 'CHOWN', '--cap-add', 'FOWNER', '--cap-add', 'DAC_OVERRIDE',
        '--security-opt', 'no-new-privileges', '--memory', '512m', '--cpus', '1', '--pids-limit', '128',
        '--tmpfs', '/lab:rw,nosuid,nodev,size=33554432,mode=755', '--tmpfs', '/tmp:rw,nosuid,nodev,size=16777216',
        '--mount', 'type=bind,src=' + str(source) + ',dst=/src,readonly', '--workdir', '/src',
        '--env', 'PYTHONDONTWRITEBYTECODE=1', '--entrypoint', 'python', manifest['image'],
        '-m', 'scripts.control_ha_maintenance_fixture']
    try:
        result = subprocess.run(arguments, input=encoded({name: packed(raw) for name, raw in issuer.items()}),
                                capture_output=True, timeout=45, env=environment)
        if result.returncode:
            with tempfile.NamedTemporaryFile(prefix='fc-ha-maintenance-error-', suffix='.log', delete=False) as output:
                output.write(result.stderr)
            raise ValueError('NATIVE_ROOT_FIXTURE_FAILED: ' + output.name)
        value = parse(result.stdout)
        return dict(settled={name: base64.b64decode(raw, validate=True) for name, raw in value['settled'].items()},
                    pending={name: base64.b64decode(raw, validate=True) for name, raw in value['pending'].items()},
                    behavior=value['behavior'])
    finally:
        inspection = subprocess.run([*docker, 'inspect', '--format', '{{json .Config.Labels}}', name],
                                    capture_output=True, timeout=15, env=environment)
        if inspection.returncode == 0:
            require(parse(inspection.stdout).get(LABEL) == token, 'ROOT_FIXTURE_NOT_OWNED')
            cleanup = subprocess.run([*docker, 'rm', '--force', name], capture_output=True, timeout=15, env=environment)
            require(cleanup.returncode == 0, 'ROOT_FIXTURE_CLEANUP_FAILED')


def artifacts_for_maintenance(fixture):
    artifacts = artifacts_for_receivers(fixture)
    capture = native_capture(artifacts['issuer_material'])
    artifacts['maintenance_state'] = capture['settled']
    return artifacts, capture


if __name__ == '__main__':
    issuer = {name: base64.b64decode(raw, validate=True) for name, raw in parse(sys.stdin.buffer.read(131073)).items()}
    print(json.dumps(root_fixture(issuer), sort_keys=True))
