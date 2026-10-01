import ast
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripts import restricted_sync_acceptance as gate
from test_restricted_runtime import bundle, environment, material_fixture

ROOT = Path(__file__).resolve().parents[1]
STATE = b'ActiveState=inactive\nSubState=dead\nResult=success\nType=oneshot\nTimeoutStartUSec=25s\nMainPID=0\nExecMainCode=1\nExecMainStatus=0\nExecMainStartTimestampMonotonic=100\n'


def records(path):
    return [json.loads(item.read_text()) for item in sorted(path.glob('*.json'))]


@pytest.fixture
def receipts(tmp_path):
    result = gate.Receipts(tmp_path / 'receipts', 'offline-test')
    yield result
    result.close()


def test_timeout_receipt_precedes_rollback_and_redacts(receipts):
    def execute(argv, timeout, payload):
        if argv == ['state']:
            return 0, STATE, b'', False, None
        return None, b'OAuth PRIVATE-IDENTITY secret', b'sensitive-proof', True, 'timeout'
    runner = gate.Runner(receipts, ['state'], execute_command=execute)
    with pytest.raises(gate.AcceptanceFailed):
        runner.run('start', ['/private/program', 'OAuth-secret'], b'private-proof')
    found = records(receipts.path)
    assert len(found) == 2
    assert found[0]['step'] == 'start' and found[0]['timeout_configured'] == 45
    assert found[0]['timeout_expired'] and found[0]['exit_status'] is None
    assert found[0]['monotonic_end'] >= found[0]['monotonic_start']
    assert found[1]['unit_state_at_timeout']['Result'] == 'success'
    text = json.dumps(found)
    assert not any(value in text for value in ('OAuth-secret', 'private-proof', 'PRIVATE-IDENTITY', '/private/program'))
    assert all(item['generation'] == 'offline-test' for item in found)


def test_real_subprocess_timeout_is_bounded_and_classified():
    result = gate.execute([sys.executable, '-c', 'import time; print("secret",flush=True); time.sleep(10)'], .05)
    assert result[0] is None and result[3] and result[4] == 'timeout'


def test_fsync_failure_cannot_pass(receipts, monkeypatch):
    monkeypatch.setattr(os, 'fsync', lambda descriptor: (_ for _ in ()).throw(OSError('disk')))
    with pytest.raises(OSError):
        receipts.persist({'event': 'test'})
    assert not list(receipts.path.glob('*.json'))


@pytest.mark.parametrize('failure', ['journal', 'start', 'generic_shell', 'stale_crl', None])
def test_exact_retained_attempt5_flow(receipts, tmp_path, monkeypatch, failure):
    import control.friends.restricted as restricted
    source = (ROOT / 'tests/fixtures/restricted_sync_attempt5.py').read_text()
    original = ROOT / 'state-client-build/prov1-attempt5/deployment.py'
    if original.exists():
        parsed = ast.parse(original.read_text())
        saved = next(ast.literal_eval(node.value) for node in parsed.body if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == 'RU_SYNC' for target in node.targets))
        assert source.strip() == saved.strip()
    work = tmp_path / 'host'
    (work / 'restricted-materials-stage-20261001').mkdir(parents=True)
    (work / 'restricted-materials-stage-20261001/revocations.pem').write_text('synthetic-stale')
    backup = tmp_path / 'backup'
    backup.mkdir()
    trust = dict(family='a' * 32, gateway='b' * 32)
    sequence = iter((13, 14))
    service = SimpleNamespace(_trust=lambda now: (trust, None, SimpleNamespace(next_update_utc=datetime.fromtimestamp(now+900, timezone.utc)), None, next(sequence)), seed_source=lambda: b'synthetic')
    monkeypatch.setattr(restricted, 'from_env', lambda access: service)
    monkeypatch.setattr(restricted, 'directory', lambda *args: dict(issued_at='2026-10-01T17:55:01Z', expires_at='2026-10-01T18:49:57Z'))
    monkeypatch.setattr('runpy.run_path', lambda *args, **kwargs: None)
    monkeypatch.setattr(sys, 'argv', list(sys.argv))
    monkeypatch.setenv('FC_FRIENDS_RESTRICTED_DIR', 'synthetic')
    calls = []
    clock = [0.0]
    runner = gate.Runner(receipts, ['state'], clock=lambda: clock[0])
    current = [None]
    def execute(argv, timeout, payload):
        if argv == ['state']:
            return 0, STATE, b'', False, None
        if current[0] == failure:
            clock[0] += timeout
            return None, b'', b'', True, 'timeout'
        clock[0] += 3.733449 if current[0] == 'start' else .01
        status = {'generic_shell': 126, 'stale_crl': 1}.get(current[0], 0)
        return status, b'', b'', False, None
    runner.execute = execute
    def run(argv, **kwargs):
        step = ('reload' if argv[:2] == ['systemctl', 'daemon-reload'] else
                'start' if argv[0] == 'systemctl' else 'journal' if argv[0] == 'journalctl'
                else 'generic_shell' if argv[-1] == 'id' else 'stale_crl')
        calls.append(step)
        current[0] = step
        assert kwargs.get('timeout') == (None if step == 'reload' else gate.STEPS[step][2])
        try:
            result = runner.run(step, argv, kwargs.get('input'))
        except gate.AcceptanceFailed:
            raise subprocess.TimeoutExpired(argv, kwargs.get('timeout')) from None
        if kwargs.get('text'):
            result.stdout = result.stdout.decode()
        return result
    monkeypatch.setattr(subprocess, 'run', run)
    source = source.replace("Path('/opt/apps/family_connect')", 'Path(' + repr(str(work)) + ')')
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(source, '<retained-attempt5>', 'exec'), {'BACKUP': str(backup)})
    result = json.loads((backup / 'ru-sync.json').read_text())
    assert result['live_sync_pass'] == (failure is None)
    if failure:
        assert result['failure_type'] == 'TimeoutExpired'
        timeout = next(item for item in records(receipts.path) if item.get('timeout_expired'))
        assert timeout['step'] == failure
    if failure == 'journal':
        assert calls == ['reload', 'start', 'journal']
        assert not (backup / 'ru-service-observation.json').exists()
        assert not (backup / 'generic-shell.json').exists()
        assert clock[0] < 18
    if failure == 'start':
        assert clock[0] >= 45


