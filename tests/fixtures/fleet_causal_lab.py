"""Disposable SQLite/queued-effect participant; never opens installed product paths."""
import base64
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from control import capture_fleet as fleet

WORKER = '''import pathlib,sqlite3,sys,time
root=pathlib.Path(sys.argv[1])
(root/'attempted').touch(exist_ok=False)
with sqlite3.connect(root/'synthetic.sqlite',timeout=120) as connection:
    connection.execute('BEGIN IMMEDIATE')
    connection.execute("INSERT OR IGNORE INTO effects VALUES ('accepted-before-capture','one effect')")
    connection.execute("UPDATE intents SET state='DONE' WHERE operation='accepted-before-capture'")
    connection.commit()
'''


class SQLiteBoundary:
    def __init__(self, root):
        self.root, self.connection, self.child = root, None, None
        self.lease = os.urandom(32).hex()

    def __enter__(self):
        self.connection = sqlite3.connect(self.root / 'synthetic.sqlite', timeout=0)
        self.connection.execute('BEGIN IMMEDIATE')
        self.child = subprocess.Popen([sys.executable, '-I', '-B', '-c', WORKER, str(self.root)],
                                      stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        deadline = time.monotonic() + 5
        while not (self.root / 'attempted').is_file():
            fleet.require(time.monotonic() < deadline and self.child.poll() is None, 'LAB_WORKER_START')
            time.sleep(0.01)
        return self

    def check(self):
        fleet.require(self.connection is not None and self.connection.in_transaction and
                      self.child is not None and self.child.poll() is None, 'LAB_BOUNDARY_LOST')
        fleet.require(self.connection.execute('SELECT count(*) FROM effects').fetchone() == (0,),
                      'LAB_LATE_EFFECT_BEFORE_RELEASE')
        return self.lease

    def snapshot(self):
        self.check()
        return {'state.sqlite': self.connection.serialize(),
                'intents.json': fleet.encoded(dict(accepted=['accepted-before-capture'], state='QUEUED')),
                'history.json': (self.root / 'history.json').read_bytes()}

    def __exit__(self, *_):
        if self.connection is not None:
            self.connection.rollback()
            self.connection.close()
            self.connection = None
        if self.child is not None:
            fleet.require(self.child.wait(timeout=5) == 0 and self.child.stderr.read() == b'', 'LAB_LATE_WORKER_EXIT')
            self.child.stderr.close()
            self.child = None
            with sqlite3.connect(self.root / 'synthetic.sqlite') as connection:
                connection.execute("INSERT OR IGNORE INTO effects VALUES ('accepted-before-capture','one effect')")
                connection.commit()
                fleet.require(connection.execute('SELECT count(*) FROM effects').fetchone() == (1,) and
                              connection.execute('SELECT state FROM intents').fetchall() == [('DONE',)],
                              'LAB_LATE_REPLAY')
            fleet.private_write(self.root, 'late-result.json', fleet.encoded(dict(
                result='QUEUED_WORK_RECONCILED_EXACTLY_ONCE', effects=1, replay_additional_effects=0)))


def serve(root, slot, source_hash, adapter_hash):
    root = Path(root)
    root.mkdir(mode=0o700, exist_ok=False)
    os.umask(0o077)
    with sqlite3.connect(root / 'synthetic.sqlite') as connection:
        connection.execute('CREATE TABLE effects(operation TEXT PRIMARY KEY,value TEXT NOT NULL)')
        connection.execute('CREATE TABLE intents(operation TEXT PRIMARY KEY,state TEXT NOT NULL)')
        connection.execute("INSERT INTO intents VALUES ('accepted-before-capture','QUEUED')")
        connection.commit()
    history = fleet.encoded(dict(original_unknown=['synthetic-uncertain'], settled=False))
    fleet.private_write(root, 'history.json', history)
    signer = Ed25519PrivateKey.generate()
    fleet.private_write(root, 'ephemeral-signing.key', signer.private_bytes_raw())
    binding = dict(public_key=signer.public_key().public_bytes_raw().hex(), source_sha256=source_hash,
                   coverage_sha256=adapter_hash, late_policy_sha256=fleet.digest(WORKER.encode()),
                   boot=fleet.kernel(), journal=str(root / 'operation'),
                   files=['history.json', 'intents.json', 'state.sqlite'])
    fleet.send(1, dict(slot=slot, binding=binding,
        boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(), fixture_only=True), time.monotonic() + 120)
    expected = fleet.receive(0, time.monotonic() + 120)
    fleet.require(expected['participants'][slot] == binding, 'LAB_PIN_CHANGED')
    boundary = SQLiteBoundary(root)
    member = fleet.Participant(expected, slot, signer, root / 'operation', boundary, boundary.snapshot, seconds=120)
    try:
        while member.state != 'RELEASED':
            command = fleet.receive(0, member.deadline)
            if command == dict(command='OBJECTS', operation=expected['operation']):
                fleet.require(member.state == 'CAPTURED', 'LAB_OBJECT_PHASE')
                member.check()
                response = {name: base64.b64encode((member.root / 'objects' / name).read_bytes()).decode()
                            for name in binding['files']}
                member.check()
            else:
                response = member.run(command)
            fleet.send(1, response, member.deadline)
        fleet.require((root / 'history.json').read_bytes() == history, 'LAB_HISTORY_CHANGED')
    finally:
        member.abort('LAB_CHANNEL_END')
