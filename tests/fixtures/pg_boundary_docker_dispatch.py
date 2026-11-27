"""Actual pre-existing Docker exec, held database dump and independent late readback."""
import hashlib
import json
import select
import subprocess
import time


def line(process, expected=None):
    assert select.select([process.stdout], [], [], 15)[0], 'DISPATCH_PROTOCOL_TIMEOUT'
    value = process.stdout.readline().strip()
    assert value and (expected is None or value == expected), 'DISPATCH_PROTOCOL'
    return value


def run(command, database, image, module, root, operation, containers):
    helper = 'fc-ha02-pg-boundary-' + operation
    sql_base = ['docker', 'exec', '-i', database, 'psql', '-X', '-qAt', '-v', 'ON_ERROR_STOP=1',
                '-U', 'fc_control_plane', '-d', 'fc_control_plane']
    def query(statement):
        return subprocess.run(sql_base, input=statement.encode(), capture_output=True,
                              check=True, timeout=10).stdout.strip()
    query('CREATE TABLE effects(operation text PRIMARY KEY,value text); '
          "INSERT INTO effects VALUES ('history','unchanged'); CREATE SEQUENCE observed_sequence;")
    code = """import hashlib,sys,psycopg
from fc_control_plane.capture_pg_boundary import PostgresBoundary,scope
connection=psycopg.connect(host='127.0.0.1',dbname='fc_control_plane',user='fc_control_plane',
    password='synthetic-capture-lab-not-a-secret',autocommit=True)
with PostgresBoundary(connection,scope(connection),milliseconds=20000) as held:
    print('HELD',flush=True)
    if sys.stdin.readline().strip() != 'RELEASE': raise ValueError('DISPATCH_CONTROLLER_LOST')
    held.check()
    assert connection.execute('SELECT operation,value FROM effects').fetchall()==[('history','unchanged')]
print('RELEASED',flush=True)
"""
    command(['create', '-i', '--name', helper, '--network', 'container:' + database, '--read-only',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--label', 'family-connect.causal-lab=' + operation,
        '--mount', 'type=bind,source=' + str(module) +
        ',destination=/app/control_plane/fc_control_plane/capture_pg_boundary.py,readonly',
        '--entrypoint', 'python', image, '-B', '-c', code])
    containers.append(helper)
    processes = []
    try:
        late = subprocess.Popen(sql_base, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(late)
        late.stdin.write(b"SET statement_timeout='15s'; SELECT pg_backend_pid();\n")
        late.stdin.flush()
        backend = int(line(late))
        holder = subprocess.Popen(['docker', 'start', '-a', '-i', helper], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(holder)
        line(holder, b'HELD')
        statement = b"INSERT INTO effects VALUES ('late','one') ON CONFLICT (operation) DO NOTHING;\n"
        late.stdin.write(statement)
        late.stdin.flush()
        deadline = time.monotonic() + 5
        while query(f"SELECT wait_event_type FROM pg_stat_activity WHERE pid={backend}") != b'Lock':
            assert late.poll() is None and time.monotonic() < deadline, 'DISPATCH_NOT_BLOCKED'
            time.sleep(.02)
        dump = command(['exec', database, 'pg_dump', '-U', 'fc_control_plane', '-d', 'fc_control_plane',
                        '--format=custom', '--no-owner', '--no-acl']).stdout
        (root / 'held-logical.dump').write_bytes(dump)
        assert query('SELECT count(*) FROM effects') == b'1'
        holder.stdin.write(b'RELEASE\n')
        holder.stdin.flush()
        line(holder, b'RELEASED')
        holder.stdin.close()
        assert holder.wait(timeout=5) == 0 and holder.stderr.read() == b''
        late.stdin.write(statement)
        late.stdin.close()
        assert late.wait(timeout=5) == 0 and late.stderr.read() == b''
        observed = query('SELECT operation,value FROM effects ORDER BY operation')
        assert observed == b'history|unchanged\nlate|one', 'DISPATCH_READBACK'
        assert query('SELECT last_value,is_called FROM observed_sequence') == b'1|f'
        verification = 'fc_capture_verify_' + operation
        command(['exec', database, 'createdb', '-U', 'fc_control_plane', verification])
        command(['exec', '-i', database, 'pg_restore', '-U', 'fc_control_plane', '-d', verification,
                 '--single-transaction', '--no-owner', '--no-acl', '--exit-on-error'], input=dump)
        restored = command(['exec', database, 'psql', '-X', '-qAt', '-v', 'ON_ERROR_STOP=1',
            '-U', 'fc_control_plane', '-d', verification, '-c',
            'SELECT operation,value FROM effects; SELECT last_value,is_called FROM observed_sequence']).stdout.strip()
        assert restored == b'history|unchanged\n1|f', 'DISPATCH_INDEPENDENT_DUMP_READBACK'
        command(['exec', database, 'dropdb', '-U', 'fc_control_plane', verification])
        result = dict(result='PREEXISTING_DOCKER_EXEC_FENCED_DUMP_LATE_REPLAY_ONCE',
            independent_readback_sha256=hashlib.sha256(observed).hexdigest(),
            dump_sha256=hashlib.sha256(dump).hexdigest(), dump_bytes=len(dump),
            independent_restored_dump_sha256=hashlib.sha256(restored).hexdigest(),
            captured_history=1, captured_late_effects=0, resumed_late_effects=1,
            repeated_effects=0, production_epoch_fenced=False)
        (root / 'docker-dispatch.json').write_text(json.dumps(result, sort_keys=True))
        return result
    finally:
        for process in reversed(processes):
            if not process.stdin.closed:
                process.stdin.close()
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()
