import ast
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from scripts import restricted_bootstrap_acceptance as gate
from test_restricted_runtime import bundle, material_fixture

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = runpy.run_path(str(ROOT / 'tests/fixtures/restricted_bootstrap_attempt8.py'))
NOW = 1790930207000000000
ISSUED = 1790930212303143974
EXPIRES = 1790933507411330475
HEALTHY = dict(ActiveState='active', SubState='running', Result='success', MainPID=123,
               NRestarts=0, ExecMainStatus=0, ExecMainStartTimestampMonotonic=200)
INACTIVE = dict(HEALTHY, ActiveState='inactive', SubState='dead', MainPID=0,
                ExecMainStartTimestampMonotonic=100)
MATERIAL = dict(binding='a' * 64, published=True, directory_valid=True, canonical_utc=True,
                seed_count=1, issued_ns=ISSUED, expires_ns=EXPIRES,
                crl_expires_ns=NOW + 900_000_000_000, gateway_expires_ns=NOW + 3600_000_000_000)


def records(path):
    return [json.loads(item.read_text()) for item in sorted(path.glob('*.json'))]


class Fake:
    def __init__(self, case='healthy', journal='available'):
        self.case, self.journal = case, journal
        self.elapsed = 0
        self.states = self.snapshots = 0
        self.calls = []

    def clock(self):
        return self.elapsed

    def sleep(self, seconds):
        self.elapsed += seconds

    def execute(self, argv, timeout):
        step = argv[0]
        self.calls.append((step, timeout))
        if step == 'state':
            self.states += 1
            value = dict(INACTIVE if self.states == 1 else HEALTHY)
            if self.states > 1:
                if self.case == 'service-failed':
                    value.update(ActiveState='failed', SubState='failed', Result='exit-code', ExecMainStatus=1)
                if self.case == 'restarts':
                    value['NRestarts'] = 3
                if self.case == 'final-failed' and self.states == 3:
                    value['ActiveState'] = 'failed'
                if self.case == 'pid-changed' and self.states == 3:
                    value['MainPID'] += 1
                if self.case == 'state-timeout':
                    self.sleep(timeout)
                    return None, b'', b'', True
            raw = '\n'.join(key + '=' + str(item) for key, item in value.items()).encode()
        elif step == 'snapshot':
            self.snapshots += 1
            value = dict(MATERIAL)
            if self.snapshots == 1 and self.case != 'stale-file' or self.case == 'no-ready':
                value.update(published=False, directory_valid=False, canonical_utc=False, seed_count=0, issued_ns=0, expires_ns=0)
            if self.snapshots > 1:
                if self.case == 'invalid-directory':
                    value['directory_valid'] = False
                if self.case == 'wrong-gateway':
                    value['binding'] = 'b' * 64
                if self.case == 'old-publication':
                    value['issued_ns'] = NOW - 1
                if self.case == 'noncanonical':
                    value['canonical_utc'] = False
                if self.case == 'wrong-seeds':
                    value['seed_count'] = 2
                if self.case == 'final-directory' and self.snapshots == 3:
                    value['directory_valid'] = False
            raw = json.dumps(value).encode()
        elif step == 'start':
            if self.case == 'start-failed':
                return 1, b'', b'private error', False
            if self.case in ('start-timeout', 'over-budget'):
                self.sleep(timeout + 1)
                return 0, b'', b'', self.case == 'start-timeout'
            raw = b''
        elif step == 'journal':
            if self.journal == 'timeout':
                self.sleep(5.01)
                return None, b'PRIVATE-PROOF', b'PRIVATE-URL', True
            if self.journal == 'failed':
                return 1, b'', b'PRIVATE-ERROR', False
            if self.journal == 'raise-timeout':
                raise subprocess.TimeoutExpired(argv, timeout)
            if self.journal == 'unavailable':
                raise OSError('PRIVATE-ERROR')
            raw = b'{"event":"bootstrap_seed_ready","private":"PRIVATE-PROOF"}'
        else:
            raise AssertionError('Unexpected command boundary')
        return 0, raw, b'', False


def make_runner(tmp_path, fake):
    receipts = gate.Receipts(tmp_path / 'receipts', 'offline-test')
    runner = gate.Runner(receipts, {key: [key] for key in ('state', 'snapshot', 'start', 'journal')},
                         execute_command=fake.execute, clock=fake.clock, wall_clock=lambda: NOW, sleep=fake.sleep)
    return runner, receipts


