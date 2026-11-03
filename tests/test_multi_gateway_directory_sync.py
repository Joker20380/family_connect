import base64
import copy
import json

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from control.friends.restricted import DOMAIN, PROTOCOL, iso, utc
from device_identity.device import DeviceIdentity
from test_activated_maintenance import Cluster, Rejected, atomic, canonical
import scheduled_evaluate as sync


@pytest.fixture
def fleet(tmp_path, monkeypatch):
    cluster = Cluster(tmp_path)
    node = cluster.nodes['RU']
    primary = cluster.nodes['NL']
    secondary = DeviceIdentity.generate()
    public = base64.b64decode(secondary.public_identity)
    key = Ed25519PrivateKey.from_private_bytes(secondary._identity.get_private_key()[32:])
    issuer = x509.load_pem_x509_certificate(primary.public_gateway()['authority'].encode())
    subject = x509.Name([x509.NameAttribute(NameOID.SERIAL_NUMBER, secondary.reference)] + [
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, claim) for claim in
        ('protocol='+PROTOCOL,'family='+cluster.family,'role=gateway','revision=1')])
    builder = (x509.CertificateBuilder().subject_name(subject).issuer_name(issuer.subject)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(utc(cluster.now-5)).not_valid_after(utc(cluster.now+14395))
        .add_extension(x509.BasicConstraints(ca=False,path_length=None),True)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(cluster.service.signing_key.public_key()),False)
        .add_extension(x509.SubjectAlternativeName([x509.UniformResourceIdentifier(
            'urn:family-connect:identity:'+public.hex())]),False))
    certificate = builder.sign(cluster.service.signing_key,None)
    manifest = json.loads(base64.b64decode(cluster.service.manifest['payload']))
    manifest['gateway'] = secondary.reference
    encoded = canonical(manifest)
    folder = node.live/'gateways'/sync.GATEWAYS[1]
    folder.mkdir(parents=True,mode=0o700)
    folder.parent.chmod(0o700)
    atomic(folder/'issuer.json',canonical(dict(payload=base64.b64encode(encoded).decode(),
        signature=base64.b64encode(cluster.root_key.sign(DOMAIN+encoded)).decode())))
    directory = json.loads((primary.live/'directory.json').read_bytes())
    directory['seeds'][0].update(gateway=secondary.reference,join_url='https://telemost.yandex.ru/j/second')
    atomic(folder/'directory.json',canonical(directory))
    profile = dict(primary.public_gateway(),certificate=certificate.public_bytes(Encoding.PEM).decode(),
                   gateway=secondary.reference)
    profiles = [primary.public_gateway(),profile]
    for item in profiles:
        item.pop('profile_sha256')
    directories = [(primary.live/'directory.json').read_bytes(),canonical(directory)]
    snapshots = {}
    for gateway_id, profile, raw in zip(sync.GATEWAYS,profiles,directories):
        snapshots[gateway_id] = dict(schema=1,profile=profile,directory=base64.b64encode(raw).decode())
    key_path, hosts = tmp_path/'key',tmp_path/'hosts'
    for path in (key_path,hosts):
        path.write_text('synthetic')
        path.chmod(0o600)
    routes = {gateway_id:dict(gateway=profile['gateway'],ssh=dict(key=str(key_path),known_hosts=str(hosts),
              target='reader@'+gateway_id+'.invalid')) for gateway_id,profile in zip(sync.GATEWAYS,profiles)}
    calls = []
    def read_gateway(**route):
        gateway_id = route['target'].split('@')[1].removesuffix('.invalid')
        calls.append(gateway_id)
        value = snapshots[gateway_id]
        if isinstance(value,Exception):
            raise value
        return copy.deepcopy(value)
    monkeypatch.setattr(sync,'read_gateway',read_gateway)
    cluster.fleet_node,cluster.routes,cluster.snapshots = node,routes,snapshots
    cluster.secondary_folder,cluster.calls = folder,calls
    return cluster


def readback(fleet):
    return {gateway_id:(fleet.fleet_node.live if gateway_id == sync.GATEWAYS[0] else fleet.secondary_folder)
            .joinpath('directory.json').read_bytes() for gateway_id in sync.GATEWAYS}