def simulation(receipts, scenario='fast'):
    clock = [0.0]
    calls = []
    snapshots = [0]
    states = [0]
    before = dict(crl_sequence=13, database_sequence=13, directory_valid=True,
                  directory_version=1, directory_issued_ns=100, directory_expires_ns=1000)
    after = dict(before, crl_sequence=14, database_sequence=14, directory_issued_ns=200)
    configured = {name: [name] for name in ('snapshot', 'state', 'reload', 'start', 'generic_shell', 'stale_crl')}
    def execute(argv, timeout, payload):
        name = argv[0]
        calls.append(name)
        clock[0] += .01
        if name == 'snapshot':
            snapshots[0] += 1
            value = before if snapshots[0] == 1 or scenario == 'missing_readback' else after
            if scenario == 'rollback_after_negative' and snapshots[0] == 3:
                value = before
            if scenario == 'invalid_directory' and snapshots[0] > 1:
                value = dict(value, directory_valid=False)
            return 0, json.dumps(value).encode(), b'', False, None
        if name == 'state':
            states[0] += 1
            value = STATE if states[0] == 1 else STATE.replace(b'=100\n', b'=200\n')
            if scenario in ('background', 'hang') and states[0] > 1:
                value = value.replace(b'ActiveState=inactive', b'ActiveState=activating')
            if scenario == 'unit_failed' and states[0] > 1:
                value = value.replace(b'Result=success', b'Result=exit-code')
            if scenario == 'cleared_exit_metadata' and states[0] > 1:
                value = value.replace(b'ExecMainCode=1', b'ExecMainCode=0').replace(b'=200\n', b'=0\n')
            return 0, value, b'', False, None
        if name == 'start':
            if scenario in ('timeout_later_success', 'hang'):
                clock[0] += timeout
                return None, b'', b'', True, 'timeout'
            if scenario == 'slow':
                clock[0] += 24
            if scenario == 'late':
                clock[0] += gate.TOTAL_SECONDS
        if name == 'generic_shell':
            if scenario == 'generic_timeout':
                clock[0] += timeout
                return None, b'', b'', True, 'timeout'
            return 126, b'', b'', False, None
        if name == 'stale_crl':
            assert payload == b'private-synthetic-crl'
            return (0 if scenario == 'stale_accepted' else 1), b'', b'', False, None
        return 0, b'', b'', False, None
    runner = gate.Runner(receipts, configured['state'], snapshot_command=configured['snapshot'],
                       execute_command=execute, clock=lambda: clock[0])
    return runner, configured, calls


@pytest.mark.parametrize('scenario', ['fast', 'slow', 'cleared_exit_metadata'])
def test_synchronous_valid_completion_and_all_negatives(receipts, scenario):
    runner, configured, calls = simulation(receipts, scenario)
    gate.accept(runner, configured, b'private-synthetic-crl')
    assert calls == ['snapshot', 'state', 'reload', 'start', 'state', 'snapshot', 'generic_shell', 'stale_crl', 'snapshot']
    result = records(receipts.path)[-1]
    assert result['passed'] and result['completed'] == ['unit', 'fresh_readback', 'generic_shell', 'stale_crl']
    assert 'journal' not in calls


