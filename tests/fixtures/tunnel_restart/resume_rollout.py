"""Resume only a proven pre-mutation invocation guard abort, retaining both attempts."""

import json
import os
import shlex
import subprocess
import sys

from preserve import ROOT, WORK, digest
from rollout import CANDIDATE, PINS


def main():
    os.umask(0o077)
    assert sys.argv[1:] and sys.argv[1] in ('refresh', 'deploy')
    assert digest(WORK / 'gateway-seed-recovery') == CANDIDATE
    path = WORK / 'transition_remote.py'
    assert digest(path) == '9321d4ef48f79f395594a024448262d9ce40fbdd17d0e4d95c442bf9d67d7d38'
    assert 'RUNTIME_CHANGED_RECHECK' in (WORK / 'private/deploy-NL.stderr').read_text()
    assert (WORK / 'private/deploy-NL.jsonl').read_bytes() == b''
    source = path.read_text()
    if sys.argv[1] == 'refresh':
        proof = r'''
import hashlib,json,subprocess
from pathlib import Path
root=Path('/opt/apps/family_connect/friends-restricted');stage=root/'bin/.tunnel-restart-20261019-stage'
assert not (stage/'deploy-intent.json').exists()
assert not (root/'bin/bootstrap-broker-signal-observation-20261012.tunnel-restart-20261019-deploy').exists()
assert not (root/'renewal-state/owner.json').exists()
unit='family-connect-restricted-bootstrap.service'
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
assert state['ActiveState']=='active' and state['MainPID']!='0'
binary=root/'bin/bootstrap-broker-signal-observation-20261012'
assert hashlib.sha256(binary.read_bytes()).hexdigest()==hashlib.sha256(Path('/proc/'+state['MainPID']+'/exe').read_bytes()).hexdigest()=='4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7'
old=json.loads((stage/'before.json').read_bytes())['state']['InvocationID']
fatal=root/'fatal-application'/('application-'+old+'.json')
print(json.dumps(dict(result='PROVED_ABORT_BEFORE_MUTATION',state=state,previous_fatal=json.loads(fatal.read_bytes()) if fatal.exists() else None)),flush=True)
'''
        target = WORK / 'private/guard-abort-readback.jsonl'
        with target.open('xb') as output, (WORK / 'private/guard-abort-readback.stderr').open('xb') as errors:
            for code, suffix in [(proof, ''), (source, ' NL refresh')]:
                result = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','root@186.246.45.246',
                    'python3 -B -c ' + shlex.quote(code) + suffix], stdout=output, stderr=errors, timeout=45)
                assert result.returncode == 0, 'Refresh outcome requires readback'
        return
    records = [json.loads(line) for line in (WORK / 'private/guard-abort-readback.jsonl').read_text().splitlines()]
    assert [row['result'] for row in records] == ['PROVED_ABORT_BEFORE_MUTATION','FRESH_PRETRANSITION_SNAPSHOT']
    old = 'else:\n    original=json.loads((stage/"before.json").read_bytes())\n    before=state()'
    assert source.count(old) == 1
    source = source.replace(old, 'else:\n    original=json.loads((stage/"before-resumed.json").read_bytes())\n    before=state()')
    target = WORK / 'transition_resumed.py'
    with target.open('x') as handle: handle.write(source)
    operator = ROOT / 'state-client-build/beta88-throughput-20261019/operate.py'
    assert digest(operator) == PINS['operate.py']
    code = operator.read_text().replace('transition_remote.py', 'transition_resumed.py').replace(
        '.beta88-throughput-observation-20261019-stage', '.tunnel-restart-20261019-stage').replace(
        'root.parent/"mesh-perf-3/diagnostic-broker-final"', 'root/"gateway-seed-recovery"').replace(
        '04886384ce0bfa80568aea7e6d6fd2fec6ee0ed300a071ea806a8ef6a29a033b', CANDIDATE)
    sys.argv = [str(WORK / 'operate-resumed.py'), 'deploy', 'resumed']
    exec(compile(code, str(WORK / 'operate-resumed.py'), 'exec'), dict(__name__='__main__', __file__=str(WORK / 'operate-resumed.py')))


if __name__ == '__main__':
    main()
