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


def test_reviewed_android108_source_baseline():
    catalog = verify()
    assert catalog['baseline'] == 'Android108'
    assert catalog['android_sources'][
        'clients/android/app/src/main/java/com/familyconnect/app/ChatThreadView.java'
    ] == 'a02c2f36ee8f8a91df929748c6535b9af6ce757a463ea086e078be14951d5328'


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


@pytest.mark.parametrize('name', [
    'clients/android/app/src/main/java/com/familyconnect/app/ChatSmileys.java',
    'clients/android/app/src/main/java/com/familyconnect/app/ChatSmileyTextView.java',
    'clients/android/app/src/main/java/com/familyconnect/app/ChatThreadView.java',
    'clients/android/app/src/main/java/com/familyconnect/app/ChatGifContour.java',
    'clients/android/app/src/main/assets/chat/icq-classic/provenance.json',
])
def test_source_mutation_rejected_with_safe_path(catalog_tree, name):
    source = catalog_tree / name
    source.write_bytes(source.read_bytes() + b'\n')
    with pytest.raises(ValueError) as failure:
        verify(catalog_tree)
    assert str(failure.value) == f'Android smiley implementation changed: {name}'
    assert str(catalog_tree) not in str(failure.value)


@pytest.mark.parametrize('name', [
    '/private/source.java', '../source.java', 'source\n.java',
    r'\private\source.java', r'C:\private\source.java', 'C:source.java', r'..\source.java',
])
def test_unsafe_source_path_not_disclosed(catalog_tree, name):
    catalog = json.loads((catalog_tree / CATALOG).read_text())
    catalog['android_sources'] = {name: '0' * 64}
    (catalog_tree / CATALOG).write_text(json.dumps(catalog))
    with pytest.raises(ValueError, match='^Unsafe Android smiley source path$'):
        verify(catalog_tree)


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


@pytest.mark.parametrize('entry', ['module', 'script'])
def test_packaging_entrypoints_without_pythonpath(tmp_path, entry):
    import subprocess
    import sys
    directory = ROOT if entry == 'module' else ROOT / 'scripts'
    module = 'scripts.package_linux' if entry == 'module' else 'package_linux'
    code = (f'import sys;sys.path.insert(0,{str(directory)!r});'
            f'from pathlib import Path;from {module} import assemble_bundle;'
            f'assemble_bundle(Path({str(tmp_path)!r}))')
    subprocess.run([sys.executable, '-I', '-B', '-c', code], cwd=tmp_path, check=True)
    verify_bundle(tmp_path)
