import json
import os
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree

import pytest

from scripts.package_receiver_capture import ROOT, build


FILES = ('test_device_notices.py', 'test_friends_chat.py', 'test_chat_service_sender.py',
         'test_paid_beta.py', 'test_referrals.py', 'test_online_diagnostics.py', 'test_technical_metadata.py')
ACCESS_CASES = ('single_use_invite_and_perpetual_device', 'parallel_claims_grant_only_one_device',
                'installation_without_invitation_cannot_enroll', 'shorter_challenge_expires_at_server_deadline',
                'device_status_unknown_registered_and_invite_revoked',
                'device_status_does_not_consume_invite_and_rejects_replay')
RUNNER = '''
import importlib,json,sys,zipfile
from pathlib import Path
archive,repo,out=sys.argv[1:4]
sys.path[:0]=[archive,str(Path(repo)/'tests'),repo]
for name in ('provisioning','messenger'):
    importlib.import_module(name).__path__.append(str(Path(repo)/name.replace('.','/')))
with zipfile.ZipFile(archive) as bundle:
    members={name[:-3].replace('/','.') for name in bundle.namelist()
        if name.endswith('.py') and not name.endswith('__init__.py') and name!='__main__.py'}
modules=['control.friends.access','control.friends.chat','control.friends.chat_service',
    'control.friends.chat_sync','control.friends.paid_beta','control.friends.referrals',
    'control.friends.diagnostics','control.friends.technical_metadata',
    'control.friends.notices','scripts.service_notices']
for name in modules:
    assert importlib.import_module(name).__file__.startswith(archive+'/'),name
import pytest
result=pytest.main(['-q','-ra','--import-mode=importlib','--junitxml='+out+'.xml',
    '--basetemp='+out+'-state',*sys.argv[4:]])
loaded=sorted(members & sys.modules.keys())
for name in loaded:
    assert sys.modules[name].__file__.startswith(archive+'/'),name
Path(out+'-imports.json').write_text(json.dumps(dict(archive_bound_modules=loaded,result=result)))
raise SystemExit(result)
'''


@pytest.mark.parametrize('variant', ['baseline', 'candidate'])
def test_legacy_contracts_use_the_archive_not_checkout(tmp_path, variant):
    value = os.environ.get('FC_TEST_RECEIVER_BASELINE')
    if not value:
        pytest.skip('requires privately retained pinned installed archive')
    baseline = Path(value)
    build(baseline, tmp_path / 'candidate')
    archive = baseline if variant == 'baseline' else tmp_path / 'candidate/friends-http.pyz'
    output = tmp_path / ('legacy-' + variant)
    paths = [str(ROOT / 'tests' / name) for name in FILES]
    paths += [str(ROOT / 'tests/test_friends_access.py') + '::test_' + name for name in ACCESS_CASES]
    result = subprocess.run([sys.executable, '-I', '-c', RUNNER, str(archive), str(ROOT), str(output), *paths],
                            cwd=tmp_path, capture_output=True, timeout=180)
    output.with_suffix('.log').write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout.decode()[-8000:] + result.stderr.decode()[-2000:]
    suites = ElementTree.parse(output.with_suffix('.xml')).getroot().findall('testsuite')
    assert suites and all(int(suite.get('skipped', 0)) == 0 for suite in suites)
    imports = json.loads(Path(str(output) + '-imports.json').read_text())
    assert len(imports['archive_bound_modules']) >= 10 and imports['result'] == 0
