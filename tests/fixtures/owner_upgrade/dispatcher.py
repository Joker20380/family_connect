"""Native unprivileged scheduler hold with synthetic SQLite and no network."""
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import time
import uuid

from scripts import control_ha_dispatcher_hold as hold
from scripts import control_ha_owner_upgrade as upgrade
from scripts.control_ha_owner_replacement import Docker, configuration, equivalent, record


CODE = '''import sqlite3,time
from pathlib import Path
Path('/fixture/started').write_text('started')
time.sleep(0.6)
with sqlite3.connect('/fixture/state.sqlite') as database:
    database.execute('CREATE TABLE IF NOT EXISTS commits (value INTEGER)')
    database.execute('INSERT INTO commits VALUES (1)')
'''


def count(root):
    path = root / 'state.sqlite'
    if not path.exists():
        return 0
    with sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True) as database:
        return database.execute('SELECT count(*) FROM commits').fetchone()[0]


def run(root):
    started_at_ns = time.time_ns()
    root = Path(root)
    root.mkdir(mode=0o700)
    source = root / 'manage.py'
    source.write_text(CODE)
    source.chmod(0o600)
    label = 'family-connect.ha-dispatcher'
    token = uuid.uuid4().hex
    name = 'fc-ha-dispatcher-' + token
    command = ['sh', '-ec', upgrade.PUBLISHER.format(origin='https://synthetic.invalid')]
    api = Docker()
    container = upgrade.docker('create', '--pull=never', '--name', name, '--label', label + '=' + token,
        '--init', '--network', 'none', '--read-only', '--user', '1000:1000', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', '--pids-limit', '32', '--memory', '128m',
        '--tmpfs', '/tmp:rw,nosuid,size=8m', '--mount', 'type=bind,source=' + str(root) + ',target=/fixture',
        '--mount', 'type=bind,source=' + str(source) + ',target=/app/control_plane/manage.py,readonly',
        upgrade.ROLES['system_publisher'], *command).decode().strip()
    receipts = []
    try:
        upgrade.docker('start', container)
        deadline = time.monotonic() + 8
        while not (root / 'started').exists():
            hold.require(time.monotonic() < deadline, 'LAB_START_TIMEOUT')
            time.sleep(0.01)
        before = api.inspect(container)
        hold.require(before['Config']['Labels'][label] == token, 'LAB_OWNERSHIP')
        parent = before['State']['Pid']
        children = Path(f'/proc/{parent}/task/{parent}/children').read_text().split()
        hold.require(len(children) == 1, 'LAB_CHILDREN')
        binding, _ = hold.process(int(children[0]))
        hold.require(binding['command_sha256'] == hashlib.sha256(b'\0'.join(part.encode() for part in command) + b'\0').hexdigest(),
                     'LAB_COMMAND')
        with hold.Hold(binding, seconds=4, lock_root=root / 'locks') as lease:
            time.sleep(0.9)
            hold.require(count(root) == 1, 'INFLIGHT_COMMIT')
            lease.check()
            time.sleep(0.3)
            hold.require(count(root) == 1, 'NEW_DISPATCH_DURING_HOLD')
        hold.require(lease.statuses == [0, 0], 'HELPER_EXITS')
        receipts.append(dict(case='normal', in_flight_commit_preserved=True, helper_exit_codes=lease.statuses))
        deadline = time.monotonic() + 14
        while count(root) != 2:
            hold.require(time.monotonic() < deadline, 'RESUME_TIMEOUT')
            time.sleep(0.1)
        for fault in ('guardian-killed', 'rescue-killed', 'guardian-frozen'):
            with hold.Hold(binding, seconds=0.5, lock_root=root / 'locks') as lease:
                child = lease.children[1 if fault == 'rescue-killed' else 0][0]
                os.kill(child, signal.SIGSTOP if fault == 'guardian-frozen' else signal.SIGKILL)
                time.sleep(0.7)
                try:
                    lease.check()
                except ValueError:
                    pass
                else:
                    raise ValueError('DEAD_HELPER_ADMITTED')
            hold.require(hold.process(binding['pid'])[1] not in ('T', 't'), 'RESUME_UNCONFIRMED')
            receipts.append(dict(case=fault, scheduler_resumed=True, helper_exit_codes=lease.statuses))
        after = api.inspect(container)
        equivalent(after, configuration(before))
        hold.require(after['State']['Pid'] == before['State']['Pid'] and
                     after['State']['StartedAt'] == before['State']['StartedAt'] and after['RestartCount'] == 0,
                     'LAB_RUNTIME_CHANGED')
        receipt = dict(cases=receipts, image=before['Image'], binding=binding, commits=count(root),
                       started_at_ns=started_at_ns, finished_at_ns=time.time_ns(),
                       work_settlement_proven=False, capture_permitted=False)
        record(root, 'receipt', receipt)
        return receipt
    finally:
        item = api.inspect(container)
        if item:
            hold.require(item['Config']['Labels'].get(label) == token, 'LAB_CLEANUP_OWNERSHIP')
            upgrade.docker('rm', '--force', container)


if __name__ == '__main__':
    import sys
    print(json.dumps(run(sys.argv[1]), sort_keys=True))
