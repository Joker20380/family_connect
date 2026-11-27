import io
import os
from pathlib import Path
import subprocess
import tarfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import pytest

from scripts import ha_wrapping_key as wrapping
from scripts import signing_key


def repack(raw, change):
    result = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as source:
        with tarfile.open(fileobj=result, mode='w:gz') as target:
            for item in source:
                data = source.extractfile(item).read()
                item, data = change(item, data)
                item.size = len(data)
                target.addfile(item, io.BytesIO(data))
    return result.getvalue()


@pytest.mark.parametrize('size', [0, 16, 31, 33, 64])
def test_exact_raw_aes256_length(size):
    with pytest.raises(ValueError, match='HA_KEY_LENGTH'):
        wrapping.archive(bytes(size))


@pytest.mark.parametrize('fault', ['purpose', 'algorithm', 'member', 'length', 'digest', 'symlink', 'extra'])
def test_archive_purpose_and_exact_member_refusals(fault):
    raw = wrapping.archive(bytes(range(32)))

    def change(item, data):
        if item.name == wrapping.MANIFEST:
            changes = {'purpose': (wrapping.PURPOSE.encode(), b'signing'),
                       'algorithm': (b'AES-256-GCM', b'Ed25519'),
                       'member': (wrapping.MEMBER.encode(), b'keys/root'),
                       'digest': (b'sha256', b'wrong')}
            if fault in changes:
                data = data.replace(*changes[fault])
        else:
            if fault == 'length':
                data = data[:-1]
            if fault == 'symlink':
                item.type, item.linkname = tarfile.SYMTYPE, '/private'
            if fault == 'extra':
                item.name = 'unknown'
        return item, data

    with pytest.raises(ValueError):
        wrapping.decode(repack(raw, change))


def test_duplicate_member_and_oversize_archive_refuse():
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as target:
        for unused in range(2):
            item = tarfile.TarInfo(wrapping.MEMBER)
            item.size = 32
            target.addfile(item, io.BytesIO(bytes(32)))
    with pytest.raises(ValueError, match='HA_ARCHIVE_MEMBER'):
        wrapping.decode(output.getvalue())
    with pytest.raises(ValueError, match='HA_ARCHIVE_SIZE'):
        wrapping.decode(bytes(8193))


def test_consumer_uses_archive_not_signing_loader(monkeypatch):
    key = bytes(range(32))
    seen = []

    def reader(args):
        seen.append(args)
        return wrapping.archive(key)

    monkeypatch.setattr(wrapping, 'vault_archive', reader)
    monkeypatch.setattr(signing_key, 'load', lambda *args: pytest.fail('signing loader used'))
    assert wrapping.load(Path('/private') / wrapping.DATABASE) == key
    assert seen[0].vault_entry == wrapping.ENTRY and seen[0].vault_password_dialog
    assert 'HA custody encryption' in seen[0].vault_purpose
    with pytest.raises(ValueError, match='HA_VAULT_DATABASE'):
        wrapping.load('/private/other.kdbx')


@pytest.mark.skipif(not Path('/usr/bin/keepassxc-cli').exists(), reason='native KeePassXC required')
def test_native_candidate_and_memory_consumer_preserve_original(tmp_path, monkeypatch):
    password = b'public disposable HA test password'
    vault = tmp_path / wrapping.DATABASE
    created = subprocess.run(['/usr/bin/keepassxc-cli', 'db-create', '-p', '-t', '100', str(vault)],
        input=password + b'\n' + password + b'\n', capture_output=True, timeout=30)
    assert created.returncode == 0
    vault.chmod(0o600)
    original = vault.read_bytes()
    actual = subprocess.run
    commands = []

    def run(command, **options):
        assert password.decode() not in ' '.join(command)
        commands.append(command)
        if command[0] == '/usr/bin/zenity':
            return subprocess.CompletedProcess(command, 0, password + b'\n')
        assert options['stdout'] == options['stderr'] == subprocess.DEVNULL
        return actual(command, **options)

    monkeypatch.setattr(wrapping.subprocess, 'run', run)
    monkeypatch.setattr(signing_key, 'load', lambda *args: pytest.fail('signing loader used'))
    receipt = wrapping.prepare(vault, tmp_path / 'candidate')
    assert receipt['original_preserved'] and not receipt['encrypted_kit']
    assert vault.read_bytes() == original
    candidate = tmp_path / 'candidate' / wrapping.DATABASE
    key = wrapping.load(candidate)
    assert len(key) == 32
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, b'synthetic recovery', wrapping.PURPOSE.encode())
    assert AESGCM(wrapping.load(candidate)).decrypt(nonce, ciphertext, wrapping.PURPOSE.encode()) == b'synthetic recovery'
    assert sorted(item.name for item in (tmp_path / 'candidate').iterdir()) == [wrapping.DATABASE]
    assert key.hex() not in str(commands) and key.hex() not in str(receipt)
    assert all(wrapping.ENTRY in command for command in commands if command[0] == '/usr/bin/keepassxc-cli')
    with pytest.raises(ValueError, match='HA_VAULT_CANDIDATE_COMMAND_REFUSED'):
        wrapping.prepare(candidate, tmp_path / 'duplicate')
    assert wrapping.load(candidate) == key
    assert vault.read_bytes() == original
