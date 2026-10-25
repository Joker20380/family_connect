import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[3]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'packaging/linux' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def runtime():
    return load('candidate_runtime')


def seal(directory, record):
    record.pop('build_id', None)
    record['build_id'] = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (directory / 'candidate.json').write_text(json.dumps(record))
    return record


@pytest.fixture
def bundle(tmp_path, runtime):
    files = {}
    for name in runtime.REQUIRED:
        path = tmp_path / name
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_bytes(b'fixture')
        path.chmod(0o644)
        files[name] = dict(sha256=hashlib.sha256(b'fixture').hexdigest(), size=7)
    record = dict(schema=1, runtime_contract=2, python=list(sys.version_info[:2]),
                  source_commit='a'*40, system=dict(build_id='b'*64, **files['embedded/system.tar.gz']), files=files)
    return tmp_path, seal(tmp_path, record)


def test_exact_candidate_inventory(runtime, bundle):
    directory, record = bundle
    assert runtime.verify(directory) == record


@pytest.mark.parametrize('change', ['changed', 'missing', 'extra', 'symlink', 'fifo', 'writable', 'hardlink', 'abi', 'build', 'system'])
def test_candidate_fail_closed(runtime, bundle, change):
    directory, record = bundle
    target = directory / 'clients/desktop/chat_daemon.py'
    if change == 'changed':
        target.write_bytes(b'changed')
    elif change == 'missing':
        target.unlink()
    elif change == 'extra':
        (directory / 'injected.py').write_text('')
    elif change == 'symlink':
        (directory / 'link').symlink_to('/tmp', target_is_directory=True)
    elif change == 'fifo':
        os.mkfifo(directory / 'pipe')
    elif change == 'writable':
        target.chmod(0o666)
    elif change == 'hardlink':
        os.link(target, directory / 'duplicate')
    else:
        if change == 'abi':
            record['python'] = [3, 10]
        elif change == 'build':
            record['source_commit'] = 'different'
        else:
            record['system']['sha256'] = '0'*64
        seal(directory, record)
    with pytest.raises((ValueError, OSError)):
        runtime.verify(directory)


def test_resealed_missing_required_client_is_not_ready(runtime, bundle):
    directory, record = bundle
    name = 'provisioning/chat_direct.py'
    (directory / name).unlink()
    del record['files'][name]
    seal(directory, record)
    with pytest.raises(ValueError, match='incomplete'):
        runtime.verify(directory)


def test_compatibility_binds_exact_system_build(runtime, bundle, monkeypatch):
    directory, record = bundle
    actual_verify = runtime.verify
    monkeypatch.setattr(runtime, 'verify', lambda: actual_verify(directory))
    assert runtime.installed_guard(dict(build_id='b'*64)) == 'READY'
    assert runtime.installed_guard(dict(build_id='c'*64)) == 'CANDIDATE_SYSTEM_BUILD_MISMATCH'
    (directory / 'clients/desktop/chat_daemon.py').unlink()
    assert runtime.installed_guard(dict(build_id='b'*64)) == 'CANDIDATE_USER_INTEGRITY_FAILED'


@pytest.mark.parametrize('name,kind', [('FamilyConnect-MESH-system-amd64/../escape', tarfile.REGTYPE),
    ('/absolute', tarfile.REGTYPE), ('FamilyConnect-MESH-system-amd64/link', tarfile.SYMTYPE),
    ('FamilyConnect-MESH-system-amd64/link', tarfile.LNKTYPE), ('FamilyConnect-MESH-system-amd64/fifo', tarfile.FIFOTYPE)])
def test_archive_paths_types_rejected_before_installer(tmp_path, name, kind):
    setup = load('candidate_setup')
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode='w:gz') as archive:
        member = tarfile.TarInfo(name)
        member.type = kind
        archive.addfile(member)
    raw = data.getvalue()
    with pytest.raises(ValueError, match='Unsafe'):
        setup.extract_verified(raw, dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest()), tmp_path)
    assert not list(tmp_path.iterdir())


def test_root_accepts_only_pkexec_caller_and_no_path(monkeypatch):
    setup = load('candidate_setup')
    monkeypatch.setattr(setup.os, 'geteuid', lambda: 0)
    for uid in ('', '0', '-1', '01', 'abc', str(2**31)):
        monkeypatch.setenv('PKEXEC_UID', uid)
        monkeypatch.setattr(sys, 'argv', ['-c'])
        with pytest.raises(ValueError, match='caller'):
            setup.root_main({})
    monkeypatch.setenv('PKEXEC_UID', '1000')
    monkeypatch.setattr(sys, 'argv', ['-c', '/untrusted/install.py'])
    with pytest.raises(ValueError, match='caller'):
        setup.root_main({})


def test_setup_does_not_accept_external_payload_path(runtime):
    with pytest.raises(TypeError):
        runtime.setup('/untrusted.tar.gz')


def test_units_match_existing_user_dbus_contract():
    from provisioning.chat_rpc import BUS_NAME
    unit = (ROOT / 'packaging/linux/family-connect-chat.service').read_text()
    activation = (ROOT / 'packaging/linux/com.familyconnect.Chat1.service').read_text()
    assert 'BusName=' + BUS_NAME in unit
    assert 'Name=' + BUS_NAME in activation
    assert 'ExecStart=/usr/bin/family-connect --chat-service' in unit
    assert '[Install]' not in unit


def test_package_public_files_do_not_inherit_group_write(tmp_path):
    from scripts.package_linux import safe_copy
    source = tmp_path / 'source'
    source.write_text('public unit')
    source.chmod(0o664)
    previous = os.umask(0o002)
    try:
        safe_copy(source, tmp_path / 'staged/unit')
    finally:
        os.umask(previous)
    assert (tmp_path / 'staged/unit').stat().st_mode & 0o777 == 0o644


@pytest.mark.parametrize('kind,action,ident,data', [('awg', 'import', None, 'synthetic'),
    ('tcp', 'up', 'fctcp12345678', None), ('chat', 'up', 'fcchat0', None)])
def test_candidate_authorization_requires_matching_system(monkeypatch, kind, action, ident, data):
    import backend
    monkeypatch.setattr(backend, 'CANDIDATE_GUARD', lambda _: 'CANDIDATE_SYSTEM_BUILD_MISMATCH')
    monkeypatch.setattr(backend, 'system_component_status', lambda: 'CANDIDATE_SYSTEM_BUILD_MISMATCH')
    monkeypatch.setattr(backend.subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('No authorization on mismatch'))
    session = backend._AuthorizationSession()
    with pytest.raises(backend.BackendError, match='CANDIDATE_SYSTEM_BUILD_MISMATCH'):
        session.call(kind, action, ident, data)
