import copy
import os
from pathlib import Path
import stat

import pytest

from scripts import control_ha_file_custody as custody
from scripts.control_ha_installed_inventory import Refused


@pytest.fixture
def source(tmp_path, monkeypatch):
    root = tmp_path / 'source'
    root.mkdir()
    monkeypatch.setattr(custody, 'ROOTS', (root,))
    (root / 'issuer.key').write_bytes(b'private-test-material')
    history = root / 'friends-restricted' / 'renewal-state'
    history.mkdir(parents=True)
    (history / 'archive').mkdir()
    (history / 'archive' / 'legacy.json').write_bytes(b'{"original":"opaque"}\n')
    (history / 'operation.lock').write_bytes(b'')
    plan = dict(slot='RU', files={'authority/key': str(root / 'issuer.key')},
                trees={'history': str(history)})
    return root, plan


def test_roundtrip_retains_opaque_bytes_and_private_modes(source, tmp_path):
    root, plan = source
    document = custody.capture(plan)
    assert custody.validate(document) == dict(files=3, bytes=43, directories=2)
    assert custody.verify_witness(custody.witness(document))['writer_fence'] is False
    capsule, checkpoint = custody.seal(document, b'k' * 32)
    assert b'private-test-material' not in capsule
    recovered = custody.unseal(capsule, b'k' * 32, checkpoint)
    private = tmp_path / 'private'
    private.mkdir(mode=0o700)
    receipt = custody.restore(recovered, private / 'restored')
    assert receipt['full_recovery'] is receipt['activation'] is False
    assert (private / 'restored/authority/key').read_bytes() == (root / 'issuer.key').read_bytes()
    assert (private / 'restored/history/archive/legacy.json').read_bytes() == b'{"original":"opaque"}\n'
    for path in (private / 'restored').rglob('*'):
        assert stat.S_IMODE(path.stat().st_mode) == (0o700 if path.is_dir() else 0o600)


@pytest.mark.parametrize('name', ['../escape', '/absolute', 'path/../escape', 'path//other', 'path\\other', '.', 'a/' , 'a\n'])
def test_unsafe_logical_names(source, name):
    root, plan = source
    plan['files'] = {name: str(root / 'issuer.key')}
    with pytest.raises(Refused, match='LOGICAL_PATH'):
        custody.capture(plan)


@pytest.mark.parametrize('name', ['technical-metadata.json', 'registry.sqlite', 'access.db', 'access.db-wal'])
def test_no_database_or_observation_copy(source, name):
    root, plan = source
    candidate = root / name
    candidate.write_bytes(b'no')
    plan['files'] = {'forbidden': str(candidate)}
    with pytest.raises(Refused, match='DATABASE_OR_OBSERVATIONS'):
        custody.capture(plan)


@pytest.mark.parametrize('kind', ['link', 'hardlink', 'fifo', 'large', 'directory'])
def test_nonregular_or_unbounded_material_refused(source, kind, monkeypatch):
    root, plan = source
    target = root / 'bad.key'
    if kind == 'link':
        target.symlink_to(root / 'issuer.key')
    elif kind == 'hardlink':
        os.link(root / 'issuer.key', target)
    elif kind == 'fifo':
        os.mkfifo(target)
    elif kind == 'large':
        monkeypatch.setattr(custody, 'MAX_FILE', 8)
        target.write_bytes(b'x' * 9)
    else:
        target.mkdir()
    plan['files'] = {'bad': str(target)}
    with pytest.raises((Refused, OSError)):
        custody.capture(plan)


@pytest.mark.parametrize('mutation', ['rewrite', 'same_bytes', 'rename', 'add', 'remove', 'directory_replace'])
def test_witness_refuses_changes_even_same_bytes(source, mutation):
    root, plan = source
    document = custody.capture(plan)
    key = root / 'issuer.key'
    history = Path(plan['trees']['history'])
    if mutation == 'rewrite':
        key.write_bytes(b'changed')
    elif mutation == 'same_bytes':
        key.write_bytes(key.read_bytes())
    elif mutation == 'rename':
        replacement = root / 'replacement'
        replacement.write_bytes(key.read_bytes())
        replacement.replace(key)
    elif mutation == 'add':
        (history / 'new.json').write_bytes(b'{}')
    elif mutation == 'remove':
        (history / 'operation.lock').unlink()
    else:
        history.rename(history.with_name('previous'))
        history.mkdir()
    with pytest.raises((Refused, OSError)):
        custody.verify_witness(custody.witness(document))


