"""Exercise the real Auto nftables guard only in an empty isolated network."""
import argparse
import errno
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
import time

parser = argparse.ArgumentParser()
parser.add_argument('--host-netns', type=int, required=True)
parser.add_argument('--host-nft', action='store_true')
args = parser.parse_args()
if os.geteuid() != 0 or os.stat('/proc/self/ns/net').st_ino == args.host_netns:
    raise SystemExit('Root in a separate network namespace is required')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'clients/linux'))
import auto_guard as guard

nft = (('/host-usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2', '--library-path',
        '/host-usr/lib/x86_64-linux-gnu', '/host-usr/sbin/nft') if args.host_nft else ('/usr/sbin/nft',))
system = guard.System(nft)
if [link['ifname'] for link in system.links()] != ['lo']:
    raise SystemExit('An empty isolated network is required')
if any('table' in entry for entry in system.run(nft + ('-j', 'list', 'tables'))['nftables']):
    raise SystemExit('An empty isolated firewall is required')


def ip(*arguments):
    return system.run(('/usr/sbin/ip',) + arguments)


def tunnel(name, address):
    descriptor = os.open('/dev/net/tun', os.O_RDWR | os.O_CLOEXEC | os.O_NONBLOCK)
    fcntl.ioctl(descriptor, 0x400454ca, struct.pack('16sH', name.encode(), 0x0001 | 0x1000))
    ip('link', 'set', 'dev', name, 'up')
    ip('address', 'add', address, 'dev', name)
    return descriptor


def drain(descriptor):
    while select.select([descriptor], [], [], 0)[0]:
        os.read(descriptor, 4096)


checks = []


def received(descriptor, address, port, source_port, protocol, payload=None):
    deadline = time.monotonic() + .1
    expected = socket.inet_pton(socket.AF_INET6 if ':' in address else socket.AF_INET, address)
    while time.monotonic() < deadline:
        if not select.select([descriptor], [], [], max(0, deadline - time.monotonic()))[0]:
            break
        packet = os.read(descriptor, 4096)
        if len(packet) < 28:
            continue
        if packet[0] >> 4 == 4:
            offset, actual_protocol, actual_address = (packet[0] & 15) * 4, packet[9], packet[16:20]
        elif packet[0] >> 4 == 6 and len(packet) >= 48:
            offset, actual_protocol, actual_address = 40, packet[6], packet[24:40]
        else:
            continue
        if actual_protocol != protocol or actual_address != expected or len(packet) < offset + 8:
            continue
        if struct.unpack('!HH', packet[offset:offset + 4]) != (source_port, port):
            continue
        if protocol == 6 and (len(packet) < offset + 20 or not packet[offset + 13] & 2):
            continue
        if payload is not None and packet[offset + 8:] != payload:
            continue
        return True
    return False


def packet(label, descriptor, allowed, *, uid=0, address='198.51.100.20', port=53, mark=0, tcp=False):
    drain(descriptor)
    program = '''import errno, json, os, socket, sys
uid, address, port, mark, tcp = json.loads(sys.argv[1])
if uid:
    os.setgroups([])
    os.setgid(uid)
    os.setuid(uid)
family = socket.AF_INET6 if ':' in address else socket.AF_INET
with socket.socket(family, socket.SOCK_STREAM if tcp else socket.SOCK_DGRAM) as client:
    if mark:
        client.setsockopt(socket.SOL_SOCKET, socket.SO_MARK, mark)
    client.setblocking(False)
    try:
        result = client.connect_ex((address, port)) if tcp else client.sendto(b'fc-auto-check', (address, port))
    except OSError as error:
        result = -error.errno
    source_port = client.getsockname()[1]
print(json.dumps({'result': result, 'source_port': source_port}))
'''
    result = subprocess.run([sys.executable, '-c', program, json.dumps([uid, address, port, mark, tcp])],
                            capture_output=True, text=True, timeout=3, check=True)
    outcome = json.loads(result.stdout)
    observed = received(descriptor, address, port, outcome['source_port'], 6 if tcp else 17,
                        None if tcp else b'fc-auto-check')
    assert observed == allowed, (label, observed, result.stdout.strip())
    if not allowed and not tcp:
        assert outcome['result'] in (-errno.EPERM, -errno.EACCES, errno.EPERM, errno.EACCES), (label, result.stdout)
    checks.append(label)
    drain(descriptor)


def rejected(action, label, exceptions=(ValueError, BlockingIOError)):
    try:
        action()
    except exceptions:
        checks.append(label)
    else:
        raise AssertionError(label)


