"""Actual socket protection in an empty, disposable network namespace only."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import types
import zipimport

if (len(sys.argv) != 3 or os.geteuid() != 0 or
        os.stat('/proc/self/ns/net').st_ino in (int(sys.argv[2]), os.stat('/proc/1/ns/net').st_ino)):
    raise SystemExit('Isolated root network namespace required')


def command(*arguments):
    return subprocess.check_output(arguments, text=True, timeout=5)


if [entry['ifname'] for entry in json.loads(command('ip', '-j', 'link', 'show'))] != ['lo']:
    raise SystemExit('An empty network namespace is required')

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'clients/linux'))
import mesh_network

command('ip', 'link', 'add', 'eth0', 'type', 'dummy')
command('ip', 'link', 'set', 'eth0', 'up')
command('ip', 'address', 'add', '192.0.2.2/24', 'dev', 'eth0')
command('ip', 'route', 'add', 'default', 'dev', 'eth0')
for arguments in mesh_network.guard_commands('add'):
    command(*arguments)

archive = str(Path(sys.argv[1]).resolve())
launcher = types.ModuleType('rns_underlay_test_launcher')
exec(zipimport.zipimporter(archive).get_code('__main__'), launcher.__dict__)
with launcher.unpack(archive) as runtime:
    specification = importlib.util.spec_from_file_location('rns_underlay_test_worker', runtime / 'fc_rns_worker.py')
    worker = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(worker)
    stop = threading.Event()
    index = socket.if_nametoindex('eth0')
    callbacks = worker.Callbacks(index, time.monotonic() + 20, stop)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as protected:
        assert callbacks.bindSocket(protected.fileno())
        assert protected.getsockopt(socket.SOL_SOCKET, socket.SO_MARK) == mesh_network.MARK
        assert protected.getsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, 256).rstrip(b'\0') == b'eth0'
        route = json.loads(command('ip', '-j', '-4', 'route', 'get', '198.51.100.10', 'mark', str(mesh_network.MARK)))
        assert route[0]['dev'] == 'eth0'
        assert subprocess.run(['ip', '-4', 'route', 'get', '198.51.100.10'], capture_output=True, timeout=5).returncode != 0
        command('ip', 'link', 'set', 'eth0', 'name', 'eth-new')
        assert not callbacks.bindSocket(protected.fileno())
        callbacks = worker.Callbacks(index, time.monotonic() + 20, stop)
        assert callbacks.bindSocket(protected.fileno())
        stop.set()
        assert not callbacks.bindSocket(protected.fileno())
    stop.clear()
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as unsupported:
        assert not callbacks.bindSocket(unsupported.fileno())
    try:
        worker.Callbacks(socket.if_nametoindex('lo'), time.monotonic() + 20, stop)
        raise AssertionError('loopback accepted')
    except ValueError:
        pass

print(json.dumps(dict(result='PASS', kernel_socket_binding=True, kernel_socket_mark=True,
    marked_route='eth0', unmarked_route='UNREACHABLE', interface_rename_rejected=True,
    replacement_interface_rebound=True, cancel_rejected=True, ipv6_rejected=True,
    scope='isolated_network_namespace', host_network_changed=False, live_application_bytes=0)))
