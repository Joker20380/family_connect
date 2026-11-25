"""Authenticated synthetic loopback qualification, also run under the actual mailbox UID."""
import json
import os
from pathlib import Path
import selectors
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import RNS
from LXMF.LXMPeer import LXMPeer

from messenger.codec import address
from messenger.relay import Spool


GENERATION = 'a' * 64


def wait_for(predicate):
    deadline = time.monotonic() + 8
    while not predicate():
        assert time.monotonic() < deadline, 'SYNTHETIC_TIMEOUT'
        time.sleep(.02)


def read_line(stream):
    with selectors.DefaultSelector() as selector:
        selector.register(stream, selectors.EVENT_READ)
        assert selector.select(35), 'SYNTHETIC_RPC_TIMEOUT'
        line = stream.readline()
        assert line, 'SYNTHETIC_PROCESS_EXIT'
        return json.loads(line)


class Peer:
    def __init__(self, role, directory, port, allowed):
        source = Path(__file__).resolve().parents[2]
        self.process = subprocess.Popen([sys.executable, '-B', str(source / 'messenger/tests/mailbox_links_peer.py'),
                                         role, str(directory), str(port), str(allowed)],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True, env={**os.environ, 'PYTHONPATH': str(source) + os.pathsep +
                                                        os.environ.get('PYTHONPATH', '')})
        try:
            self.info = read_line(self.process.stdout)
        except BaseException:
            self.close()
            raise

    def call(self, operation, **request):
        self.process.stdin.write(json.dumps(dict(op=operation, **request)) + '\n')
        self.process.stdin.flush()
        return read_line(self.process.stdout)

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.process.stdin.close()
        self.process.stdout.close()
        self.process.stderr.close()


def qualify(tmp_path):
    identities = {name: RNS.Identity() for name in ('support', 'peer')}
    for name, identity in identities.items():
        directory = tmp_path / name
        directory.mkdir(mode=0o700)
        identity.to_file(str(directory / 'synthetic.identity'))
    allowed = tmp_path / 'allowed.json'
    allowed.write_text(json.dumps([identity.get_public_key().hex() for identity in identities.values()]))
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    peers = []

    def start(role, name):
        process = Peer(role, tmp_path / name, port, allowed)
        peers.append(process)
        return process

    def blob(name):
        return (address(identities[name].get_public_key()) + os.urandom(160)).hex()

    def connect(client, name, identify=True):
        assert node.call('announce') is True
        assert client.call('connect', public=node.info['public'], name=name, identify=identify) is True

    try:
        node = start('node', 'node')
        support = start('client', 'support')
        peer = start('client', 'peer')
        connect(support, 'old')
        connect(support, 'anonymous', False)
        connect(peer, 'peer-old')
        assert peer.call('request', name='peer-old', blob=blob('support'))[0] == 'stored'
        incoming = peer.call('request', name='peer-old', blob=blob('support'))[1]
        assert node.call('stats')['count'] == 2
        assert node.call('arm') is True
        with ThreadPoolExecutor(max_workers=1) as executor:
            delayed = executor.submit(support.call, 'request', name='old', blob=blob('peer'))
            try:
                wait_for(lambda: node.call('paused') is True)
                command = ('import os,signal,sys\n'
                           'os.write(int(sys.argv[1]), (sys.argv[3]+"\\n").encode())\n'
                           'response=b""\n'
                           'while not response.endswith(b"\\n"): response+=os.read(int(sys.argv[2]), 1)\n'
                           'print(response.decode(), end="", flush=True)\n'
                           'signal.pause()\n')
                request = json.dumps(dict(op='hold', public=support.info['public'], generation=GENERATION))
                controller = subprocess.Popen([sys.executable, '-c', command, str(node.process.stdin.fileno()),
                                               str(node.process.stdout.fileno()), request],
                                              pass_fds=(node.process.stdin.fileno(), node.process.stdout.fileno()),
                                              stdout=subprocess.PIPE, text=True)
                try:
                    held = read_line(controller.stdout)
                    assert held['in_process_drained'] and held['new_link_admission'] == 'CLOSED'
                finally:
                    controller.kill()
                    controller.wait(timeout=3)
                    controller.stdout.close()
                assert node.call('observe')['new_link_admission'] == 'CLOSED'
                opened = node.call('open', generation=GENERATION)
                assert opened['new_link_admission'] == 'OPEN_LOCAL_ONLY'
                assert not opened['activation_ready'] and not opened['cross_host_bound']
            finally:
                node.call('release')
            assert delayed.result(timeout=25) == ['unavailable']
        assert support.call('identify', name='anonymous') is True
        assert support.call('request', name='anonymous', blob=blob('peer')) == ['unavailable']
        assert support.call('request', name='old', purge=[incoming]) == LXMPeer.ERROR_NO_ACCESS
        assert node.call('stats')['count'] == 2
        assert peer.call('request', name='peer-old', blob=blob('support'))[0] == 'stored'
        connect(support, 'new')
        assert support.call('request', name='new', blob=blob('peer'))[0] == 'stored'
        assert support.call('request', name='new', purge=[incoming]) == []
        assert node.call('stats')['count'] == 3
        assert node.call('abort', generation=GENERATION)['reason'] == 'OPEN_LINEAGE_REQUIRES_GUARD'
        assert support.call('request', name='old', blob=blob('peer')) == ['unavailable']
    finally:
        for process in reversed(peers):
            process.close()
    reopened = Spool(tmp_path / 'node/spool')
    try:
        assert reopened.stats()['count'] == 3
    finally:
        reopened.close()
    return dict(uid=os.getuid(), gid=os.getgid(), authenticated_rns=True, late_identification_refused=True,
                captured_callback_refused=True, old_link_purge_refused=True, new_link_put_and_purge=True,
                unrelated_old_link_continues=True, controller_sigkill=True, reopened_native_rows=3,
                restart_protected=False, cross_host_bound=False, activation_ready=False, capture_permitted=False)


if __name__ == '__main__':
    runtime = Path(sys.argv[1])
    assert os.getuid() == int(sys.argv[2]), 'EXPECTED_UID'
    result = qualify(runtime)
    with (runtime / 'receipt.json').open('x') as output:
        json.dump(result, output, sort_keys=True)
    print(json.dumps(result, sort_keys=True))
