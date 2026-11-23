from copy import deepcopy
import json
import sqlite3
import ssl

import pytest

from control.friends import control_shadow as shadow, transport_policy
from control.friends.control_quorum import QuorumUnavailable, ShadowConflict, ShadowQuorum, encoded, KEY
from test_paid_beta import NOW, event, registry, snapshot

KEY_MATERIAL = bytes(range(32))
ENDPOINTS = ['https://127.0.0.1:' + str(port) for port in (32101, 32102, 32103)]


def capture(registry, observed=NOW):
    return shadow.capture(registry[0].path, KEY_MATERIAL, observed_at=observed)


def test_fingerprint_is_readonly_private_and_deterministic(registry):
    event(registry)
    before = snapshot(registry[0])
    manifest = capture(registry)
    assert manifest == capture(registry)
    assert snapshot(registry[0]) == before
    text = json.dumps(manifest)
    for private in (registry[1].reference, registry[1].public_identity,
                    registry[1].wireguard_public_key, 'synthetic-receipt', 'event-00000001'):
        assert private not in text
    assert shadow.validate(manifest, KEY_MATERIAL, now=NOW)['mode'] == 'shadow-only'
    with pytest.raises(ValueError):
        transport_policy.validate(manifest, 'gateway-ru', NOW)


def test_isolated_backup_matches_and_revoke_changes_projection(registry, tmp_path):
    event(registry)
    original = capture(registry)
    with sqlite3.connect(registry[0].path) as source, sqlite3.connect(tmp_path / 'copy.db') as target:
        source.backup(target)
    restored = shadow.capture(tmp_path / 'copy.db', KEY_MATERIAL, observed_at=NOW)
    assert shadow.compare(original, restored, KEY_MATERIAL, now=NOW)['matches']
    event(registry, 'revoke', 'ha-revoke')
    revoked = capture(registry)
    assert not shadow.compare(original, revoked, KEY_MATERIAL, now=NOW)['matches']
    assert all(original['payload']['decisions'][node] != revoked['payload']['decisions'][node]
               for node in transport_policy.NODES)


def test_all_tables_and_nodes_share_one_sqlite_snapshot(registry, monkeypatch):
    with sqlite3.connect(registry[0].path) as database:
        database.execute('PRAGMA journal_mode=WAL')
    before = capture(registry)
    original = transport_policy.read_snapshot
    written = []

    def interleaved(database, node, now):
        if not written:
            with sqlite3.connect(registry[0].path) as writer:
                writer.execute('UPDATE devices SET revoked=1')
            written.append(True)
        return original(database, node, now)

    monkeypatch.setattr(transport_policy, 'read_snapshot', interleaved)
    assert capture(registry) == before
    assert capture(registry) != before


@pytest.mark.parametrize('offset,valid', [(0, True), (119, True), (120, False), (-5, True), (-6, False)])
def test_freshness_never_extends_a_snapshot(registry, offset, valid):
    manifest = capture(registry)
    if valid:
        shadow.validate(manifest, KEY_MATERIAL, now=NOW + offset)
    else:
        with pytest.raises(ValueError, match='INVALID_SHADOW'):
            shadow.validate(manifest, KEY_MATERIAL, now=NOW + offset)


def test_authentication_and_same_observation_required(registry):
    manifest = capture(registry)
    with pytest.raises(ValueError):
        shadow.validate(manifest, b'x' * 32, now=NOW)
    changed = deepcopy(manifest)
    changed['payload']['mode'] = 'authority'
    with pytest.raises(ValueError):
        shadow.validate(changed, KEY_MATERIAL, now=NOW)
    with pytest.raises(ValueError, match='SAME_OBSERVATION'):
        shadow.compare(manifest, capture(registry, NOW + 1), KEY_MATERIAL, now=NOW + 1)


def test_empty_missing_partial_schema_and_symlink_fail(registry, tmp_path):
    link = tmp_path / 'link.db'
    link.symlink_to(registry[0].path)
    with pytest.raises(ValueError, match='SYMLINK'):
        shadow.capture(link, KEY_MATERIAL, observed_at=NOW)
    with pytest.raises(ValueError):
        shadow.capture(tmp_path / 'absent.db', KEY_MATERIAL, observed_at=NOW)
    assert not (tmp_path / 'absent.db').exists()
    with sqlite3.connect(registry[0].path) as database:
        database.execute('DROP TABLE paid_beta_events')
    with pytest.raises(ValueError, match='INCOMPLETE'):
        capture(registry)