def fresh(fleet, gateway_id):
    entry = fleet.snapshots[gateway_id]
    directory = json.loads(base64.b64decode(entry['directory']))
    directory.update(issued_at=iso(fleet.now),expires_at=iso(fleet.now+3599))
    directory['seeds'][0]['join_url'] += '-fresh'
    entry['directory'] = base64.b64encode(canonical(directory)).decode()


def test_two_distinct_gateways_read_only_and_scoped_directory_sync(fleet):
    before = readback(fleet)
    profiles = {role:node.inspect() for role,node in fleet.nodes.items()}
    for gateway_id in sync.GATEWAYS:
        fresh(fleet,gateway_id)
    result = sync.inspect_gateways(fleet.fleet_node,fleet.routes)
    assert result['result'] == 'NOOP' and result['files_changed'] == 0
    assert readback(fleet) == before
    result = sync.inspect_gateways(fleet.fleet_node,fleet.routes,directory_only=True)
    assert result['result'] == 'DIRECTORIES_SYNCED' and result['files_changed'] == 2
    assert result['remote_writes'] == result['restarts'] == result['crl_publications'] == 0
    assert profiles == {role:node.inspect() for role,node in fleet.nodes.items()}
    assert all(node.barrier.starts == 0 for node in fleet.nodes.values())
    for gateway_id,raw in readback(fleet).items():
        assert raw == base64.b64decode(fleet.snapshots[gateway_id]['directory']) != before[gateway_id]
    assert sync.inspect_gateways(fleet.fleet_node,fleet.routes,directory_only=True)['files_changed'] == 0


@pytest.mark.parametrize('failed',sync.GATEWAYS)
def test_one_unreachable_gateway_preserves_other_sync_and_old_directory(fleet,failed):
    before = readback(fleet)
    other = next(gateway_id for gateway_id in sync.GATEWAYS if gateway_id != failed)
    fresh(fleet,other)
    fleet.snapshots[failed] = Rejected('GATEWAY_READ_UNAVAILABLE')
    result = sync.inspect_gateways(fleet.fleet_node,fleet.routes,directory_only=True)
    assert result['result'] == 'GATEWAY_CHECK_REQUIRED'
    assert result['gateways'][failed] == dict(result='FAIL_CLOSED',cause='GATEWAY_READ_UNAVAILABLE')
    assert result['gateways'][other]['result'] == 'DIRECTORY_SYNCED'
    assert readback(fleet)[failed] == before[failed]
    assert readback(fleet)[other] != before[other]


@pytest.mark.parametrize('defect',['gateway','family','authority','certificate','private_key','minimum_revision',
                                  'floor_ahead','floor_boolean','revocations','directory','expired_directory'])
def test_wrong_secondary_material_is_not_published_or_defaulted(fleet,defect):
    before = readback(fleet)
    secondary = fleet.snapshots[sync.GATEWAYS[1]]
    primary = fleet.snapshots[sync.GATEWAYS[0]]
    if defect in ('gateway','certificate'):
        secondary['profile'][defect] = primary['profile'][defect]
    elif defect == 'family':
        secondary['profile']['family'] = 'e'*32
    elif defect in ('authority','revocations','private_key'):
        secondary['profile'][defect] = 'not acceptable'
    elif defect == 'minimum_revision':
        secondary['profile'][defect] += 1
    elif defect.startswith('floor_'):
        secondary['profile']['minimum_crl'] = True if defect == 'floor_boolean' else 2
    elif defect == 'directory':
        secondary['directory'] = primary['directory']
    else:
        fleet.now += 3600
    result = sync.inspect_gateways(fleet.fleet_node,fleet.routes,directory_only=True)
    assert result['result'] == 'GATEWAY_CHECK_REQUIRED'
    assert result['gateways'][sync.GATEWAYS[1]]['result'] == 'FAIL_CLOSED'
    assert readback(fleet) == before


