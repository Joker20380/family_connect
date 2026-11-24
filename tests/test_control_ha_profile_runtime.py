import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace

import pytest

from scripts import control_ha_profile_runtime as observer


def digest(raw):
    return base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip('=')


def write_distribution(site, name, version):
    distribution = site / f'{name}-{version}.dist-info'
    distribution.mkdir()
    metadata = distribution / 'METADATA'
    metadata.write_text(f'Name: {name}\nVersion: {version}\n\n')
    module = site / (name + '.py')
    module.write_text('raise RuntimeError("Package imports are forbidden")\n')
    output = io.StringIO()
    writer = csv.writer(output)
    for member in (metadata, module):
        writer.writerow([str(member.relative_to(site)), 'sha256=' + digest(member.read_bytes()), member.stat().st_size])
    writer.writerow([str((distribution / 'RECORD').relative_to(site)), '', ''])
    (distribution / 'RECORD').write_text(output.getvalue())
    return distribution


@pytest.fixture
def runtime():
    previous = os.umask(0o022)
    temporary = tempfile.TemporaryDirectory(prefix='runtime-observe-',
        dir=os.environ.get('FC_TEST_SNAPSHOT_ROOT', str(Path.home())))
    root = Path(temporary.name)
    root.chmod(0o755)
    (root / 'bin').mkdir()
    executable = root / 'bin/python3.14'
    shutil.copyfile(Path(sys.executable).resolve(), executable)
    executable.chmod(0o755)
    (root / 'pyvenv.cfg').write_text('home = /usr/bin\nversion = 3.14.4\ninclude-system-site-packages = false\n')
    site = root / 'lib/python3.14/site-packages'
    site.mkdir(parents=True)
    for name, version in observer.EXPECTED.items():
        write_distribution(site, name, version)
    account = observer.launcher.Account(123456, os.getegid(), (os.getegid(),))
    value = dict(executable=str(executable), target=str(executable), version=[3, 14, 4],
        implementation='cpython', uid=account.uid, gid=account.gid, groups=list(account.groups),
        isolated=1, no_site=1, no_user_site=1, no_bytecode=True, path=['/usr/lib/python3.14'])
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps(value).encode(), stderr=b'')

    try:
        yield SimpleNamespace(root=root, site=site, executable=str(executable), account=account,
                              value=value, calls=calls, run=run)
    finally:
        temporary.cleanup()
        os.umask(previous)


def observe(runtime, **kwargs):
    return observer.observe(runtime.executable, runtime.account, '3.14', run=kwargs.get('run', runtime.run))


def test_observation_pins_dependencies_and_disables_site(runtime):
    result = observe(runtime)
    assert result['classification'] == 'RUNTIME_BINDINGS_OBSERVED'
    assert result['all_selected_versions_match'] is True
    assert result['package_imports_executed'] is result['site_hooks_executed'] is False
    assert result['capture_permitted'] is result['independent_approval'] is False
    assert len(result['dependencies']) == 5
    assert all(item['hashed_files'] == 2 for item in result['dependencies'].values())
    argv, options = runtime.calls[0]
    assert argv == [runtime.executable, '-I', '-S', '-B', '-c', observer.PROBE]
    assert options['cwd'] == '/' and options['env'] == {'PATH': '/usr/bin:/bin', 'LANG': 'C'}
    assert options['timeout'] == 15 and options['preexec_fn'] == runtime.account.enter


def test_startup_files_are_recorded_without_execution(runtime):
    (runtime.site / 'injected.pth').write_text('import os; raise RuntimeError("Do not execute")\n')
    (runtime.site / 'sitecustomize.py').write_text('raise RuntimeError("Do not execute")\n')
    (runtime.site / 'sitecustomize.pyc').write_bytes(b'not executed')
    (runtime.site / 'usercustomize').mkdir()
    (runtime.site / 'usercustomize/__init__.py').write_text('raise RuntimeError("Do not execute")\n')
    result = observe(runtime)
    assert len(result['startup_files']) == 4
    assert result['site_hooks_executed'] is False