@pytest.mark.parametrize(('case', 'journal', 'passed', 'diagnostic'), [
    ('healthy', 'available', True, 'diagnostic_available'),
    ('healthy', 'timeout', True, 'diagnostic_timeout'),
    ('healthy', 'failed', True, 'diagnostic_unavailable'),
    ('service-failed', 'available', False, 'diagnostic_available'),
    ('service-failed', 'unavailable', False, 'diagnostic_unavailable'),
    ('no-ready', 'available', False, 'diagnostic_available'),
    ('invalid-directory', 'available', False, 'diagnostic_available'),
    ('restarts', 'available', False, 'diagnostic_available'),
    ('healthy', 'raise-timeout', True, 'diagnostic_timeout'),
])
def test_authoritative_diagnostic_matrix(tmp_path, case, journal, passed, diagnostic):
    fake = Fake(case, journal)
    runner, receipts = make_runner(tmp_path, fake)
    try:
        assert runner.accept() is passed
        before = {path.name: path.read_bytes() for path in receipts.path.glob('authoritative-*.json')}
        verdict = [record for record in records(receipts.path) if record['event'] == 'verdict']
        assert len(verdict) == 1 and verdict[0]['passed'] is passed
        assert not any(step == 'journal' for step, _ in fake.calls)
        assert runner.diagnose(True)['classification'] == diagnostic
        assert before == {path.name: path.read_bytes() for path in receipts.path.glob('authoritative-*.json')}
        assert all('PRIVATE-' not in path.read_text() and 'binding' not in path.read_text()
                   for path in receipts.path.glob('diagnostic-*.json'))
        assert len([record for record in records(receipts.path) if record['event'] == 'verdict']) == 1
        if case == 'no-ready':
            assert fake.elapsed <= gate.READY_SECONDS + gate.JOURNAL_SECONDS
            assert verdict[0]['failure'] == 'ready_deadline'
    finally:
        receipts.close()


@pytest.mark.parametrize('case', ['start-failed', 'start-timeout', 'over-budget', 'state-timeout',
                                 'final-failed', 'pid-changed', 'stale-file', 'wrong-gateway',
                                 'old-publication', 'noncanonical', 'wrong-seeds', 'final-directory'])
def test_real_authoritative_failures_never_waived(tmp_path, case):
    runner, receipts = make_runner(tmp_path, Fake(case, 'timeout'))
    try:
        assert not runner.accept()
        assert runner.diagnose(True)['classification'] == 'diagnostic_timeout'
        assert [record['passed'] for record in records(receipts.path) if record['event'] == 'verdict'] == [False]
    finally:
        receipts.close()


def test_fsync_before_diagnostics_and_no_overwrite(tmp_path, monkeypatch):
    synced = []
    real_fsync = os.fsync
    monkeypatch.setattr(os, 'fsync', lambda descriptor: (synced.append(descriptor), real_fsync(descriptor))[1])
    runner, receipts = make_runner(tmp_path, Fake())
    try:
        assert runner.accept()
        assert len(synced) == 1 + 2 * len(records(receipts.path))
        saved = synced[:]
        assert runner.diagnose(False)['classification'] == 'diagnostic_not_requested'
        assert len(synced) == len(saved) + 2
        with pytest.raises(FileExistsError):
            gate.Receipts(receipts.path, 'another-run')
    finally:
        receipts.close()


def test_failed_fsync_never_claims_acceptance(tmp_path, monkeypatch):
    runner, receipts = make_runner(tmp_path, Fake())
    def fail(descriptor):
        raise OSError('fsync unavailable')
    monkeypatch.setattr(os, 'fsync', fail)
    try:
        with pytest.raises(OSError):
            runner.accept()
        assert not list(receipts.path.glob('*.json'))
    finally:
        receipts.close()


def test_real_timeout_and_redacted_command_receipt(tmp_path):
    result = gate.execute([sys.executable, '-c', 'import time; print("PRIVATE-PROOF",flush=True); time.sleep(5)'], .05)
    assert result[0] is None and result[3]
    runner, receipts = make_runner(tmp_path, Fake())
    runner.execute = lambda argv, timeout: result
    try:
        assert not runner.accept()
        text = json.dumps(records(receipts.path))
        assert 'PRIVATE-PROOF' not in text and 'state_timeout' in text
    finally:
        receipts.close()


def test_attempt8_exact_retained_flow():
    flow = FIXTURE['FLOW']
    assert hashlib.sha256(flow.encode()).hexdigest() == FIXTURE['FLOW_SHA256']
    source = ROOT / 'state-client-build/prov1-attempt5/deployment.py'
    if source.exists():
        tree = ast.parse(source.read_text())
        old = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'NL_START' for target in node.targets))
        old = old.replace('attempt5', 'attempt8').replace("'-o','json','--no-pager'", "'-o','json','-n','100','--no-pager'")
        old = old.replace("capture_output=True,text=True,check=True).stdout\n    events=", "capture_output=True,text=True,check=True,timeout=5).stdout\n    events=")
        assert flow == old
    assert flow.index("validation=json.loads") < flow.index("logs=subprocess.run") < flow.index("persist('nl-live.json'")