@pytest.mark.parametrize('limit,value,reason', [('MAX_ROWS', 1, 'ROW_LIMIT'), ('MAX_TABLES', 1, 'TABLE_LIMIT')])
def test_bounded_snapshot(registry, monkeypatch, limit, value, reason):
    monkeypatch.setattr(shadow, limit, value)
    with pytest.raises(ValueError, match=reason):
        capture(registry)


def test_capture_deadline(registry, monkeypatch):
    ticks = iter((0, 11))
    monkeypatch.setattr(shadow.time, 'monotonic', lambda: next(ticks, 11))
    with pytest.raises((ValueError, sqlite3.OperationalError)):
        capture(registry)


class MemoryQuorum(ShadowQuorum):
    def __init__(self):
        self.value, self.revision, self.writes = None, 0, 0
        self.lost_ack, self.unavailable, self.concurrent = False, False, None

    def read(self):
        if self.unavailable:
            raise QuorumUnavailable('synthetic')
        return self.value, self.revision

    def replace(self, manifest, revision):
        self.writes += 1
        if self.concurrent is not None:
            self.value, self.revision = self.concurrent, self.revision + 1
        if revision != self.revision:
            return False
        self.value, self.revision = manifest, revision + 1
        if self.lost_ack:
            raise QuorumUnavailable('synthetic-ack-loss')
        return True


def test_publish_is_idempotent_and_refuses_replay_or_same_time_conflict(registry):
    quorum = MemoryQuorum()
    manifest = capture(registry)
    assert quorum.publish(manifest, KEY_MATERIAL, now=NOW) == 'published'
    assert quorum.publish(manifest, KEY_MATERIAL, now=NOW) == 'unchanged'
    with pytest.raises(ShadowConflict):
        quorum.publish(capture(registry, NOW - 1), KEY_MATERIAL, now=NOW)
    event(registry)
    with pytest.raises(ShadowConflict):
        quorum.publish(capture(registry), KEY_MATERIAL, now=NOW)
    assert quorum.writes == 1


def test_lost_ack_is_reconciled_without_second_write(registry):
    quorum = MemoryQuorum()
    quorum.lost_ack = True
    assert quorum.publish(capture(registry), KEY_MATERIAL, now=NOW) == 'confirmed-by-readback'
    assert quorum.writes == 1


def test_no_quorum_does_not_try_a_write(registry):
    quorum = MemoryQuorum()
    quorum.unavailable = True
    with pytest.raises(QuorumUnavailable):
        quorum.publish(capture(registry), KEY_MATERIAL, now=NOW)
    assert quorum.writes == 0


def test_concurrent_writer_is_not_overwritten(registry):
    quorum = MemoryQuorum()
    quorum.concurrent = capture(registry, NOW + 1)
    with pytest.raises(ShadowConflict):
        quorum.publish(capture(registry), KEY_MATERIAL, now=NOW)
    assert quorum.value == quorum.concurrent


@pytest.mark.parametrize('bad', ['http://127.0.0.1:2379', 'https://example.invalid:2379',
    'https://127.0.0.1:2379/path', 'https://user@127.0.0.1:2379', 'https://127.0.0.1:2379?x=1'])
def test_only_loopback_mtls_endpoints(bad):
    with pytest.raises(ValueError):
        ShadowQuorum([bad, *ENDPOINTS[1:]], ssl.create_default_context())


def test_duplicates_and_unverified_tls_are_forbidden():
    with pytest.raises(ValueError):
        ShadowQuorum([ENDPOINTS[0]] * 3, ssl.create_default_context())
    with pytest.raises(ValueError):
        ShadowQuorum(ENDPOINTS, ssl._create_unverified_context())