@pytest.mark.parametrize('scenario,step', [
    ('timeout_later_success', 'start'), ('hang', 'start'), ('late', 'start'),
    ('background', 'unit_completed'), ('unit_failed', 'unit_completed'),
    ('missing_readback', 'fresh_readback'), ('invalid_directory', 'fresh_readback'),
    ('generic_timeout', 'generic_shell'), ('stale_accepted', 'stale_crl_rejected'),
    ('rollback_after_negative', 'no_rollback')])
def test_failure_never_promotes_later_crl_to_pass(receipts, scenario, step):
    runner, configured, calls = simulation(receipts, scenario)
    with pytest.raises(gate.AcceptanceFailed, match=step):
        gate.accept(runner, configured, b'private-synthetic-crl')
    found = records(receipts.path)
    assert found[-1]['event'] == 'verdict' and not found[-1]['passed']
    assert any(item.get('step') == step for item in found)
    if scenario in ('timeout_later_success', 'hang', 'background', 'missing_readback'):
        assert 'generic_shell' not in calls and 'stale_crl' not in calls
    if scenario == 'generic_timeout':
        assert 'stale_crl' not in calls
    if scenario == 'stale_accepted':
        assert calls.index('generic_shell') < calls.index('stale_crl')


def test_commands_enforce_synchronous_start_and_strict_host_verification():
    configured = gate.commands(Path('/protected/root'), Path('/protected/archive'))
    assert configured['start'] == ['/usr/bin/systemctl', 'start', gate.UNIT]
    assert '--no-block' not in configured['start']
    for name in ('generic_shell', 'stale_crl'):
        command = configured[name]
        for required in ('IdentitiesOnly=yes', 'BatchMode=yes', 'StrictHostKeyChecking=yes', 'ConnectTimeout=5',
                         'UserKnownHostsFile=/protected/root/friends-restricted/known_hosts'):
            assert required in command
        assert command[-2] == 'family-restricted@186.246.45.246'


def test_budget_derived_from_existing_bounds():
    unit = (ROOT / 'deploy/friends/restricted/family-connect-restricted-sync.service').read_text()
    assert 'Type=oneshot' in unit and 'TimeoutStartSec=25' in unit
    source = (ROOT / 'control/friends/restricted_sync.py').read_text()
    assert 'timeout=15' in source
    assert gate.STEPS['start'][2] == 45
    assert sum(value[2] for key, value in gate.STEPS.items() if key != 'journal') + 2 + 5 + 1 == gate.TOTAL_SECONDS


def test_receipts_survive_shell_exit_trap_and_hard_exit(tmp_path):
    evidence = tmp_path / 'receipts'
    program = ('from scripts.restricted_sync_acceptance import Receipts; import os; '
               f'receipts=Receipts({str(evidence)!r},"exit-test"); '
               'receipts.persist({"step":"journal","timeout_expired":True}); os._exit(23)')
    import shlex
    command = f"trap 'printf rollback > {shlex.quote(str(tmp_path / 'rollback'))}' EXIT; " + shlex.join([sys.executable, '-c', program])
    result = subprocess.run(['sh', '-c', command], cwd=ROOT, capture_output=True)
    assert result.returncode == 23 and (tmp_path / 'rollback').read_text() == 'rollback'
    assert records(evidence)[0]['timeout_expired']


def test_real_journal_delay_reproduces_ten_second_boundary(receipts):
    runner = gate.Runner(receipts, [sys.executable, '-c', 'print("ActiveState=inactive\\nResult=success")'])
    with pytest.raises(gate.AcceptanceFailed, match='journal'):
        runner.run('journal', [sys.executable, '-c', 'import time;time.sleep(30)'])
    receipt = records(receipts.path)[0]
    assert receipt['timeout_configured'] == 10 and receipt['timeout_expired']
    assert 10 <= receipt['elapsed'] < 15


