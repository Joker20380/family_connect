"""Disposable two-UID SQLite/gate qualification; refuses outside an explicit root stand."""
from contextlib import contextmanager
import ctypes
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

sys.path.insert(0, '/stand')
from control.capture_gate import Gate, GateError
from control import capture_group as group

ACTOR = '''import json,os,sqlite3,stat,sys
from pathlib import Path
sys.path.insert(0,'/stand')
from control.capture_gate import Gate,Busy,initialize
directory=Path(sys.argv[1]);action=sys.argv[2]
if action=='initialize':
    gate=initialize(directory/'gate')
    with sqlite3.connect(directory/'record.sqlite') as database:
        database.execute('CREATE TABLE record (value INTEGER NOT NULL)')
        database.execute('INSERT INTO record VALUES (1)')
    print(json.dumps(gate.pins))
else:
    gate=Gate(directory/'gate')
    if action=='permissions':
        for name,mode in (('.',0o700),('pending',0o700),('admission.lock',0o600),('operations.lock',0o600)):
            info=(gate.directory/name).stat()
            assert info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==mode
        print(len(list((gate.directory/'pending').iterdir())))
    elif action=='read':
        database=sqlite3.connect((directory/'record.sqlite').as_uri()+'?mode=ro',uri=True)
        print(database.execute('SELECT value FROM record').fetchone()[0]);database.close()
    else:
        try:
            with gate.operation() as admitted:
                if action=='pending':
                    admitted.uncertain()
                else:
                    assert action=='write'
                    with sqlite3.connect(directory/'record.sqlite') as database:
                        database.execute('UPDATE record SET value=value+1')
            print('OK')
        except Busy:
            print('BUSY')
'''
GUARD = '''import json,socket,sys
sys.path.insert(0,'/stand')
from control.capture_gate import Gate
from control.capture_group import serve
try:
    serve(Gate(sys.argv[1]),socket.socket(fileno=int(sys.argv[2])),json.loads(sys.argv[3]),json.loads(sys.argv[4]))
except (OSError,ValueError):
    sys.exit(1)
'''


def actor(specification, action):
    result = subprocess.run([sys.executable, '-I', '-B', '-c', ACTOR, specification['directory'], action],
        user=specification['uid'], group=specification['uid'], extra_groups=[], capture_output=True, timeout=4)
    assert result.returncode == 0 and not result.stderr, 'ACTOR_REFUSED'
    return result.stdout.decode().strip()


def fresh(label):
    specifications = []
    for uid in (10001, 1000):
        directory = Path('/sandbox') / (label + '-' + str(uid))
        directory.mkdir(mode=0o700)
        os.chown(directory, uid, uid)
        specification = dict(uid=uid, directory=str(directory))
        specification['pins'] = json.loads(actor(specification, 'initialize'))
        specifications.append(specification)
    return specifications


@contextmanager
def guards(specifications):
    participants, children = [], []
    try:
        for specification in specifications:
            parent, child = group.channel_pair()
            process = subprocess.Popen([sys.executable, '-I', '-B', '-c', GUARD,
                specification['directory'] + '/gate', str(child.fileno()), json.dumps(group.identity()),
                json.dumps(specification['pins'])], pass_fds=(child.fileno(),),
                user=specification['uid'], group=specification['uid'], extra_groups=[],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            child.close()
            children.append(process)
            participants.append(group.Participant(parent, (process.pid, specification['uid'], specification['uid']),
                                                   specification['pins']))
        yield participants, children
    finally:
        for participant in participants:
            participant.channel.close()
        for child in children:
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=2)
            assert child.stderr.read() == b''
            child.stderr.close()


def coordinator(specifications):
    try:
        with guards(specifications) as (participants, children):
            with group.joint(participants):
                print(json.dumps(dict(status='READY', children=[child.pid for child in children])), flush=True)
                assert sys.stdin.readline() == 'FINISH\n'
        print('CONFIRMED', flush=True)
    except (OSError, AssertionError):
        print('REFUSED', flush=True)