@pytest.mark.parametrize('defect',['unsigned','family','authority','minimum_revision','gateway','expired','symlink'])
def test_secondary_delegation_must_be_current_signed_distinct_and_shared(fleet,defect):
    path = fleet.secondary_folder/'issuer.json'
    before = readback(fleet)
    envelope = json.loads(path.read_bytes())
    payload = json.loads(base64.b64decode(envelope['payload']))
    if defect == 'symlink':
        path.rename(path.with_suffix('.saved'))
        path.symlink_to(path.with_suffix('.saved'))
    else:
        if defect == 'unsigned':
            envelope['signature'] = base64.b64encode(b'bad'*21+b'x').decode()
        else:
            if defect == 'expired':
                payload['expires_at'] = fleet.now
            elif defect == 'gateway':
                payload[defect] = fleet.gateway
            elif defect == 'family':
                payload[defect] = 'e'*32
            elif defect == 'minimum_revision':
                payload[defect] += 1
            else:
                payload[defect] = 'wrong authority'
            raw = canonical(payload)
            envelope = dict(payload=base64.b64encode(raw).decode(),
                            signature=base64.b64encode(fleet.root_key.sign(DOMAIN+raw)).decode())
        atomic(path,canonical(envelope))
    result = sync.inspect_gateways(fleet.fleet_node,fleet.routes,directory_only=True)
    assert result['gateways'][sync.GATEWAYS[1]]['result'] == 'FAIL_CLOSED'
    assert readback(fleet) == before


@pytest.mark.parametrize('defect',['older','same_time_conflict','offset_same_time_conflict'])
def test_directory_rollback_and_conflict_do_not_replace_current(fleet,defect):
    before = readback(fleet)
    gateway_id = sync.GATEWAYS[1]
    raw = json.loads(base64.b64decode(fleet.snapshots[gateway_id]['directory']))
    raw['seeds'][0]['join_url'] += '-changed'
    if defect == 'older':
        raw['issued_at'] = iso(fleet.now-2)
        raw['expires_at'] = iso(fleet.now+3598)
    elif defect == 'offset_same_time_conflict':
        raw['issued_at'] = raw['issued_at'].replace('Z','+00:00')
    fleet.snapshots[gateway_id]['directory'] = base64.b64encode(canonical(raw)).decode()
    result = sync.inspect_gateways(fleet.fleet_node,fleet.routes,directory_only=True)
    assert result['gateways'][gateway_id]['cause'] in ('DIRECTORY_ROLLBACK','DIRECTORY_CONFLICT')
    assert readback(fleet) == before


def test_maintenance_fence_prevents_reads_and_directory_changes(fleet):
    before = readback(fleet)
    atomic(fleet.fleet_node.state/'owner.json',canonical(dict(operation_id='synthetic-maintenance')))
    assert sync.inspect_gateways(fleet.fleet_node,fleet.routes,directory_only=True) == dict(
        result='MAINTENANCE_IN_PROGRESS',mutations=0)
    assert not fleet.calls and readback(fleet) == before


def test_nanosecond_directory_and_maintenance_warning_are_preserved(fleet):
    fleet.now += 10000.75
    for gateway_id in sync.GATEWAYS:
        entry = fleet.snapshots[gateway_id]
        directory = json.loads(base64.b64decode(entry['directory']))
        directory.update(issued_at=iso(int(fleet.now)).replace('Z','.5Z'),expires_at=iso(int(fleet.now)+3599))
        entry['directory'] = base64.b64encode(canonical(directory)).decode()
    result = sync.inspect_gateways(fleet.fleet_node,fleet.routes,directory_only=True)
    assert result['result'] == 'DIRECTORIES_SYNCED'
    assert all(value['credentials']['result'] == 'MAINTENANCE_REQUIRED' for value in result['gateways'].values())


