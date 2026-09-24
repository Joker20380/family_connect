import fcntl
import io
import json
from pathlib import Path
import sqlite3
import tarfile

import pytest
from scripts.server_secret_snapshot import snapshot, verify


@pytest.fixture
def source(tmp_path):
    for name in ['friends-awg','friends-tcp','friends-access','state-product']:
        (tmp_path/name).mkdir(mode=0o700)
    for name in ['friends-awg/registration.lock','friends-awg/server.conf','friends-awg/settings.json',
                 'friends-tcp/server.json','friends-access/referral.key','friends-access/catalog.json']:
        (tmp_path/name).write_bytes(b'PUBLIC TEST ONLY')
    for name in ['friends-awg/peers.db','friends-access/access.db','friends-access/notices.sqlite','state-product/product.db']:
        with sqlite3.connect(tmp_path/name) as c:
            c.execute('CREATE TABLE records (value TEXT)');c.execute("INSERT INTO records VALUES ('synthetic')")
    return tmp_path


def unpack(raw):
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        return {i.name:archive.extractfile(i).read() for i in archive}


def test_restores_databases_and_keys_without_writing_sources(source):
    before={p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()}
    archive=snapshot(source,'ru');report=verify(archive)
    assert report=={'files':9,'databases_verified':4,'role':'ru'}
    assert before=={p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()}
    restored=unpack(archive)
    assert restored['friends-access/referral.key']==b'PUBLIC TEST ONLY'
    with sqlite3.connect(':memory:') as c:
        c.deserialize(restored['friends-access/access.db'])
        assert c.execute('SELECT value FROM records').fetchone()==('synthetic',)
    assert verify(snapshot(source,'nl'))=={'files':4,'databases_verified':1,'role':'nl'}


def test_wal_commit_is_in_snapshot_without_sidecars(source):
    with sqlite3.connect(source/'friends-access/access.db') as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.execute("INSERT INTO records VALUES ('wal-record')");c.commit()
        archive=snapshot(source,'ru');verify(archive)
        restored=unpack(archive)
        assert not any(p.endswith(('-wal','-shm')) for p in restored)
        with sqlite3.connect(':memory:') as recovery:
            recovery.deserialize(restored['friends-access/access.db'])
            assert recovery.execute('SELECT count(*) FROM records').fetchone()==(2,)


def test_busy_registration_and_missing_key_refuse(source):
    with (source/'friends-awg/registration.lock').open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):snapshot(source,'ru')
    (source/'friends-access/referral.key').unlink()
    with pytest.raises(ValueError,match='required'):snapshot(source,'ru')


def test_symlinks_and_unfinished_registration_refuse(source):
    (source/'friends-awg/leak').symlink_to('/etc/passwd')
    with pytest.raises(ValueError,match='symlink'):snapshot(source,'ru')
    (source/'friends-awg/leak').unlink()
    (source/'friends-tcp/server.pending').write_text('synthetic')
    with pytest.raises(ValueError,match='unfinished'):snapshot(source,'ru')


def test_modified_attachment_refused(source):
    files=unpack(snapshot(source,'ru'));files['friends-access/referral.key']=b'changed'
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w:gz') as archive:
        for name,data in files.items():
            item=tarfile.TarInfo(name);item.size=len(data);archive.addfile(item,io.BytesIO(data))
    with pytest.raises(ValueError,match='digest'):verify(out.getvalue())


@pytest.fixture
def infrastructure(tmp_path):
    for name in ('etc/ssh/ssh_host_ed25519_key', 'root/.ssh/authorized_keys'):
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'synthetic')
    base=tmp_path/'opt/apps/family_connect'
    tls=base/'state-product-https/certificates'
    (tls/'archive/example').mkdir(parents=True)
    (tls/'archive/example/key1.pem').write_bytes(b'synthetic TLS')
    (tls/'live/example').mkdir(parents=True)
    (tls/'live/example/privkey.pem').symlink_to('../../archive/example/key1.pem')
    node=base/'mailbox-pilot'
    for name in ('node.identity','settings.json','members.json','state/.volume-id',
                 'state/rns/config','state/rns/storage/transport_identity'):
        path=node/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'synthetic')
    (node/'state/spool').mkdir()
    with sqlite3.connect(node/'state/spool/spool.sqlite') as db:
        db.execute('CREATE TABLE messages (ciphertext BLOB)')
        db.execute('INSERT INTO messages VALUES (?)',(b'synthetic encrypted message',))
    return tmp_path


def test_infrastructure_preserves_tls_link_metadata_and_mailbox(infrastructure):
    raw=snapshot(infrastructure,'ru',infrastructure=True)
    assert verify(raw)['files']==3
    files=unpack(raw);manifest=json.loads(files['PRIVATE-INVENTORY.json'])
    assert len(manifest['symlinks'])==1
    assert files[manifest['symlinks'][0]['target']]==b'synthetic TLS'
    raw=snapshot(infrastructure,'nl',infrastructure=True)
    assert verify(raw)==dict(files=9,databases_verified=1,role='nl')
    assert not any('cache' in p for p in unpack(raw))


def test_infrastructure_rejects_escaping_tls_link(infrastructure):
    tls=infrastructure/'opt/apps/family_connect/state-product-https/certificates'
    (tls/'escape').symlink_to(infrastructure/'etc/ssh/ssh_host_ed25519_key')
    with pytest.raises(ValueError,match='unsafe TLS link'):
        snapshot(infrastructure,'ru',infrastructure=True)


def test_infrastructure_requires_identity(infrastructure):
    (infrastructure/'opt/apps/family_connect/mailbox-pilot/node.identity').unlink()
    with pytest.raises(FileNotFoundError):snapshot(infrastructure,'nl',infrastructure=True)
