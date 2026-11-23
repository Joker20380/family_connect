"""Disposable bytes for bundle qualification, not a complete external authority model."""
from types import SimpleNamespace
import secrets

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from control.friends.access import Access
from control.friends import pseudonyms, restricted
from scripts.control_ha_import import EXTERNAL_ROLES, digest, encoded
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_rehearsal import private_file, require
from scripts.referral_postgres_rehearsal import NOW

OPAQUE_PROBES = frozenset(('admission', 'maintenance_state', 'node_allocations', 'receiver_state'))


def artifacts_for(fixture):
    parts = {role: {'opaque-probe': encoded(dict(purpose='synthetic-byte-probe/not-runtime-authority',
              checkpoint=CHECKPOINT, role=role, nonce=secrets.token_hex(32)))} for role in OPAQUE_PROBES}
    hmac_key, legacy_key = secrets.token_bytes(32), secrets.token_bytes(32)
    aliases = pseudonyms.prepare(dict(device=[fixture.device.reference, fixture.child.reference], panel_event=[]),
                                hmac_key, legacy_key=legacy_key)
    parts['aliases'] = {'manifest': encoded(aliases.document), 'current-hmac': hmac_key, 'legacy-hmac': legacy_key}
    parts['sender_policy'] = {'support.json': (fixture.paths['registry'].parent / 'support.json').read_bytes()}
    parts['routing_files'] = {path.name: path.read_bytes() for path in fixture.pending['routing'].directory.iterdir()}
    parts['issuer_material'] = dict(zip(('runtime-key', 'referral-secret', 'directory', 'crl', 'delegation'),
        (fixture.service.signing_key.private_bytes_raw(), fixture.referral_secret, fixture.service.seed_source(),
         fixture.service.crl_source(), encoded(fixture.service.manifest)), strict=True))
    require(set(parts) == EXTERNAL_ROLES, 'FIXTURE_ROLE_COVERAGE')
    return parts


def reconstruct(fixture, recovered, anchor, root):
    root.mkdir(mode=0o700)
    paths = {store: root / (store + '.sqlite') for store in recovered.stores}
    for store, path in paths.items():
        private_file(path, recovered.stores[store])
    routing = root / 'gateway-routing'
    routing.mkdir(mode=0o700)
    for name, raw in recovered.artifacts['routing_files'].items():
        private_file(routing / name, raw)
    private_file(root / 'support.json', recovered.artifacts['sender_policy']['support.json'])
    issuer = recovered.artifacts['issuer_material']
    access = Access(paths['registry'], clock=lambda: NOW)
    fixture.access = access
    fixture.service = restricted.RestrictedReadiness(access, manifest=parse(issuer['delegation']), anchor=anchor,
        signing_key=Ed25519PrivateKey.from_private_bytes(issuer['runtime-key']),
        seed_source=lambda: issuer['directory'], crl_source=lambda: issuer['crl'])
    fixture.referral_secret = issuer['referral-secret']
    fixture.paths = paths
    fixture.stores = recovered.stores
    fixture.external = recovered.references
    fixture.expected = {role: digest(raw) for role, raw in recovered.references.items()}
    fixture.bootstrap = recovered.bootstrap
    fixture.pending['routing'] = SimpleNamespace(root=root)
    return fixture