def test_attempt8_old_fail_new_pass(tmp_path, monkeypatch):
    from cryptography import x509
    root = tmp_path / 'old'
    material = root / 'friends-restricted'
    material.mkdir(parents=True)
    (material / 'gateway.json').write_text(json.dumps({'revocations': 'synthetic'}))
    (material / 'directory.json').write_text(json.dumps({'issued_at': '2026-10-02T08:36:52.303143974Z',
        'expires_at': '2026-10-02T09:31:47.411330475Z', 'seeds': [{}]}))
    evidence = tmp_path / 'old-receipts'
    evidence.mkdir(mode=0o700)
    fake = Fake(journal='timeout')
    def run(argv, **kwargs):
        if argv[0] == 'systemctl':
            if argv[1] == 'start':
                return SimpleNamespace(returncode=0)
            fake.states += 1
            state = INACTIVE if fake.states == 1 else HEALTHY
            return SimpleNamespace(stdout='\n'.join(key + '=' + str(value) for key, value in state.items()))
        if 'directory-check' in argv:
            Path(argv[argv.index('--receipt') + 1]).write_text(json.dumps({'result': 'passed'}))
            return SimpleNamespace(returncode=0)
        assert argv[0] == 'journalctl' and kwargs['timeout'] == 5
        fake.sleep(5.01)
        raise subprocess.TimeoutExpired(argv, 5)
    with monkeypatch.context() as patched:
        patched.setattr(subprocess, 'run', run)
        patched.setattr(x509, 'load_pem_x509_crl', lambda raw: SimpleNamespace(next_update_utc=SimpleNamespace(timestamp=lambda: gate.time.time() + 900)))
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(FIXTURE['FLOW'].replace('/opt/apps/family_connect', str(root)), '<attempt8>', 'exec'), {'BACKUP': str(evidence)})
    old = json.loads((evidence / 'nl-live.json').read_text())
    assert old['directory_validation']['result'] == 'passed'
    assert old['service_state']['NRestarts'] == '0'
    assert old['failure_type'] == 'TimeoutExpired' and not old['bootstrap_ready']
    assert fake.elapsed > 5
    runner, receipts = make_runner(tmp_path, Fake(journal='timeout'))
    try:
        assert runner.accept()
        assert runner.diagnose(True)['classification'] == 'diagnostic_timeout'
    finally:
        receipts.close()


@pytest.mark.parametrize('case', ['healthy', 'service-failed'])
def test_authoritative_receipts_survive_exit_and_rollback(tmp_path, case):
    evidence = tmp_path / 'receipts'
    code = '''import os,runpy,sys
sys.path.insert(0,sys.argv[1])
sys.path.insert(0,os.path.join(sys.argv[1],'tests'))
scope=runpy.run_path(sys.argv[2])
gate=scope['gate'];fake=scope['Fake'](sys.argv[4])
receipts=gate.Receipts(sys.argv[3],'exit-test')
def execute(argv,timeout):
 if argv[0]=='journal':os._exit(7)
 return fake.execute(argv,timeout)
runner=gate.Runner(receipts,{key:[key] for key in ('state','snapshot','start','journal')},execute_command=execute,clock=fake.clock,wall_clock=lambda:scope['NOW'],sleep=fake.sleep)
runner.accept()
runner.diagnose(True)
'''
    marker = tmp_path / 'rollback'
    command = [sys.executable, '-I', '-c', code, str(ROOT), str(Path(__file__).resolve()), str(evidence), case]
    result = subprocess.run(['sh', '-c', 'trap \'printf rollback > "$MARKER"\' EXIT; "$@"', 'test', *command],
                            env=dict(os.environ, MARKER=str(marker)), capture_output=True, timeout=10)
    assert result.returncode == 7 and marker.read_text() == 'rollback'
    found = records(evidence)
    assert [record['passed'] for record in found if record['event'] == 'verdict'] == [case == 'healthy']
    assert all(record['kind'] == 'authoritative' for record in found)


def test_no_default_execution_or_diagnostic_services():
    result = subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/restricted_bootstrap_acceptance.py')], capture_output=True, timeout=5)
    assert result.returncode == 2
    configured = gate.commands(Path('/synthetic/root'), Path('/synthetic/runtime.pyz'))
    assert configured['start'] == ['/usr/bin/systemctl', 'start', gate.UNIT]
    assert configured['snapshot'][1] == '-I'
    assert not any('ssh' in argument or 'refresh' in argument for argv in configured.values() for argument in argv)


def test_diagnostics_cannot_precede_durable_decision(tmp_path):
    fake = Fake()
    runner, receipts = make_runner(tmp_path, fake)
    try:
        with pytest.raises(gate.AcceptanceFailed, match='authoritative_verdict_missing'):
            runner.diagnose(True)
        assert not fake.calls
    finally:
        receipts.close()


