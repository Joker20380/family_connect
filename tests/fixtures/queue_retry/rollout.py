"""Fresh ordinary transitions, with current1011 baseline and unique intents."""

import json
import os
from pathlib import Path
import sys

from prepare import ROOT, WORK, GATEWAY, digest

PINS={'operate.py':'c24f1ee919874d04ff262f77f6ddc1b69637f505238c9fdf44cc7c5fda45e4c8',
      'transition_remote.py':'c7346a16ae425018eef11af4d47c9edf28c997746f53c05cda177861e803ea46',
      'readiness.py':'859fd99a9e5f95c0891adc29bc2f703461d470036beaaef18b087c138ba4499a'}


def main():
    os.umask(0o077)
    variant,mode=sys.argv[1:3]
    assert variant in ('a','b') and mode in ('stage','deploy','rollback','readiness')
    label='observation-queue' if variant=='a' else 'candidate-observed'
    artifact=json.loads((WORK/(label+'-build.json')).read_text())
    candidate=artifact['sha256'];baseline=GATEWAY if variant=='a' else json.loads((WORK/'observation-queue-build.json').read_text())['sha256']
    assert artifact['bootstrap1011_preserved'] and digest(WORK/('gateway-'+label))==candidate
    suite=WORK/'tests'/('observation-suite-1.jsonl' if variant=='a' else 'candidate-observed-suite.jsonl')
    events=[json.loads(line) for line in suite.read_text().splitlines() if line.startswith('{')]
    assert not any(row['Action']=='fail' for row in events)
    assert sum(row['Action']=='pass' and not row.get('Test') for row in events)>=7
    target=WORK/'transitions'/variant
    (target/'private').mkdir(parents=True,exist_ok=True);(target/'receipts').mkdir(exist_ok=True)
    previous=ROOT/'state-client-build/beta88-throughput-20261019'
    replacements={
        '4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7':baseline,
        '04886384ce0bfa80568aea7e6d6fd2fec6ee0ed300a071ea806a8ef6a29a033b':candidate,
        '0eb38db8e1ec95ce67a358de2aaf910d4aa666fe9a80ee349d26a601aef734e6':candidate,
        '.beta88-throughput-observation-20261019-stage':'.queue-retry-'+variant+'-20261019-stage',
        '".transport-write-batching-"+mode':'".queue-retry-'+variant+'-20261019-"+mode',
        'root.parent/"mesh-perf-3/diagnostic-broker-final"':repr(str(WORK/('gateway-'+label))),
        "root.parent / 'field65-export16/gateway-seed-supervisor-op-readiness-1/receipts'":"Path("+repr(str(ROOT/'state-client-build/field65-export16/gateway-seed-supervisor-op-readiness-1/receipts'))+")",
    }
    sources={}
    for name,pin in PINS.items():
        path=previous/name;assert digest(path)==pin
        text=path.read_text()
        for old,new in replacements.items():text=text.replace(old,new)
        if name=='readiness.py':
            text=text.replace("('before', 'observation', 'candidate', 'accepted-return', 'final')", "('before', 'observation', 'candidate', 'accepted-return', 'accepted-return-refresh', 'final')")
            text=text.replace("('before','accepted-return')", "('before','accepted-return','accepted-return-refresh')")
        text=text.replace('artifact='+repr(str(WORK/('gateway-'+label))),'artifact=Path('+repr(str(WORK/('gateway-'+label)))+')')
        sources[name]=text
    remote=target/'transition_remote.py'
    if remote.exists():assert remote.read_text()==sources['transition_remote.py']
    else:
        with remote.open('x') as output:output.write(sources['transition_remote.py'])
    name='readiness.py' if mode=='readiness' else 'operate.py'
    sys.argv=[str(target/name),*(sys.argv[3:] if mode=='readiness' else [mode])]
    exec(compile(sources[name],str(target/name),'exec'),dict(__name__='__main__',__file__=str(target/name)))


if __name__=='__main__':main()