def forwarded(label, source_fd, destination_fd, allowed, reverse=False):
    drain(destination_fd)
    source, destination = ('198.51.100.20', '10.12.0.2') if reverse else ('10.12.0.2', '198.51.100.20')
    source_port, destination_port = (53, 55555) if reverse else (55555, 53)
    payload = b'fc-auto-forward'
    header = struct.pack('!BBHHHBBH4s4s', 0x45, 0, 28 + len(payload), 1, 0, 64, 17, 0,
                         socket.inet_aton(source), socket.inet_aton(destination))
    total = sum(struct.unpack('!10H', header))
    while total >> 16:
        total = (total & 65535) + (total >> 16)
    header = header[:10] + struct.pack('!H', ~total & 65535) + header[12:]
    os.write(source_fd, header + struct.pack('!HHHH', source_port, destination_port, 8 + len(payload), 0) + payload)
    observed = received(destination_fd, destination, destination_port, source_port, 17, payload)
    assert observed == allowed, (label, observed)
    drain(destination_fd)
    checks.append(label)


assert Path('/proc/sys/net/ipv4/ip_forward').read_text().strip() == '1', 'Enable forwarding only in this namespace'
ip('link', 'set', 'lo', 'up')
outer = tunnel('outer0', '192.0.2.2/24')
lan = tunnel('lan0', '10.12.0.1/24')
ip('-6', 'address', 'add', '2001:db8:1::2/64', 'dev', 'outer0', 'nodad')
ip('route', 'add', 'default', 'dev', 'outer0')
ip('-6', 'route', 'add', 'default', 'dev', 'outer0')
system.apply([{'add': {'table': {'family': 'inet', 'name': 'fc_parity_unrelated'}}}])
packet('baseline-user-v4', outer, True, uid=65534)
packet('baseline-user-v6', outer, True, uid=65534, address='2001:db8:9::8')
forwarded('baseline-forward', lan, outer, True)
with tempfile.TemporaryDirectory(prefix='fc-auto-guard-') as directory:
    owner = guard.Guard(1000, 'a' * 32, directory, system)
    try:
        owner.acquire()
        packet('blocked-user-dns4', outer, False, uid=65534)
        packet('blocked-user-dns6', outer, False, uid=65534, address='2001:db8:9::8')
        packet('blocked-root-unmarked', outer, False)
        packet('root-service-mark4', outer, True, mark=64640)
        packet('root-service-no-ipv6-bypass', outer, False, mark=64640, address='2001:db8:9::8')
        packet('wrong-mark-blocked', outer, False, mark=64641)
        forwarded('forward-closed-before-ready', lan, outer, False)
        rejected(lambda: guard.Guard(1000, 'a' * 32, directory, system), 'exclusive-owner-lock')
        owner.prepare(guard.candidate('awg', 'fcawg12345678', '8.8.8.8', 51820))
        packet('awg-root-exact-endpoint', outer, True, address='8.8.8.8', port=51820)
        packet('awg-user-no-endpoint-bypass', outer, False, uid=65534, address='8.8.8.8', port=51820)
        packet('awg-wrong-port', outer, False, address='8.8.8.8', port=51821)
        owner.block()
        packet('handoff-closes-old-endpoint', outer, False, address='8.8.8.8', port=51820)
        owner.prepare(guard.candidate('tcp', 'fctcp12345678', '8.8.8.8', 443))
        packet('tcp-root-exact-endpoint-mark', outer, True, address='8.8.8.8', port=443, mark=64630, tcp=True)
        packet('tcp-unmarked-root-blocked', outer, False, address='8.8.8.8', port=443, tcp=True)
        packet('tcp-mark-wrong-endpoint-blocked', outer, False, address='8.8.4.4', port=443, mark=64630, tcp=True)
        packet('tcp-user-endpoint-blocked', outer, False, uid=65534, address='8.8.8.8', port=443, tcp=True)
        owner.block()
        owner.prepare(guard.candidate('mesh', 'fcmesh0'))
        packet_fd = tunnel('fcmesh0', '10.79.1.2/32')
        ip('route', 'add', '198.51.100.20/32', 'dev', 'fcmesh0')
        packet('root-probe-before-ready', packet_fd, True)
        packet('user-blocked-before-ready', packet_fd, False, uid=65534)
        index = next(link['ifindex'] for link in system.links() if link['ifname'] == 'fcmesh0')
        owner.ready(index)
        packet('user-ready-real-tun', packet_fd, True, uid=65534)
        forwarded('ready-forward-enters-vpn', lan, packet_fd, True)
        forwarded('ready-forward-reply', packet_fd, lan, True, reverse=True)
        ip('-6', 'address', 'add', '2001:db8:3::2/64', 'dev', 'fcmesh0', 'nodad')
        ip('-6', 'route', 'add', '2001:db8:9::8/128', 'dev', 'fcmesh0')
        packet('mesh-ipv6-remains-blocked', packet_fd, False, uid=65534, address='2001:db8:9::8')
        packet('ready-does-not-open-underlay', outer, False, uid=65534, address='8.8.4.4')
        rejected(owner.release, 'no-release-before-block')
        os.close(packet_fd)
        packet_fd = tunnel('fcmesh0', '10.79.1.2/32')
        ip('route', 'add', '198.51.100.20/32', 'dev', 'fcmesh0')
        packet('reused-interface-name-is-not-ready', packet_fd, False, uid=65534)
        packet('root-cannot-use-stale-probe-rule', packet_fd, False)
        rejected(owner.snapshot, 'stale-interface-is-not-reported-ready')
        owner.block()
        os.close(packet_fd)
        owner.prepare(guard.candidate('mesh', 'fcmesh0'))
        packet_fd = tunnel('fcmesh0', '10.79.1.2/32')
        ip('route', 'add', '198.51.100.20/32', 'dev', 'fcmesh0')
        index = next(link['ifindex'] for link in system.links() if link['ifname'] == 'fcmesh0')
        owner.ready(index)
        owner.close()
        packet('guard-persists-after-owner-exit', outer, False, uid=65534, address='8.8.4.4')
        owner = guard.Guard(1000, 'a' * 32, directory, system)
        owner.acquire()
        packet('restart-blocks-old-ready-tun', packet_fd, False, uid=65534)
        forwarded('restart-blocks-established-forward', lan, packet_fd, False)
        rejected(owner.release, 'no-release-before-tun-cleanup')
        rejected(lambda: owner.prepare(guard.candidate('mesh', 'fcmesh0')), 'no-handoff-with-old-tun')
        os.close(packet_fd)
        owner.release()
        packet('disconnect-restores-underlay4', outer, True, uid=65534)
        packet('disconnect-restores-underlay6', outer, True, uid=65534, address='2001:db8:9::8')
        assert system.read() is None
        assert any(entry.get('table', {}).get('name') == 'fc_parity_unrelated'
                   for entry in system.run(nft + ('-j', 'list', 'tables'))['nftables'])
        checks.append('unrelated-firewall-preserved')
    except BaseException:
        try:
            actual = system.read()
        except Exception:
            actual = None
        if owner.record and actual:
            expected_state = (owner.record['pending'] or {}).get('state') or owner.record['current']
            if expected_state:
                expected = guard.objects(owner.generation, expected_state)
                for wanted, found in zip(expected, actual):
                    if wanted != found:
                        print(json.dumps({'first_mismatch': {'wanted': wanted, 'found': found}}), file=sys.stderr)
                        break
        raise
    finally:
        owner.close()
