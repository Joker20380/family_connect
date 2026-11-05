import json
import os
from pathlib import Path
import secrets
import signal
import socket
import subprocess
import sys


SOCKET = '/run/fc-mesh-supervisor.sock'


def request(value):
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(20)
        connection.connect(SOCKET)
        connection.sendall(json.dumps(value).encode()+b'\n')
        result = json.loads(connection.makefile('rb').readline(65536))
    if 'error' in result:
        raise RuntimeError(result['error'])
    return result


def serve(root):
    assert os.geteuid() == 0 and Path('/.dockerenv').exists() and root.is_relative_to('/run')
    specifications, processes, instances, starts = {}, {}, {}, {}
    drop_start = set()
    def reader(unit):
        command = specifications.get(unit, {}).get('command', [])
        if '-publication-observer' not in command:
            return None
        return Path(command[command.index('-publication-observer')+1])
    def stop(unit):
        process = processes.get(unit)
        path = reader(unit)
        before = path.stat() if path is not None and path.exists() else None
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if before is not None and path.exists():
            after = path.stat()
            assert before.st_dev == after.st_dev and before.st_ino == after.st_ino
            path.unlink()
        return process.returncode if process else None
    with socket.socket(socket.AF_UNIX) as listener:
        listener.bind(SOCKET)
        os.chmod(SOCKET, 0o600)
        listener.listen(16)
        signal.signal(signal.SIGTERM, lambda *_: listener.close())
        try:
            while True:
                connection, _ = listener.accept()
                with connection:
                    try:
                        value = json.loads(connection.makefile('rb').readline(65536))
                        command, unit = value['command'], value['unit']
                        if command == 'register':
                            assert unit not in specifications
                            specifications[unit] = value['specification']
                        elif command == 'start':
                            assert unit in specifications
                            process = processes.get(unit)
                            if not process or process.poll() is not None:
                                specification = specifications[unit]
                                with (root/(unit+'.log')).open('ab') as output:
                                    process = subprocess.Popen(specification['command'], env=specification['environment'],
                                        stdin=subprocess.DEVNULL, stdout=output, stderr=output)
                                processes[unit] = process
                                instances[unit] = secrets.token_hex(16)
                                starts[unit] = starts.get(unit, 0)+1
                        elif command == 'stop':
                            stop(unit)
                        elif command == 'kill':
                            process = processes[unit]
                            process.kill()
                            process.wait(timeout=5)
                            stop(unit)
                        elif command == 'lose-start-response':
                            drop_start.add(unit)
                        else:
                            assert command == 'show'
                        process = processes.get(unit)
                        running = process is not None and process.poll() is None
                        state = dict(ActiveState='active' if running else 'inactive', SubState='running' if running else 'dead',
                            MainPID=str(process.pid) if running else '0', InvocationID=instances.get(unit, ''),
                            NRestarts=str(max(0, starts.get(unit, 0)-1)), Result='success' if not process or process.returncode in (None, 0) else 'exit-code')
                        drop = command == 'start' and unit in drop_start
                        if drop:
                            drop_start.remove(unit)
                        connection.sendall(json.dumps(dict(state=state, returncode=process.returncode if process else None,
                            drop_response=drop)).encode()+b'\n')
                    except Exception as error:
                        connection.sendall(json.dumps(dict(error=type(error).__name__)).encode()+b'\n')
        except OSError:
            pass
        finally:
            for unit in processes:
                stop(unit)
            Path(SOCKET).unlink(missing_ok=True)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'serve':
        serve(Path(sys.argv[2]))
    else:
        assert sys.argv[1] in ('show', 'start', 'stop') and len(sys.argv) in (3, 4)
        result = request(dict(command=sys.argv[1], unit=sys.argv[2]))
        if result['drop_response']:
            os._exit(86)
        if sys.argv[1] == 'show':
            for name, value in result['state'].items():
                print(name+'='+value)
