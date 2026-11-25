from copy import deepcopy
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts import control_ha_forward_signing as signing
from scripts import control_ha_forward_checkpoint as forward
from scripts.control_ha_import import ImportRejected, digest, encoded
from test_control_ha_forward_checkpoint import candidate, current, native_current


NOW = 100


def write(path, raw):
    path.write_bytes(raw)
    path.chmod(0o600)


@pytest.fixture
def inputs(tmp_path):
    tmp_path.chmod(0o700)
    document = dict(version=1, purpose=forward.PURPOSE, action=forward.ACTION, checkpoint_id='1' * 32,
        sequence=2, captured_at=NOW, expires_at=NOW + 300,
        recovery=dict(checkpoint='1' * 32, bundle_sha256='a' * 64, anchor_sha256='b' * 64, snapshot_sha256='c' * 64),
        history=dict(identifier='2' * 32, bundle_sha256='d' * 64, manifest_sha256='e' * 64, inventory_sha256='f' * 64),
        sources={node: dict(runtime_sha256='a' * 64, configuration_sha256='b' * 64) for node in forward.NODES},
        publications={node: 'c' * 64 for node in forward.GATEWAYS}, issuer_public_sha256='d' * 64,
        gateways={node: dict(identity=str(index) * 32, authority_sha256='e' * 64)
                  for index, node in enumerate(sorted(forward.GATEWAYS), start=3)})
    signer = Ed25519PrivateKey.generate()
    request, public = encoded(document), signer.public_key().public_bytes_raw()
    signature = signer.sign(forward.DOMAIN + request)
    for name, raw in (('request', request), ('public', public), ('seed', signer.private_bytes_raw()),
                      ('signature', signature)):
        write(tmp_path / name, raw)
    return SimpleNamespace(command='sign', request=tmp_path/'request', request_sha256=digest(request),
        trusted_key=tmp_path/'public', trusted_key_sha256=digest(public), key_file=tmp_path/'seed',
        minimum_sequence=1, confirm_offline_only=True, output=tmp_path/'new-signature',
        signature=tmp_path/'signature', signature_sha256=digest(signature))


def execute(inputs, **changes):
    args = deepcopy(inputs)
    for name, value in changes.items():
        setattr(args, name, value)
    return signing.execute(args, clock=lambda: NOW)


def change_request(inputs, change):
    document = json.loads(inputs.request.read_bytes())
    change(document)
    raw = encoded(document)
    write(inputs.request, raw)
    inputs.request_sha256 = digest(raw)


def test_review_sign_and_verify_preserve_inputs_and_scope(inputs):
    before = {path: path.read_bytes() for path in inputs.request.parent.iterdir()}
    review = execute(inputs, command='review')
    assert review['result'] == 'FORWARD_REQUEST_REVIEWED_NOT_APPROVED'
    assert review['signature_sha256'] is None and not inputs.output.exists()
    receipt = execute(inputs)
    assert receipt['result'] == 'FORWARD_OFFLINE_SIGNATURE_WRITTEN'
    assert inputs.output.read_bytes() == inputs.signature.read_bytes()
    assert stat.S_IMODE(inputs.output.stat().st_mode) == 0o600
    verified = execute(inputs, command='verify', signature=inputs.output,
                       signature_sha256=receipt['signature_sha256'])
    assert verified['result'] == 'FORWARD_OFFLINE_SIGNATURE_VALID'
    for value in (review, receipt, verified):
        assert value['action'] == forward.ACTION
        assert all(value[name] is False for name in ('independent_approval_established', 'trust_enrolled',
            'replay_floor_updated', 'material_validation_performed', 'capture_permitted',
            'database_import_authorized', 'activation_authorized'))
    assert all(path.read_bytes() == raw for path, raw in before.items())


def test_signature_is_consumed_by_unchanged_full_checkpoint_verifier(inputs, candidate):
    write(inputs.request, candidate['request'])
    write(inputs.trusted_key, candidate['trusted_key'])
    write(inputs.key_file, candidate['signer'].private_bytes_raw())
    inputs.request_sha256 = candidate['expected_request_sha256']
    inputs.trusted_key_sha256 = digest(candidate['trusted_key'])
    receipt = signing.execute(inputs, clock=lambda: candidate['arguments']['now'])
    qualified = forward.verify(candidate['request'], inputs.output.read_bytes(), candidate['trusted_key'],
                               candidate['expected_request_sha256'], **candidate['arguments'])
    assert qualified.summary()['result'] == 'FORWARD_CHECKPOINT_OFFLINE_QUALIFIED'
    assert qualified.summary()['activation'] == 'FORBIDDEN'
    assert receipt['material_validation_performed'] is False


