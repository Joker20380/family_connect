import importlib.util
import io
from pathlib import Path
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('desktop_rns_builder', ROOT / 'scripts/build_desktop_rns.py')
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)
LAUNCHER_SPEC = importlib.util.spec_from_file_location('desktop_rns_launcher', ROOT / 'clients/rns/launcher.py')
launcher = importlib.util.module_from_spec(LAUNCHER_SPEC)
LAUNCHER_SPEC.loader.exec_module(launcher)


def test_relay_archive_reproducible_independent_of_insertion_order():
    entries = {'package/second.py': b'second', '__main__.py': b'first'}
    actual = builder.archive(entries)
    assert actual == builder.archive(dict(reversed(list(entries.items()))))
    with zipfile.ZipFile(io.BytesIO(actual)) as archive:
        assert archive.namelist() == sorted(entries)
        assert all(entry.date_time == (1980, 1, 1, 0, 0, 0) for entry in archive.infolist())


def test_builder_rejects_changed_reference_before_loading_dependencies(tmp_path, monkeypatch):
    source = tmp_path / 'clients/rns'
    source.mkdir(parents=True)
    (source / 'fc_rns_transport.py').write_bytes(b'unaccepted')
    monkeypatch.setattr(builder, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='Accepted106'):
        builder.assemble(tmp_path / 'build')
    assert not (tmp_path / 'build').exists()


@pytest.mark.parametrize('name', ['../escape', '/absolute', 'package/../../escape', 'package//alias.py', 'C:/escape', 'package\\escape'])
def test_private_runtime_extraction_rejects_unsafe_members(tmp_path, name):
    archive = tmp_path / 'test.pyz'
    archive.write_bytes(builder.archive({name: b'not executable'}))
    with pytest.raises(ValueError, match='RNS_ARCHIVE_MEMBER'):
        with launcher.unpack(archive):
            pytest.fail('unsafe archive was extracted')


def test_private_runtime_extraction_is_private_and_removed(tmp_path):
    archive = tmp_path / 'test.pyz'
    archive.write_bytes(builder.archive({'package/module.py': b'body'}))
    with launcher.unpack(archive) as runtime:
        assert runtime.stat().st_mode & 0o777 == 0o700
        assert (runtime / 'package/module.py').stat().st_mode & 0o777 == 0o600
        assert (runtime / 'package/module.py').read_bytes() == b'body'
    assert not runtime.exists()