def test_version_drift_is_reported_not_approved(runtime):
    shutil.rmtree(runtime.site / 'rns-1.5.1.dist-info')
    write_distribution(runtime.site, 'rns', '1.0.0')
    result = observe(runtime)
    assert result['all_selected_versions_match'] is False
    assert result['dependencies']['rns']['version'] == '1.0.0'
    assert result['capture_permitted'] is False


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'modified', 'symlink', 'record_escape', 'hashless', 'size', 'hash'])
def test_refuses_invalid_static_distribution(runtime, change):
    distribution = runtime.site / 'rns-1.5.1.dist-info'
    record = distribution / 'RECORD'
    if change == 'missing':
        shutil.rmtree(distribution)
    elif change == 'duplicate':
        write_distribution(runtime.site, 'rns', '1.0.0')
    elif change == 'modified':
        (runtime.site / 'rns.py').write_text('changed')
    elif change == 'symlink':
        (runtime.site / 'link').symlink_to(distribution, target_is_directory=True)
    elif change == 'record_escape':
        record.write_text('../../../../../../etc/passwd,sha256=' + 'a' * 43 + ',1\n')
    elif change == 'hashless':
        record.write_text('rns.py,,\n')
    elif change == 'size':
        record.write_text('rns.py,sha256=' + digest((runtime.site / 'rns.py').read_bytes()) + ',0\n')
    else:
        record.write_text('rns.py,sha256=' + 'a' * 43 + ',1\n')
    with pytest.raises((ValueError, observer.launcher.LauncherError)):
        observe(runtime)
    assert not runtime.calls


@pytest.mark.parametrize(('field', 'value'), [('uid', 0), ('gid', True), ('groups', []),
    ('isolated', True), ('no_site', 0), ('no_user_site', 0), ('no_bytecode', False),
    ('path', []), ('path', ['']), ('path', ['/tmp/site-packages']),
    ('version', [3, 12, 3]), ('version', [3, 14, True]), ('implementation', 'pypy'),
    ('executable', '/usr/bin/python3'), ('target', '/usr/bin/python3')])
def test_refuses_incompatible_probe(runtime, field, value):
    runtime.value[field] = value
    with pytest.raises(ValueError, match='OBSERVATION_REFUSED'):
        observe(runtime)


def test_final_inventory_detects_change_during_probe(runtime):
    def run(argv, **kwargs):
        result = runtime.run(argv, **kwargs)
        (runtime.site / 'rns.py').write_text('changed')
        return result
    with pytest.raises(ValueError, match='OBSERVATION_REFUSED'):
        observe(runtime, run=run)


def test_inaccessible_cache_does_not_silently_weaken_inventory(runtime):
    cache = runtime.site / 'cryptography/__pycache__'
    cache.mkdir(parents=True)
    cache.chmod(0o700)
    with pytest.raises(observer.launcher.LauncherError, match='BLOCKED_SNAPSHOT_RUNTIME_UNSAFE'):
        observe(runtime)
    assert not runtime.calls


@pytest.mark.parametrize('changed', [False, True])
def test_record_scripts_outside_site_are_rechecked(runtime, changed):
    target = runtime.root / 'bin/test-tool'
    target.write_text('not executed\n')
    with (runtime.site / 'rns-1.5.1.dist-info/RECORD').open('a') as stream:
        csv.writer(stream).writerow(['../../../bin/test-tool', 'sha256=' + digest(target.read_bytes()), target.stat().st_size])

    def run(argv, **kwargs):
        result = runtime.run(argv, **kwargs)
        if changed:
            target.write_text('replaced now\n')
        return result

    if changed:
        with pytest.raises(ValueError, match='OBSERVATION_REFUSED'):
            observe(runtime, run=run)
    else:
        result = observe(runtime, run=run)
        assert set(result['dependencies']['rns']['external_files']) == {'bin/test-tool'}


@pytest.mark.parametrize('raw', [b'', b'Name: rns\n', b'Name: rns\nName: other\nVersion: 1\n',
    b'Name: rns\nVersion: 1\nVersion: 2\n', b'a' * 1048577])
def test_metadata_requires_unique_bounded_fields(raw):
    with pytest.raises(ValueError):
        observer.metadata(raw)


def test_tree_time_limit_and_missing_root(runtime):
    with pytest.raises(ValueError):
        observer.bounded_tree(runtime.site, clock=iter([0, 16]).__next__)
    with pytest.raises(ValueError):
        observer.bounded_tree(runtime.site / 'absent')


def test_real_probe_ignores_pythonpath_and_never_runs_site(tmp_path):
    marker = tmp_path / 'executed'
    (tmp_path / 'sitecustomize.py').write_text(f'open({str(marker)!r}, "w").write("bad")\n')
    environment = dict(os.environ, PYTHONPATH=str(tmp_path))
    result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', observer.PROBE],
        capture_output=True, timeout=15, check=True, env=environment)
    value = json.loads(result.stdout)
    assert value['isolated'] == value['no_site'] == value['no_user_site'] == 1
    assert value['uid'] == os.getuid() and value['no_bytecode'] is True
    assert str(tmp_path) not in value['path'] and not marker.exists()
    assert not any('site-packages' in Path(path).parts for path in value['path'])
