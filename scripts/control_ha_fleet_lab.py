"""Four-process or explicit authorized four-host synthetic causal protocol qualification."""
import argparse
import base64
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import sys
import time

from control import capture_fleet as fleet

HOSTS = {'RU': '185.251.89.19', 'NL1': '185.10.158.212', 'NL2': '185.10.158.196'}


def bootstrap(protocol, adapter, slot, root):
    return '''import base64,sys,types
sources=''' + repr([base64.b64encode(protocol).decode(), base64.b64encode(adapter).decode()]) + '''
package=types.ModuleType('control');package.__path__=[];sys.modules['control']=package
module=types.ModuleType('control.capture_fleet');sys.modules[module.__name__]=module
package.capture_fleet=module;exec(compile(base64.b64decode(sources[0]),'capture_fleet.py','exec'),module.__dict__)
adapter=types.ModuleType('lab');exec(compile(base64.b64decode(sources[1]),'fleet_causal_lab.py','exec'),adapter.__dict__)
adapter.serve(''' + repr(str(root)) + ',' + repr(slot) + ',' + repr(fleet.digest(protocol)) + ',' + repr(fleet.digest(adapter)) + ')'


def qualify(destination, known_hosts=None):
    root = Path(destination)
    root.mkdir(mode=0o700, exist_ok=False)
    os.umask(0o077)
    repository = Path(__file__).resolve().parents[1]
    protocol = (repository / 'control/capture_fleet.py').read_bytes()
    adapter = (repository / 'tests/fixtures/fleet_causal_lab.py').read_bytes()
    operation = secrets.token_hex(16)
    streams, errors, handshakes, remote_roots = {}, {}, {}, {}
    ssh = ['ssh', '-oBatchMode=yes', '-oStrictHostKeyChecking=yes', '-oConnectTimeout=6',
           '-oUserKnownHostsFile=' + str(known_hosts)] if known_hosts else None
    deadline = time.monotonic() + 110
    try:
        for slot in fleet.SLOTS:
            private = root / ('native-' + slot)
            if known_hosts and slot in HOSTS:
                private = Path('/root') / ('fc-ha02-causal-lab-' + operation)
            remote_roots[slot] = str(private)
            source = bootstrap(protocol, adapter, slot, private)
            command = [sys.executable, '-I', '-B', '-c', source]
            if known_hosts and slot in HOSTS:
                command = ssh + ['root@' + HOSTS[slot], 'python3 -I -B -c ' + shlex.quote(source)]
            errors[slot] = (root / (slot + '.stderr')).open('xb')
            streams[slot] = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                             stderr=errors[slot], start_new_session=True)
        for slot, process in streams.items():
            handshake = fleet.receive(process.stdout.fileno(), deadline)
            fleet.require(handshake['slot'] == slot and handshake['fixture_only'] is True and
                          handshake['binding']['source_sha256'] == fleet.digest(protocol) and
                          handshake['binding']['coverage_sha256'] == fleet.digest(adapter), 'LAB_SOURCE_BINDING')
            handshakes[slot] = handshake
        if known_hosts:
            fleet.require(len({value['boot'] for value in handshakes.values()}) == 4, 'LAB_DISTINCT_KERNELS_REQUIRED')
        expected = dict(purpose=fleet.PURPOSE, operation=operation, challenge=secrets.token_hex(32),
                        participants={slot: value['binding'] for slot, value in handshakes.items()})
        fleet.contract(expected)
        for process in streams.values():
            fleet.send(process.stdin.fileno(), expected, deadline)

        def exchange(phase, payload):
            for process in streams.values():
                fleet.send(process.stdin.fileno(), dict(command=phase, operation=operation, payload=payload), deadline)
            return {slot: fleet.receive(process.stdout.fileno(), deadline) for slot, process in streams.items()}

        ready = exchange('HELD', {})
        snapshots = exchange('CAPTURED', dict(ready=ready))
        files = {}
        for slot, process in streams.items():
            fleet.send(process.stdin.fileno(), dict(command='OBJECTS', operation=operation), deadline)
            response = fleet.receive(process.stdout.fileno(), deadline)
            files[slot] = {name: base64.b64decode(raw, validate=True) for name, raw in response.items()}
        for name, value in dict(contract=expected, ready=ready, snapshots=snapshots).items():
            fleet.private_write(root, name + '.json', fleet.encoded(value))
        for slot, objects in files.items():
            directory = root / slot
            directory.mkdir(mode=0o700)
            for name, raw in objects.items():
                fleet.private_write(directory, name, raw)
        reader = '''import json,pathlib,sys
sys.path.insert(0,sys.argv[1])
from control import capture_fleet as fleet
root=pathlib.Path(sys.argv[2])
values={name:fleet.document((root/(name+'.json')).read_bytes()) for name in ('contract','ready','snapshots')}
files={slot:{item.name:item.read_bytes() for item in (root/slot).iterdir()} for slot in fleet.SLOTS}
print(fleet.encoded(fleet.verified_manifest(values['contract'],values['ready'],values['snapshots'],files)).decode())
'''
        readback = subprocess.run([sys.executable, '-I', '-B', '-c', reader, str(repository), str(root)],
                                 capture_output=True, timeout=10, check=True)
        manifest = fleet.document(readback.stdout.strip())
        fleet.private_write(root, 'independent-manifest.json', fleet.encoded(manifest))
        seals = exchange('SEALED', dict(snapshots=snapshots, manifest=manifest))
        releases = exchange('RELEASED', dict(seals=seals))
        for process in streams.values():
            process.stdin.close()
            fleet.require(process.wait(timeout=10) == 0, 'LAB_PARTICIPANT_EXIT')
        result = fleet.verify_bundle(expected, ready, snapshots, seals, releases, files)
        late = {}
        for slot in fleet.SLOTS:
            target = str(Path(remote_roots[slot]) / 'late-result.json')
            if known_hosts and slot in HOSTS:
                readback = subprocess.run(ssh + ['root@' + HOSTS[slot], 'cat ' + shlex.quote(target)],
                                         capture_output=True, timeout=10, check=True)
                late[slot] = fleet.document(readback.stdout)
            else:
                late[slot] = fleet.document(Path(target).read_bytes())
            fleet.require(late[slot] == dict(result='QUEUED_WORK_RECONCILED_EXACTLY_ONCE', effects=1,
                                             replay_additional_effects=0), 'LAB_LATE_WORK')
        for name, value in dict(seals=seals, releases=releases, late=late, handshakes=handshakes).items():
            fleet.private_write(root, name + '.json', fleet.encoded(value))
        result.update(fixture_only=True, distinct_kernels=len({value['boot'] for value in handshakes.values()}),
                      private_roots=remote_roots, protocol_sha256=fleet.digest(protocol),
                      adapter_sha256=fleet.digest(adapter), independent_reader_process=True,
                      late_work='FOUR_SYNTHETIC_JOURNALS_EXACTLY_ONCE', product_paths_opened=0)
        fleet.private_write(root, 'result.json', fleet.encoded(result))
        return result
    finally:
        for process in streams.values():
            if not process.stdin.closed:
                process.stdin.close()
        for process in streams.values():
            try:
                process.wait(timeout=125)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process.stdout.close()
        for stream in errors.values():
            stream.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--authorized-hosts-known-hosts', type=Path)
    arguments = parser.parse_args()
    result = qualify(arguments.destination, arguments.authorized_hosts_known_hosts)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
