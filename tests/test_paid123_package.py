from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from control.friends import paid_beta, support_ids
from test_friends_http_runtime import request, running, runtime
from test_paid_beta import activated_device, snapshot
from test_paid_policy_package import packages, run_archive


ROOT = Path(__file__).resolve().parents[1]
SIGNED123 = 'ae011307b4afc58ea211ea6c5cd27c28bc472bda6af9b19892de400a3d3de15d'
UNSIGNED123 = '96a4eaed68ab31313d2d5ace3136998880d2d2fb8a803bde2d30cc17816efcae'


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def invoke(operator, database, arguments, *, clock=None, reason=None):
    command = [sys.executable, '-I', '-B']
    if clock is not None:
        command += ['-c', 'import sys,time,runpy;clock=float(sys.argv.pop(1));time.time=lambda:clock;'
                    'sys.path.insert(0,sys.argv[1]);sys.argv=sys.argv[1:];'
                    'runpy.run_path(sys.argv[0],run_name="__main__")', str(clock)]
    command += [str(operator), '--db', str(database), *arguments]
    result = subprocess.run(command, cwd=database.parent, capture_output=True, text=True, timeout=30)
    assert result.returncode == (2 if reason else 0), result.stdout + result.stderr
    value = json.loads(result.stdout)
    if reason:
        assert value == dict(schema=1, result='REJECTED', reason=reason)
    return value


def activation(support, now, *, code=123, apk=None, event='package-activation-123', until=None):
    release = next(item for item in paid_beta.PAID_ANDROID_RELEASES if item.version_code == code)
    return ['activate', '--support-id', support, '--event-id', event, '--reference', 'synthetic-only',
            '--period-start', utc(now), '--paid-until', utc(until or now + 3600),
            '--apk-sha256', apk or release.apk_sha256]


@pytest.fixture
def setup(runtime, packages):
    http, operator = packages
    runtime['command'][2] = str(http)
    access, device = runtime['access'], runtime['canary']
    now = int(time.time())
    with access.db() as database:
        support = support_ids.registered(database, device.reference)
        database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=?,last_seen=? WHERE device=?',
                         ('android', '0.1.18-beta123', 123, now, device.reference))
    invoke(operator, access.path, ['migrate'])
    return runtime, http, operator, support, now


def projection(http, database):
    program = '''import hashlib,json,sys
from pathlib import Path
namespace={}
exec(Path(sys.argv[1]).read_text(),namespace)
config=dict(archive=sys.argv[2],archive_sha256=hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest())
print(json.dumps(namespace['collect_subscriptions'](config,Path(sys.argv[3]),bytes(range(32)),include_history=True)))
'''
    result = subprocess.run([sys.executable, '-I', '-B', '-c', program,
        str(ROOT / 'control_plane/apps/console/subscription_collector.py'), str(http), str(database)],
        cwd=database.parent, capture_output=True, text=True, check=True, timeout=20)
    value = json.loads(result.stdout)
    assert value['status'] == 'ok'
    assert value['runtime_sha256'] == hashlib.sha256(http.read_bytes()).hexdigest()
    return value


def own_subscription(runtime):
    device = runtime['canary']
    status, raw = request(runtime['backend'], '/friends/challenge', body=dict(
        public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key,
        purpose='subscription', invitation=''))
    assert status == 200
    proof = device.prove_transport_key(json.loads(raw)['challenge'])
    status, raw = request(runtime['backend'], '/friends/device/subscription', body=proof)
    assert status == 200
    assert request(runtime['backend'], '/friends/device/subscription', body=proof)[0] == 403
    return json.loads(raw)


def test_packaged_activate_renew_grace_http_and_readonly_projection_agree(setup):
    runtime, http, operator, support, now = setup
    access, device = runtime['access'], runtime['canary']
    policy = run_archive(operator, 'policy')
    assert next(item for item in policy['releases'] if item['version_code'] == 123)['apk_sha256'] == SIGNED123
    before = snapshot(access)
    observed = projection(http, access.path)
    assert all(not row['cohort'] for row in observed['devices'])
    assert snapshot(access) == before
    commands = [activation(support, now),
                activation(support, now, event='package-renewal-123', until=now + 7200),
                ['grace', '--support-id', support, '--event-id', 'package-grace-123',
                 '--reference', 'synthetic-grace-not-payment', '--grace-until', utc(now + 10800)]]
    with running(runtime):
        for revision, command in enumerate(commands, 1):
            applied = invoke(operator, access.path, command)
            assert applied['event']['result'] == 'APPLIED'
            before_read = snapshot(access)
            own = own_subscription(runtime)
            observation = projection(http, access.path)
            pseudonym = hmac.new(bytes(range(32)), device.reference.encode(), hashlib.sha256).hexdigest()
            row = next(row for row in observation['devices'] if row['pseudonym'] == pseudonym)
            status = run_archive(operator, '--db', str(access.path), 'status', '--support-id', support)
            assert own['device'] == device.reference and own['cohort'] and row['cohort']
            assert own['subscription']['version'] == status['subscription']['version'] == revision
            assert all(own['subscription'][key] == value for key, value in row['subscription'].items())
            assert row['event']['event_type'] == applied['event']['event_type']
            assert len(observation['history']['events']) == revision
            assert any(not entry['cohort'] for entry in observation['devices'])
            assert snapshot(access) == before_read
    after = snapshot(access)
    assert all(before[name] == after[name] for name in ('devices', 'invites', 'device_support'))


