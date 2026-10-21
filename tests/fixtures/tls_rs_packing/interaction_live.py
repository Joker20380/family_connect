"""At most six predeclared phases. Stop on any error, no automatic tuning/retry."""
import json
import os
import subprocess
import sys
from interaction_prepare import WORK, FIX, SOURCE, digest, inventory, save


def main():
    repair='--resume-proof-repair' in sys.argv
    if repair:
        assert json.loads((WORK/'live-stop.json').read_text())=={'phase':'A1','exit':1,'error':'SERVER_BODY_COMPLETION_FAILED'}
        assert not (WORK/'repair-plan.json').exists()
    else:
        assert not (WORK/'live-plan.json').exists()
    build=json.loads((WORK/'build.json').read_text())
    assert inventory(SOURCE)==build['source_inventory']
    controller=json.loads((WORK/'controller-repair.json').read_text()) if repair else build
    assert digest(WORK/'run_phase.py')==controller['operator_sha256']
    assert digest(WORK/'worker.py')==build['worker_sha256']
    assert json.loads((WORK/'local-unrestricted/result.json').read_text())['exit']==0
    assert all(row['exit']==0 for row in json.loads((WORK/'retry-results.json').read_text()))
    audit=json.loads((WORK/'external-audit.json').read_text())
    assert not audit['existing_lab_stages']
    phases=[('A1','A',False),('B1','B2',False),('C1','A',True),('D1','B2',True),('D2','B2',True),('C2','A',True)]
    if repair:phases[0]=('A1r','A',False)
    save(WORK/('repair-plan.json' if repair else 'live-plan.json'),dict(phases=phases,reason='primary packing interaction D-C at128 repeats in reverse; A/B retain64 controls, no T repeat; A1 repair charged, not accepted or erased',source_cap=64*1024**2,live_source_cap=64*1024**2,media_cap=128*1024**2,local_bulk_bytes=6*1024**2,transfer_deadline_s=180,small='six sequential32B echo controls idle and six from1s after single start,100ms gaps; report actual overlap, n/median/max/errors, not p99',admission='LAB ONLY; latency non-regression not established with n6'))
    env=dict(os.environ,PYTHONPATH=str(FIX))
    for phase,packing,credit in phases:
        command=[sys.executable,str(WORK/'run_phase.py'),phase,'--mode','P','--send','32','--receive','32','--packing',packing]
        if credit:command.append('--credit128')
        with (WORK/(phase+'-operator.log')).open('x') as output:
            result=subprocess.run(command,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=420)
        receipt=WORK/phase/'phase-result.json'
        summary=json.loads(receipt.read_text()) if receipt.exists() else {'error':'missing result'}
        print(json.dumps(dict(phase=phase,exit=result.returncode,error=summary.get('error'),media_charged=summary.get('wire_charged'))),flush=True)
        if result.returncode or summary.get('error'):
            save(WORK/('repair-stop.json' if repair else 'live-stop.json'),dict(phase=phase,exit=result.returncode,error=summary.get('error')))
            return
    save(WORK/'live-complete.json',dict(phases=[row[0] for row in phases],status='all operators completed; independent final analysis required'))


if __name__=='__main__':
    main()
