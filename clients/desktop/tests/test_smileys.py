import hashlib
import json
from pathlib import Path
import shutil

import pytest

from smiley_catalog import FACES, find, insertion, whitespace
from scripts.smiley_assets import ASSETS, CATALOG, ROOT, android_faces, copy_assets, verify, verify_bundle


def test_exact_android_catalog_and_assets():
    assert len(FACES) == 49
    assert list(FACES) == android_faces()
    assert verify()['faces'] == list(FACES)
    assert [face['asset'] for face in FACES] == [f'{first}{last}.gif' for first, letters in [('a', 'abcdefghijklmnopqrstuvwxyz'), ('b', 'abcdefghijklmnopqrstuvw')] for last in letters]
    for index, face in enumerate(FACES):
        assert find(face['token']) == [(0, len(face['token']), index)]
        for alias in face['aliases']:
            assert find(alias) == [(0, len(alias), index)]
        assert hashlib.sha256((ROOT / ASSETS / face['asset']).read_bytes()).hexdigest() == face['sha256']


@pytest.mark.parametrize('boundary', [' ', '\n', '\t', '\r', '\v', '\f', '\x1c', '\u2003', '\u2028', '\u2029'])
def test_android_whitespace(boundary):
    assert whitespace(boundary)
    assert find(boundary + ':)' + boundary) == [(1, 3, 1)]


@pytest.mark.parametrize('boundary', ['a', '\u00a0', '\u2007', '\u202f', '\x85', '.', '🙂'])
def test_not_android_whitespace(boundary):
    assert not whitespace(boundary)
    assert find(boundary + ':)') == find(':)' + boundary) == []


def test_longest_alias_and_original_text():
    text = 'Привет *YAHOO!* *THUMBS UP* *IN LOVE* *ROFL* :) 🙂'
    assert [text[start:end] for start, end, _ in find(text)] == ['*YAHOO!*', '*THUMBS UP*', '*IN LOVE*', '*ROFL*', ':)']
    assert find(':)' * 4) == []
    assert len(find(' '.join([':)'] * 12))) == 12
    with pytest.raises(ValueError):
        find('🙂' * 2049)


def test_longest_boundary_match_wins(monkeypatch):
    import smiley_catalog
    monkeypatch.setattr(smiley_catalog, 'FACES', ({'aliases': ['*HI*']}, {'aliases': ['*HI* *HI*']}))
    assert smiley_catalog.find('*HI* *HI*') == [(0, 9, 1)]


@pytest.mark.parametrize('text,start,end,expected', [
    ('', 0, 0, ':)'), ('аб', 1, 1, ' :) '), ('аб', 0, 0, ':) '),
    ('аб', 2, 2, ' :)'), ('а б', 2, 3, ':)'), ('аб', 0, 2, ':)'),
    ('а\nб', 2, 2, ':) '), ('а\u00a0б', 2, 2, ' :) '),
])
def test_boundary_insertion(text, start, end, expected):
    assert insertion(text, start, end, ':)') == expected


@pytest.fixture
def catalog_tree(tmp_path):
    catalog = verify()
    for name in [CATALOG, *catalog['android_sources']]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    shutil.copytree(ROOT / ASSETS, tmp_path / ASSETS, dirs_exist_ok=True)
    return tmp_path


@pytest.mark.parametrize('mutation', ['missing', 'modified', 'renamed', 'extra', 'symlink'])
def test_build_rejects_asset_inventory_changes(catalog_tree, mutation):
    path = catalog_tree / ASSETS / 'ab.gif'
    if mutation == 'missing':
        path.unlink()
    elif mutation == 'modified':
        path.write_bytes(path.read_bytes() + b'changed')
    elif mutation == 'renamed':
        path.rename(path.with_name('other.gif'))
    elif mutation == 'extra':
        path.with_name('extra.gif').write_bytes(path.read_bytes())
    else:
        path.unlink()
        path.symlink_to(ROOT / ASSETS / 'ab.gif')
    with pytest.raises((ValueError, OSError)):
        copy_assets(catalog_tree / 'bundle', catalog_tree)


def test_packaged_bytes_and_extra_inventory(tmp_path):
    copy_assets(tmp_path)
    shutil.copyfile(ROOT / CATALOG, tmp_path / CATALOG)
    verify_bundle(tmp_path)
    (tmp_path / 'clients/desktop/assets/chat/icq-classic/extra.gif').write_bytes(b'extra')
    with pytest.raises(ValueError):
        verify_bundle(tmp_path)
