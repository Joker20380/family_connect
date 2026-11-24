"""Actual wrapper bytes over synthetic archives, only in a disposable root container."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

sys.path.insert(0, '/stand/source')
from control.capture_profile import command


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    assert os.geteuid() == 0 and Path('/.dockerenv').is_file() and sys.flags.optimize == 0
    assert os.environ.get('FC_CAPTURE_PROFILE_NATIVE_STAND') == '1'
    product = Path('/opt/apps/family_connect')
    profiles = Path('/usr/local/lib/fc-profile-tools')
    assert product.is_dir() and not list(product.iterdir())
    assert profiles.is_dir() and not list(profiles.iterdir())
    supplied = sys.stdin.buffer.read(65537)
    assert len(supplied) <= 65536
    inventory = json.loads(supplied)
    assert len(inventory) == 2 and {entry['node'] for entry in inventory} == {'NL1', 'NL2'}
    root = Path(tempfile.mkdtemp(prefix='capture-profile-', dir='/tmp'))
    root.chmod(0o755)
    launcher = root / 'receiver.pyz'
    shutil.copyfile('/stand/receiver.pyz', launcher)
    launcher.chmod(0o644)
    results = []
    for record in inventory:
        uid = {'NL1': 979, 'NL2': 993}[record['node']]
        assert record['uid'] == uid
        entry, package, executable = (Path(record[field]) for field in ('entry_path', 'snapshot_path', 'executable'))
        assert entry.is_relative_to(product) or entry.is_relative_to(profiles)
        assert package.is_relative_to(profiles) and package.name == 'snapshot.pyz'
        assert executable.is_relative_to(product) and executable.name == 'python'
        for selected in (entry, package, executable):
            assert str(selected) == os.path.normpath(selected) and '..' not in selected.parts
            assert all(not item.is_symlink() for item in (selected, *selected.parents))
            selected.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        wrapper = base64.b64decode(record['entry_base64'], validate=True)
        assert digest(wrapper) == record['entry_sha256']
        command(wrapper, [dict(path=str(package))], str(executable))
        entry.write_bytes(wrapper)
        entry.chmod(0o755)
        executable.symlink_to(sys.executable)
        home = root / record['node']
        home.mkdir(mode=0o700)
        gate = home / 'gate'
        initialize = ('import sys\nsys.path.insert(0,"/stand/source")\n'
                      'from control.capture_gate import initialize\n'
                      f'initialize({str(gate)!r})\n')
        options = dict(user=uid, group=uid, extra_groups=[], capture_output=True, timeout=10)
        payload = ('import json,os,sys\nprint(json.dumps(dict(uid=os.getuid(),cwd=os.getcwd(),'
                   'executable=sys.executable,isolated=sys.flags.isolated,bytecode=sys.dont_write_bytecode,'
                   'command=os.environ["SSH_ORIGINAL_COMMAND"],sentinel="FC_CAPTURE_TEST_SENTINEL" in os.environ,'
                   'request=json.load(sys.stdin))))\n')
        with zipfile.ZipFile(package, 'x') as archive:
            archive.writestr('__main__.py', payload)
        package.chmod(0o644)
        binding = home / 'binding.json'
        binding_raw = json.dumps(dict(schema=1, kind='profile-launcher', capture_gate=str(gate),
            entry_path=str(entry), entry_sha256=digest(wrapper),
            libraries=[dict(path=str(package), sha256=digest(package.read_bytes()))])).encode()
        binding.write_bytes(binding_raw)
        binding.chmod(0o600)
        os.chown(binding, uid, uid)
        arguments = [str(executable), '-I', '-B', str(launcher), '--binding', str(binding),
                     '--binding-sha256', digest(binding_raw)]
        os.chown(home, uid, uid)
        setup = subprocess.run([str(executable), '-I', '-B', '-c', initialize], **options)
        assert setup.returncode == 0, 'STAND_GATE_SETUP'
        def pending_count():
            check = subprocess.run([str(executable), '-I', '-B', '-c',
                f'from pathlib import Path; print(len(list(Path({str(gate / "pending")!r}).iterdir())))'], **options)
            assert check.returncode == 0, 'STAND_PENDING_READ'
            return int(check.stdout)
        environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'SSH_ORIGINAL_COMMAND': 'restricted-sync',
                       'FC_CAPTURE_TEST_SENTINEL': 'synthetic'}
        request = b'{"schema":1,"operation":"READ_ONLY_SECURITY_SNAPSHOT"}'
        native = subprocess.run(arguments, input=request, env=environment, **options)
        assert native.returncode == 0, 'STAND_NATIVE_FAILED'
        assert json.loads(native.stdout) == dict(uid=uid, cwd='/', executable=str(executable),
            isolated=1, bytecode=True, command='restricted-sync', sentinel=False, request=json.loads(request))
        assert pending_count() == 0
        closed = ('import subprocess,sys\nsys.path.insert(0,"/stand/source")\n'
                  'from control.capture_gate import Gate\n'
                  f'with Gate({str(gate)!r}).drain(.5):\n'
                  f' result=subprocess.run({arguments!r},input=b"do not consume",capture_output=True,timeout=5)\n'
                  ' assert result.returncode==75 and not result.stdout and result.stderr==b"CAPTURE_BUSY\\n"\n')
        busy = subprocess.run([str(executable), '-I', '-B', '-c', closed], env=environment, **options)
        assert busy.returncode == 0 and pending_count() == 0, 'STAND_BUSY_FAILED'
        package.write_bytes(b'replaced')
        refused = subprocess.run(arguments, input=request, env=environment, **options)
        assert refused.returncode == 1 and not refused.stdout and pending_count() == 0
        assert entry.read_bytes() == wrapper
        results.append(dict(node=record['node'], uid=uid, wrapper_sha256=digest(wrapper),
            observed_snapshot_sha256=record['snapshot_sha256'], synthetic_archive=True,
            preserved_wrapper=True, isolated_success=True, busy_refused=True, changed_archive_refused=True))
    print(json.dumps(dict(schema=1, result='ISOLATED_PROFILE_WRAPPER_PASS', python=sys.version.split()[0],
        profiles=results, production_changed=False, installed=False, capture_permitted=False), sort_keys=True))


if __name__ == '__main__':
    main()
