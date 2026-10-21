"""Reuse bound-Pion missing-head fixture at RS32, keeping carrier A0 unchanged."""

import json
import os
import shutil
import subprocess
import time
from prepare import WORK, TOOLS, environment, write, digest


def main():
    results = []
    for side, original in [('android', WORK/'android-source/carrier'), ('gateway',WORK/'gateway-source')]:
        source = WORK / ('head32-' + side)
        if not source.exists():
            shutil.copytree(original, source)
            path = source / 'telemost/head_loss_test.go'
            text = path.read_text()
            text = text.replace('"github.com/Joker20380/family_connect/carrier/reliablestream"', '"github.com/Joker20380/family_connect/carrier/reliablestream"\n"os"')
            if '"github.com/Joker20380/family_connect/carrier/localwrite"' not in text:
                text = text.replace('"os"', '"os"\n"github.com/Joker20380/family_connect/carrier/localwrite"')
            start = text.index('func TestHeadLossBoundPionAttempts(')
            end = text.index('\nfunc ',start+10)
            body = text[start:end]
            body = body.replace('defer cancel()', 'defer cancel()\nif os.Getenv("SPEED_TEST_PROFILE")=="P2" {ctx=localwrite.WithCompletion(ctx)}')
            body = body.replace('config := reliablestream.DefaultConfig()', 'config := reliablestream.DefaultConfig()\nconfig.SendWindow,config.ReceiveWindow=32,32')
            body = body.replace('== 254','== 4294967294').replace('== 255','== 4294967295').replace('!= 7','!= 31').replace('== head+8','== head+32')
            write(path, text[:start]+body+text[end:])
        for profile in ('P1','P2'):
            env = environment();env['SPEED_TEST_PROFILE']=profile
            log=WORK/(side+'-head32-'+profile+'-'+str(time.time_ns())+'.jsonl')
            with log.open('x') as output:
                result=subprocess.run([TOOLS/'go/bin/go','test','-race','-json','-count=1','-timeout=180s','-run','^TestHeadLossBoundPionAttempts$','./telemost'],cwd=source,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=240)
            results.append(dict(side=side,profile=profile,exit=result.returncode,log=log.name,sha256=digest(log)))
            (WORK/'head32-results.json').write_text(json.dumps(results,indent=2))
            print(json.dumps(results[-1]),flush=True)
    if any(result['exit'] for result in results):raise SystemExit(1)


if __name__=='__main__':main()
