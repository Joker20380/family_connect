import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import select
import subprocess
import sys

import pytest

from test_friends_http_runtime import port, running, runtime
from test_restricted_activation_http import activated_device, enable


def line(process):
    assert select.select([process.stdout], [], [], 35)[0], 'bounded synthetic RNS timeout'
    value = process.stdout.readline().strip()
    assert value, 'synthetic RNS peer failed'
    return value


def test_existing_identities_without_field_grants_over_pinned_rns(runtime, tmp_path):
    for name in ('FC_ANDROID_RNS_SOURCE', 'FC_RNS_PROVIDER_SOURCE'):
        if not os.environ.get(name):
            pytest.skip('exact Android/provider candidate paths required')
    devices = [activated_device(runtime), activated_device(runtime)]
    enable(runtime)
    peer = Path(__file__).parent / 'fixtures/existing_users/rns_peer.py'
    number = port()
    processes = []
    try:
        with running(runtime):
            server = subprocess.Popen([sys.executable, str(peer), 'server', str(tmp_path / 'relay'), str(number),
                str(runtime['backend'])], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            processes.append(server)
            public = line(server)
            assert len(base64.b64decode(public, validate=True)) == 64
            clients = []
            for index in range(2):
                client = subprocess.Popen([sys.executable, str(peer), 'client', str(tmp_path / ('client' + str(index))),
                    str(number), public], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                processes.append(client)
                assert line(client) == 'READY'
                clients.append(client)

            def request(index, path, body):
                client = clients[index]
                client.stdin.write(json.dumps(dict(path=path, body=body)) + '\n')
                client.stdin.flush()
                envelope = json.loads(line(client))
                raw = base64.b64decode(envelope['body'], validate=True)
                return envelope['status'], json.loads(raw) if raw else None

            def fetch(index):
                device = devices[index]
                status, challenge = request(index, '/friends/restricted-readiness/challenge',
                    dict(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key))
                assert status == 200
                proof = device.prove_transport_key(challenge['challenge'])
                status, body = request(index, '/friends/restricted-readiness', proof)
                assert status == 200 and body['device'] == device.reference
                assert request(index, '/friends/restricted-readiness', proof)[0] == 403
                return body['device']

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(fetch, range(2)))
            assert results == [device.reference for device in devices] and results[0] != results[1]
            with runtime['access'].db() as database:
                assert all(database.execute('SELECT COUNT(*) FROM restricted_grants WHERE device=?',
                    (device.reference,)).fetchone()[0] == 0 for device in devices)
                database.execute('UPDATE devices SET revoked=1 WHERE device=?', (devices[0].reference,))
            assert request(0, '/friends/restricted-readiness/challenge', dict(public_identity=devices[0].public_identity,
                wireguard_public_key=devices[0].wireguard_public_key))[0] == 403
            assert fetch(1) == devices[1].reference
    finally:
        for process in reversed(processes):
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
