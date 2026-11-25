"""Synthetic UID/sandbox qualification; never reads the working mailbox state."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from messenger.relay import Spool


def wait_for(predicate):
    deadline = time.monotonic() + 8
    while not predicate():
        assert time.monotonic() < deadline, 'FIXTURE_TIMEOUT'
        time.sleep(.01)


def request(root, command):
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(4)
        client.connect(str(root / 'control.sock'))
        client.sendall(json.dumps(command).encode() + b'\n')
        return json.loads(client.makefile('rb').readline(8192))


def qualify(root):
    fixture = Path(__file__).with_name('mailbox_fence.py')
    process = subprocess.Popen([sys.executable, '-B', str(fixture), str(root)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    controller = None
    try:
        wait_for(lambda: (root / 'ready').exists() or process.poll() is not None)
        assert process.poll() is None, 'MAILBOX_FIXTURE_EXIT'
        code = ('import json,socket,sys,time;from pathlib import Path\n'
                'root=Path(sys.argv[1]);client=socket.socket(socket.AF_UNIX);client.connect(str(root/"control.sock"))\n'
                'client.sendall(b\'{"action":"hold"}\\n\');response=json.loads(client.makefile("rb").readline())\n'
                'assert response["in_process_drained"];(root/"controller-ready").touch();time.sleep(30)\n')
        controller = subprocess.Popen([sys.executable, '-B', '-c', code, str(root)])
        wait_for(lambda: (root / 'controller-ready').exists() or controller.poll() is not None)
        assert controller.poll() is None, 'CONTROLLER_FIXTURE_EXIT'
        controller.kill()
        controller.wait(timeout=3)
        assert controller.returncode == -9
        time.sleep(.1)
        assert request(root, dict(action='put-support')) == ['unavailable']
        assert request(root, dict(action='put-peer')) == ['stored']
        observed = request(root, dict(action='status'))
        assert observed['in_process_drained'] and not observed['activation_ready']
        assert request(root, dict(action='abort', generation='b' * 64)) == dict(error='GENERATION_MISMATCH')
        assert request(root, dict(action='abort', generation='a' * 64)) == dict(restored=True)
        assert request(root, dict(action='put-support')) == ['stored']
        assert request(root, dict(action='stop')) == dict(count=2)
        assert process.wait(timeout=5) == 0
        reopened = Spool(root / 'spool')
        try:
            assert reopened.stats()['count'] == 2
        finally:
            reopened.close()
        return dict(uid=os.getuid(), gid=os.getgid(), controller_sigkill=True, admission_still_closed=True,
                    unrelated_sender_continues=True, stale_generation_refused=True, abort_restored=True,
                    reopened_native_rows=2, activation_ready=False, capture_permitted=False)
    finally:
        if controller is not None and controller.poll() is None:
            controller.kill()
            controller.wait(timeout=3)
        if process.poll() is None:
            process.kill()
            process.wait(timeout=3)


if __name__ == '__main__':
    root = Path(sys.argv[1])
    assert os.getuid() == int(sys.argv[2]), 'EXPECTED_UID'
    receipt = qualify(root)
    with (root / 'receipt.json').open('x') as output:
        json.dump(receipt, output, sort_keys=True)
    print(json.dumps(receipt, sort_keys=True))