@pytest.mark.parametrize('field,value', [('purpose', 'live-deployment'), ('action', 'CAPTURE_NOW'),
    ('version', True), ('checkpoint_id', 'a' * 32), ('sequence', 0), ('sequence', True),
    ('captured_at', 0), ('expires_at', NOW + 3601), ('sources', {}), ('gateways', {}),
    ('publications', {}), ('issuer_public_sha256', 'not-a-hash'), ('unexpected', 'private-value')])
def test_invalid_request_cannot_reach_private_key(inputs, field, value, monkeypatch):
    change_request(inputs, lambda document: document.update({field: value}))
    original = signing.read_private
    def read(path, *args, **kwargs):
        assert path != inputs.key_file
        return original(path, *args, **kwargs)
    monkeypatch.setattr(signing, 'read_private', read)
    with pytest.raises(ImportRejected):
        execute(inputs)
    assert not inputs.output.exists()


@pytest.mark.parametrize('changes', [dict(request_sha256='a'*64), dict(trusted_key_sha256='b'*64),
    dict(minimum_sequence=2), dict(minimum_sequence=3), dict(minimum_sequence=-1), dict(minimum_sequence=True),
    dict(confirm_offline_only=False), dict(command='unrecognized')])
def test_independent_pins_floor_and_explicit_action_required(inputs, changes):
    with pytest.raises(ImportRejected):
        execute(inputs, **changes)
    assert not inputs.output.exists()


@pytest.mark.parametrize('now', [NOW - 1, NOW + 300, NOW + 301])
def test_expired_or_future_request_cannot_be_signed(inputs, now):
    with pytest.raises(ImportRejected, match='SIGNING_TIME'):
        signing.execute(inputs, clock=lambda: now)
    assert not inputs.output.exists()


@pytest.mark.parametrize('raw', [b'', b'{' + b'x' * forward.MAX_REQUEST, b'{"version":1,"version":1}',
                                b'{"version":NaN}', b'[]', b'\xff'])
def test_bad_bytes_and_bounds_refuse(inputs, raw):
    write(inputs.request, raw)
    inputs.request_sha256 = digest(raw)
    with pytest.raises(ImportRejected):
        execute(inputs)


def test_noncanonical_request_is_not_reformatted_and_signed(inputs):
    raw = json.dumps(json.loads(inputs.request.read_bytes()), indent=2).encode()
    write(inputs.request, raw)
    inputs.request_sha256 = digest(raw)
    with pytest.raises(ImportRejected, match='FORWARD_NONCANONICAL'):
        execute(inputs)
    assert inputs.request.read_bytes() == raw


def test_key_mismatch_issuer_key_and_release_key_path_refuse(inputs):
    seed = inputs.key_file.read_bytes()
    write(inputs.key_file, Ed25519PrivateKey.generate().private_bytes_raw())
    with pytest.raises(ImportRejected, match='SIGNING_KEY_MISMATCH'):
        execute(inputs)
    write(inputs.key_file, seed)
    with pytest.raises(ImportRejected, match='SIGNING_RELEASE_KEY_FORBIDDEN'):
        execute(inputs, key_file=inputs.key_file.parent/'update-signing'/'ed25519.key')
    change_request(inputs, lambda document: document.update(issuer_public_sha256=inputs.trusted_key_sha256))
    with pytest.raises(ImportRejected, match='SIGNING_DEDICATED_KEY_REQUIRED'):
        execute(inputs)
    assert not inputs.output.exists()


@pytest.mark.parametrize('field', ['request', 'trusted_key', 'key_file', 'signature'])
@pytest.mark.parametrize('kind', ['mode', 'symlink', 'hardlink', 'fifo', 'directory', 'oversize'])
def test_private_input_rules(inputs, field, kind):
    path = getattr(inputs, field)
    raw = path.read_bytes()
    if kind == 'mode':
        path.chmod(0o644)
    elif kind == 'hardlink':
        os.link(path, path.with_suffix('.alias'))
    else:
        path.unlink()
        if kind == 'symlink':
            alternate = path.with_suffix('.target')
            write(alternate, raw)
            path.symlink_to(alternate)
        elif kind == 'fifo':
            os.mkfifo(path, 0o600)
        elif kind == 'directory':
            path.mkdir(mode=0o700)
        else:
            write(path, b'x' * (forward.MAX_REQUEST + 1))
    with pytest.raises((ImportRejected, OSError)):
        execute(inputs, command='verify' if field == 'signature' else 'sign')
    assert not inputs.output.exists()


