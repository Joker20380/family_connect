import argparse
import datetime
from lab import *

parser=argparse.ArgumentParser()
parser.add_argument('group',choices=['original','normalized','product','product-resume','product-gated','product-tail','product-finish','baseline-finish'])
args=parser.parse_args()
groups={'original':[('AO','P',False,True),('QO','QN',False,True)],'normalized':[('AN','P',True,True),('QNsmoke','QN',True,True),('QS','QS',True,True)],'product':[('A1','P',True,False),('QN1','QN',True,False),('QN2','QN',True,False),('A2','P',True,False)]}
groups['product-resume']=[('A1R','P',True,False),('QN1','QN',True,False),('QN2','QN',True,False),('A2','P',True,False)]
groups['product-gated']=[('A1G','P',True,False),('QN1','QN',True,False),('QN2','QN',True,False),('A2','P',True,False)]
groups['product-tail']=[('QN1','QN',True,False),('QN2','QN',True,False),('A2','P',True,False)]
groups['product-finish']=[('QN2','QN',True,False),('A2','P',True,False)]
groups['baseline-finish']=[('A2','P',True,False)]
if args.group=='baseline-finish':
    assert (WORK/'QN2/cleanup.json').exists()
if args.group=='product-tail':
    assert (WORK/'A1G/cleanup.json').exists()
    assert json.loads((WORK/'A1G/phase-result.json').read_text())['production_equal']
plan=groups[args.group]
assert not (WORK/'verification.json').exists()
save(WORK/(args.group+'-plan.json'),dict(utc=datetime.datetime.now(datetime.UTC).isoformat(),phases=plan,main_reserved=32*2**20,live_limits=dict(source=64*2**20,media=128*2**20),local='separate, not included in live charge',cadence='original2ms/frame vs normalized1MiB/s bounded2ms credit; 33ms timestamps unchanged',no_automatic_expansion=True))
for phase,mode,normalized,short in plan:
    command=[sys.executable,str(WORK/'run_phase.py'),phase,'--mode',mode,'--fragment','L','--packing','A','--credit128','--send','32','--receive','32','--count','8','--sizes','16384','--normalized' if normalized else '--original-carrier']
    if short:command.append('--short')
    with (WORK/(phase+'-operator.log')).open('x') as log:
        result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=350)
    print(phase,result.returncode,flush=True)
    if result.returncode:
        save(WORK/(args.group+'-stop.json'),dict(phase=phase,exit=result.returncode,reason='retained first failure; inspect before any subsequent candidate'))
        raise SystemExit(result.returncode)
