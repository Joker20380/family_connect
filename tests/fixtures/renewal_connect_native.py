"""Disposable root-only OpenSSH transport qualification; no production paths."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time


def main():
    assert os.geteuid() == 0
    os.umask(0o077)
    root = Path(tempfile.mkdtemp(prefix='fc-connect-native-', dir='/root'))
    for name in ('host', 'client'):
        subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(root / name)],
                       check=True, timeout=10, stdout=subprocess.DEVNULL)
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    port = listener.getsockname()[1]
    listener.close()
    (root / 'known_hosts').write_text('[127.0.0.1]:' + str(port) + ' ' + (root / 'host.pub').read_text())
    (root / 'effect.py').write_text('import os\nfrom pathlib import Path\nroot=Path(' + repr(str(root)) +
        ')\nwith (root/"effects").open("ab", buffering=0) as stream:\n stream.write(b"once\\n")\n os.fsync(stream.fileno())\n' +
        'if (root/"lost").exists(): os.kill(os.getppid(),9)\nelse: print("REPLY")\n')
    (root / 'authorized_keys').write_text('restrict,command="/usr/bin/python3 ' + str(root / 'effect.py') +
                                        '" ' + (root / 'client.pub').read_text())
    (root / 'sshd_config').write_text('\n'.join(('Port ' + str(port), 'ListenAddress 127.0.0.1',
        'HostKey ' + str(root / 'host'), 'AuthorizedKeysFile ' + str(root / 'authorized_keys'),
        'PidFile ' + str(root / 'sshd.pid'), 'PermitRootLogin forced-commands-only',
        'PasswordAuthentication no', 'KbdInteractiveAuthentication no', 'UsePAM no',
        'AllowUsers root', 'LogLevel VERBOSE')) + '\n')
    servers = []

    def start():
        time.sleep(1.4)
        with (root / 'server.log').open('wb') as output:
            servers.append(subprocess.Popen(['/usr/sbin/sshd', '-D', '-e', '-f', str(root / 'sshd_config')],
                                            stdout=output, stderr=output))

    thread = threading.Thread(target=start)
    thread.start()
    command = ['/usr/bin/ssh', '-F', '/dev/null', '-o', 'BatchMode=yes', '-o', 'ConnectionAttempts=3',
        '-o', 'ConnectTimeout=8', '-o', 'LogLevel=DEBUG1', '-o', 'IdentitiesOnly=yes',
        '-o', 'StrictHostKeyChecking=yes', '-o', 'UserKnownHostsFile=' + str(root / 'known_hosts'),
        '-i', str(root / 'client'), '-p', str(port), 'root@127.0.0.1', 'restricted-sync']
    try:
        first = subprocess.run(command, capture_output=True, timeout=30)
        thread.join(5)
        (root / 'first.stderr').write_bytes(first.stderr)
        assert first.returncode == 0 and first.stdout == b'REPLY\n'
        assert first.stderr.count(b'Connecting to ') == 3
        assert (root / 'effects').read_bytes() == b'once\n'
        (root / 'lost').touch()
        second = subprocess.run(command, capture_output=True, timeout=30)
        (root / 'second.stderr').write_bytes(second.stderr)
        assert second.returncode == 255 and second.stderr.count(b'Connecting to ') == 1
        assert (root / 'effects').read_bytes() == b'once\nonce\n'
        print(json.dumps(dict(result='CONNECT_RETRY_ONLY_PASS', first_connections=3,
            first_effects=1, lost_reply_connections=1, lost_reply_effects=1, rpc_retries=0,
            production_paths=0, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())))
    finally:
        thread.join(5)
        for process in servers:
            process.terminate()
            process.wait(5)


if __name__ == '__main__':
    main()
