import json

import pytest

from scripts import package_metadata_panel_overlay as overlay


@pytest.fixture
def baseline(tmp_path, monkeypatch):
    root = tmp_path / 'baseline'
    for group in ('REPLACED', 'PRESERVED'):
        pins = {}
        for name in getattr(overlay, group):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'accepted generation2 bytes\n')
            pins[name] = overlay.digest(target.read_bytes())
        monkeypatch.setattr(overlay, group, pins)
    return root


def test_only_metadata_files_and_query_free_command(baseline, tmp_path):
    output = tmp_path / 'context'
    receipt = overlay.prepare(baseline, overlay.IMAGE, output)
    assert set(receipt['installed']) == set(overlay.REPLACED) | set(overlay.ADDED)
    assert len(receipt['installed']) == 14
    assert not set(receipt['installed']) & set(overlay.PRESERVED)
    assert {str(path.relative_to(output)) for path in output.rglob('*') if path.is_file()} == set(receipt['installed']) | {'Dockerfile'}
    lines = (output / 'Dockerfile').read_text().splitlines()
    assert lines[0] == 'FROM ' + overlay.IMAGE
    assert lines[-2] == 'USER console'
    command = json.loads(lines[-1].removeprefix('CMD '))
    assert command[-2:] == ['--access-logformat', '%(m)s %(U)s %(s)s %(D)s']
    for name in receipt['installed']:
        assert (output / name).read_bytes() == (overlay.ROOT / name).read_bytes()
    with pytest.raises(FileExistsError):
        overlay.prepare(baseline, overlay.IMAGE, output)


@pytest.mark.parametrize('name', tuple(overlay.REPLACED) + tuple(overlay.PRESERVED))
def test_rejects_unknown_runtime_or_lost_alias_layer(baseline, tmp_path, name):
    (baseline / name).write_bytes(b'unexpected bytes')
    with pytest.raises(ValueError, match='preimage'):
        overlay.prepare(baseline, overlay.IMAGE, tmp_path / 'context')
    assert not (tmp_path / 'context').exists()


def test_rejects_pre_hmac_image_and_existing_metadata(baseline, tmp_path):
    with pytest.raises(ValueError, match='Unqualified'):
        overlay.prepare(baseline, 'sha256:' + '0' * 64, tmp_path / 'context')
    target = baseline / overlay.ADDED[0]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b'existing metadata')
    with pytest.raises(ValueError, match='already present'):
        overlay.prepare(baseline, overlay.IMAGE, tmp_path / 'context')
