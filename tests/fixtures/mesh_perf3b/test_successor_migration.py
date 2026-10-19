import importlib.util
import json
from pathlib import Path
import sqlite3

import pytest

from test_successor_lifecycle import saved, handoff, successor, prepare, current


spec = importlib.util.spec_from_file_location('successor_migrate', Path(__file__).with_name('successor_migrate.py'))
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)


def test_exact_operator_commit_and_independent_readback(saved, tmp_path):
    service, owner, now, first, original = saved
    expected = operator.digest(operator.encoded([original]))
    receipt = operator.commit_migration(service.access, handoff, expected)
    result = operator.readback(service.access.path, expected)
    assert receipt['result'] == 'MIGRATED' and result['canonical_history_preserved']
    assert result['phase'] == 'CLEANED' and result['unfinished_count'] == 0
    target = tmp_path/'receipt.json'
    operator.durable(target,result)
    with pytest.raises(FileExistsError):operator.durable(target,result)
    assert json.loads(operator.private(target)) == result
    probe = operator.allocation_probe(service.access.path,tmp_path/'full-copy.db',type(service.access),handoff,expected)
    assert probe['result']=='PASS_ON_FULL_DB_COPY_ONLY' and probe['generation']==2
    assert probe['original_database_unchanged']


def test_commit_survives_receipt_failure_no_repeat_migration(saved, monkeypatch, tmp_path):
    service, owner, now, first, original = saved
    expected = operator.digest(operator.encoded([original]))
    operator.commit_migration(service.access, handoff, expected)
    def failed(*args):raise OSError('synthetic durable receipt failure')
    monkeypatch.setattr(operator.os, 'fsync', failed)
    with pytest.raises(OSError):operator.durable(tmp_path/'receipt.json',dict(result='interrupted'))
    result = operator.readback(service.access.path, expected)
    assert result['operation_count'] == 1 and result['retained_security_preserved']


def test_wrong_canonical_input_never_migrates(saved):
    service, *_ = saved
    with pytest.raises(RuntimeError,match='LEGACY_CHANGED'):
        operator.commit_migration(service.access,handoff,'0'*64)
    with service.access.db() as database:assert not handoff.exists(database,handoff.SCHEMA)


def test_read_only_allocation_preflight_current_not_empty_table(successor):
    service, owner, now, *_ = successor
    before=current(successor)
    database=operator.connection(service.access.path)
    try:
        result=handoff.prepare_preflight(database,'fresh-attempt',owner.reference,'a'*32,'b'*32,now+2400,now)
        assert result['generation']==2 and result['existing'] is None
        assert result['predecessor']=='retired-01'
        assert result['saved']==before['floor']
    finally:database.close()
    assert current(successor)==before
    prepare(successor)
    with service.access.db() as database:
        with pytest.raises(ValueError):handoff.prepare_preflight(database,'different-attempt',owner.reference,'a'*32,'b'*32,now+2400,now)


@pytest.mark.parametrize('arguments,expected', [([], '/opt/apps/family_connect/friends-access/access.db'),
    (['--root','/tmp/test-fixture'],'/tmp/test-fixture/access.db')])
def test_exact_deployed_api_database_default(arguments,expected):
    root=Path(__file__).resolve().parents[3]
    archive=root/'state-client-build/field65-export16/warm-start-collector-rebase-1/preservation/deployed-api.pyz'
    assert str(operator.database_path(arguments,archive))==expected


def test_ambiguous_api_root_rejected(tmp_path):
    import zipfile
    archive=tmp_path/'invalid.pyz'
    with zipfile.ZipFile(archive,'w') as package:package.writestr('friends_http.py',"ROOT=Path('/tmp/one')\nROOT=Path('/tmp/two')\n")
    with pytest.raises(RuntimeError,match='API_ROOT_DEFAULT_AMBIGUOUS'):operator.database_path([],archive)


@pytest.mark.parametrize('commit',[False,True])
def test_process_death_before_or_after_prepare_commit(successor,commit):
    import subprocess
    import sys
    service, owner, now, *_ = successor
    root=Path(__file__).resolve().parents[3]
    code='''
import importlib.util,os,sys
sys.path.insert(0,sys.argv[1])
from control.friends.access import Access
spec=importlib.util.spec_from_file_location('control.friends.owner_handoff',sys.argv[2])
handoff=importlib.util.module_from_spec(spec);spec.loader.exec_module(handoff)
with Access(sys.argv[3]).db() as database:
 handoff.prepare(database,'crash-successor',sys.argv[4],'a'*32,'b'*32,int(sys.argv[5])+2400,int(sys.argv[5]))
 if sys.argv[6]=='before':os._exit(17)
os._exit(23)
'''
    process=subprocess.run([sys.executable,'-c',code,str(root/'state-client-build/mesh-perf-3b/api'),
        str(Path(__file__).with_name('successor_owner_handoff.py')),str(service.access.path),owner.reference,str(now),
        'after' if commit else 'before'],capture_output=True,timeout=10)
    assert process.returncode==(23 if commit else 17)
    assert current(successor)['operation']==('crash-successor' if commit else 'retired-01')
    with service.access.db() as database:
        result=handoff.prepare(database,'crash-successor',owner.reference,'a'*32,'b'*32,now+2400,now)
        assert result['generation']==2
        assert database.execute('SELECT COUNT(*) FROM restricted_owner_handoff_operations').fetchone()[0]==2
