import subprocess
import zipfile

import pytest

from scripts.package_technical_metadata_overlay import ADDED, EXISTING, ROOT, build, digest

PINS = {'friends_http.py': '59d1a3cacc0baa6d064696bc415b9e660ee54728b3023a9b5e94665c6e439c32',
        'control/friends/access.py': '6f7755d5b0a98bf8cd40326904927e301c57d359ac2e99d162f309f2b91056d7'}
OVERLAY_SOURCE = '430278008af38943de51cab8454614cb60b5837f'


def baseline(tmp_path):
    path = tmp_path / 'baseline.pyz'
    stage = tmp_path / 'source'
    for source in EXISTING.values():
        copied = stage / source
        copied.parent.mkdir(parents=True, exist_ok=True)
        copied.write_bytes(subprocess.check_output(['git', 'show', OVERLAY_SOURCE + ':' + source], cwd=ROOT))
    subprocess.run(['git', 'apply', '--reverse', str(ROOT / 'deploy/friends/technical-metadata-runtime.patch')],
                   cwd=stage, check=True, capture_output=True)
    with zipfile.ZipFile(path, 'w') as archive:
        for member, source in EXISTING.items():
            raw = (stage / source).read_bytes()
            if member.endswith('access.py'):
                start = raw.index(b' def revoke_device(')
                end = raw.index(b' @staticmethod', start)
                raw = raw[:start] + raw[end:]
            assert digest(raw) == PINS[member]
            archive.writestr(member, raw)
        archive.writestr('control/friends/paid_beta.py', b'accepted policy must remain untouched\n')
        archive.writestr('independent_support.py', b'accepted support must remain untouched\n')
    return path


def test_overlay_preserves_all_unrelated_runtime_bytes_and_no_main_import(tmp_path):
    prior = baseline(tmp_path); target = tmp_path / 'candidate.pyz'
    receipt = build(prior, digest(prior.read_bytes()), target)
    assert set(receipt['changed']) == set(EXISTING) | set(ADDED)
    with zipfile.ZipFile(prior) as old, zipfile.ZipFile(target) as new:
        for member in ('control/friends/paid_beta.py', 'independent_support.py'):
            assert old.read(member) == new.read(member)
        assert b'revoke_device' not in new.read('control/friends/access.py')
        assert b'technical-metadata-v1' in new.read('control/friends/access.py')
        assert b'/friends/device/technical-metadata/v1' in new.read('friends_http.py')
    with pytest.raises(ValueError, match='already installed'):
        build(target, digest(target.read_bytes()), tmp_path / 'second.pyz')


def test_overlay_wrong_pin_and_no_replace_existing_file(tmp_path):
    prior = baseline(tmp_path); target = tmp_path / 'candidate.pyz'
    with pytest.raises(ValueError, match='pin'):
        build(prior, '0'*64, target)
    assert not target.exists()
    target.write_bytes(b'keep immutable artifact')
    with pytest.raises(FileExistsError):
        build(prior, digest(prior.read_bytes()), target)
    assert target.read_bytes() == b'keep immutable artifact'
