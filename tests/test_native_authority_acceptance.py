import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from scripts import native_authority_acceptance as operator
from scripts import package_native_authority_check as packaging

PASS = dict(version=1, status='PASS', stage='complete', reason='validated',
            object='authority', comparison='positive_and_negatives')
FAIL = dict(version=1, status='FAIL', stage='revision_negative', reason='unexpected_acceptance',
            object='device_certificate', comparison='above_signed_revision')


@pytest.mark.parametrize('value,exit_code,valid', [(PASS,0,True),(FAIL,1,True),(PASS,1,False),(FAIL,0,False),
                                              (dict(FAIL, object='private-id'),1,False),
                                              (dict(FAIL, private_key='secret'),1,False),
                                              (dict(PASS, version=True),0,False),
                                              (dict(FAIL, stage=[]),1,False)])
def test_allowlisted_schema(value, exit_code, valid):
    assert (operator.parse(json.dumps(value).encode(), exit_code) is not None) is valid


def test_duplicate_and_malformed_receipts_rejected():
    assert operator.parse(b'{"status":"PASS","status":"PASS"}', 0) is None
    assert operator.parse(b'private material, not JSON', 1) is None
    assert operator.parse(b'[]', 0) is None


@pytest.mark.parametrize('case', ['pass', 'fail', 'timeout', 'malformed', 'changed', 'oversized'])
def test_durable_receipt_precedes_verdict(tmp_path, monkeypatch, case):
    binary = tmp_path / 'checker'
    binary.write_bytes(b'accepted-artifact')
    pin = hashlib.sha256(binary.read_bytes()).hexdigest()
    events = []
    actual_fsync = operator.os.fsync
    def sync(descriptor):
        events.append('fsync')
        actual_fsync(descriptor)
    def run(command, **options):
        events.append('execute')
        assert options['cwd'] == '/' and options['timeout'] == 10
        if case == 'timeout':
            raise subprocess.TimeoutExpired(command, 10, output=b'secret-private-key')
        response = PASS if case in ('pass', 'changed') else FAIL
        output = json.dumps(response).encode()
        if case == 'malformed':
            output = b'private-device-id'
        if case == 'oversized':
            output = b'secret' * 1000
        options['stdout'].write(output)
        if case == 'changed':
            binary.write_bytes(b'changed-artifact')
        return subprocess.CompletedProcess(command, 0 if case in ('pass', 'changed') else 1)
    monkeypatch.setattr(operator.os, 'fsync', sync)
    monkeypatch.setattr(operator.subprocess, 'run', run)
    destination = tmp_path / 'receipts' / 'verdict.json'
    result = operator.execute(binary, pin, '/unused/profile', '/unused/certificate', destination)
    events.append('return')
    assert events == ['execute', 'fsync', 'fsync', 'return']
    assert json.loads(destination.read_bytes()) == result
    assert result['passed'] is (case == 'pass')
    assert not any(secret in destination.read_text() for secret in ('secret', 'private-device-id', '/unused'))
    assert destination.stat().st_mode & 0o777 == 0o600
    with pytest.raises(ValueError, match='Existing receipt'):
        operator.execute(binary, pin, '/unused/profile', '/unused/certificate', destination)
    assert events.count('execute') == 1


def test_pin_mismatch_never_executes(tmp_path, monkeypatch):
    binary = tmp_path/'checker'
    binary.write_bytes(b'incorrect-artifact')
    monkeypatch.setattr(operator.subprocess, 'run', lambda *args, **kwargs: pytest.fail('executed'))
    result = operator.execute(binary, '0'*64, 'unused', 'unused', tmp_path/'receipts/verdict.json')
    assert not result['passed'] and result['classification'] == 'artifact_mismatch'


def test_persistence_failure_forbids_verdict(tmp_path, monkeypatch):
    binary = tmp_path/'checker'
    binary.write_bytes(b'checked')
    def run(command, **options):
        options['stdout'].write(json.dumps(PASS).encode())
        return subprocess.CompletedProcess(command, 0)
    def fail(*args):
        raise OSError('disk failure')
    monkeypatch.setattr(operator.subprocess, 'run', run)
    monkeypatch.setattr(operator.os, 'fsync', fail)
    with pytest.raises(OSError):
        operator.execute(binary, hashlib.sha256(binary.read_bytes()).hexdigest(), 'unused', 'unused', tmp_path/'receipts/verdict.json')


@pytest.mark.parametrize('revision', ['HEAD', '../main', 'a'*39, 'A'*40, 'a'*41])
def test_clean_export_requires_exact_commit(tmp_path, revision):
    with pytest.raises(ValueError, match='Exact full source commit'):
        packaging.build(tmp_path/'output', revision, '/unused/go')


def test_source_guards():
    root = Path(__file__).resolve().parents[1]
    source = (root/'carrier/cmd/native-authority-check/main.go').read_text()
    assert 'changed.MinimumRevision = revision + 1' in source
    assert 'changed.MinimumCRL = crl.Number.Int64() + 1' in source
    assert 'familysession.Configuration(raw, true)' in source
    assert 'configuration.VerifyConnection(state)' in source
    assert 'json.NewEncoder(os.Stdout).Encode(result)' in source
    assert 'time.Now()' in source and '--now' not in source
    operator_source = (root/'scripts/native_authority_acceptance.py').read_text()
    assert operator_source.index('persist(receipt_path, record)') < operator_source.index('return record')
    for forbidden in ('systemctl', 'ssh ', 'adb ', 'publish_crl', 'issuer.key'):
        assert forbidden not in source + operator_source
    guide = (root/'deploy/friends/restricted/NATIVE_AUTHORITY.md').read_text()
    assert 'validated peer revision + 1' in guide
    assert 'before' in guide and 'rollback' in guide
    assert 'Delegation2/grant1 is not automatically stale' in guide
