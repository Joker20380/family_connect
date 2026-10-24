"""Run the native policy/root-guard integration in an empty isolated kernel network."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import select
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time

parser = argparse.ArgumentParser()
parser.add_argument('--host-netns', type=int, required=True)
parser.add_argument('--worker', type=Path, required=True)
parser.add_argument('--host-nft', action='store_true')
args = parser.parse_args()
if os.geteuid() != 0 or os.stat('/proc/self/ns/net').st_ino == args.host_netns:
    raise SystemExit('Root in a separate network namespace is required')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'clients/linux'))
import auto_guard
import auto_policy

nft = (('/host-usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2', '--library-path',
        '/host-usr/lib/x86_64-linux-gnu', '/host-usr/sbin/nft') if args.host_nft else ('/usr/sbin/nft',))
system = auto_guard.System(nft)
if [link['ifname'] for link in system.links()] != ['lo']:
    raise SystemExit('An empty isolated network is required')
if any('table' in entry for entry in system.run(nft + ('-j', 'list', 'tables'))['nftables']):
    raise SystemExit('An empty isolated firewall is required')
version = json.loads(subprocess.run([str(args.worker), '--version'], check=True, capture_output=True, timeout=4).stdout)
assert version['auto_policy_protocol'] == 1 and version['core_reference'] == 'android106-native105'


def ip(*arguments):
    return system.run(('/usr/sbin/ip',) + arguments)


def tunnel(name, address):
    descriptor = os.open('/dev/net/tun', os.O_RDWR | os.O_CLOEXEC | os.O_NONBLOCK)
    fcntl.ioctl(descriptor, 0x400454ca, struct.pack('16sH', name.encode(), 0x0001 | 0x1000))
    ip('link', 'set', 'dev', name, 'up')
    ip('address', 'add', address, 'dev', name)
    return descriptor


checks = []


def packet(label, descriptor, allowed):
    while select.select([descriptor], [], [], 0)[0]:
        os.read(descriptor, 4096)
    program = '''import json, os, socket
os.setgroups([])
os.setgid(65534)
os.setuid(65534)
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
    try:
        result = client.sendto(b'fc-auto-native', ('198.51.100.20', 53))
    except OSError as error:
        result = -error.errno
    print(json.dumps({'result': result, 'port': client.getsockname()[1]}))
'''
    outcome = json.loads(subprocess.run([sys.executable, '-c', program], check=True, capture_output=True,
                                        text=True, timeout=3).stdout)
    observed = False
    until = time.monotonic() + .1
    while time.monotonic() < until and select.select([descriptor], [], [], max(0, until - time.monotonic()))[0]:
        raw = os.read(descriptor, 4096)
        if len(raw) >= 28 and raw[0] >> 4 == 4 and raw[9] == 17 and raw[16:20] == socket.inet_aton('198.51.100.20'):
            offset = (raw[0] & 15) * 4
            if struct.unpack('!HH', raw[offset:offset + 4]) == (outcome['port'], 53) and raw[offset + 8:] == b'fc-auto-native':
                observed = True
                break
    assert observed == allowed, (label, outcome)
    if not allowed:
        assert outcome['result'] < 0, (label, outcome)
    checks.append(label)


class FixturePlatform:
    def __init__(self, mode):
        self.mode, self.descriptor, self.attempts = mode, None, 0
        self.opened, self.cancelled, self.allow_completion = threading.Event(), threading.Event(), threading.Event()
        self.actions = []

    def configure(self, context):
        context.check()
        self.actions.append('configure')
        return ['awg']

    def prepare(self, context, candidate):
        context.check()
        assert candidate == 'awg'
        self.actions.append('prepare')
        return auto_guard.candidate('awg', 'fcawg12345678', '8.8.8.8', 51820)

    def open(self, context, candidate):
        context.check()
        assert self.descriptor is None and candidate == 'awg'
        self.attempts += 1
        self.descriptor = tunnel('fcawg12345678', '10.79.1.2/32')
        ip('route', 'add', '198.51.100.20/32', 'dev', 'fcawg12345678')
        self.actions.append('open')
        self.opened.set()
        if self.mode == 'cancel':
            assert context.cancel.wait(4), 'host did not receive native cancellation'
            self.cancelled.set()
            assert self.allow_completion.wait(4), 'test did not release delayed completion'
        index = next(link['ifindex'] for link in system.links() if link['ifname'] == 'fcawg12345678')
        return index, False

    def close(self, context):
        context.check()
        self.actions.append('close')
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None

    def release(self, context):
        context.check()
        assert self.descriptor is None
        self.actions.append('release')

    def remember(self, context, candidate):
        context.check()
        assert candidate == 'awg'
        self.actions.append('remember')


def reply(ticket, state=None):
    result = ticket.wait(7)
    assert result['ok'] is True, result
    if state is not None:
        assert result['snapshot']['state'] == state, result
    return result['snapshot']


ip('link', 'set', 'lo', 'up')
outer = tunnel('outer0', '192.0.2.2/24')
ip('route', 'add', 'default', 'dev', 'outer0')
packet('baseline-nonroot-packet', outer, True)
for generation, mode in enumerate(('normal', 'cancel', 'offline', 'child-exit'), 1):
    with tempfile.TemporaryDirectory(prefix='fc-auto-policy-') as directory:
        guard = auto_guard.Guard(1000, format(generation, '032x'), directory, system)
        platform = FixturePlatform(mode)
        host = auto_policy.GuardedHost(guard, platform, generation)
        process = auto_policy.PolicyProcess(host, str(args.worker))
        try:
            assert reply(process.submit('status'))['generation'] == 0
            connect = process.submit('connect', generation, network=True, preferred='awg')
            if mode == 'cancel':
                assert platform.opened.wait(4)
                packet('probe-blocks-unprivileged-packet', platform.descriptor, False)
                disconnect = process.submit('disconnect', generation)
                assert platform.cancelled.wait(4)
                assert not reply(process.submit('status'))['desired_connected']
                assert platform.descriptor is not None and platform.actions[-1] == 'open'
                packet('cancel-waits-for-host-ack-with-guard', platform.descriptor, False)
                platform.allow_completion.set()
                assert not reply(connect)['desired_connected']
                reply(disconnect, 'DISCONNECTED')
                assert 'remember' not in platform.actions
                checks.append('late-open-cannot-resurrect-cancelled-session')
            else:
                connected = reply(connect, 'CONNECTED')
                assert connected['selected'] == 'awg'
                packet(mode + '-ready-real-tun', platform.descriptor, True)
                if mode == 'normal':
                    reply(process.submit('lost', generation, reason='NETWORK'), 'CONNECTED')
                    assert platform.attempts == 2
                    packet('shared-policy-recovery-new-tun', platform.descriptor, True)
                    checks.append('one-shared-recovery-owner')
                elif mode == 'offline':
                    reply(process.submit('network', generation, network=False))
                    restoring = reply(process.submit('lost', generation, reason='NETWORK'), 'RESTORING')
                    assert restoring['desired_connected'] and restoring['retry_at_ms'] > 0
                    assert platform.descriptor is None
                    packet('offline-recovery-keeps-underlay-blocked', outer, False)
                else:
                    process.process.kill()
                    assert process.stopping.wait(3)
                    process.operator.join(timeout=4)
                    assert not process.operator.is_alive() and not process.abort_failed
                    assert platform.descriptor is None and guard.snapshot()['current']['mode'] == 'blocked'
                    packet('native-death-does-not-release-guard', outer, False)
                    checks.append('native-eof-aborts-platform-without-release')
                if mode != 'child-exit':
                    reply(process.submit('disconnect', generation), 'DISCONNECTED')
                    before = list(platform.actions)
                    reply(process.submit('retry', generation), 'DISCONNECTED')
                    assert platform.actions == before
                    stale = process.submit('retry', generation + 1).wait(3)
                    assert not stale['ok'] and stale['error'] == 'STALE'
                    checks.append(mode + '-disconnect-cancels-recovery')
            process.close()
            if mode == 'child-exit':
                guard.release()
            assert system.read() is None
            packet(mode + '-cleanup-restores-underlay', outer, True)
        finally:
            platform.allow_completion.set()
            if process.process.poll() is None or process.reader.is_alive() or process.operator.is_alive():
                process.close()
            guard.close()
os.close(outer)
print(json.dumps(dict(result='PASS', checks=checks, count=len(checks),
    native=version, host_network_changed=False, external_application_bytes=0,
    test_netns_inode=os.stat('/proc/self/ns/net').st_ino, host_netns_inode=args.host_netns,
    scope='actual native Auto policy IPC + root adapter + isolated nftables/TUN; synthetic platform, no AWG/MESH gateway or product service'), indent=2))
