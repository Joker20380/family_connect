import base64
from copy import deepcopy
import inspect
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from scripts import control_ha_forward_archive as archive
from scripts import control_ha_forward_checkpoint as forward
from scripts.control_ha_import import ImportRejected, digest, encoded
from scripts.control_ha_recovery_bundle import parse
from test_control_ha_forward_checkpoint import candidate, current, native_current, verify as verify_candidate


def fingerprint(qualified):
    return digest(encoded(dict(stores={name: digest(raw) for name, raw in qualified.current.stores.items()},
        artifacts={role: {name: digest(raw) for name, raw in parts.items()}
                   for role, parts in qualified.current.artifacts.items()},
        references={name: digest(raw) for name, raw in qualified.current.references.items()},
        bootstrap=digest(qualified.current.bootstrap),
        history=qualified.history.manifest_sha256,
        sources={node: dict(configuration=digest(parts['configuration']),
                           files={name: digest(raw) for name, raw in parts['files'].items()})
                 for node, parts in qualified.source_materials.items()},
        publications={name: digest(raw) for name, raw in qualified.publications.items()},
        authorities={name: digest(raw) for name, raw in qualified.authorities.items()})))


@pytest.fixture
def packed(candidate):
    return packed_for(candidate)


def packed_for(candidate):
    arguments = candidate['arguments']
    material = {name: arguments[name] for name in
                ('recovery_bundle', 'history_bundle', 'publications', 'authorities', 'source_materials')}
    key = secrets.token_bytes(32)
    bundle, checksum = archive.seal(candidate['request'], candidate['signature'], key, **material)
    external = {name: arguments[name] for name in ('minimum_sequence', 'minimum_crl',
                'minimum_authority_sequences', 'now', 'recovery_key', 'history_key', 'anchor')}
    external.update(expected_request_sha256=candidate['expected_request_sha256'], trusted_key=candidate['trusted_key'])
    return dict(bundle=bundle, key=key, checksum=checksum, external=deepcopy(external))


def verify(packed, **overrides):
    return archive.verify(packed['bundle'], packed['key'], packed['checksum'], **(packed['external'] | overrides))


def plaintext(packed):
    bundle, offset = packed['bundle'], len(archive.MAGIC)
    return AESGCM(packed['key']).decrypt(bundle[offset:offset + 12], bundle[offset + 12:],
        archive.MAGIC + archive.PURPOSE.encode() + bytes.fromhex(packed['external']['expected_request_sha256']))


def replace_plaintext(packed, raw):
    nonce = secrets.token_bytes(12)
    packed['bundle'] = archive.MAGIC + nonce + AESGCM(packed['key']).encrypt(nonce, raw,
        archive.MAGIC + archive.PURPOSE.encode() + bytes.fromhex(packed['external']['expected_request_sha256']))
    packed['checksum'] = digest(packed['bundle'])


def change_sidecars(packed, change):
    parts = archive.unframe(plaintext(packed))
    document = parse(parts['sidecars'])
    change(document)
    parts['sidecars'] = encoded(document)
    replace_plaintext(packed, archive.frame(parts))


def test_exact_roundtrip_preserves_all_inputs_and_permissions(candidate, packed):
    expected = verify_candidate(candidate)
    qualified = verify(packed)
    assert fingerprint(qualified) == fingerprint(expected)
    assert qualified.summary() == expected.summary()
    assert qualified.summary()['activation'] == 'FORBIDDEN'
    assert qualified.summary()['full_recovery'] == 'NOT_QUALIFIED'
    assert qualified.summary()['database_import'] == qualified.summary()['host_resume'] == 'NOT_AUTHORIZED'
    assert '/not-followed' not in repr(qualified)


def test_fresh_process_reads_only_archive_and_external_custody_after_source_removal(candidate, packed, tmp_path):
    expected = fingerprint(verify_candidate(candidate))
    for root in candidate['current']['roots'].values():
        shutil.rmtree(root)
    bundle_path = tmp_path / 'checkpoint.enc'
    bundle_path.write_bytes(packed.pop('bundle'))
    bundle_path.chmod(0o600)
    inputs = dict(external=packed['external'], key=packed['key'].hex(), checksum=packed['checksum'])
    for name in ('trusted_key', 'anchor', 'history_key', 'recovery_key'):
        inputs['external'][name] = inputs['external'][name].hex()
    candidate.clear()
    repository = Path(__file__).resolve().parents[1]
    code = f'''import json,sys
from pathlib import Path
sys.path.insert(0,{str(repository)!r})
from scripts import control_ha_forward_archive as archive
from scripts.control_ha_import import digest,encoded
{inspect.getsource(fingerprint)}
inputs=json.load(sys.stdin)
external=inputs['external']
for name in ('trusted_key','anchor','history_key','recovery_key'):
    external[name]=bytes.fromhex(external[name])
qualified=archive.verify(Path(sys.argv[1]).read_bytes(),bytes.fromhex(inputs['key']),inputs['checksum'],**external)
print(json.dumps(dict(fingerprint=fingerprint(qualified),summary=qualified.summary())))
'''
    result = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(bundle_path)],
        input=json.dumps(inputs), text=True, capture_output=True, check=True, timeout=60, cwd=tmp_path)
    received = json.loads(result.stdout)
    assert received['fingerprint'] == expected
    assert received['summary']['activation'] == 'FORBIDDEN'
    assert not result.stderr


