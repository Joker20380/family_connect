"""Materialize existing guarded transition: exact f631 rollback, no deployment."""
import hashlib
import json
import subprocess
from prepare import BASE, WORK


def main():
    build=json.loads((WORK/'gateway-build.json').read_text())
    assert hashlib.sha256((WORK/'gateway-speed').read_bytes()).hexdigest()==build['sha256']
    target=WORK/'transitions'
    assert not target.exists()
    for name in ('private','receipts'):(target/name).mkdir(mode=0o700,parents=True)
    pins={}
    for name in ('operate.py','transition_remote.py','readiness.py'):
        original=BASE/'transitions'/name;pins[name]=hashlib.sha256(original.read_bytes()).hexdigest()
        source=original.read_text().replace(build['parent_sha256'],'CANDIDATE_HASH')
        source=source.replace('ae527cbd0b93a5d34d10af1a5424cdf8254d79e253c9994a57520408614ce1dd',build['parent_sha256'])
        source=source.replace('CANDIDATE_HASH',build['sha256']).replace('p1-owner-acceptance-20261021','p1-lifecycle-101-20261021')
        if name=='transition_remote.py':
            source=source.replace('else:\n    original=json.loads((stage/"before.json").read_bytes())',
                                  'else:\n    observed=stage/"before-resumed.json"\n    original=json.loads((observed if observed.exists() else stage/"before.json").read_bytes())')
        subprocess.run(['apply_patch','*** Begin Patch\n*** Add File: '+str(target/name)+'\n'+''.join('+'+line+'\n' for line in source.splitlines())+'*** End Patch\n'],check=True)
    (target/'prepared.json').write_text(json.dumps(dict(candidate=build['sha256'],baseline=build['parent_sha256'],source_pins=pins,shared_restart_required=True,network_operations=0),indent=2))


if __name__=='__main__':main()
