import json
import os
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.control_ha_support_exit import NativeRetirement, PersistenceWork, census

ready, release = int(sys.argv[1]), int(sys.argv[2])
target_done = threading.Event()
deleted = threading.Event()


class Tail(threading.Thread):
    def _delete(self):
        super()._delete()
        deleted.set()
        assert os.read(release, 1) == b'x'


owners = [('main', threading.main_thread())]
with PersistenceWork(owners) as work:
    worker = Tail(target=target_done.wait)
    worker.start()
    retirement = NativeRetirement([('owned-tail', worker)])
    target_done.set()
    assert deleted.wait(5)
    snapshot = census('before-persistence', owners, 'python-target-completed')
    assert worker.native_id in snapshot['native_without_python']
    assert snapshot['complete']
    os.write(ready, (json.dumps(snapshot) + '\n').encode())
    if sys.argv[3] == 'kernel':
        retirement.wait()
    work.finish()
    assert not (Path('/proc/self/task') / str(worker.native_id)).exists()
    retirement.close()
os.write(ready, b'REAPED\n')