def lost_coordinator(specifications, failure):
    process = subprocess.Popen([sys.executable, '-I', '-B', __file__, '--coordinator', json.dumps(specifications)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    owned = []
    try:
        assert select.select([process.stdout], [], [], 6)[0], 'COORDINATOR_START_TIMEOUT'
        ready = json.loads(process.stdout.readline())
        assert ready['status'] == 'READY' and len(ready['children']) == 2
        owned = ready['children']
        assert all(actor(specification, 'write') == 'BUSY' for specification in specifications)
        os.kill(process.pid, signal.SIGKILL if failure == 'kill' else signal.SIGSTOP)
        started = time.monotonic()
        for specification in specifications:
            while actor(specification, 'write') == 'BUSY':
                assert time.monotonic() - started < 3.5, 'BOUNDARY_NOT_RELEASED'
                time.sleep(.03)
        if failure == 'stop':
            os.kill(process.pid, signal.SIGCONT)
            process.stdin.write('FINISH\n')
            process.stdin.flush()
            output, error = process.communicate(timeout=3)
            assert process.returncode == 0 and output == 'REFUSED\n' and not error
        else:
            output, error = process.communicate(timeout=3)
            assert process.returncode == -signal.SIGKILL and not output and not error
            for pid in owned:
                assert os.waitpid(pid, 0)[0] == pid
        return round(time.monotonic() - started, 3)
    finally:
        if process.poll() is None:
            os.kill(process.pid, signal.SIGCONT)
            process.kill()
            process.communicate(timeout=3)
        for pid in owned:
            try:
                if os.waitpid(pid, os.WNOHANG)[0] == 0:
                    os.kill(pid, signal.SIGKILL)
                    os.waitpid(pid, 0)
            except (ProcessLookupError, ChildProcessError):
                pass


def main():
    assert os.geteuid() == 0 and Path('/.dockerenv').is_file()
    assert os.environ.get('FC_CAPTURE_GROUP_STAND') == '1'
    assert Path('/sandbox').is_dir() and not list(Path('/sandbox').iterdir())
    assert ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0
    specifications = fresh('joint')
    for specification in specifications:
        try:
            Gate(specification['directory'] + '/gate')
        except OSError:
            pass
        else:
            raise AssertionError('ROOT_GATE_ACCESS_SHOULD_REFUSE')
    with guards(specifications) as (participants, children):
        with group.joint(participants) as window:
            assert all(actor(specification, 'write') == 'BUSY' for specification in specifications)
            snapshot = [int(actor(specification, 'read')) for specification in specifications]
        assert window.receipt['status'] == 'LOCAL_INTERVAL_CONFIRMED' and snapshot == [1, 1]
        assert window.receipt['capture_permitted'] is False
        assert all(child.wait(timeout=2) == 0 for child in children)
    assert all(actor(specification, 'write') == 'OK' for specification in specifications)
    assert all(actor(specification, 'permissions') == '0' for specification in specifications)
    assert [int(actor(specification, 'read')) for specification in specifications] == [2, 2]
    with guards(specifications) as (participants, children):
        participants[0].identity = (children[0].pid, 0, 0)
        try:
            with group.joint(participants):
                raise AssertionError('WRONG_IDENTITY_ACCEPTED')
        except GateError:
            pass
    uncertain = fresh('uncertain')
    assert actor(uncertain[1], 'pending') == 'OK'
    with guards(uncertain) as (participants, children):
        try:
            with group.joint(participants):
                raise AssertionError('UNCERTAIN_ACCEPTED')
        except OSError:
            pass
    assert actor(uncertain[1], 'permissions') == '1'
    delays = {failure: lost_coordinator(fresh(failure), failure) for failure in ('kill', 'stop')}
    assert all(actor(specification, 'permissions') == '0' for specification in specifications)
    print(json.dumps(dict(status='PASS', uids=[10001, 1000], sqlite_snapshot=snapshot,
                          coordinator_loss_seconds=delays, capture_permitted=False, services_changed=False)), flush=True)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--coordinator':
        assert os.geteuid() == 0 and Path('/.dockerenv').is_file() and os.environ.get('FC_CAPTURE_GROUP_STAND') == '1'
        coordinator(json.loads(sys.argv[2]))
    else:
        main()
