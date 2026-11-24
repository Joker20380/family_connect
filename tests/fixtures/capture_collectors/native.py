import json
from pathlib import Path
import sqlite3
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from control_plane import monitor_inventory, probe_network

base = Path(sys.argv[2])


def run(command, **options):
    if command[0] != 'docker':
        destination = base / '.local' / (command[-1] + '-native.json')
        destination.write_text(json.dumps(dict(source=command[-1], scope='production',
            observed_at='2026-11-24T00:00:00Z', registry_status='unavailable', devices=[])))
        return subprocess.CompletedProcess(command, 0, stdout=str(destination).encode())
    with sqlite3.connect(base / 'synthetic.db') as database:
        database.execute('CREATE TABLE sample(value)')
        database.execute('INSERT INTO sample VALUES (?)', ('retained',))
    print('committed', flush=True)
    sys.stdin.readline()
    return subprocess.CompletedProcess(command, 0)


if sys.argv[1] == 'monitor':
    monitor_inventory.SOURCES = ('gateway-ru',)
    monitor_inventory.cycle(base, run)
else:
    probe_network.ENDPOINTS = ('gateway-ru',)
    probe_network.cycle(base, lambda source: dict(source=source, observed_at='synthetic', outcome='reachable'), run)
