import json
import subprocess
import sys
from lab import WORK, save


def main():
    group=sys.argv[1]
    selections={
        'smoke':[('CL','L','C'),('CS','S','C')],
        'reliable':[('R0','L','R'),('RL','L','R'),('RS','S','R'),('RSF','SF','R')],
        'product':[('PL1','L','P'),('PS1','S','P'),('PSF1','SF','P'),('PSF2','SF','P'),('PS2','S','P'),('PL2','L','P')],
    }
    phases=selections[group]
    save(WORK/(group+'-plan.json'),dict(phases=phases,maximum_source=128*1024**2,maximum_media=256*1024**2,primary_bulk_reserved=48*1024**2))
    for phase,variant,mode in phases:
        command=[sys.executable,str(WORK/'run_phase.py'),phase,'--mode',mode,'--send','32','--receive','32','--packing','A','--credit128','--fragment',variant,'--count','8']
        if mode=='C':command+=['--sizes','64,1024,8192,16448','--rate','65536','--seconds','2']
        if phase=='R0':command+=['--original-carrier']
        with (WORK/(phase+'-operator.log')).open('x') as log:
            result=subprocess.run(command,cwd=WORK,stdout=log,stderr=subprocess.STDOUT,timeout=340)
        print(phase,'exit',result.returncode,flush=True)
        if result.returncode:
            save(WORK/(group+'-stop.json'),dict(phase=phase,exit=result.returncode))
            return result.returncode
        receipt=json.loads((WORK/phase/'phase-result.json').read_text())
        assert receipt['production_equal'] and receipt['isolated_identities_removed']
    return 0


if __name__=='__main__':sys.exit(main())
