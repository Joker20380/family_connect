"""Q0/Q1 is a separately labelled existing correctness candidate, not A/B/C/D."""
import json
import subprocess
from interaction_prepare import WORK, SOURCE, TOOLS, environment, save


def main():
    results=[]
    for mode in ['0','1']:
        env=environment()
        env['FC_QUEUE_COMPLETION_EXPECTED']=mode
        path=WORK/('retry-Q'+mode+'.log')
        with path.open('x') as output:
            result=subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-v','-run','^TestQueueRetryHeldLocalWriter$','-count=1','-timeout=30s','./telemost'],cwd=SOURCE,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=120)
        results.append(dict(mode='Q'+mode,exit=result.returncode))
    with (WORK/'retry-correctness.log').open('x') as output:
        result=subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-v','-run','TestLocalCompletion|TestACKReleases|TestWrite|Test.*Loss|Test.*Reorder|Test.*Cancel|Test.*Deadline|Test.*Obsolete|Test.*Generation','-count=1','-timeout=120s','./localwrite','./reliablestream'],cwd=SOURCE,env=environment(),stdout=output,stderr=subprocess.STDOUT,timeout=180)
    results.append(dict(mode='correctness',exit=result.returncode))
    save(WORK/'retry-results.json',results)
    print(json.dumps(results))


if __name__=='__main__':
    main()
