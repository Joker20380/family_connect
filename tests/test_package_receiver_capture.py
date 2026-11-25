import difflib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import zipfile

import pytest

from scripts import package_receiver_capture as package


@pytest.fixture
def synthetic(tmp_path):
    source = tmp_path / 'source'
    originals = {name: b'VALUE = 1\n' for name in package.MODIFIED}
    originals['independent.py'] = b'POLICY = "preserve"\n'
    originals['transport_reconcile.py'] = b'VALUE = 77\n'
    originals['control/'] = b''
    baseline = tmp_path / 'baseline.pyz'
    with zipfile.ZipFile(baseline, 'w') as archive:
        for name, raw in originals.items():
            archive.writestr(name, raw)
    patch = ''.join(''.join(difflib.unified_diff(['VALUE = 1\n'], ['VALUE = 2\n'],
        fromfile='a/' + name, tofile='b/' + name)) for name in sorted(package.MODIFIED))
    contents = {package.PATCH: patch.encode(), package.UNIT: b'[Service]\nKillMode=mixed\n'}
    contents.update({Path(name): b'VALUE = 3\n' for name in package.ADDED})
    contract = dict(schema=1, baseline_sha256=package.digest(baseline.read_bytes()),
        before={name: package.digest(originals[name]) for name in package.MODIFIED},
        after={name: package.digest(b'VALUE = 2\n') for name in package.MODIFIED},
        added={name: package.digest(contents[Path(name)]) for name in package.ADDED},
        patch_sha256=package.digest(contents[package.PATCH]), unit_sha256=package.digest(contents[package.UNIT]))
    contents[package.CONTRACT] = json.dumps(contract).encode()
    for name, raw in contents.items():
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    return source, baseline, tmp_path / 'candidate'


def test_closed_delta_preserves_other_members_and_is_deterministic(synthetic):
    source, baseline, output = synthetic
    first = package.build(baseline, output, source=source)
    second = package.build(baseline, output.with_name('second'), source=source)
    assert first == second
    assert first['installed'] is False and first['removed'] == []
    assert set(first['modified']) == package.MODIFIED and set(first['added']) == package.ADDED
    with zipfile.ZipFile(baseline) as before, zipfile.ZipFile(output / 'friends-http.pyz') as after:
        assert set(after.namelist()) == set(before.namelist()) | package.ADDED
        for name in before.namelist():
            assert after.read(name) == (b'VALUE = 2\n' if name in package.MODIFIED else before.read(name))
            for field in ('date_time', 'compress_type', 'create_system', 'external_attr', 'comment', 'extra'):
                assert getattr(after.getinfo(name), field) == getattr(before.getinfo(name), field)
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in output.iterdir())


@pytest.mark.parametrize('mutation,reason', [
    ('baseline', 'INSTALLED_ARCHIVE_PIN'), ('before', 'INSTALLED_MEMBER_PIN'),
    ('after', 'PATCH_RESULT_PIN'), ('scope', 'CONTRACT_SCOPE'),
    ('patch', 'DELTA_PIN'), ('unit', 'DELTA_PIN'), ('added', 'ADDED_SOURCE_PIN')])
def test_each_binding_refuses_drift_without_creating_output(synthetic, mutation, reason):
    source, baseline, output = synthetic
    path = source / package.CONTRACT
    contract = json.loads(path.read_text())
    if mutation == 'baseline':
        baseline.write_bytes(baseline.read_bytes() + b'changed')
    elif mutation in ('before', 'after'):
        contract[mutation][next(iter(package.MODIFIED))] = '0' * 64
    elif mutation == 'scope':
        contract['before']['extra.py'] = '0' * 64
    else:
        name = {'patch': package.PATCH, 'unit': package.UNIT, 'added': next(iter(package.ADDED))}[mutation]
        (source / name).write_bytes(b'changed')
    path.write_text(json.dumps(contract))
    with pytest.raises(ValueError, match=reason):
        package.build(baseline, output, source=source)
    assert not output.exists()


def test_wrong_patch_even_with_updated_input_pin_cannot_change_scope(synthetic):
    source, baseline, output = synthetic
    path = source / package.PATCH
    path.write_text(path.read_text().replace('VALUE = 1', 'VALUE = 9'))
    contract = json.loads((source / package.CONTRACT).read_text())
    contract['patch_sha256'] = package.digest(path.read_bytes())
    (source / package.CONTRACT).write_text(json.dumps(contract))
    with pytest.raises(subprocess.CalledProcessError):
        package.build(baseline, output, source=source)
    assert not output.exists()


