import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

SPEC = importlib.util.spec_from_file_location('monitor_inventory', Path(__file__).resolve().parents[1] / 'control_plane/monitor_inventory.py')
monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)


@pytest.mark.parametrize('failure', [None, 'collect', 'import', 'path', 'scope'])
def test_monitor_is_bounded_sanitized_and_preserves_unknown(tmp_path, failure):
    calls = []
    outside = tmp_path / 'keep.json'
    outside.write_text('untouched')

    def run(command, **options):
        calls.append(command)
        assert options['capture_output'] and options['check'] and options['timeout'] == 60
        if command[0] != 'docker':
            if failure == 'collect':
                raise subprocess.CalledProcessError(1, command, stderr=b'private credentials must not leak')
            if failure == 'path':
                return subprocess.CompletedProcess(command, 0, stdout=str(outside).encode())
            source = command[-1]
            snapshot = tmp_path / '.local' / (source + '-test.json')
            snapshot.write_text(json.dumps(dict(source=source, scope='synthetic' if failure == 'scope' else 'production',
                observed_at='2026-10-27T00:00:00Z', registry_status='unavailable', devices=[])))
            return subprocess.CompletedProcess(command, 0, stdout=str(snapshot).encode())
        if failure == 'import':
            raise subprocess.TimeoutExpired(command, 60, stderr=b'private details')
        assert json.loads(options['input'])['registry_status'] == 'unavailable'
        assert command[-1] == 'import_inventory'
        return subprocess.CompletedProcess(command, 0, stdout=b'local receipt')

    receipt = monitor.cycle(tmp_path, run)
    assert receipt['production_writes'] == 0
    assert len(receipt['sources']) == 2
    assert all(item['status'] == ('FAILED' if failure else 'IMPORTED') for item in receipt['sources'])
    assert 'private' not in json.dumps(receipt)
    if not failure:
        assert all(item['registry_status'] == 'unavailable' for item in receipt['sources'])
    assert outside.read_text() == 'untouched'
    assert not list((tmp_path / '.local').glob('gateway-*.json'))
    assert (tmp_path / '.local/monitor-latest.json').stat().st_mode & 0o777 == 0o600


def test_monitor_rejects_symlink_local_directory(tmp_path):
    target = tmp_path / 'target'
    target.mkdir()
    (tmp_path / '.local').symlink_to(target)
    with pytest.raises(ValueError):
        monitor.cycle(tmp_path)
