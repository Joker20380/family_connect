import base64
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import struct
import subprocess
import time

import pytest

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = os.environ.get('FC_DESKTOP_RNS_ARTIFACT')
pytestmark = pytest.mark.skipif(not ARTIFACT, reason='requires the built isolated RNS zipapp')


def read_exact(stream, length, deadline):
    result = bytearray()
    while len(result) < length:
        remaining = deadline - time.monotonic()
        assert remaining > 0 and select.select([stream], [], [], remaining)[0], 'bounded RNS read timed out'
        part = os.read(stream.fileno(), length - len(result))
        assert part, 'RNS worker closed its pipe'
        result.extend(part)
    return bytes(result)


def stop(process):
    if process is not None:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def test_packaged_rns_actual_link_four_paths_and_maximum_response(tmp_path):
    archive = str(Path(ARTIFACT).resolve())
    fixture = str(ROOT / 'tests/desktop_rns_peer.py')
    base = ['/usr/bin/python3', '-I', '-S', fixture]
    client = None
    with (tmp_path / 'server.log').open('wb') as server_error, (tmp_path / 'client.log').open('wb') as client_error:
        server = subprocess.Popen(base + ['server', archive, str(tmp_path)], stdout=subprocess.PIPE, stderr=server_error)
        try:
            assert read_exact(server.stdout, 6, time.monotonic() + 10) == b'READY\n'
            client = subprocess.Popen(base + ['client', archive, str(tmp_path)], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=client_error)
            paths = ['/friends/restricted-readiness' + suffix for suffix in ('/challenge', '', '/ack-challenge', '/ack')]
            requests = [b'{}', bytes(range(256)) * 32, b'ack-challenge', b'ack']
            started = time.monotonic()
            for identifier, (path, body) in enumerate(zip(paths, requests), 1):
                command = dict(schema=1, id=identifier, underlying_index=1, budget_ms=40000,
                               path=path, body=base64.b64encode(body).decode())
                raw = json.dumps(command).encode()
                client.stdin.write(struct.pack('!I', len(raw)) + raw)
                client.stdin.flush()
                size = struct.unpack('!I', read_exact(client.stdout, 4, started + 45))[0]
                assert 0 < size <= 131072
                reply = json.loads(read_exact(client.stdout, size, started + 45))
                assert (reply['schema'], reply['id'], reply['code']) == (1, identifier, 'OK')
                envelope = json.loads(base64.b64decode(reply['body'], validate=True))
                expected = bytes(range(256)) * 256 if identifier == 2 else body
                assert envelope['status'] == 200 and base64.b64decode(envelope['body'], validate=True) == expected
            client.stdin.close()
            assert client.wait(timeout=5) == 0
            assert json.loads((tmp_path / 'client-result.json').read_text()) == dict(exit_code=0, binds=[True], crypto_provider='internal')
            records = [json.loads(line) for line in (tmp_path / 'requests.jsonl').read_text().splitlines()]
            assert records == [dict(path=path, size=len(body), sha256=hashlib.sha256(body).hexdigest())
                               for path, body in zip(paths, requests)]
            private = tmp_path / 'private'
            private.mkdir(mode=0o700)
            client = subprocess.Popen(base + ['client', archive, str(tmp_path)], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=client_error, env={**os.environ, 'TMPDIR': str(private)})
            raw = json.dumps(dict(schema=1, id=1, underlying_index=1, budget_ms=20000,
                path=paths[0], body=base64.b64encode(requests[0]).decode())).encode()
            client.stdin.write(struct.pack('!I', len(raw)) + raw)
            client.stdin.flush()
            deadline = time.monotonic() + 25
            size = struct.unpack('!I', read_exact(client.stdout, 4, deadline))[0]
            assert 0 < size <= 131072
            assert json.loads(read_exact(client.stdout, size, deadline))['code'] == 'OK'
            client.send_signal(signal.SIGINT)
            client.stdin.close()
            assert client.wait(timeout=5) == 0
            assert not list(private.iterdir()), 'RNS private runtime or ephemeral identity survived cancellation'
        finally:
            stop(client)
            stop(server)