for variant in ('symlink', 'hardlink', 'public-mode', 'oversized', 'directory-mode', 'lock-symlink'):
    with tempfile.TemporaryDirectory(prefix='fc-auto-storage-') as directory:
        root = Path(directory)
        stored = root / 'guard.json'
        original = root / 'original'
        original.write_text('{}')
        original.chmod(0o600)
        if variant == 'symlink':
            stored.symlink_to(original)
        elif variant == 'hardlink':
            os.link(original, stored)
        elif variant == 'public-mode':
            stored.write_text('{}')
            stored.chmod(0o644)
        elif variant == 'oversized':
            stored.write_bytes(b' ' * 4097)
            stored.chmod(0o600)
        elif variant == 'directory-mode':
            root.chmod(0o777)
        else:
            (root / 'lock').symlink_to(original)

        def unsafe_acquire():
            with guard.Guard(1000, 'a' * 32, root, system) as unsafe:
                unsafe.acquire()

        rejected(unsafe_acquire, 'storage-rejects-' + variant, (ValueError, OSError))
        assert system.read() is None
        assert original.read_text() == '{}'
os.close(outer)
os.close(lan)
print(json.dumps(dict(result='PASS', checks=checks, count=len(checks),
    scope='isolated Linux kernel nftables and TUN packets; no product Auto/MESH session or installer',
    test_netns_inode=os.stat('/proc/self/ns/net').st_ino, host_netns_inode=args.host_netns,
    kernel=os.uname().release,
    external_application_bytes=0, host_network_changed=False), indent=2))