def test_isolated_cli_publisher_gateway_and_safe_snapshot_timing(bundle, tmp_path):
    import time
    material, service = material_fixture(bundle)
    profile, seed = tmp_path / 'gateway.json', tmp_path / 'seed.json'
    from control.friends.restricted import delegation
    trust, _ = delegation(service.manifest, service.anchor, int(time.time()))
    profile.write_text(json.dumps(dict(authority=trust['authority'], revocations=service.crl_source().decode(),
                                      minimum_crl=1, family=trust['family'], gateway=trust['gateway'])))
    seed.write_bytes(service.seed_source())
    profile.chmod(0o600)
    seed.chmod(0o600)
    script = '''import contextlib,io,json,runpy,subprocess,sys,time
archive,root,profile,seed=sys.argv[1:]
started=time.monotonic();sys.argv=[archive,'--help']
with contextlib.redirect_stdout(io.StringIO()):
    try:runpy.run_path(archive,run_name='__main__')
    except SystemExit as error:assert error.code==0
from control.friends import restricted_sync as sync
from pathlib import Path
assert sync.__file__.startswith(archive+'/')
assert not any('PycharmProjects' in value for value in sys.path)
real_run=subprocess.run;real_publish=sync.publish_crl;timings={}
def publish(*args):
    start=time.monotonic();result=real_publish(*args);timings['publisher_seconds']=time.monotonic()-start;return result
def ssh(command,**kwargs):
    assert command[0]=='/usr/bin/ssh' and 'StrictHostKeyChecking=yes' in command and command[-1]=='restricted-sync'
    start=time.monotonic();time.sleep(.02)
    result=real_run([sys.executable,'-I',archive,'gateway','--profile',profile,'--directory',seed],input=kwargs['input'],capture_output=True,timeout=kwargs['timeout'])
    assert result.returncode==0
    kwargs['stdout'].write(result.stdout);kwargs['stdout'].flush()
    timings['forced_command_simulation_seconds']=time.monotonic()-start
    return subprocess.CompletedProcess(command,0)
sync.publish_crl=publish;subprocess.run=ssh
sys.argv=[archive,'sync','--db',root+'/friends-access/access.db','--host','186.246.45.246','--ssh-key',root+'/friends-restricted/sync.key','--known-hosts',root+'/friends-restricted/known_hosts']
sync.main();timings['isolated_cli_seconds']=time.monotonic()-started
print(json.dumps(timings))
'''
    output = subprocess.run([sys.executable, '-I', '-c', script, str(bundle / 'restricted-sync.pyz'),
                             str(bundle.parent), str(profile), str(seed)], env=environment(material),
                            cwd=tmp_path, capture_output=True, check=True, timeout=25)
    timings = json.loads(output.stdout)
    started = time.monotonic()
    result = subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/restricted_sync_acceptance.py'),
                             '--snapshot', '--root', str(bundle.parent), '--runtime', str(bundle / 'restricted-sync.pyz')],
                            env=environment(), cwd=tmp_path, capture_output=True, check=True, timeout=5)
    timings['readback_seconds'] = time.monotonic() - started
    metadata = json.loads(result.stdout)
    assert metadata['directory_valid'] and metadata['crl_sequence'] == metadata['database_sequence'] == 2
    assert set(metadata) == set(gate.METADATA)
    assert timings['publisher_seconds'] < 25 and timings['forced_command_simulation_seconds'] < 15
    assert timings['isolated_cli_seconds'] < 25 and timings['readback_seconds'] < 5
    print('offline_timing=' + json.dumps(timings, sort_keys=True))


def test_failure_state_probe_timeout_does_not_hide_original(receipts):
    calls = []
    def execute(argv, timeout, payload):
        calls.append(timeout)
        return None, b'', b'', True, 'timeout'
    runner = gate.Runner(receipts, ['state'], execute_command=execute)
    with pytest.raises(gate.AcceptanceFailed, match='start'):
        runner.run('start', ['start'])
    found = records(receipts.path)
    assert found[0]['step'] == 'start' and found[0]['timeout_configured'] == 45
    assert found[1]['unit_state_at_timeout']['timeout_expired']
    assert found[1]['diagnostic']['step'] == 'timeout_state'
    assert found[1]['diagnostic']['timeout_configured'] == 2
    assert found[1]['diagnostic']['timeout_expired']
    assert calls == [45, 2]


def test_later_fresh_readback_is_evidence_not_success(receipts):
    runner, configured, _ = simulation(receipts, 'timeout_later_success')
    with pytest.raises(gate.AcceptanceFailed):
        gate.accept(runner, configured, b'private-synthetic-crl')
    found = records(receipts.path)
    after = next(item for item in found if item.get('event') == 'timeout-readback')
    assert after['observed_before']['crl_sequence'] == 13
    assert after['observed_after']['crl_sequence'] == 14
    assert after['diagnostic']['step'] == 'timeout_readback'
    assert after['diagnostic']['timeout_configured'] == 5
    assert not found[-1]['passed'] and found[-1]['completed'] == []


def test_operator_interrupt_preserves_step(receipts):
    def interrupted(*args):
        raise KeyboardInterrupt()
    runner = gate.Runner(receipts, ['state'], execute_command=interrupted)
    with pytest.raises(gate.AcceptanceFailed, match='start'):
        runner.run('start', ['start'])
    assert records(receipts.path)[0]['failure'] == 'operator-interrupted'
