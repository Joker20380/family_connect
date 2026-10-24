import fcntl
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

if os.geteuid() != 0 or len(sys.argv) != 3 or os.stat('/proc/self/ns/net').st_ino in (int(sys.argv[2]), os.stat('/proc/1/ns/net').st_ino):
    raise SystemExit('Isolated root network namespace required')
sys.path.insert(0, str(Path(sys.argv[1]) / 'clients/linux'))
import mesh_network as network

def command(*arguments, check=True):
    return subprocess.run(arguments, check=check, capture_output=True, text=True, timeout=5)

def query(*arguments):
    return json.loads(command('ip', '-j', *arguments).stdout)

if [link.get('ifname') for link in query('link', 'show')] != ['lo']:
    raise SystemExit('An empty isolated namespace is required')
command('ip', 'link', 'set', 'lo', 'up')
command('ip', 'link', 'add', 'eth0', 'type', 'dummy')
command('ip', 'link', 'set', 'eth0', 'up')
command('ip', 'address', 'add', '192.0.2.2/24', 'dev', 'eth0')
command('ip', 'route', 'add', 'default', 'dev', 'eth0')
network.available(query('-4', 'rule', 'show'), query('-6', 'rule', 'show'), query('-4', 'route', 'show', 'table', 'all'), query('-d', 'link', 'show'))
for arguments in network.guard_commands('add'):
    command(*arguments)

def guard():
    rules4=query('-4', 'rule', 'show')
    rules6=query('-6', 'rule', 'show')
    routes4=query('-4', 'route', 'show', 'table', str(network.TABLE))
    routes6=query('-6', 'route', 'show', 'table', str(network.TABLE))
    network.verify_guard(rules4, rules6, routes4, routes6)
    return dict(rules4=rules4, rules6=rules6, routes4=routes4, routes6=routes6)

receipt={'guard_initial':guard(), 'scope':'isolated_network_namespace', 'dns':'NOT_RUN', 'mesh_session':'NOT_RUN'}
assert command('ip', '-4', 'route', 'get', '198.51.100.10', check=False).returncode != 0
assert command('ip', '-6', 'route', 'get', '2001:db8::1', check=False).returncode != 0
route=query('-4', 'route', 'get', '198.51.100.10', 'mark', str(network.MARK))
assert route[0]['dev']=='eth0'
assert network.underlying_index(route, query('-d', 'link', 'show')) > 0
descriptor=os.open('/dev/net/tun', os.O_RDWR | os.O_CLOEXEC)
fcntl.ioctl(descriptor, 0x400454ca, struct.pack('16sH', b'fcmesh0', 0x0001 | 0x1000 | 0x8000))
try:
    for arguments in network.packet_commands()[:3]:
        command(*arguments)
    network.verify_packet(query('address', 'show', 'dev', 'fcmesh0'), query('-4', 'route', 'show', 'table', str(network.TABLE)))
    receipt['guard_with_tun']=guard()
    assert query('-4', 'route', 'get', '198.51.100.10')[0]['dev']=='fcmesh0'
    assert query('-4', 'route', 'get', '198.51.100.10', 'mark', str(network.MARK))[0]['dev']=='eth0'
finally:
    os.close(descriptor)
receipt['guard_after_tun_crash']=guard()
assert command('ip', '-4', 'route', 'get', '198.51.100.10', check=False).returncode != 0
for arguments in network.guard_commands('del'):
    command(*arguments)
network.available(query('-4', 'rule', 'show'), query('-6', 'rule', 'show'), query('-4', 'route', 'show', 'table', 'all'), query('-d', 'link', 'show'))
assert query('-4', 'route', 'get', '198.51.100.10')[0]['dev']=='eth0'
receipt.update(result='PASS', host_network_changed=False, live_application_bytes=0)
print(json.dumps(receipt, indent=2))