def test_etcd_uses_linearizable_reads_and_cas(registry, monkeypatch):
    quorum = ShadowQuorum(ENDPOINTS, ssl.create_default_context())
    calls = []

    def request(route, payload, **options):
        calls.append((route, payload))
        return {'succeeded': True} if route.endswith('txn') else {}

    monkeypatch.setattr(quorum, 'request', request)
    assert quorum.read() == (None, 0)
    assert calls[-1] == ('/v3/kv/range', {'key': encoded(KEY), 'serializable': False})
    assert quorum.replace(capture(registry), 0)
    assert calls[-1][1]['compare'][0] == dict(key=encoded(KEY), target='VERSION', result='EQUAL', version='0')
    assert quorum.replace(capture(registry), 14)
    assert calls[-1][1]['compare'][0] == dict(key=encoded(KEY), target='MOD', result='EQUAL', mod_revision='14')
    assert calls[-1][1]['failure'] == []


def test_blob_fingerprints_are_private_and_schema_changes_detected(registry):
    with registry[0].db() as database:
        database.execute('CREATE TABLE shadow_test(value BLOB)')
        database.execute('INSERT INTO shadow_test VALUES (?)', (b'private-test-blob',))
    first = capture(registry)
    assert 'private-test-blob' not in json.dumps(first)
    with registry[0].db() as database:
        database.execute('CREATE INDEX shadow_test_index ON shadow_test(value)')
    second = capture(registry)
    assert first['payload']['tables'] == second['payload']['tables']
    assert first['payload']['schema_hmac'] != second['payload']['schema_hmac']


def test_expired_manifest_cannot_be_republished_even_idempotently(registry):
    quorum = MemoryQuorum()
    manifest = capture(registry)
    quorum.publish(manifest, KEY_MATERIAL, now=NOW)
    with pytest.raises(ValueError):
        quorum.publish(manifest, KEY_MATERIAL, now=NOW + 120)
    assert quorum.writes == 1


def test_disposable_certificates_have_strict_x509_extensions(tmp_path):
    from cryptography import x509
    from scripts.control_ha_rehearsal import certificates
    certificates(tmp_path)
    authority = x509.load_pem_x509_certificate((tmp_path / 'ca.pem').read_bytes())
    assert authority.extensions.get_extension_for_class(x509.KeyUsage).value.key_cert_sign
    for label in ('client', 'node0', 'node1', 'node2'):
        certificate = x509.load_pem_x509_certificate((tmp_path / (label + '.pem')).read_bytes())
        certificate.verify_directly_issued_by(authority)
        assert certificate.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier).value.key_identifier
        assert not certificate.extensions.get_extension_for_class(x509.KeyUsage).value.key_cert_sign
        assert (tmp_path / (label + '.key')).stat().st_mode & 0o777 == 0o600


def test_rehearsal_rejects_unpinned_binary_before_creating_state(tmp_path):
    from scripts.control_ha_rehearsal import Rehearsal
    binary = tmp_path / 'not-etcd'
    binary.write_bytes(b'not a binary')
    with pytest.raises(ValueError, match='PIN_MISMATCH'):
        Rehearsal(binary, tmp_path / 'state')
    assert not (tmp_path / 'state').exists()


@pytest.mark.parametrize('status,body', [(302, b'{}'), (200, b'{}'), (200, b'{'),
    (503, b'{"error":"unavailable"}'), (200, b'x' * (shadow.MAX_BYTES * 2 + 1))])
def test_invalid_http_responses_are_not_quorum_ack(monkeypatch, status, body):
    from control.friends import control_quorum
    calls = []

    class Connection:
        def __init__(self, host, port, **options):
            calls.append(port)

        def request(self, *arguments):
            pass

        def getresponse(self):
            return type('Response', (), {'status': status, 'read': lambda self, size: body})()

        def close(self):
            pass

    monkeypatch.setattr(control_quorum.http.client, 'HTTPSConnection', Connection)
    quorum = ShadowQuorum(ENDPOINTS, ssl.create_default_context())
    with pytest.raises(QuorumUnavailable):
        quorum.read(first_only=True)
    assert len(calls) == 1
    with pytest.raises(QuorumUnavailable):
        quorum.read()
    assert len(calls) == 4


def test_invalid_signed_projection_is_not_a_valid_shadow_manifest(registry):
    manifest = capture(registry)
    manifest['payload']['decisions']['gateway-ru']['rows'] = True
    manifest['mac'] = shadow.digest(KEY_MATERIAL, 'manifest', manifest['payload'])
    with pytest.raises(ValueError, match='PROJECTIONS'):
        shadow.validate(manifest, KEY_MATERIAL, now=NOW)