@pytest.mark.parametrize('kind', ['parent-mode', 'parent-symlink', 'relative', 'traversal', 'root'])
def test_parent_and_path_rules(inputs, kind):
    path = inputs.request
    if kind == 'parent-mode':
        path.parent.chmod(0o755)
    elif kind == 'parent-symlink':
        alias = path.parent.parent / (path.parent.name + '-alias')
        alias.symlink_to(path.parent, target_is_directory=True)
        path = alias / path.name
    elif kind == 'relative':
        path = Path(path.name)
    elif kind == 'traversal':
        path = path.parent / '..' / path.parent.name / path.name
    else:
        path = Path('/')
    with pytest.raises((ImportRejected, OSError)):
        execute(inputs, request=path)


@pytest.mark.parametrize('kind', ['file', 'symlink', 'directory'])
def test_signature_output_never_overwrites(inputs, kind):
    if kind == 'file':
        write(inputs.output, b'keep')
    elif kind == 'symlink':
        inputs.output.symlink_to(inputs.key_file)
    else:
        inputs.output.mkdir(mode=0o700)
    seed = inputs.key_file.read_bytes()
    with pytest.raises(FileExistsError):
        execute(inputs)
    assert inputs.key_file.read_bytes() == seed
    if kind == 'file':
        assert inputs.output.read_bytes() == b'keep'


def test_mutated_input_is_rejected_even_before_digest_check(inputs, monkeypatch):
    original = signing.os.fstat
    calls = 0
    def observe(descriptor):
        nonlocal calls
        info = original(descriptor)
        if stat.S_ISREG(info.st_mode):
            calls += 1
            if calls == 1:
                write(inputs.request, inputs.request.read_bytes() + b' ')
        return info
    monkeypatch.setattr(signing.os, 'fstat', observe)
    with pytest.raises(ImportRejected, match='SIGNING_INPUT_CHANGED'):
        execute(inputs)


@pytest.mark.parametrize('instants,exists', [([NOW, NOW, NOW+300], False), ([NOW, NOW, NOW, NOW+300], True)])
def test_expiry_during_signing_is_not_success(inputs, instants, exists):
    clock = iter(instants)
    with pytest.raises(ImportRejected, match='SIGNING_TIME'):
        signing.execute(inputs, clock=lambda: next(clock))
    assert inputs.output.exists() == exists


def test_fsync_failure_is_uncertain_and_cannot_be_blindly_retried(inputs, monkeypatch):
    with monkeypatch.context() as scoped:
        scoped.setattr(signing.os, 'fsync', lambda descriptor: (_ for _ in ()).throw(OSError('private-detail')))
        with pytest.raises(OSError):
            execute(inputs)
    signature = inputs.output.read_bytes()
    with pytest.raises(FileExistsError):
        execute(inputs)
    receipt = execute(inputs, command='verify', signature=inputs.output, signature_sha256=digest(signature))
    assert receipt['result'] == 'FORWARD_OFFLINE_SIGNATURE_VALID'
    assert not receipt['independent_approval_established'] and not receipt['capture_permitted']


@pytest.mark.parametrize('raw', [b'\x00'*64, b'wrong-domain'+b'x'*52])
def test_bad_signature_refuses(inputs, raw):
    write(inputs.signature, raw)
    with pytest.raises(signing.InvalidSignature):
        execute(inputs, command='verify', signature_sha256=digest(raw))


def argv(inputs, command):
    arguments = [command, '--request', str(inputs.request), '--request-sha256', inputs.request_sha256,
        '--trusted-key', str(inputs.trusted_key), '--trusted-key-sha256', inputs.trusted_key_sha256,
        '--minimum-sequence', str(inputs.minimum_sequence)]
    if command == 'sign':
        arguments += ['--key-file', str(inputs.key_file), '--output', str(inputs.output), '--confirm-offline-only']
    if command == 'verify':
        arguments += ['--signature', str(inputs.output), '--signature-sha256', digest(inputs.output.read_bytes())]
    return arguments


def test_native_cli_roundtrip_and_sanitized_failures(inputs):
    now = int(time.time())
    change_request(inputs, lambda document: document.update(captured_at=now, expires_at=now+300))
    for command in ('review', 'sign', 'verify'):
        result = subprocess.run([sys.executable, '-m', 'scripts.control_ha_forward_signing', *argv(inputs, command)],
                                capture_output=True, timeout=15)
        assert result.returncode == 0 and result.stderr == b''
        receipt = json.loads(result.stdout)
        assert receipt['request_sha256'] == inputs.request_sha256
        assert not receipt['activation_authorized']
        assert str(inputs.request.parent).encode() not in result.stdout
    for arguments in (argv(inputs, 'sign'), ['sign', '--key-file', '/private-do-not-print'],
                      ['sign', '--minimum-sequence', 'private-invalid-value']):
        result = subprocess.run([sys.executable, '-m', 'scripts.control_ha_forward_signing', *arguments],
                                capture_output=True, timeout=15)
        assert result.returncode == 1 and result.stdout == b''
        assert result.stderr == b'FORWARD_SIGNING_REFUSED\n'
