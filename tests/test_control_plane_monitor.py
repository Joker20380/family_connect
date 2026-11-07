import json
from pathlib import Path
import subprocess

import pytest

from control_plane import monitor_inventory as monitor


@pytest.mark.parametrize('failure', [None, 'collect', 'import', 'path', 'scope', 'source'])
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
            snapshot.write_text(json.dumps(dict(source='unapproved' if failure == 'source' else source,
                scope='synthetic' if failure == 'scope' else 'production',
                observed_at='2026-10-27T00:00:00Z', registry_status='unavailable', devices=[])))
            return subprocess.CompletedProcess(command, 0, stdout=str(snapshot).encode())
        if failure == 'import':
            raise subprocess.TimeoutExpired(command, 60, stderr=b'private details')
        assert json.loads(options['input'])['registry_status'] == 'unavailable'
        assert command[-1] == 'import_inventory'
        return subprocess.CompletedProcess(command, 0, stdout=b'local receipt')

    receipt = monitor.cycle(tmp_path, run)
    assert receipt['production_writes'] == 0
    assert [item['source'] for item in receipt['sources']] == ['gateway-ru', 'nl-amsterdam-1', 'nl-amsterdam-2']
    assert all(item['status'] == ('FAILED' if failure else 'IMPORTED') for item in receipt['sources'])
    assert 'private' not in json.dumps(receipt)
    if not failure:
        assert all(item['registry_status'] == 'unavailable' for item in receipt['sources'])
    assert outside.read_text() == 'untouched'
    assert sorted(path.name for path in (tmp_path / '.local').glob('*.json')) == ['monitor-latest.json']
    assert (tmp_path / '.local/monitor-latest.json').stat().st_mode & 0o777 == 0o600


def test_monitor_rejects_symlink_local_directory(tmp_path):
    target = tmp_path / 'target'
    target.mkdir()
    (tmp_path / '.local').symlink_to(target)
    with pytest.raises(ValueError):
        monitor.cycle(tmp_path)


def test_timer_budget_covers_all_three_bounded_collection_import_pairs():
    unit = (monitor.BASE / 'monitor.service.in').read_text()
    timeout = next(int(line.split('=', 1)[1]) for line in unit.splitlines() if line.startswith('TimeoutStartSec='))
    assert timeout >= len(monitor.SOURCES) * 120 + 20


def test_subscription_source_failure_imports_unknown_not_zero(tmp_path):
    local = tmp_path / '.local'
    local.mkdir()
    (local / 'subscriptions-source.json').write_text('{}')
    imports = []

    def run(command, **options):
        assert options['timeout'] == 60
        if command[0] != 'docker':
            raise subprocess.TimeoutExpired(command, 60)
        assert command[-1] == 'import_subscriptions'
        imports.append(json.loads(options['input']))
        return subprocess.CompletedProcess(command, 0)

    receipt = monitor.cycle(tmp_path, run)
    assert len(imports) == 1 and imports[0]['status'] == 'unavailable'
    assert imports[0]['devices'] == [] and imports[0]['runtime_sha256'] is None
    assert all(row['status'] == 'FAILED' for row in receipt['sources'])


def test_one_missing_node_never_reuses_other_node_or_stops_the_cycle(tmp_path):
    collected = []
    imported = []
    known_hosts = tmp_path / 'approved-hosts'

    def run(command, **options):
        if command[0] != 'docker':
            source = command[-1]
            assert command[-3:-1] == ['--known-hosts', str(known_hosts)]
            collected.append(source)
            if source == 'nl-amsterdam-1':
                raise subprocess.TimeoutExpired(command, 60)
            path = tmp_path / '.local' / (source + '-sample.json')
            path.write_text(json.dumps(dict(source=source, scope='production',
                observed_at='2026-11-03T00:00:00Z', registry_status='not_collected')))
            return subprocess.CompletedProcess(command, 0, stdout=str(path).encode())
        imported.append(json.loads(options['input'])['source'])
        return subprocess.CompletedProcess(command, 0, stdout=b'')

    result = monitor.cycle(tmp_path, run, known_hosts)
    assert collected == list(monitor.SOURCES)
    assert imported == ['gateway-ru', 'nl-amsterdam-2']
    assert [item['status'] for item in result['sources']] == ['IMPORTED', 'FAILED', 'IMPORTED']
    assert result['sources'][1]['error'] == 'COLLECTION_FAILED'