def test_wrong_san_identity_cannot_use_valid_family_signature(fleet):
    original = x509.load_pem_x509_certificate(fleet.snapshots[sync.GATEWAYS[1]]['profile']['certificate'].encode())
    replacement = (x509.CertificateBuilder().subject_name(original.subject).issuer_name(original.issuer)
        .public_key(original.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(original.not_valid_before_utc).not_valid_after(original.not_valid_after_utc))
    for extension in original.extensions:
        value = extension.value
        if isinstance(value,x509.SubjectAlternativeName):
            value = x509.SubjectAlternativeName([x509.UniformResourceIdentifier('urn:family-connect:identity:'+'a'*128)])
        replacement = replacement.add_extension(value,extension.critical)
    certificate = replacement.sign(fleet.service.signing_key,None)
    fleet.snapshots[sync.GATEWAYS[1]]['profile']['certificate'] = certificate.public_bytes(Encoding.PEM).decode()
    result = sync.inspect_gateways(fleet.fleet_node,fleet.routes)
    assert result['gateways'][sync.GATEWAYS[1]]['cause'] == 'GATEWAY_CERTIFICATE_IDENTITY'


def test_revoked_gateway_leaf_is_never_published(fleet):
    node = fleet.fleet_node
    issuer = x509.load_pem_x509_certificate(fleet.snapshots[sync.GATEWAYS[0]]['profile']['authority'].encode())
    leaf = x509.load_pem_x509_certificate(fleet.snapshots[sync.GATEWAYS[1]]['profile']['certificate'].encode())
    revoked = (x509.RevokedCertificateBuilder().serial_number(leaf.serial_number)
               .revocation_date(utc(fleet.now-1)).build())
    crl = (x509.CertificateRevocationListBuilder().issuer_name(issuer.subject)
           .last_update(utc(fleet.now-1)).next_update(utc(fleet.now+14395))
           .add_extension(x509.CRLNumber(2),False).add_revoked_certificate(revoked)
           .sign(fleet.service.signing_key,None).public_bytes(Encoding.PEM).decode())
    atomic(node.live/'revocations.pem',crl.encode())
    for entry in fleet.snapshots.values():
        entry['profile']['revocations'] = crl
    before = readback(fleet)
    result = sync.inspect_gateways(node,fleet.routes,directory_only=True)
    assert result['gateways'][sync.GATEWAYS[1]]['cause'] == 'GATEWAY_REVOKED'
    assert readback(fleet) == before


def test_cli_uses_explicit_routes_and_returns_partial_failure(fleet,monkeypatch,capsys,tmp_path):
    path = tmp_path/'routes.json'
    atomic(path,canonical(dict(schema=1,gateways=fleet.routes)))
    primary = fleet.routes[sync.GATEWAYS[0]]['ssh']
    fleet.fleet_node.snapshot_target = primary['target']
    monkeypatch.setattr(sync,'construct',lambda unused:(fleet.fleet_node,'source'))
    monkeypatch.setattr(sync.resource,'setrlimit',lambda *unused:None)
    monkeypatch.setattr(sync.os,'umask',lambda unused:None)
    monkeypatch.setattr(sync.sys,'argv',['scheduled_evaluate.py','--config',str(tmp_path/'unused.json'),
        '--ssh-key',primary['key'],'--known-hosts',primary['known_hosts'],'--gateway-routes',str(path),'--directory-only'])
    sync.main()
    assert json.loads(capsys.readouterr().out)['result'] == 'DIRECTORIES_SYNCED'
    fleet.snapshots[sync.GATEWAYS[1]] = RuntimeError('private-token-must-not-appear')
    with pytest.raises(SystemExit) as error:
        sync.main()
    assert error.value.code == 75
    output = capsys.readouterr().out
    assert 'private-token' not in output and 'join_url' not in output and 'certificate' not in output
    assert json.loads(output)['gateways'][sync.GATEWAYS[1]] == dict(result='FAIL_CLOSED',cause='UNKNOWN')


@pytest.mark.parametrize('defect',[None,'missing','extra','duplicate_identity','duplicate_host','primary_route',
                                  'unknown_field','shell_target','schema_boolean'])
def test_routes_require_exact_members_and_preserve_primary_pins(fleet,defect):
    primary_route = copy.deepcopy(fleet.routes[sync.GATEWAYS[0]]['ssh'])
    value = dict(schema=1,gateways=copy.deepcopy(fleet.routes))
    secondary = value['gateways'][sync.GATEWAYS[1]]
    if defect == 'missing':
        del value['gateways'][sync.GATEWAYS[1]]
    elif defect == 'extra':
        value['gateways']['nl-amsterdam-3'] = secondary
    elif defect == 'duplicate_identity':
        secondary['gateway'] = fleet.gateway
    elif defect == 'duplicate_host':
        secondary['ssh']['target'] = 'other@'+primary_route['target'].split('@')[1]
    elif defect == 'primary_route':
        value['gateways'][sync.GATEWAYS[0]]['ssh']['target'] = 'reader@elsewhere.invalid'
    elif defect == 'unknown_field':
        secondary['shell'] = 'not permitted'
    elif defect == 'shell_target':
        secondary['ssh']['target'] += ';command'
    elif defect == 'schema_boolean':
        value['schema'] = True
    if defect is None:
        assert sync.gateway_routes(canonical(value),primary_route) == fleet.routes
    else:
        with pytest.raises(Rejected):
            sync.gateway_routes(canonical(value),primary_route)
