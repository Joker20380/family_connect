"""Disposable root stand with retained native renewal locks and synthetic state only."""
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def require(condition):
    if not condition:
        raise RuntimeError('NATIVE_SETTLEMENT_REFUSED')


def main():
    require(os.geteuid() == 0 and Path('/.dockerenv').is_file() and not sys.flags.optimize and
            os.environ.get('FC_CAPTURE_RENEWAL_STAND') == '1' and not list(Path('/sandbox').iterdir()))
    raw = sys.stdin.buffer.read(16385)
    require(len(raw) <= 16384)
    inventory = json.loads(raw)
    require(set(inventory) == {'NL1', 'NL2'})
    source = Path('/sandbox/guardians.pyz')
    source_sha = subprocess.check_output([sys.executable, '-I', '-B', '/stand/scripts/package_capture_guardians.py',
                                         '--output', str(source)], text=True, timeout=3).strip()
    descriptor = os.memfd_create('approved-stand-source', os.MFD_ALLOW_SEALING | os.MFD_CLOEXEC)
    with os.fdopen(os.dup(descriptor), 'wb') as output:
        output.write(source.read_bytes())
    fcntl.fcntl(descriptor, fcntl.F_ADD_SEALS,
                fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
    sys.path.insert(0, '/proc/self/fd/' + str(descriptor))
    from control import capture_group as group, capture_launch as launch
    from control.capture_gate import initialize
    launch.trusted_entrypoint(source_sha)
    remote_home = Path('/sandbox/restricted')
    remote_home.mkdir(mode=0o700)
    os.chown(remote_home, 993, 993)
    helper = ('import json,sys\nsys.path.insert(0,"/proc/self/fd/"+sys.argv[1])\n'
              'from control.capture_gate import initialize\nprint(json.dumps(initialize(sys.argv[2]).pins))')
    remote_gate = str(remote_home / 'gate')
    pins = json.loads(subprocess.check_output([sys.executable, '-I', '-S', '-B', '-c', helper,
        str(descriptor), remote_gate], user=993, group=993, extra_groups=[], pass_fds=(descriptor,), timeout=3))
    remote = dict(uid=993, gid=993, groups=[], gate=remote_gate, pins=pins, renewal=None)
    results = []
    for node, expected in sorted(inventory.items()):
        directory = Path('/stand/native') / node
        require(set(expected) == {'production_transport.py', 'credential_renewal.py'})
        for name, digest in expected.items():
            require(hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest)
        for name in ('production_transport', 'credential_renewal'):
            sys.modules.pop(name, None)
        sys.path.insert(0, str(directory))
        native = importlib.import_module('production_transport')
        require(Path(native.__file__) == directory / 'production_transport.py')
        root = Path('/sandbox') / node
        root.mkdir(mode=0o700)
        gate = initialize(root / 'gate')
        state = root / 'unsettled'
        state.mkdir(mode=0o700)
        operation = native.DurableOperation(state)
        with gate.operation(), operation.lock():
            owner = operation.acquire('synthetic-renewal-operation', 'a' * 64)
        require(owner['state'] == 'ACQUIRED' and not list((gate.directory / 'pending').iterdir()))
        with gate.drain(.1):
            pass
        with open('/proc/self/exe', 'rb') as runtime:
            runtime_sha = launch.runtime_sha(runtime.fileno())
        binding = dict(schema=2, source_sha256=source_sha, runtime_sha256=runtime_sha,
            namespaces=launch.namespaces(), mappings=launch.mappings(), coordinator=[0, 0])
        config = root / 'node.json'
        binding_path = root / 'binding.json'
        def arguments():
            config_raw = json.dumps(dict(schema=1, role='NL', state=str(state))).encode()
            config.write_bytes(config_raw)
            config.chmod(0o600)
            selected = dict(config=str(config), config_sha256=hashlib.sha256(config_raw).hexdigest(), state=str(state),
                pins={name: [info.st_dev, info.st_ino] for name in ('.', 'operation.lock')
                      for info in [(state / name).stat()]})
            binding['guardians'] = [dict(uid=0, gid=0, groups=[], gate=str(gate.directory),
                                        pins=group.pins(gate.pins), renewal=selected), remote]
            content = json.dumps(binding, sort_keys=True).encode()
            binding_path.write_bytes(content)
            binding_path.chmod(0o600)
            return str(binding_path), launch.digest(content), str(source)
        refused = False
        with launch.launch(*arguments()) as participants:
            try:
                with group.joint(participants):
                    raise RuntimeError('OPEN_TRANSACTION_ADMITTED')
            except OSError:
                refused = True
        require(refused and (state / 'owner.json').is_file())
        state = root / 'initial-idle'
        state.mkdir(mode=0o700)
        with native.DurableOperation(state).lock():
            pass
        probe = ('import sys\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\n'
                 'from production_transport import DurableOperation,Rejected\n'
                 'try:\n with DurableOperation(Path(sys.argv[2])).lock(): print("IDLE")\n'
                 'except Rejected: print("BUSY")\n')
        def lock_result():
            return subprocess.check_output([sys.executable, '-I', '-B', '-c', probe, str(directory), str(state)],
                                           text=True, timeout=3).strip()
        with launch.launch(*arguments()) as participants:
            require(participants[0].identity[1:] == (0, 0) and participants[1].identity[1:] == (993, 993))
            with group.joint(participants) as window:
                require(lock_result() == 'BUSY')
            require(window.receipt['status'] == 'LOCAL_INTERVAL_CONFIRMED' and not window.receipt['capture_permitted'])
        require(lock_result() == 'IDLE')
        expired = False
        with launch.launch(*arguments()) as participants:
            try:
                with group.joint(participants):
                    time.sleep(2.1)
                    require(lock_result() == 'IDLE')
            except OSError:
                expired = True
        require(expired and lock_result() == 'IDLE')
        results.append(dict(node=node, native_modules=expected, ack_is_not_settlement=True, open_refused=True,
                            actual_native_lock_held=True, deadline_releases_native_lock=True))
        sys.path.remove(str(directory))
    print(json.dumps(dict(schema=1, result='NATIVE_RENEWAL_SETTLEMENT_PASS', source_sha256=source_sha,
        python=sys.version.split()[0], nodes=results, synthetic_state=True, installed=False,
        capture_permitted=False), sort_keys=True))


if __name__ == '__main__':
    main()