def test_encrypted_archive_contains_no_keys_or_plaintext_material(candidate, packed):
    raw = plaintext(packed)
    for key in (packed['key'], packed['external']['recovery_key'], packed['external']['history_key']):
        assert key not in raw
        assert key.hex().encode() not in raw
        assert base64.b64encode(key) not in raw
    for node in forward.NODES:
        material = candidate['arguments']['source_materials'][node]
        assert material['configuration'] not in packed['bundle']
    assert candidate['request'] not in packed['bundle']
    assert b'/not-followed' not in packed['bundle']


def test_nonce_is_fresh_and_ciphertext_has_its_own_pin(candidate, packed):
    arguments = candidate['arguments']
    material = {name: arguments[name] for name in
                ('recovery_bundle', 'history_bundle', 'publications', 'authorities', 'source_materials')}
    original_checksum = packed['checksum']
    second, checksum = archive.seal(candidate['request'], candidate['signature'], packed['key'], **material)
    assert second != packed['bundle'] and checksum != original_checksum
    packed['bundle'] = second
    with pytest.raises(ImportRejected, match='FORWARD_ARCHIVE_DIGEST'):
        verify(packed)
    packed['checksum'] = checksum
    verify(packed)


@pytest.mark.parametrize('key', [None, b'', b'k' * 31, b'k' * 33, bytearray(b'k' * 32), b'k' * 32])
def test_missing_malformed_or_wrong_outer_key_refuses(packed, key):
    packed['key'] = key
    with pytest.raises(ImportRejected, match='FORWARD_ARCHIVE_(KEY|AUTHENTICATION)'):
        verify(packed)


@pytest.mark.parametrize('kind', ['checksum', 'request-pin', 'bad-checksum-shape', 'bad-pin-shape'])
def test_independent_pins_are_not_taken_from_the_archive(packed, kind):
    if kind == 'checksum':
        packed['checksum'] = '0' * 64
    elif kind == 'bad-checksum-shape':
        packed['checksum'] = None
    else:
        packed['external']['expected_request_sha256'] = '0' * 64 if kind == 'request-pin' else 'bad'
    with pytest.raises(ImportRejected, match='FORWARD_ARCHIVE_(DIGEST|EXTERNAL_PINS|AUTHENTICATION)'):
        verify(packed)


@pytest.mark.parametrize('kind', ['magic', 'truncated', 'ciphertext', 'nonce', 'appended'])
def test_damage_refuses_even_if_ciphertext_is_repinned(packed, kind):
    bundle = packed['bundle']
    if kind == 'magic':
        packed['bundle'] = b'X' + bundle[1:]
    elif kind == 'truncated':
        packed['bundle'] = bundle[:-19]
    elif kind == 'appended':
        packed['bundle'] += b'ignored'
    else:
        offset = len(archive.MAGIC) if kind == 'nonce' else len(bundle) - 1
        packed['bundle'] = bundle[:offset] + bytes([bundle[offset] ^ 1]) + bundle[offset + 1:]
    packed['checksum'] = digest(packed['bundle'])
    with pytest.raises(ImportRejected, match='FORWARD_ARCHIVE_(FORMAT|AUTHENTICATION)'):
        verify(packed)


@pytest.mark.parametrize('kind', ['zero-length', 'huge-length', 'truncated-length', 'truncated-frame', 'trailing'])
def test_authenticated_but_malformed_frames_refuse(packed, kind):
    raw = plaintext(packed)
    if kind == 'zero-length':
        raw = bytes(8) + raw[8:]
    elif kind == 'huge-length':
        raw = (2**64 - 1).to_bytes(8, 'big') + raw[8:]
    elif kind == 'truncated-length':
        raw = raw[:7]
    elif kind == 'truncated-frame':
        raw = raw[:-1]
    else:
        raw += b'unclaimed'
    replace_plaintext(packed, raw)
    with pytest.raises(ImportRejected, match='FORWARD_ARCHIVE_(FRAME_BOUNDS|TRAILING_BYTES)'):
        verify(packed)


@pytest.mark.parametrize('change', [dict(version=True), dict(version=2), dict(purpose='restore'),
    dict(trusted_key='self-signed'), dict(minimum_sequence=0), dict(source_materials={}),
    dict(publications={}), dict(authorities={})])
