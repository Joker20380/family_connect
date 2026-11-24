from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile

import pytest

from scripts import control_ha_recovery_kit as kit
from scripts import control_ha_recovery_cold as cold
from scripts import control_ha_recovery_probe as probe


def wheel(name='fixture', version='1.0', extra=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr(f'{name}-{version}.dist-info/METADATA', f'Name: {name}\nVersion: {version}\n')
        if extra:
            archive.writestr(extra, b'unsafe')
    return stream.getvalue()


@pytest.fixture
def sources():
    result = {name: b'fixture==1.0\n' for name in kit.LOCKS}
    result.update({name: b'{}' for name in kit.SCHEMAS})
    result.update({name: b'fixture' for name in kit.NATIVE})
    result[kit.BOOTSTRAP] = Path(kit.__file__).read_bytes()
    result['scripts/__init__.py'] = b''
    return result


@pytest.fixture
def wheels():
    return {'fixture-1.0-py3-none-any.whl': wheel()}


def repack(raw, checkpoint, mutate):
    stream = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        entries = [(member, archive.extractfile(member).read()) for member in archive]
    mutate(entries)
    with tarfile.open(fileobj=stream, mode='w:') as archive:
        for member, body in entries:
            archive.addfile(member, io.BytesIO(body))
    raw = stream.getvalue()
    return raw, checkpoint | {'archive_sha256': kit.digest(raw)}


def test_standalone_exact_private_restore_without_project_imports(sources, wheels, tmp_path):
    raw, checkpoint = kit.pack(sources, wheels, 'a' * 40)
    assert (raw, checkpoint) == kit.pack(sources, wheels, 'a' * 40)
    for name, body in [('kit.tar', raw), ('checkpoint.json', kit.encoded(checkpoint)),
                       ('bootstrap.py', sources[kit.BOOTSTRAP])]:
        kit.private_file(tmp_path / name, body)
    output = tmp_path / 'restored'
    result = subprocess.run([sys.executable, '-I', str(tmp_path / 'bootstrap.py'), str(tmp_path / 'kit.tar'),
        str(tmp_path / 'checkpoint.json'), str(output)], cwd=tmp_path, capture_output=True, check=True)
    receipt = json.loads(result.stdout)
    assert receipt['source_files'] == len(sources) and receipt['wheels'] == 1
    assert receipt['activation'] is receipt['full_recovery'] is False
    for name, body in sources.items():
        target = output / 'source' / name
        assert target.read_bytes() == body and target.stat().st_mode & 0o777 == 0o600
    assert '--hash=sha256:' in (output / 'requirements-hashed.txt').read_text()
    with pytest.raises(FileExistsError):
        kit.restore(raw, checkpoint, output)


@pytest.mark.parametrize('mutation', ['archive', 'purpose', 'source_commit', 'manifest_sha256', 'bootstrap_sha256'])
def test_changed_or_stale_input_refuses_before_output(sources, wheels, tmp_path, mutation):
    raw, checkpoint = kit.pack(sources, wheels, 'a' * 40)
    if mutation == 'archive':
        raw += b'changed'
    else:
        checkpoint[mutation] = 'b' * len(checkpoint[mutation])
    with pytest.raises(ValueError):
        kit.restore(raw, checkpoint, tmp_path / 'output')
    assert not (tmp_path / 'output').exists()


@pytest.mark.parametrize('fault', ['duplicate', 'traversal', 'symlink', 'size', 'bytes', 'extra'])
def test_malformed_archive_even_with_external_digest_fails_closed(sources, wheels, fault):
    raw, checkpoint = kit.pack(sources, wheels, 'a' * 40)

    def mutate(entries):
        member, body = entries[-1]
        if fault == 'duplicate':
            entries.append(deepcopy(entries[-1]))
        elif fault == 'traversal':
            member.name = '../escape'
        elif fault == 'symlink':
            member.type, member.linkname = tarfile.SYMTYPE, '/tmp/escape'
        elif fault == 'size':
            member.size = kit.FILE_LIMIT + 1
            entries[-1] = member, b'x' * member.size
        elif fault == 'bytes':
            entries[-1] = member, b'x' * len(body)
        else:
            extra = tarfile.TarInfo('unexpected')
            entries.append((extra, b''))

    with pytest.raises(ValueError):
        kit.verify(*repack(raw, checkpoint, mutate))


@pytest.mark.parametrize('fault', ['missing', 'extra', 'version', 'duplicate', 'path', 'unlocked', 'conflict', 'schema'])
def test_dependency_set_is_closed_and_hash_locked(sources, wheels, fault):
    if fault == 'missing':
        wheels.clear()
    elif fault == 'extra':
        wheels['other-1.0-py3-none-any.whl'] = wheel('other')
    elif fault == 'version':
        wheels['fixture-1.0-py3-none-any.whl'] = wheel(version='2.0')
    elif fault == 'duplicate':
        wheels['fixture-1.0-cp313-none-any.whl'] = wheel()
    elif fault == 'path':
        wheels['fixture-1.0-py3-none-any.whl'] = wheel(extra='../bad')
    elif fault == 'unlocked':
        sources[kit.LOCKS[0]] = b'fixture>=1.0\n'
    elif fault == 'conflict':
        sources[kit.LOCKS[0]] = b'fixture==2.0\n'
    else:
        del sources[kit.SCHEMAS[0]]
    with pytest.raises(ValueError):
        kit.pack(sources, wheels, 'a' * 40)


@pytest.mark.parametrize('path', ['state/key.py', '../control/unsafe.py', '/control/app.py', 'scripts/x/../bad.py',
                                 'control/secret.key', 'deploy/control-ha/private.env', 'control/state.sqlite'])
def test_source_scope_excludes_private_state_and_unsafe_paths(path):
    assert not kit.source_allowed(path)


@pytest.mark.parametrize('fault', ['public', 'symlink'])
def test_restore_parent_safety(sources, wheels, tmp_path, fault):
    raw, checkpoint = kit.pack(sources, wheels, 'a' * 40)
    if fault == 'public':
        tmp_path.chmod(0o755)
        target = tmp_path / 'restored'
    else:
        (tmp_path / 'alias').symlink_to(tmp_path, target_is_directory=True)
        target = tmp_path / 'alias' / 'restored'
    with pytest.raises(ValueError):
        kit.restore(raw, checkpoint, target)


def test_only_committed_regular_source_is_collected(sources, tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    for name, raw in sources.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    subprocess.run(['git', 'add', '.'], cwd=tmp_path, check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-qm', 'fixture'], cwd=tmp_path, check=True)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=tmp_path).decode().strip()
    (tmp_path / kit.BOOTSTRAP).write_bytes(b'UNCOMMITTED')
    (tmp_path / 'scripts/private.py').write_bytes(b'UNTRACKED')
    assert kit.collect_sources(tmp_path, commit) == sources


def test_cold_execution_is_offline_and_uses_only_explicit_restored_inputs():
    arguments = cold.command('/retained/rootfs', '/owned/work', '/input/kit', '/pins/checkpoint', '/pins/bootstrap', '/input/custody')
    assert '--unshare-all' in arguments and '--clearenv' in arguments and '--cap-drop' in arguments
    assert '--no-index' in cold.SHELL and '--require-hashes' in cold.SHELL and '--only-binary=:all:' in cold.SHELL
    assert 'PYTHONPATH=/tmp/fc-work/restored/source' in cold.SHELL and '-m venv' in cold.SHELL
    assert not any(name in arguments for name in ('/home', '/run', '/var/run/docker.sock', str(Path.cwd())))
    assert len(cold.CUSTODY_FILES) == 21
    assert 'node-NL2.aesgcm' in cold.CUSTODY_FILES and 'worker.checkpoint.json' in cold.CUSTODY_FILES


def test_new_mountpoints_live_under_writable_tmpfs_not_readonly_image_root():
    arguments = cold.command('/retained/rootfs', '/owned/work', '/input/kit', '/pins/checkpoint', '/pins/bootstrap', '/input/custody')
    destinations = [arguments[index + 2] for index, value in enumerate(arguments) if value in ('--bind', '--ro-bind')]
    assert destinations[0] == '/'
    assert all(path.startswith('/tmp/') for path in destinations[1:])
    assert arguments.index('--tmpfs') < arguments.index('--bind')
    assert arguments[arguments.index('--chdir') + 1] == '/tmp/fc-work'


def test_required_entry_modules_exist_in_selected_source():
    root = Path(kit.__file__).resolve().parents[1]
    assert all((root / (name.replace('.', '/') + '.py')).is_file() for name in probe.MODULES)


def test_recovery_entry_imports_need_no_original_checkout(tmp_path):
    root = Path(kit.__file__).resolve().parents[1]
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root).decode().strip()
    source = tmp_path / 'source'
    for name, raw in kit.collect_sources(root, commit).items():
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    code = '''import importlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root))
for name in json.loads(sys.argv[2]):
    module=importlib.import_module(name)
    assert root in Path(module.__file__).resolve().parents
for name,module in tuple(sys.modules.items()):
    if name.split('.')[0] in ('control','device_identity','scripts','provisioning','messenger','clients') and getattr(module,'__file__',None):
        assert root in Path(module.__file__).resolve().parents
print('CLOSED_SOURCE_IMPORTS_PASS')
'''
    result = subprocess.run([sys.executable, '-I', '-c', code, str(source), json.dumps(probe.MODULES)],
                            cwd=tmp_path, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr.decode()
    assert result.stdout.strip() == b'CLOSED_SOURCE_IMPORTS_PASS'
