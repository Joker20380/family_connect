"""Fixed disposable-role configuration contracts; never production profile reuse."""

import base64
import datetime
import re
import uuid

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.x509.oid import NameOID, ExtensionOID

from .contracts import canonical, digest, exact, fail, load

ROLES = ('awg', 'tcp', 'mesh', 'profile-reader', 'publisher', 'snapshot', 'monitoring', 'load-monitor')
DISABLED = ('mailbox', 'chat-services', 'renewal', 'restricted-sync', 'registry', 'control-plane-database')
INTERFACE = 'fcrh0'
SUBNET = '10.203.217.0/30'
ADDRESS = '10.203.217.1/30'
PEER_ADDRESS = '10.203.217.2/32'
PORTS = dict(awg=51827, tcp=4443, mesh=18444, monitoring=19727)
MTU = 1280
SNI = 'www.cloudflare.com'


def key32(value):
    try:
        decoded = base64.b64decode(value, validate=True)
        if len(decoded) != 32 or base64.b64encode(decoded).decode() != value:
            fail('role_key')
        return decoded
    except (ValueError, TypeError):
        fail('role_key')


def awg_config(raw):
    value = load(raw)
    exact(value, ('server_private_key', 'peer_public_key', 'scope'))
    if value['scope'] != 'DISPOSABLE_FLEET_REHEARSAL':
        fail('awg_scope')
    private = X25519PrivateKey.from_private_bytes(key32(value['server_private_key']))
    peer = key32(value['peer_public_key'])
    if private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw) == peer:
        fail('awg_peer_is_server')
    text = ('[Interface]\nPrivateKey = '+value['server_private_key']+'\nListenPort = 51827\n'
            'Jc = 4\nJmin = 40\nJmax = 70\nS1 = 81\nS2 = 93\nS3 = 17\nS4 = 23\n'
            'H1 = 1010123\nH2 = 2020234\nH3 = 3030345\nH4 = 4040456\n\n'
            '[Peer]\nPublicKey = '+value['peer_public_key']+'\nAllowedIPs = '+PEER_ADDRESS+'\n')
    return text.encode(), dict(peer_sha256=digest(peer), server_sha256=digest(private.public_key().public_bytes(
        serialization.Encoding.Raw,serialization.PublicFormat.Raw)),port=PORTS['awg'], address=ADDRESS, mtu=MTU)