def test_archive_cannot_supply_trust_floors_or_expand_scope(packed, change):
    change_sidecars(packed, lambda document: document.update(change))
    with pytest.raises(ImportRejected):
        verify(packed)


@pytest.mark.parametrize('part', ['request', 'signature', 'recovery_bundle', 'history_bundle'])
def test_each_inner_frame_still_requires_original_authorization(packed, part):
    parts = archive.unframe(plaintext(packed))
    if part == 'request':
        document = parse(parts[part])
        document['sequence'] += 1
        parts[part] = encoded(document)
    else:
        raw = parts[part]
        parts[part] = raw[:-1] + bytes([raw[-1] ^ 1])
    replace_plaintext(packed, archive.frame(parts))
    with pytest.raises(ImportRejected):
        verify(packed)


@pytest.mark.parametrize('kind', ['publication', 'authority', 'source', 'configuration', 'invalid-base64', 'duplicate-json'])
def test_encryption_does_not_make_sidecar_substitution_valid(packed, kind):
    if kind == 'duplicate-json':
        parts = archive.unframe(plaintext(packed))
        parts['sidecars'] = b'{"version":1,"version":1}'
        replace_plaintext(packed, archive.frame(parts))
    else:
        def change(document):
            if kind == 'publication':
                document['publications']['NL2'] = base64.b64encode(b'{}').decode()
            elif kind == 'authority':
                document['authorities']['NL2'] = base64.b64encode(b'{}').decode()
            elif kind == 'source':
                document['source_materials']['RU']['files']['node.py'] = base64.b64encode(b'changed').decode()
            elif kind == 'configuration':
                document['source_materials']['NL1']['configuration'] = base64.b64encode(b'{}').decode()
            else:
                document['publications']['NL'] = 'not base64'
        change_sidecars(packed, change)
    with pytest.raises(ImportRejected):
        verify(packed)


@pytest.mark.parametrize('kind', ['signer', 'sequence', 'crl', 'authority-NL', 'authority-NL2', 'expired',
    'recovery-key', 'history-key', 'anchor'])
def test_external_authority_time_and_replay_floors_remain_mandatory(packed, kind):
    external = packed['external']
    if kind == 'signer':
        external['trusted_key'] = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    elif kind == 'sequence':
        external['minimum_sequence'] = 2
    elif kind == 'crl':
        external['minimum_crl'] += 1
    elif kind.startswith('authority-'):
        external['minimum_authority_sequences'][kind.removeprefix('authority-')] += 1
    elif kind == 'expired':
        external['now'] += 300
    else:
        external[kind.replace('-', '_')] = b'z' * 32
    with pytest.raises(ImportRejected):
        verify(packed)


def test_sealing_is_not_signature_approval(candidate, packed):
    arguments = candidate['arguments']
    material = {name: arguments[name] for name in
                ('recovery_bundle', 'history_bundle', 'publications', 'authorities', 'source_materials')}
    packed['bundle'], packed['checksum'] = archive.seal(candidate['request'], b'x' * 64, packed['key'], **material)
    with pytest.raises(ImportRejected, match='FORWARD_SIGNATURE_INVALID'):
        verify(packed)


@pytest.mark.parametrize('name', ['recovery_bundle', 'history_bundle', 'publications', 'authorities', 'source_materials'])
def test_packer_refuses_inputs_not_bound_by_request(candidate, name):
    material = {part: candidate['arguments'][part] for part in
                ('recovery_bundle', 'history_bundle', 'publications', 'authorities', 'source_materials')}
    material[name] = b'changed' if name.endswith('bundle') else {}
    with pytest.raises(ImportRejected):
        archive.seal(candidate['request'], candidate['signature'], b'k' * 32, **material)


def test_fixed_frame_count_and_limits():
    parts = {name: b'x' for name, _ in archive.FRAMES}
    assert archive.unframe(archive.frame(parts)) == parts
    for name in parts:
        with pytest.raises(ImportRejected, match='FORWARD_ARCHIVE_FRAMES'):
            archive.frame({key: value for key, value in parts.items() if key != name})
    with pytest.raises(ImportRejected, match='FORWARD_ARCHIVE_FRAME_BOUNDS'):
        archive.frame(parts | {'signature': b'x' * 65})
    with pytest.raises(ImportRejected, match='FORWARD_ARCHIVE_FRAMES'):
        archive.frame(parts | {'extra': b'x'})


def test_ciphertext_bound_is_checked_before_decryption(packed, monkeypatch):
    monkeypatch.setattr(archive, 'MAX_PLAINTEXT', 1)
    with pytest.raises(ImportRejected, match='FORWARD_ARCHIVE_FORMAT'):
        verify(packed)