def test_authoritative_deadline_and_single_verdict(tmp_path):
    runner, receipts = make_runner(tmp_path, Fake())
    runner.deadline = -1
    try:
        assert not runner.accept()
        with pytest.raises(gate.AcceptanceFailed, match='already_written'):
            runner.accept()
        assert [record['failure'] for record in records(receipts.path) if record['event'] == 'verdict'] == ['authoritative_deadline']
        assert gate.TOTAL_SECONDS == 2 + 5 + 30 + 120 + 2 + 5 + 1
    finally:
        receipts.close()


@pytest.mark.parametrize('case', ['missing', 'valid', 'invalid', 'offset', 'wrong-family', 'wrong-gateway', 'future', 'expired'])
def test_isolated_snapshot_uses_real_archive_validator(bundle, tmp_path, case):
    from cryptography.hazmat.primitives.serialization import Encoding
    from control.friends.restricted import delegation, iso
    material, service = material_fixture(bundle)
    now = int(time.time())
    trust, authority = delegation(service.manifest, service.anchor, now)
    profile = dict(family=trust['family'], gateway=trust['gateway'], authority=trust['authority'],
                   certificate=authority.public_bytes(Encoding.PEM).decode(), minimum_revision=1,
                   revocations=service.crl_source().decode(), private_key='synthetic-not-used')
    profile_path = material / 'gateway.json'
    profile_path.write_text(json.dumps(profile))
    profile_path.chmod(0o600)
    value = json.loads(service.seed_source())
    if case == 'invalid':
        value['version'] = 2
    if case == 'offset':
        value['issued_at'] = value['issued_at'].replace('Z', '+00:00')
    if case == 'wrong-family':
        value['family'] = 'c' * 32
    if case == 'wrong-gateway':
        value['seeds'][0]['gateway'] = 'c' * 32
    if case == 'future':
        value['issued_at'] = iso(now + 600)
    if case == 'expired':
        value['issued_at'], value['expires_at'] = iso(now - 100), iso(now - 1)
    if case != 'missing':
        directory_path = material / 'directory.json'
        directory_path.write_text(json.dumps(value))
        directory_path.chmod(0o600)
    before = {path.name: path.read_bytes() for path in material.iterdir() if path.is_file()}
    result = subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/restricted_bootstrap_acceptance.py'),
                             '--snapshot', '--root', str(bundle.parent), '--runtime', str(bundle / 'restricted-sync.pyz')],
                            cwd=tmp_path, env={key: value for key, value in os.environ.items() if key not in ('PYTHONPATH', 'PYTHONHOME')},
                            capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr
    snapshot = json.loads(result.stdout)
    assert snapshot['published'] is (case != 'missing')
    assert snapshot['directory_valid'] is (case in ('valid', 'offset'))
    assert snapshot['canonical_utc'] is (case == 'valid')
    assert snapshot['gateway_expires_ns'] > now * 1_000_000_000
    assert before == {path.name: path.read_bytes() for path in material.iterdir() if path.is_file()}
    assert not any(marker in result.stdout for marker in (b'PRIVATE KEY', b'https://', b'synthetic-not-used', trust['family'].encode()))


def test_receipt_persistence_failure_during_diagnostics_preserves_verdict(tmp_path, monkeypatch):
    runner, receipts = make_runner(tmp_path, Fake())
    try:
        assert runner.accept()
        before = {path.name: path.read_bytes() for path in receipts.path.glob('authoritative-*.json')}
        def fail(descriptor):
            raise OSError('diagnostic evidence storage unavailable')
        monkeypatch.setattr(os, 'fsync', fail)
        with pytest.raises(OSError):
            runner.diagnose(True)
        assert before == {path.name: path.read_bytes() for path in receipts.path.glob('authoritative-*.json')}
    finally:
        receipts.close()


@pytest.mark.parametrize(('case', 'expected'), [('healthy', 0), ('service-failed', 1)])
def test_cli_keeps_authoritative_verdict_with_journal_warning(tmp_path, monkeypatch, capsys, case, expected):
    fake = Fake(case, 'timeout')
    original = gate.Runner
    def runner(receipts, commands):
        return original(receipts, {key: [key] for key in commands}, execute_command=fake.execute,
                        clock=fake.clock, wall_clock=lambda: NOW, sleep=fake.sleep)
    monkeypatch.setattr(gate, 'Runner', runner)
    monkeypatch.setattr(sys, 'argv', ['operator', '--execute', '--runtime', str(tmp_path / 'unused.pyz'),
                                    '--root', str(tmp_path / 'runtime'), '--evidence', str(tmp_path / 'receipts'),
                                    '--generation', 'offline-cli', '--journal'])
    assert gate.main() == expected
    assert json.loads(capsys.readouterr().out) == dict(authoritative='PASS' if expected == 0 else 'FAIL', journal='diagnostic_timeout')
