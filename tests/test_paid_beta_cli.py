import json
import hashlib
import subprocess
import sys
import zipfile

from control.friends import paid_beta, paid_beta_admin
from scripts.package_support_operator import build
from test_paid_beta import NOW, registry, snapshot


def test_cli_utc_commands_and_private_receipts(registry, monkeypatch, capsys):
    access, _, support = registry
    monkeypatch.setattr(paid_beta_admin.time, 'time', lambda: NOW)
    def invoke(*arguments):
        result = paid_beta_admin.main(['--db', str(access.path), *arguments])
        output = capsys.readouterr().out
        assert support not in output and 'private-reference' not in output
        return result, json.loads(output)
    assert invoke('migrate')[1]['cohort_size'] == 0
    before = snapshot(access)
    assert not invoke('status', '--support-id', support)[1]['cohort']
    assert snapshot(access) == before
    base = ['activate', '--support-id', support, '--event-id', 'event-cli-0001', '--reference', 'private-reference',
            '--period-start', '2027-01-15T08:00:00Z', '--paid-until', '2027-01-16T08:00:00Z',
            '--apk-sha256', paid_beta.APK_SHA256]
    assert invoke(*base)[1]['event']['new_state'] == 'active'
    assert invoke(*base)[1]['duplicate']
    assert invoke('status', '--support-id', support)[1]['effective_state'] == 'active'
    assert invoke('grace', '--support-id', support, '--event-id', 'event-cli-0002', '--reference', 'private-reference',
                  '--grace-until', '2027-01-17T08:00:00Z')[1]['event']['new_state'] == 'grace'
    for action in ('expire', 'revoke'):
        assert invoke(action, '--support-id', support, '--event-id', 'event-cli-' + action,
                      '--reference', 'private-reference')[0] == 0
    assert invoke('status', '--support-id', support)[1]['effective_state'] == 'revoked'
    assert invoke(*base)[1]['duplicate']


def test_cli_rejects_bad_time_and_hash_without_raw_input(registry, monkeypatch, capsys):
    access, _, support = registry
    monkeypatch.setattr(paid_beta_admin.time, 'time', lambda: NOW)
    before = snapshot(access)
    assert paid_beta_admin.main(['--db', str(access.path), 'activate', '--support-id', support,
        '--event-id', 'event-invalid', '--reference', 'secret-reference', '--period-start', 'local-secret-time',
        '--paid-until', '2027-01-16T08:00:00Z', '--apk-sha256', 'wrong']) == 2
    output = capsys.readouterr().out
    assert all(value not in output for value in (support, 'secret-reference', 'local-secret-time'))
    assert snapshot(access) == before


def test_paid_operator_artifact_reproducible_and_isolated(tmp_path):
    first, second = tmp_path / 'paid-beta.pyz', tmp_path / 'second.pyz'
    assert build(first, operator='paid-beta') == build(second, operator='paid-beta')
    with zipfile.ZipFile(first) as archive:
        assert 'control/friends/paid_beta.py' in archive.namelist()
        assert 'control/friends/paid_beta_admin.py' in archive.namelist()
    result = subprocess.run([sys.executable, '-I', str(first), '--help'], cwd=tmp_path,
                            capture_output=True, text=True, check=True)
    assert 'activate' in result.stdout and 'revoke' in result.stdout
    result = subprocess.run([sys.executable, '-I', str(first), '--db', str(tmp_path / 'absent.db'), 'migrate'],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 2 and not (tmp_path / 'absent.db').exists()


def test_cli_argument_errors_do_not_echo_private_inputs(capsys):
    assert paid_beta_admin.main(['--unknown', 'private-argument']) == 2
    captured = capsys.readouterr()
    assert 'private-argument' not in captured.out + captured.err
    assert json.loads(captured.out)['reason'] == 'INVALID_ARGUMENTS'


def test_pinned_overlay_includes_new_runtime_dependency(tmp_path, monkeypatch, capsys):
    from scripts import build_bridge_access
    baseline = tmp_path / 'baseline.pyz'
    with zipfile.ZipFile(baseline, 'w') as archive:
        for name in build_bridge_access.OVERLAYS:
            archive.writestr(name, 'baseline = True\n')
    monkeypatch.setattr(build_bridge_access, 'BASE_API_SHA256', hashlib.sha256(baseline.read_bytes()).hexdigest())
    output = tmp_path / 'built'
    monkeypatch.setattr(sys, 'argv', ['build_bridge_access', '--baseline', str(baseline), '--output', str(output)])
    build_bridge_access.main()
    receipt = json.loads(capsys.readouterr().out)
    assert receipt['additions'] == ['control/friends/paid_beta.py']
    with zipfile.ZipFile(output / 'bridge-access-v2.pyz') as archive:
        assert 'control/friends/paid_beta.py' in archive.namelist()