def tcp_config(raw):
    value = load(raw)
    exact(value, ('scope', 'private_key', 'public_key', 'uuid', 'short_id', 'sni', 'destination'))
    if value['scope'] != 'DISPOSABLE_FLEET_REHEARSAL' or value['sni'] != SNI or value['destination'] != SNI+':443':
        fail('tcp_scope_or_destination')
    try:
        private = X25519PrivateKey.from_private_bytes(base64.urlsafe_b64decode(value['private_key']+'='))
        public = base64.urlsafe_b64encode(private.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode().rstrip('=')
        identity = uuid.UUID(value['uuid'])
        if (public != value['public_key'] or str(identity) != value['uuid'] or identity.version != 4
                or not re.fullmatch(r'[0-9a-f]{16}', value['short_id'])):
            fail('tcp_material')
    except (ValueError, TypeError):
        fail('tcp_material')
    config = dict(log=dict(loglevel='none'), inbounds=[dict(tag='rehearsal', listen='0.0.0.0', port=4443,
        protocol='vless', settings=dict(clients=[dict(id=value['uuid'], flow='xtls-rprx-vision')], decryption='none'),
        streamSettings=dict(network='tcp', security='reality', realitySettings=dict(show=False,
            dest=value['destination'], xver=0, serverNames=[SNI], privateKey=value['private_key'],
            shortIds=[value['short_id']])) )], outbounds=[dict(protocol='freedom', tag='direct')],
        routing=dict(rules=[dict(type='field', ip=['geoip:private'], outboundTag='blocked')]))
    config['outbounds'].append(dict(protocol='blackhole', tag='blocked'))
    config['routing']['rules'][0]['ip'] = ['10.0.0.0/8','172.16.0.0/12','192.168.0.0/16','127.0.0.0/8',
                                          '169.254.0.0/16','::1/128','fc00::/7','fe80::/10']
    return canonical(config)


def mesh_config(raw, *, instance_id, now, permit_expires_at):
    value = load(raw)
    exact(value, ('scope', 'instance_id', 'credentials'))
    if value['scope'] != 'DISPOSABLE_FLEET_REHEARSAL' or value['instance_id'] != instance_id:
        fail('mesh_scope')
    credentials = value['credentials']
    exact(credentials, ('certificate','private_key','authority','revocations','family','gateway','minimum_revision','minimum_crl'))
    if (any(not re.fullmatch(r'[0-9a-f]{32}', str(credentials[name])) for name in ('family','gateway'))
            or type(credentials['minimum_revision']) is not int or credentials['minimum_revision'] != 1
            or type(credentials['minimum_crl']) is not int or credentials['minimum_crl'] != 1):
        fail('mesh_fresh_identity_floor')
    try:
        authority = x509.load_pem_x509_certificate(credentials['authority'].encode())
        leaf = x509.load_pem_x509_certificate(credentials['certificate'].encode())
        private = serialization.load_pem_private_key(credentials['private_key'].encode(), password=None)
        revocations = x509.load_pem_x509_crl(credentials['revocations'].encode())
        if not isinstance(authority.public_key(), Ed25519PublicKey):
            fail('mesh_issuer_type')
        authority.verify_directly_issued_by(authority)
        leaf.verify_directly_issued_by(authority)
        authority.public_key().verify(revocations.signature, revocations.tbs_certlist_bytes)
        if (not authority.extensions.get_extension_for_oid(ExtensionOID.BASIC_CONSTRAINTS).value.ca
                or revocations.issuer != authority.subject
                or revocations.extensions.get_extension_for_oid(ExtensionOID.CRL_NUMBER).value.crl_number != credentials['minimum_crl']
                or any(entry.serial_number == leaf.serial_number for entry in revocations)
                or private.public_key() != leaf.public_key()):
            fail('mesh_profile_binding')
        for start, end in ((authority.not_valid_before_utc, authority.not_valid_after_utc),
                           (leaf.not_valid_before_utc, leaf.not_valid_after_utc),
                           (revocations.last_update_utc, revocations.next_update_utc)):
            if not start.timestamp() <= now < end.timestamp() <= permit_expires_at:
                fail('mesh_material_expiry')
        claims = [attribute.value for attribute in leaf.subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)]
        if sorted(claims) != sorted(['protocol=family-connect-5n3-test-v1', 'family='+credentials['family'],
                                    'role=gateway', 'revision=1']):
            fail('mesh_leaf_claims')
        names = leaf.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME).value
        identities = names.get_values_for_type(x509.UniformResourceIdentifier)
        if len(identities) != 1 or not re.fullmatch(r'urn:family-connect:identity:[0-9a-f]{128}', identities[0]):
            fail('mesh_identity_uri')
        identity = bytes.fromhex(identities[0].split(':')[-1])
        if (leaf.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw) != identity[32:]
                or digest(identity)[:32] != credentials['gateway']
                or leaf.subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)[0].value != credentials['gateway']):
            fail('mesh_identity_binding')
    except Exception:
        fail('mesh_profile_rejected')
    return canonical(credentials), dict(gateway=credentials['gateway'], family=credentials['family'],
                                       expires_at=int(min(authority.not_valid_after_utc.timestamp(),leaf.not_valid_after_utc.timestamp(),
                                                          revocations.next_update_utc.timestamp())), crl_number=1)


def publisher_config(raw):
    value = load(raw)
    exact(value, ('scope', 'token'))
    if (value['scope'] != 'DISPOSABLE_FLEET_REHEARSAL' or type(value['token']) is not str
            or not re.fullmatch(r'[A-Za-z0-9_.-]{16,4096}', value['token'])):
        fail('publisher_material')
    return ('YANDEX_TELEMOST_OAUTH_TOKEN='+value['token']+'\n').encode()


def ready_check(raw, binding, *, now, permit_expires_at):
    if len(raw) > 8192:
        fail('mesh_directory_bound')
    value = load(raw)
    exact(value, ('version','family','issued_at','expires_at','seeds'))
    if value['version'] != 1 or value['family'] != binding['family'] or type(value['seeds']) is not list or len(value['seeds']) != 1:
        fail('mesh_directory_binding')
    for name in ('issued_at','expires_at'):
        if not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,9})?(?:Z|[+-]\d\d:\d\d)', value[name]):
            fail('mesh_directory_time')
    issued = datetime.datetime.fromisoformat(value['issued_at']).timestamp()
    expires = datetime.datetime.fromisoformat(value['expires_at']).timestamp()
    if not issued <= now < expires <= permit_expires_at or expires-issued > 14400:
        fail('mesh_directory_expired')
    seed = value['seeds'][0]
    exact(seed, ('transport','join_url','gateway'))
    if (seed['gateway'] != binding['gateway'] or seed['transport'] != 'telemost-webrtc'
            or not re.fullmatch(r'https://telemost.yandex.ru/j/[A-Za-z0-9_-]{1,128}', seed['join_url'])):
        fail('mesh_seed_binding')
    return dict(sha256=digest(raw), expires_at=int(expires))