def test_never_overwrites_existing_or_partial_output(synthetic, monkeypatch):
    source, baseline, output = synthetic
    original = package.os.fsync
    monkeypatch.setattr(package.os, 'fsync', lambda descriptor: (_ for _ in ()).throw(OSError('synthetic fsync')))
    with pytest.raises(OSError, match='synthetic fsync'):
        package.build(baseline, output, source=source)
    retained = {path.name: path.read_bytes() for path in output.iterdir()}
    monkeypatch.setattr(package.os, 'fsync', original)
    with pytest.raises(ValueError, match='OUTPUT_EXISTS'):
        package.build(baseline, output, source=source)
    assert {path.name: path.read_bytes() for path in output.iterdir()} == retained


@pytest.mark.parametrize('kind', ['file', 'parent', 'fifo'])
def test_unsafe_inputs_refused_without_reading(synthetic, kind):
    source, baseline, output = synthetic
    alternative = baseline.with_name('alternative')
    if kind == 'file':
        alternative.symlink_to(baseline)
        expected = 'SYMLINK_INPUT'
    elif kind == 'parent':
        alternative.symlink_to(baseline.parent, target_is_directory=True)
        alternative /= baseline.name
        expected = 'SYMLINK_INPUT'
    else:
        os.mkfifo(alternative)
        expected = 'REGULAR_INPUT_REQUIRED'
    with pytest.raises(ValueError, match=expected):
        package.build(alternative, output, source=source)
    assert not output.exists()


@pytest.mark.parametrize('name', ['../escape.py', '/absolute.py', 'nested/../escape.py',
                                  'nested//duplicate.py', 'nested\\escape.py', './file.py'])
def test_unsafe_zip_paths_refused(name):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr(name, b'pass\n')
    with pytest.raises(ValueError, match='UNSAFE_MEMBER'):
        package.inventory(buffer.getvalue())


def test_duplicate_and_symlink_archive_members_refused():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('file.py', b'pass\n')
        with pytest.warns(UserWarning):
            archive.writestr('file.py', b'pass\n')
    with pytest.raises(ValueError, match='DUPLICATE_MEMBER'):
        package.inventory(buffer.getvalue())
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        entry = zipfile.ZipInfo('link')
        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(entry, b'elsewhere')
    with pytest.raises(ValueError, match='UNSUPPORTED_MEMBER'):
        package.inventory(buffer.getvalue())


@pytest.fixture
def installed(tmp_path):
    path = os.environ.get('FC_TEST_RECEIVER_BASELINE')
    if not path:
        pytest.skip('requires privately retained pinned installed archive')
    output = tmp_path / 'native'
    receipt = package.build(Path(path), output)
    return output, receipt


def test_real_installed_archive_closure_and_isolated_import(installed):
    output, receipt = installed
    assert len(receipt['modified']) == 6 and len(receipt['added']) == 2 and receipt['removed'] == []
    command = [sys.executable, '-I', str(output / 'friends-http.pyz'), '--help']
    result = subprocess.run(command, cwd=output, capture_output=True, timeout=10)
    assert result.returncode == 0 and not result.stderr
    code = '''
import sys
sys.path.insert(0, sys.argv[1])
from control.friends.access import Access
from control.friends import http_lifecycle, paid_beta, transport_reconcile, notices
from scripts.service_notices import Notices
from control.capture_gate import Gate
assert not hasattr(Access, 'enrollment')
for name in ('control.friends.access', 'control.friends.http_lifecycle', 'scripts.service_notices'):
    assert sys.modules[name].__file__.startswith(sys.argv[1] + '/')
'''
    subprocess.run([sys.executable, '-I', '-c', code, str(output / 'friends-http.pyz')],
                   cwd=output, capture_output=True, check=True, timeout=10)


