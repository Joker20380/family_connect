"""Materialize the existing guarded gateway transition for this exact delta."""
import json
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'state-client-build/p1-owner-acceptance-20261021'
BASE=ROOT/'state-client-build/speed-candidate-20261021'


def main():
    helpers=runpy.run_path(str(ROOT/'tests/fixtures/speed_candidate/prepare.py'))
    digest,write=helpers['digest'],helpers['write']
    build=json.loads((WORK/'gateway-build.json').read_text());assert digest(WORK/'gateway-speed')==build['sha256']
    target=WORK/'transitions';assert not target.exists()
    for name in ('private','receipts'):(target/name).mkdir(mode=0o700,parents=True)
    pins={}
    for name in ('operate.py','transition_remote.py','readiness.py'):
        original=BASE/'transitions'/name;pins[name]=digest(original)
        source=original.read_text()
        source=source.replace('ae527cbd0b93a5d34d10af1a5424cdf8254d79e253c9994a57520408614ce1dd','CANDIDATE_HASH')
        source=source.replace('734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e',build['parent_sha256'])
        source=source.replace('CANDIDATE_HASH',build['sha256']).replace('speed-candidate-20261021','p1-owner-acceptance-20261021')
        write(target/name,source)
    (target/'prepared.json').write_text(json.dumps(dict(candidate=build['sha256'],baseline=build['parent_sha256'],source_pins=pins,network_operations=0,shared_restart_required=True),indent=2))
    print('PREPARED_TRANSITION_NO_DEPLOYMENT')


if __name__=='__main__':main()
