import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from apps.console import metrics_collector


@pytest.mark.parametrize('failure', [None, 'transfer', 'hash', 'duplicate-binding'])
def test_real_binding_mapping_read_failure_never_becomes_zero(tmp_path, monkeypatch, failure):
    files = {
        'proc/stat': 'cpu  10 20 30 40 10 0 0 0 0 0\ncpu0 1\ncpu1 1\n',
        'proc/sys/kernel/random/boot_id': 'synthetic-boot',
        'sys/class/net/eth0/ifindex': '2', 'sys/class/net/eth0/statistics/rx_bytes': '1234',
        'sys/class/net/eth0/statistics/tx_bytes': '5678', 'sys/class/net/fcopen31/ifindex': '5',
    }
    for name, contents in files.items():
        path = tmp_path/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(contents)
    root = tmp_path/'gateway'; root.mkdir()
    archive = root/'paid-transport.pyz'; archive.write_bytes(b'verified synthetic archive')
    records = {'a'*32: dict(decision=dict(public_key='synthetic-public-key'))}
    if failure == 'duplicate-binding':
        records['b'*32] = records['a'*32]
    state = root/'transport-state.json'; state.write_text(json.dumps(dict(schema=1, node='gateway-ru', records=records)))
    before = state.read_bytes()
    commands = []
    def run(arguments):
        commands.append(arguments)
        if arguments == ['ip', '-j', 'route', 'show', 'default']:
            return '[{"dev":"eth0"}]'
        assert arguments[:3] == [str(root/'awg'), 'show', 'fcopen31']
        if arguments[-1] == 'transfer':
            if failure == 'transfer':
                raise subprocess.CalledProcessError(1, arguments)
            return 'synthetic-public-key\t12\t34\nunknown-key\t56\t78\n'
        assert arguments[-1] == 'latest-handshakes'
        return 'synthetic-public-key\t0\n'
    monkeypatch.setattr(metrics_collector, 'metric_command', run)
    monkeypatch.setattr(metrics_collector, 'Path', lambda path: tmp_path/str(path).lstrip('/'))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest() if failure != 'hash' else '0'*64
    result = metrics_collector.collect_metrics('gateway-ru', digest, root=root)
    assert result['node']['rx'] == 1234 and result['node']['cpu_total'] == 110
    assert result['node']['cpu_idle'] == 50
    assert result['tcp_status'] == result['mesh_status'] == 'not_collected'
    assert state.read_bytes() == before
    if failure:
        assert result['awg_status'] == 'unavailable' and result['unknown_peers'] is None and result['devices'] == []
    else:
        assert result['awg_status'] == 'ok' and result['unknown_peers'] == 1
        assert len(result['devices']) == 1 and result['devices'][0]['device'] == 'a'*32
        assert result['devices'][0]['rx'] == 12 and result['devices'][0]['last_handshake'] is None
        assert len(commands) == 3
