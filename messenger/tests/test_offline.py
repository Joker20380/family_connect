"""Three real processes, offline recipient, persistent encrypted propagation spool."""
import json
import os
from pathlib import Path
import selectors
import socket
import subprocess
import sys
import time

import pytest


class Peer:
    def __init__(self, role, directory, port):
        root=Path(__file__).resolve().parents[2]
        self.process=subprocess.Popen([sys.executable,str(root/'messenger/tests/wire_peer.py'),
            role,str(directory),str(port)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,text=True,
            env={**os.environ,'PYTHONPATH':str(root)+os.pathsep+os.environ.get('PYTHONPATH','')})
        try:self.info=self.read()
        except BaseException:self.close();raise

    def read(self):
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout,selectors.EVENT_READ)
            assert selector.select(15), 'Synthetic peer RPC timed out'
            line=self.process.stdout.readline()
            assert line, 'Synthetic peer exited'
            return json.loads(line)

    def call(self, op, **request):
        self.process.stdin.write(json.dumps(dict(op=op,**request))+'\n');self.process.stdin.flush()
        return self.read()

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=5)
        self.process.stdin.close();self.process.stdout.close()


def wait_for(predicate, timeout=40):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if predicate():return
        time.sleep(.2)
    raise AssertionError('Offline acceptance condition timed out')


def wait_sync(peer, expected):
    def done():
        result=peer.call('sync')
        if result['state']=='running':return False
        assert result['state']==expected, result
        return True
    wait_for(done)


@pytest.mark.parametrize('cleanup',['quota','expiry','ack'])
def test_offline_spool_restart_fetch_and_cleanup(tmp_path,cleanup):
    from messenger.codec import address
    with socket.socket() as socket_:
        socket_.bind(('127.0.0.1',0));port=socket_.getsockname()[1]
    peers=[]
    def start(role,name):
        peer=Peer(role,tmp_path/name,port);peers.append(peer);return peer
    try:
        node=start('node','node')
        alice=start('client','alice');bob=start('client','bob')
        alice.call('trust',public=bob.info['public']);bob.call('trust',public=alice.info['public'])
        bob_public=bob.info['public'];node_address=node.info['node'];node_public=node.info['public']
        bob.close() # No recipient process exists during send or relay restart.
        alice.call('relay',node=node_address)
        for _ in range(3):node.call('announce');time.sleep(.25)
        text='OFFLINE-SYNTHETIC-SECRET-'+('Привет! '*80)
        ident=alice.call('send',peer=address(bytes.fromhex(bob_public)).hex(),text=text,via_relay=True)
        wait_for(lambda:node.call('stats')['count']==1)
        wait_for(lambda:alice.call('messages')[0]['status']=='relayed')
        assert alice.call('messages')[0]['status']!='delivered'
        spool=list((tmp_path/'node/router/lxmf/messagestore').iterdir())
        assert len(spool)==1
        ciphertext=spool[0].read_bytes()
        assert text.encode() not in ciphertext and b'OFFLINE-SYNTHETIC-SECRET-' not in ciphertext
        assert ciphertext[:16]==address(bytes.fromhex(bob_public))
        alice.close();node.close()
        node=start('node','node')
        assert node.info['node']==node_address and node.call('stats')['count']==1
        bob=start('client','bob')
        assert bob.info['public']==bob_public
        bob.call('relay',node=node_address,public=node_public)
        for _ in range(3):node.call('announce');time.sleep(.25)
        # Download requires an allowed identity; refusal must leave spool intact.
        bob.call('fetch')
        wait_sync(bob,'access_denied')
        assert bob.call('messages')==[] and node.call('stats')['count']==1
        node.call('allow',public=bob_public)
        bob.call('fail_writes',enabled=True)
        bob.call('fetch',delete=True)
        wait_sync(bob,'storage_error')
        assert not bob.call('messages') and node.call('stats')['count']==1
        bob.call('fail_writes',enabled=False)
        bob.call('fetch')
        wait_sync(bob,'complete')
        received=bob.call('messages')
        assert received==[dict(id=ident,text=text,status='received',outgoing=False)]
        assert node.call('stats')['count']==1 # Retain on node, test a second retrieval.
        bob.close();bob=start('client','bob')
        bob.call('relay',node=node_address,public=node_public);node.call('announce');time.sleep(.3)
        bob.call('fetch')
        wait_sync(bob,'complete')
        assert bob.call('messages')==received
        if cleanup=='quota':node.call('clean_quota',kilobytes=.001)
        elif cleanup=='expiry':node.call('expire')
        else:
            bob.call('fetch',delete=True)
            wait_sync(bob,'complete')
            assert bob.call('sync')['duplicates']==1 and bob.call('sync')['purged']==1
        assert node.call('stats')==dict(count=0,bytes=0)
        assert not list((tmp_path/'node/router/lxmf/messagestore').iterdir())
    finally:
        for peer in reversed(peers):peer.close()
