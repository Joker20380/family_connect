import sqlite3
import pytest
from scripts.sqlite_backup_compare import snapshot,equivalent,logical_digest


def image(rows,*,version=0):
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE records(value)')
        db.executemany('INSERT INTO records VALUES (?)',[(v,) for v in rows])
        db.execute('PRAGMA user_version='+str(version));db.commit()
        return db.serialize()


def test_rows_rowids_types_duplicates_and_versions_preserved():
    values=[None,b'\x00\xff','тест',1,1.5,1]
    assert equivalent(image(values),image(values))
    assert not equivalent(image(values),image(values[::-1]))
    for other in [image(values[:-1]),image([*values,'1']),image(values,version=1)]:
        assert not equivalent(image(values),other)


def test_live_wal_snapshot_includes_committed_pages(tmp_path):
    path=tmp_path/'state.sqlite'
    with sqlite3.connect(path) as db:
        path.chmod(0o600);db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE records(value)');db.execute('INSERT INTO records VALUES (1)');db.commit()
        raw=snapshot(path)
        assert equivalent(raw,image([1]))
        db.execute('INSERT INTO records VALUES (2)');db.commit()
        assert not equivalent(raw,snapshot(path))


def test_rejects_bad_image_and_unsafe_source(tmp_path):
    with pytest.raises(ValueError):logical_digest(b'invalid')
    path=tmp_path/'db';path.write_bytes(image([1]));path.chmod(0o644)
    with pytest.raises(ValueError):snapshot(path)
    path.chmod(0o600);link=tmp_path/'link';link.symlink_to(path)
    with pytest.raises(OSError):snapshot(link)


def test_schema_and_without_rowid_tables():
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE "quoted""table"(id INTEGER PRIMARY KEY, data BLOB) WITHOUT ROWID')
        db.execute('INSERT INTO "quoted""table" VALUES (?,?)',(1,b'bytes'));db.commit()
        before=db.serialize()
        assert equivalent(before,before)
        db.execute('CREATE INDEX by_data ON "quoted""table"(data)');db.commit()
        assert not equivalent(before,db.serialize())
