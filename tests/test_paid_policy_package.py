from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

import pytest

from control.friends import paid_beta
from scripts.package_friends_http import build as build_http
from scripts.package_paid_policy_overlay import MEMBER, build as build_overlay
from scripts.package_support_operator import build as build_operator
from test_paid_beta import registry, snapshot
from test_paid_release_policy import set_release


@pytest.fixture
def packages(tmp_path):
    supplied_http = os.environ.get('FC_TEST_PAID_HTTP')
    supplied_operator = os.environ.get('FC_TEST_PAID_OPERATOR')
    if supplied_http or supplied_operator:
        assert supplied_http and supplied_operator, 'Both accepted package inputs are required'
        return Path(supplied_http).resolve() / 'friends-http.pyz', Path(supplied_operator).resolve()
    http = tmp_path / 'http'
    build_http(http)
    operator = tmp_path / 'operator.pyz'
    build_operator(operator, operator='paid-beta')
    return http / 'friends-http.pyz', operator


def run_archive(archive, *args):
    result = subprocess.run([sys.executable, '-I', '-B', str(archive), *args],
                            cwd=archive.parent, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_packaged_policy_reports_matching_modules_without_registry(packages, tmp_path):
    http, operator = packages
    absent = tmp_path / 'absent.sqlite'
    policy = run_archive(operator, '--db', str(absent), 'policy')
    assert not absent.exists()
    assert policy['releases'] == paid_beta.policy()['releases']
    assert policy['archive_sha256'] == hashlib.sha256(operator.read_bytes()).hexdigest()
    with zipfile.ZipFile(http) as package:
        assert policy['modules'][MEMBER] == hashlib.sha256(package.read(MEMBER)).hexdigest()
    code = "import json,sys;sys.path.insert(0,sys.argv[1]);from control.friends import paid_beta;print(json.dumps(paid_beta.policy()))"
    result = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(http)],
                            cwd=tmp_path, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == paid_beta.policy()


@pytest.mark.parametrize('code', [108, 119, 123])
def test_actual_operator_and_http_paid_module_apply_same_policy(packages, registry, code):
    http, operator = packages
    access, device, support = registry
    set_release(registry, code)
    release = next(item for item in paid_beta.PAID_ANDROID_RELEASES if item.version_code == code)
    now = int(time.time())
    utc = lambda stamp: datetime.fromtimestamp(stamp, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    command = ['--db', str(access.path), 'activate', '--support-id', support,
               '--event-id', 'package-payment-policy', '--reference', 'synthetic', '--apk-sha256', release.apk_sha256,
               '--period-start', utc(now), '--paid-until', utc(now + 3600)]
    original = run_archive(operator, *command)
    assert original['event']['result'] == 'APPLIED'
    probe = '''import json,sys
sys.path.insert(0,sys.argv[1])
from control.friends import paid_beta
assert paid_beta.__loader__.archive == sys.argv[1]
with paid_beta.connection(sys.argv[2],write=True) as database:
    result = paid_beta.apply_event(database,sys.argv[3],'grace','package-grace-policy','synthetic',
                                  now=int(sys.argv[4]),grace_until=int(sys.argv[4])+7200)
print(json.dumps(result))
'''
    result = subprocess.run([sys.executable, '-I', '-B', '-c', probe, str(http), str(access.path), support, str(now)],
                            cwd=http.parent, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)['event']['new_state'] == 'grace'
    before = snapshot(access)
    assert run_archive(operator, *command) == dict(original, duplicate=True)
    assert snapshot(access) == before
    assert run_archive(operator, '--db', str(access.path), 'status', '--support-id', support)['subscription']['version'] == 2


def test_overlay_preserves_complete_serving_inventory_and_executes_policy(packages, tmp_path):
    original, _ = packages
    http = tmp_path / 'overlay-baseline.pyz'
    http.write_bytes(original.read_bytes())
    with zipfile.ZipFile(http, 'a') as archive:
        archive.writestr('unrelated-installed-bootstrap.txt', b'keep the accepted serving revision')
    with zipfile.ZipFile(http) as archive:
        module_pin = hashlib.sha256(archive.read(MEMBER)).hexdigest()
    source = tmp_path / 'source'
    target = source / MEMBER
    target.parent.mkdir(parents=True)
    target.write_bytes(Path(paid_beta.__file__).read_bytes() + b'\n')
    pin = hashlib.sha256(http.read_bytes()).hexdigest()
    output = tmp_path / 'overlay.pyz'
    receipt = build_overlay(http, pin, module_pin, output, source)
    assert receipt['changed'] == [MEMBER]
    assert set(receipt['before']) == set(receipt['after'])
    assert all(receipt['before'][name] == receipt['after'][name] for name in receipt['before'] if name != MEMBER)
    for wrong_archive, wrong_module in [(('0' * 64), module_pin), (pin, '0' * 64)]:
        with pytest.raises(ValueError, match='pin mismatch'):
            build_overlay(http, wrong_archive, wrong_module, tmp_path / 'rejected.pyz', source)
    code = "import sys,json;sys.path.insert(0,sys.argv[1]);from control.friends import paid_beta;print(json.dumps(paid_beta.policy()))"
    actual = subprocess.check_output([sys.executable, '-I', '-B', '-c', code, str(output)], cwd=tmp_path)
    assert json.loads(actual) == paid_beta.policy()
