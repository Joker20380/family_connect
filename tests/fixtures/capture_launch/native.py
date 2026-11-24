"""Disposable no-network root stand only: pinned launch across actual OWNER UID shapes."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def require(condition):
    if not condition:
        raise RuntimeError('NATIVE_LAUNCH_REFUSED')


def main():
    require(os.geteuid() == 0 and Path('/.dockerenv').exists() and
            os.environ.get('FC_CAPTURE_LAUNCH_STAND') == '1' and not list(Path('/sandbox').iterdir()))
    source = Path('/sandbox/guardians.pyz')
    source_sha = subprocess.check_output([sys.executable, '-I', '-B', '/stand/scripts/package_capture_guardians.py',
                                          '--output', str(source)], text=True, timeout=3).strip()
    raw = source.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == source_sha)
    descriptor = os.memfd_create('approved-stand-source', os.MFD_ALLOW_SEALING | os.MFD_CLOEXEC)
    with os.fdopen(os.dup(descriptor), 'wb') as output:
        output.write(raw)
    os.fchmod(descriptor, 0o444)
    fcntl.fcntl(descriptor, fcntl.F_ADD_SEALS,
                fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
    sys.path.insert(0, '/proc/self/fd/' + str(descriptor))
    from control import capture_group as group, capture_launch as launcher
    launcher.trusted_entrypoint(source_sha)
    helper = '''import json,sys
from pathlib import Path
sys.path.insert(0,'/proc/self/fd/'+sys.argv[1])
from control.capture_gate import initialize, Gate, Busy
from control.capture_group import pins
if sys.argv[3]=='initialize':
    print(json.dumps(pins(initialize(sys.argv[2]).pins)))
elif sys.argv[3]=='health':
    records = []
    for name in ('.','admission.lock','operations.lock','pending'):
        info = (Path(sys.argv[2])/name).stat()
        records.append([info.st_uid,info.st_gid,info.st_mode & 0o7777])
    print(json.dumps(records))
else:
    try:
        with Gate(sys.argv[2]).operation():
            print('WRITE')
    except Busy:
        print('BUSY')
'''

    def actor(item, operation):
        return subprocess.check_output([sys.executable, '-I', '-S', '-B', '-c', helper, str(descriptor),
            item['gate'], operation], user=item['uid'], group=item['gid'], extra_groups=[],
            pass_fds=(descriptor,), cwd='/', env={'LANG': 'C.UTF-8'}, text=True, timeout=3).strip()

    guardians = []
    for uid in (10001, 1000):
        directory = Path('/sandbox') / str(uid)
        directory.mkdir(mode=0o700)
        os.chown(directory, uid, uid)
        item = dict(uid=uid, gid=uid, groups=[], gate=str(directory / 'gate'))
        item['pins'] = json.loads(actor(item, 'initialize'))
        guardians.append(item)
    with open('/proc/self/exe', 'rb') as executable:
        runtime_sha = hashlib.file_digest(executable, 'sha256').hexdigest()
    binding = dict(schema=1, source_sha256=source_sha, runtime_sha256=runtime_sha,
                   namespaces=launcher.namespaces(), mappings=launcher.mappings(), coordinator=[0, 0], guardians=guardians)
    binding_path = Path('/sandbox/binding.json')

    def arguments():
        binding_raw = json.dumps(binding, sort_keys=True).encode()
        binding_path.write_bytes(binding_raw)
        binding_path.chmod(0o600)
        return str(binding_path), hashlib.sha256(binding_raw).hexdigest(), str(source)

    with launcher.launch(*arguments()) as participants:
        owned = [item.identity[0] for item in participants]
        require([item.identity[1:] for item in participants] == [(10001, 10001), (1000, 1000)])
        source.write_bytes(b'changed path must not affect the sealed children')
        with group.joint(participants) as window:
            require(all(actor(item, 'write') == 'BUSY' for item in guardians))
        require(window.receipt['status'] == 'LOCAL_INTERVAL_CONFIRMED' and not window.receipt['capture_permitted'])
    for pid in owned:
        try:
            os.waitpid(pid, os.WNOHANG)
            raise RuntimeError('UNREAPED_CHILD')
        except ChildProcessError:
            pass
    require(all(actor(item, 'write') == 'WRITE' for item in guardians))
    refused = 0
    try:
        with launcher.launch(*arguments()):
            raise RuntimeError('CHANGED_SOURCE_ACCEPTED')
    except OSError:
        refused += 1
    source.write_bytes(raw)
    binding_file, binding_sha, source_file = arguments()
    probe = subprocess.run([sys.executable, '-I', '-S', '-B', '/stand/scripts/control_ha_guardian_probe.py',
        '--source', source_file, '--source-sha256', source_sha, '--binding', binding_file,
        '--binding-sha256', binding_sha], capture_output=True, text=True, timeout=5)
    require(probe.returncode == 0 and not probe.stderr and
            json.loads(probe.stdout)['status'] == 'LOCAL_LAUNCH_PROBE_CONFIRMED')
    binding['guardians'][1]['pins']['admission.lock'][1] += 100000
    try:
        with launcher.launch(*arguments()):
            raise RuntimeError('WRONG_GATE_ACCEPTED')
    except OSError:
        refused += 1
    require(refused == 2 and all(actor(item, 'write') == 'WRITE' for item in guardians))
    for item in guardians:
        require(json.loads(actor(item, 'health')) ==
                [[item['uid'], item['gid'], mode] for mode in (0o700, 0o600, 0o600, 0o700)])
    os.close(descriptor)
    print(json.dumps(dict(status='PASS', uids=[10001, 1000], sealed_root_import=True,
                         sealed_child_launch=True, source_replacement_safe=True, wrong_gate_refused=True,
                         trusted_standalone_probe=True, permissions_preserved=True, owned_children_reaped=True,
                         capture_permitted=False), sort_keys=True))


if __name__ == '__main__':
    main()