def test_capture_changed_mid_read_refused(source, monkeypatch):
    root, plan = source
    original = custody.Reader.verify
    def changed(reader):
        (root / 'issuer.key').write_bytes(b'concurrent-change')
        original(reader)
    monkeypatch.setattr(custody.Reader, 'verify', changed)
    with pytest.raises(Refused, match='OBSERVATION_CHANGED'):
        custody.capture(plan)


@pytest.mark.parametrize('mutation', ['cipher', 'key', 'stale', 'document_pin'])
def test_authenticated_checkpoint_refuses_mismatch(source, mutation):
    root, plan = source
    document = custody.capture(plan)
    key = b'k' * 32
    capsule, checkpoint = custody.seal(document, key)
    if mutation == 'cipher':
        capsule = capsule[:-1] + bytes([capsule[-1] ^ 1])
    elif mutation == 'key':
        key = b'z' * 32
    elif mutation == 'stale':
        newer = copy.deepcopy(document)
        newer['finished_at_ns'] += 1
        _, checkpoint = custody.seal(newer, key)
    else:
        checkpoint['document_sha256'] = '0' * 64
    with pytest.raises((Refused, ValueError)):
        custody.unseal(capsule, key, checkpoint)


@pytest.mark.parametrize('mutation', ['missing', 'digest', 'path', 'parent', 'scope', 'mode'])
def test_document_rejected_before_restore(source, tmp_path, mutation):
    root, plan = source
    document = custody.capture(plan)
    if mutation == 'missing':
        del document['entries']['authority/key']
    elif mutation == 'digest':
        document['entries']['authority/key']['sha256'] = '0' * 64
    elif mutation == 'path':
        document['entries']['authority/key']['path'] = str(root / 'different.key')
    elif mutation == 'parent':
        del document['entries']['history/archive']
    elif mutation == 'mode':
        document['entries']['authority/key']['stamp'][4] = stat.S_IFLNK | 0o777
    else:
        document['writer_fence'] = True
    destination = tmp_path / 'must-not-exist'
    with pytest.raises(Refused):
        custody.restore(document, destination)
    assert not destination.exists()


@pytest.mark.parametrize('mutation', ['outside', 'overlap', 'tree_scope', 'duplicate'])
def test_plan_scope_refused(source, mutation):
    root, plan = source
    if mutation == 'outside':
        plan['files']['outside'] = '/etc/shadow'
    elif mutation == 'overlap':
        plan['files']['history/item'] = str(root / 'other')
    elif mutation == 'tree_scope':
        plan['trees']['history'] = str(root / 'all-files')
    else:
        plan['files']['duplicate'] = plan['files']['authority/key']
    with pytest.raises(Refused):
        custody.capture(plan)


def test_existing_or_shared_restore_parent_refused(source, tmp_path):
    root, plan = source
    document = custody.capture(plan)
    private = tmp_path / 'private'
    private.mkdir(mode=0o700)
    target = private / 'existing'
    target.mkdir()
    with pytest.raises(FileExistsError):
        custody.restore(document, target)
    private.chmod(0o755)
    with pytest.raises(Refused, match='RESTORE_PARENT'):
        custody.restore(document, private / 'new')


def test_nested_implicit_directories_remain_private(source, tmp_path):
    root, plan = source
    plan['files'] = {'authority/deep/nested/key': str(root / 'issuer.key')}
    document = custody.capture(plan)
    private = tmp_path / 'private'
    private.mkdir(mode=0o700)
    custody.restore(document, private / 'restored')
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o700
               for path in (private / 'restored').rglob('*') if path.is_dir())


def test_duplicate_json_keys_refused(source):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    root, plan = source
    raw = b'{"purpose":"one","purpose":"two"}'
    nonce, key = b'n' * 12, b'k' * 32
    capsule = custody.MAGIC + nonce + AESGCM(key).encrypt(nonce, raw, custody.PURPOSE.encode())
    checkpoint = dict(ciphertext_sha256=custody.digest(capsule), document_sha256=custody.digest(raw))
    with pytest.raises(Refused, match='DUPLICATE_JSON_KEY'):
        custody.unseal(capsule, key, checkpoint)