@pytest.mark.parametrize('version,code,apk,reason', [
    ('0.1.18-beta123', 123, UNSIGNED123, 'PAYMENT_BOUNDS_OR_APK_INVALID'),
    ('0.1.18-beta123', 123, '0' * 64, 'PAYMENT_BOUNDS_OR_APK_INVALID'),
    ('0.1.18-beta119', 123, SIGNED123, 'ANDROID_BASELINE_REQUIRED'),
    ('0.1.18-beta124', 124, SIGNED123, 'ANDROID_BASELINE_REQUIRED'),
])
def test_packaged_operator_rejects_inexact_release_without_mutation(setup, version, code, apk, reason):
    runtime, _, operator, support, now = setup
    access = runtime['access']
    with access.db() as database:
        database.execute('UPDATE device_support SET app_version=?,version_code=?', (version, code))
    before = snapshot(access)
    invoke(operator, access.path, activation(support, now, apk=apk), reason=reason)
    assert snapshot(access) == before


@pytest.mark.parametrize('old_code', [108, 119])
@pytest.mark.parametrize('state', ['active', 'natural_expiry', 'expire', 'revoke'])
def test_packaged_old_replay_after123_is_exact_and_conflicts_reject(setup, old_code, state):
    runtime, _, operator, support, now = setup
    access = runtime['access']
    with access.db() as database:
        database.execute('UPDATE device_support SET app_version=?,version_code=?', (f'0.1.18-beta{old_code}', old_code))
    original = activation(support, now, code=old_code)
    first = invoke(operator, access.path, original, clock=now)
    grace = ['grace', '--support-id', support, '--event-id', 'old-grace-event',
             '--reference', 'synthetic-only', '--grace-until', utc(now + 7200)]
    first_grace = invoke(operator, access.path, grace, clock=now)
    with access.db() as database:
        database.execute('UPDATE device_support SET app_version=?,version_code=?', ('0.1.18-beta123', 123))
    if state in ('expire', 'revoke'):
        invoke(operator, access.path, [state, '--support-id', support, '--event-id', 'synthetic-terminal',
                                      '--reference', 'synthetic-only'])
    later = now + 8000 if state == 'natural_expiry' else now + 1
    before = snapshot(access)
    assert invoke(operator, access.path, original, clock=later) == dict(first, duplicate=True)
    assert invoke(operator, access.path, grace, clock=later) == dict(first_grace, duplicate=True)
    conflict = original.copy()
    conflict[-1] = SIGNED123
    invoke(operator, access.path, conflict, clock=later, reason='EVENT_ID_CONFLICT')
    if state == 'revoke':
        invoke(operator, access.path, activation(support, now, event='new-after-revoke', until=now + 9000),
               reason='REVOCATION_TERMINAL')
    assert snapshot(access) == before


def test_packaged_wrong_recipient_and_cohort_limit_remain_enforced(setup):
    runtime, _, operator, support, now = setup
    access = runtime['access']
    first = activation(support, now)
    invoke(operator, access.path, first)
    others = [activated_device(access) for _ in range(10)]
    with access.db() as database:
        database.execute('UPDATE device_support SET app_version=?,version_code=?', ('0.1.18-beta123', 123))
    wrong = first.copy()
    wrong[2] = others[0][1]
    before = snapshot(access)
    invoke(operator, access.path, wrong, reason='EVENT_ID_CONFLICT')
    assert snapshot(access) == before
    for index, (_, other_support) in enumerate(others[:9]):
        invoke(operator, access.path, activation(other_support, now, event=f'cohort-limit-{index}'))
    before = snapshot(access)
    invoke(operator, access.path, activation(others[-1][1], now, event='cohort-limit-final'), reason='COHORT_LIMIT')
    assert snapshot(access) == before


@pytest.mark.parametrize('other', [108, 119])
def test_packaged_conflicting_latest_observations_reject_payment_and_grace(setup, other):
    runtime, _, operator, support, now = setup
    access, device = runtime['access'], runtime['canary']
    invoke(operator, access.path, activation(support, now))
    with access.db() as database:
        database.execute('INSERT INTO restricted_readiness_results(nonce,correlation,device,challenge_at,ack,ack_at) '
            'VALUES (?,?,?,?,?,?)', ('1' * 64, '2' * 32, device.reference, now - 10,
                                    json.dumps(dict(app_version=f'0.1.18-beta{other}', version_code=other)), now))
    before = snapshot(access)
    invoke(operator, access.path, activation(support, now, event='conflict-renewal'), reason='ANDROID_VERSION_CONFLICT')
    invoke(operator, access.path, ['grace', '--support-id', support, '--event-id', 'conflict-grace',
        '--reference', 'synthetic-only', '--grace-until', utc(now + 7200)], reason='ANDROID_VERSION_CONFLICT')
    assert snapshot(access) == before