@pytest.mark.parametrize('version', [1, 2])
@pytest.mark.parametrize('failure', ['file-sync', 'rename', 'directory-sync'])
def test_installed_shape_native_export_failure_retains_pending(installed, tmp_path, version, failure):
    output, _ = installed
    code = '''
import json,os,stat,sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.service_notices import Notices
from control.capture_gate import initialize, GateError
root=Path(sys.argv[2]);version=int(sys.argv[3]);failure=sys.argv[4]
gate=initialize(root/'gate');store=Notices(root/'notices.sqlite')
store.grant('Synthetic', root/'token')
store.publish((root/'token').read_text(),kind='information',title='Synthetic',body='Not production',platforms=['android'],lifetime=86400)
public=root/'public';public.mkdir()
original_sync,original_replace=os.fsync,os.replace
counts={'file-sync':0,'rename':0,'directory-sync':0}
def fail(phase):
    counts[phase]+=1
    if phase==failure and counts[phase]==version:raise OSError('synthetic failure')
def sync(descriptor):
    path=Path(os.readlink('/proc/self/fd/'+str(descriptor)))
    if path==public or path.parent==public:fail('directory-sync' if stat.S_ISDIR(os.fstat(descriptor).st_mode) else 'file-sync')
    original_sync(descriptor)
def replace(source,target):
    fail('rename');original_replace(source,target)
os.fsync,os.replace=sync,replace
with gate.operation():
    try:store.export_all(public/'family-connect-events-v1.json')
    except OSError:pass
    else:raise AssertionError('failure was not exercised')
assert not store.db.in_transaction
os.fsync,os.replace=original_sync,original_replace
with gate.operation():store.export_all(public/'family-connect-events-v1.json')
try:
    with gate.drain(.1):pass
except GateError as error:assert str(error)=='UNSETTLED_OPERATION'
else:raise AssertionError('partial publication allowed capture')
assert len(list(public.glob('*.json')))==2
assert not list(public.glob('.notices-*'))
store.db.close()
'''
    subprocess.run([sys.executable, '-I', '-c', code, str(output / 'friends-http.pyz'),
                    str(tmp_path), str(version), failure], capture_output=True, check=True, timeout=10)


@pytest.mark.parametrize('target', ['transport', 'chat'])
@pytest.mark.parametrize('outcome', ['success', 'nonzero', 'invalid'])
def test_real_admitted_child_side_effect_and_lost_ack(installed, tmp_path, target, outcome):
    output, _ = installed
    code = r'''
import json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from control.capture_gate import initialize,GateError
from control.friends.access import Access
from control.friends import chat_sync,paid_beta,transport_membership,transport_policy
from control.friends.chat import ChatAccess
from device_identity.device import DeviceIdentity
root=Path(sys.argv[2]);target,outcome=sys.argv[3:5]
gate=initialize(root/'gate');access=Access(root/'access.db');access.initialize()
device=DeviceIdentity.generate()
challenge=access.challenge(device.public_identity,device.wireguard_public_key,'activate',access.invite())
access.complete(device.prove_transport_key(challenge['challenge']),'activate')
child = """
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);name,outcome,target=sys.argv[2:5]
request=json.load(sys.stdin)
(root/(name+'-committed')).touch()
if outcome=='nonzero':raise SystemExit(1)
if target=='transport':reply=dict(schema=1,node=name,result='prepared',token=request['token'])
else:reply=dict(sequence=request['sequence'],expires_at=request['expires_at'],**json.loads((root/'chat-node.json').read_text()))
if outcome=='invalid':reply['unexpected']=True
print(json.dumps(reply))
"""
if target=='transport':
    with access.db() as database:paid_beta.migrate(database)
    document=dict(schema=1,profile=transport_policy.PROFILE,enabled=True,hosts={node:node for node in transport_policy.NODES})
    config=root/'transport-enforcement.json';config.write_text(json.dumps(document));config.chmod(0o600)
    commands={node:[sys.executable,'-I','-c',child,str(root),node,outcome,target] for node in transport_policy.NODES}
    config=root/'transport-commands.json';config.write_text(json.dumps(commands));config.chmod(0o600)
    def invoke():
        with access.db() as database:transport_membership.prepare(database,device.reference,'b'*64,1800000000)
else:
    chat=ChatAccess(access);chat.initialize();chat_sync.ROOT=root
    (root/'chat-node.json').write_text(json.dumps(dict(host='192.0.2.1',port=4243,public_key='a'*128)))
    native_run=subprocess.run
    def exchange(command,**kwargs):
        assert command[0]=='/usr/bin/ssh' and '-o' in command and 'StrictHostKeyChecking=yes' in command
        return native_run([sys.executable,'-I','-c',child,str(root),'chat',outcome,target],**kwargs)
    chat_sync.subprocess.run=exchange
    def invoke():chat_sync.synchronize(chat)
failed=False
with gate.operation():
    try:invoke()
    except (paid_beta.PaidBetaError,RuntimeError,ValueError):failed=True
assert failed==(outcome!='success')
assert list(root.glob('*-committed'))
try:
    with gate.drain(.1):pass
except GateError as error:
    assert outcome!='success' and str(error)=='UNSETTLED_OPERATION'
else:assert outcome=='success'
'''
    subprocess.run([sys.executable, '-I', '-c', code, str(output / 'friends-http.pyz'),
                    str(tmp_path), target, outcome], capture_output=True, check=True, timeout=20)
