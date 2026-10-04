import copy
import base64
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from control.friends import restricted, restricted_sync
from control.friends.restricted import DirectoryValidationError, directory, timestamp_ns
from scripts.package_restricted_runtime import build
from test_friends_restricted import configured, proof

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/vectors/bootstrap-live-issuance.json').read_text())
FAMILY, GATEWAY = 'a' * 32, 'b' * 32
NOW_NS = FIXTURE['observed_at_ns']


def encoded(value=None):
    return json.dumps(FIXTURE['directory'] if value is None else value, separators=(',', ':')).encode()


def test_live_shape_rounding_reproduces_old_predicate():
    raw = encoded()
    assert len(raw) == 291
    issued = timestamp_ns(FIXTURE['directory']['issued_at'])
    assert issued > (NOW_NS // 1_000_000_000) * 1_000_000_000
    with pytest.raises(DirectoryValidationError) as failure:
        directory(raw, FAMILY, GATEWAY, NOW_NS // 1_000_000_000)
    assert (failure.value.stage, failure.value.predicate, failure.value.field) == ('time', 'issued_in_future', 'issued_at')
    assert directory(raw, FAMILY, GATEWAY, now_ns=NOW_NS) == FIXTURE['directory']


@pytest.mark.parametrize('fraction', [1, 532852358, 999999999])
def test_no_future_grace_or_expiry_extension(fraction):
    value = copy.deepcopy(FIXTURE['directory'])
    value['issued_at'] = f'2026-10-01T17:13:53.{fraction:09d}Z'
    issued = timestamp_ns(value['issued_at'])
    expires = timestamp_ns(value['expires_at'])
    for instant, predicate in [(issued - 1, 'issued_in_future'), (expires, 'expired'), (expires + 1, 'expired')]:
        with pytest.raises(DirectoryValidationError) as failure:
            directory(encoded(value), FAMILY, GATEWAY, now_ns=instant)
        assert failure.value.predicate == predicate
    for instant in (issued, issued + 1, expires - 1):
        assert directory(encoded(value), FAMILY, GATEWAY, now_ns=instant)


def negative(case):
    value = copy.deepcopy(FIXTURE['directory'])
    seed = value['seeds'][0]
    if case == 'version': value['version'] = True
    elif case == 'family': value['family'] = 'c' * 32
    elif case == 'gateway': seed['gateway'] = 'c' * 32
    elif case == 'transport': seed['transport'] = 'dedicated'
    elif case == 'extra': value['certificate'] = 'private-marker'
    elif case == 'null': value['issued_at'] = None
    elif case == 'integer': value['issued_at'] = NOW_NS
    elif case == 'absent': del seed['join_url']
    elif case == 'empty': value['seeds'] = []
    elif case == 'many': value['seeds'] = [seed] * 5
    elif case == 'duplicate': value['seeds'].append(seed)
    elif case == 'lifetime': value['expires_at'] = '2026-10-01T21:13:53.532852359Z'
    elif case == 'ordering': value['expires_at'] = value['issued_at']
    elif case == 'seed_null': value['seeds'] = [None]
    else: seed['join_url'] = case
    return encoded(value)


NEGATIVES = ['version', 'family', 'gateway', 'transport', 'extra', 'null', 'integer', 'absent', 'empty',
             'many', 'duplicate', 'lifetime', 'ordering', 'seed_null',
             None, 1, 'https://telemost.yandex.ru/j/test?secret=private-marker',
             'https://telemost.yandex.ru/j/test#private-marker', 'https://private-marker@telemost.yandex.ru/j/test',
             'https://telemost.yandex.ru:443/j/test', 'http://telemost.yandex.ru/j/test',
             'https://telemost.yandex.ru.evil/j/test', 'https://telemost.yandex.ru/j/%74est',
             'https://telemost.yandex.ru/j/' + 'x' * 129, 'https://telemost.yandex.ru/j/']


@pytest.mark.parametrize('case', NEGATIVES)
def test_negative_categories_are_bounded_and_private(case):
    with pytest.raises(DirectoryValidationError) as failure:
        directory(negative(case), FAMILY, GATEWAY, now_ns=NOW_NS)
    message = str(failure.value)
    assert message.startswith('directory_validation_failed: stage=') and len(message) < 160
    assert 'private-marker' not in message and 'https://' not in message and FAMILY not in message


@pytest.mark.parametrize('raw', [b'', b' ' * 8193, b'{', b'[]', b'{"version":1,"version":1}', b'\xff'])
def test_parse_negatives(raw):
    with pytest.raises(DirectoryValidationError):
        directory(raw, FAMILY, GATEWAY, now_ns=NOW_NS)


def test_default_clock_preserves_nanoseconds(monkeypatch):
    monkeypatch.setattr(restricted.time, 'time_ns', lambda: NOW_NS)
    assert directory(encoded(), FAMILY, GATEWAY)
    assert restricted.clock_nanoseconds(restricted.time.time) == NOW_NS
    assert restricted.clock_nanoseconds(lambda: Decimal(NOW_NS) / 1_000_000_000) == NOW_NS


def test_gateway_and_delivery_sample_precise_clock_after_read(tmp_path, monkeypatch):
    service, device, _ = configured(tmp_path, NOW_NS // 1_000_000_000)
    service.access.clock = lambda: Decimal(NOW_NS) / 1_000_000_000
    profile = tmp_path / 'gateway.json'
    trust, _ = restricted.delegation(service.manifest, service.anchor, NOW_NS // 1_000_000_000)
    profile.write_text(json.dumps(dict(authority=trust['authority'],
                                      revocations=service.crl_source().decode(), minimum_crl=1, family=FAMILY, gateway=GATEWAY)))
    profile.chmod(0o600)
    seed = tmp_path / 'directory.json'
    seed.write_bytes(encoded()); seed.chmod(0o600)
    monkeypatch.setattr(restricted.time, 'time_ns', lambda: NOW_NS)
    monkeypatch.setattr(restricted_sync.time, 'time', lambda: NOW_NS / 1_000_000_000)
    raw = restricted_sync.gateway(profile, seed, json.dumps(dict(revocations=service.crl_source().decode())).encode())
    assert raw == encoded()
    service.seed_source = lambda: raw
    assert service.fetch(proof(service, device))['directory'] == FIXTURE['directory']


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    tool = os.environ.get('FC_TEST_GO')
    if not tool:
        pytest.skip('FC_TEST_GO required for actual Go/native contract')
    output = tmp_path_factory.mktemp('directory-go')
    for name, source in [('directory', './bootstrap/testdata/directory-check.go'), ('delivery', './wholedevice/testdata/delivery-check.go')]:
        subprocess.run([tool, 'build', '-o', str(output / name), source], cwd=ROOT / 'carrier', capture_output=True, check=True, timeout=120)
    return output


def native_request(native, raw, now_ns=NOW_NS, serialize=False):
    payload = json.dumps(dict(directory=json.loads(raw), family=FAMILY, gateway=GATEWAY, now_ns=now_ns, serialize=serialize)).encode()
    return subprocess.run([str(native / 'directory')], input=payload, capture_output=True, timeout=10)


def test_go_serialization_python_sync_delivery_android_native(native, tmp_path, monkeypatch):
    output = native_request(native, encoded(), serialize=True)
    assert output.returncode == 0
    raw = output.stdout.strip()
    assert raw == encoded()
    service, device, _ = configured(tmp_path, NOW_NS // 1_000_000_000)
    service.access.clock = lambda: Decimal(NOW_NS) / 1_000_000_000
    trust, _ = restricted.delegation(service.manifest, service.anchor, NOW_NS // 1_000_000_000)
    profile, seed = tmp_path / 'gateway.json', tmp_path / 'directory.json'
    profile.write_text(json.dumps(dict(authority=trust['authority'], revocations=service.crl_source().decode(),
                                      minimum_crl=1, family=FAMILY, gateway=GATEWAY)))
    profile.chmod(0o600)
    seed.write_bytes(raw); seed.chmod(0o600)
    monkeypatch.setattr(restricted.time, 'time_ns', lambda: NOW_NS)
    monkeypatch.setattr(restricted_sync.time, 'time', lambda: NOW_NS / 1_000_000_000)
    exported = restricted_sync.gateway(profile, seed, json.dumps(dict(revocations=service.crl_source().decode())).encode())
    assert exported == raw
    service.seed_source = lambda: exported
    response = service.fetch(proof(service, device))
    payload = dict(response=response, public=device.public_identity, identity='', anchor=base64.b64encode(service.anchor).decode(), now_ns=NOW_NS)
    result = subprocess.run([str(native / 'delivery')], input=json.dumps(payload).encode(), capture_output=True, timeout=10)
    assert result.returncode == 0 and result.stdout == b'compatible\n', 'native delivery rejected'


def test_sync_does_not_truncate_receiver_clock(tmp_path, monkeypatch):
    service, _, _ = configured(tmp_path, NOW_NS // 1_000_000_000)
    service.access.clock = lambda: Decimal(NOW_NS) / 1_000_000_000
    monkeypatch.setenv('FC_FRIENDS_RESTRICTED_DIR', str(tmp_path))
    monkeypatch.setattr(restricted_sync, 'from_env', lambda access: service)
    published_lifetimes = []
    monkeypatch.setattr(restricted_sync, 'publish_crl',
                        lambda service, target, *, lifetime: published_lifetimes.append(lifetime))
    def receive(command, **kwargs):
        kwargs['stdout'].write(encoded())
        kwargs['stdout'].flush()
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(restricted_sync.subprocess, 'run', receive)
    restricted_sync.sync(service.access, '186.246.45.246', tmp_path / 'key', tmp_path / 'known_hosts')
    assert (tmp_path / 'directory.json').read_bytes() == encoded()
    assert published_lifetimes == [900]


@pytest.mark.parametrize('case', NEGATIVES)
def test_native_security_parity(native, case):
    assert native_request(native, negative(case)).returncode != 0


def test_native_nanosecond_edges(native):
    issued = timestamp_ns(FIXTURE['directory']['issued_at'])
    expires = timestamp_ns(FIXTURE['directory']['expires_at'])
    for instant in (issued - 1, expires, expires + 1):
        assert native_request(native, encoded(), instant).returncode != 0
    for instant in (issued, issued + 1, expires - 1):
        assert native_request(native, encoded(), instant).returncode == 0


@pytest.mark.parametrize('expires_at', ['2026-10-01T18:13:53.532852359Z',
                                       '2026-10-01T21:13:53.532852358Z'])
def test_extended_directory_lifetime_security_parity(native, expires_at):
    value = copy.deepcopy(FIXTURE['directory'])
    value['expires_at'] = expires_at
    raw = encoded(value)
    assert directory(raw, FAMILY, GATEWAY, now_ns=NOW_NS) == value
    assert native_request(native, raw).returncode == 0


def test_packaged_failure_receipt_survives_shell_exit_and_rollback(tmp_path):
    artifact = tmp_path / 'bundle'
    build(artifact)
    profile = tmp_path / 'bindings.json'
    profile.write_text(json.dumps(dict(family=FAMILY, gateway=GATEWAY))); profile.chmod(0o600)
    seed = tmp_path / 'directory.json'
    value = copy.deepcopy(FIXTURE['directory']); value['version'] = False
    seed.write_bytes(encoded(value)); seed.chmod(0o600)
    receipt = tmp_path / 'receipt.json'
    operator = tmp_path / 'operator.sh'
    operator.write_text('set -eu\nreceipt=$1\nmarker=$2\nshift 2\ntrap \'test -s "$receipt" && cp "$receipt" "$marker"\' EXIT\n"$@"\n')
    marker = tmp_path / 'rollback-receipt.json'
    command = [sys.executable, '-I', str(artifact / 'restricted-sync.pyz'), 'directory-check', '--profile', str(profile),
               '--directory', str(seed), '--receipt', str(receipt), '--generation', 'isolated-failure']
    result = subprocess.run(['/bin/sh', str(operator), str(receipt), str(marker), *command], cwd=tmp_path, capture_output=True, timeout=15)
    assert result.returncode != 0 and not result.stdout
    assert b'stage=structure predicate=invalid_version field=version' in result.stderr
    assert b'Traceback' not in result.stderr and b'https://' not in result.stderr
    assert receipt.read_bytes() == marker.read_bytes()
    assert json.loads(receipt.read_bytes())['predicate'] == 'invalid_version'
    assert receipt.stat().st_mode & 0o777 == 0o600


def test_receipt_precedes_error_and_fsync_failure_is_fatal(tmp_path, monkeypatch):
    profile, seed, receipt = [tmp_path / name for name in ('profile', 'directory', 'receipt')]
    profile.write_text(json.dumps(dict(family=FAMILY, gateway=GATEWAY))); profile.chmod(0o600)
    seed.write_bytes(encoded()); seed.chmod(0o600)
    issued = timestamp_ns(FIXTURE['directory']['issued_at'])
    with pytest.raises(DirectoryValidationError):
        restricted_sync.check_directory(profile, seed, receipt, 'clock-boundary', now_ns=issued - 1)
    assert json.loads(receipt.read_bytes())['predicate'] == 'issued_in_future'
    restricted_sync.check_directory(profile, seed, receipt, 'clock-boundary', now_ns=NOW_NS)
    assert json.loads(receipt.read_bytes())['result'] == 'passed'
    def failed(descriptor):
        raise OSError('test fsync failure')
    monkeypatch.setattr(os, 'fsync', failed)
    with pytest.raises(OSError):
        restricted_sync.check_directory(profile, seed, receipt, 'clock-boundary', now_ns=NOW_NS)


def test_packaged_receipt_survives_hard_process_exit(tmp_path):
    artifact = tmp_path / 'bundle'
    build(artifact)
    profile, seed, receipt = [tmp_path / name for name in ('profile', 'directory', 'receipt')]
    profile.write_text(json.dumps(dict(family=FAMILY, gateway=GATEWAY))); profile.chmod(0o600)
    seed.write_bytes(encoded()); seed.chmod(0o600)
    program = '''import contextlib,io,os,runpy,sys
from pathlib import Path
archive,profile,seed,receipt,instant=sys.argv[1:]
sys.argv=[archive,"--help"]
with contextlib.redirect_stdout(io.StringIO()):
 try:runpy.run_path(archive,run_name="__main__")
 except SystemExit as error:assert error.code==0
from control.friends.restricted_sync import check_directory
check_directory(Path(profile),Path(seed),Path(receipt),"hard-exit",now_ns=int(instant))
os._exit(23)
'''
    result = subprocess.run([sys.executable, '-I', '-c', program, str(artifact / 'restricted-sync.pyz'),
                             str(profile), str(seed), str(receipt), str(NOW_NS)], capture_output=True, cwd=tmp_path, timeout=15)
    assert result.returncode == 23 and not result.stdout and not result.stderr
    assert json.loads(receipt.read_bytes())['result'] == 'passed'
