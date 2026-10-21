"""Matched laboratory windows only; never builds or deploys a gateway."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from prepare import WORK, FIXTURE, TOOLS, environment, digest
from measure import counters


def main():
    os.umask(0o077)
    mode=sys.argv[1]
    if mode=='prepare':
        rows=counters(WORK/'matrix/capture-private.jsonl')
        first,last=(row['performance']['Window'] for row in (rows[0],rows[-1]))
        acknowledgements=sum(last['FirstACKNoRetry']['Count'])-sum(first['FirstACKNoRetry']['Count'])
        ack_ns=last['FirstACKNoRetry']['TotalNS']-first['FirstACKNoRetry']['TotalNS']
        new=sum(last['NewDATA']['Count'])-sum(first['NewDATA']['Count'])
        retries=sum(last['RetryDATA']['Count'])-sum(first['RetryDATA']['Count'])
        configuration=dict(delay_ns=round(ack_ns/acknowledgements/2),loss_every=round(new/retries),
            no_retry_ack_mean_ms=ack_ns/acknowledgements/1e6,new_blocks=new,retry_blocks=retries,
            interpretation='effective symmetric transport-delay proxy, not subscriber RTT; retry density does not identify forward loss',
            fault_shape='first-attempt drop and adjacent reorder; measured density, not reconstruction of unknown actual losses',
            body_bytes=524288,windows=[65536,131072,262144],source_capture_sha256=digest(WORK/'matrix/capture-private.jsonl'))
        assert configuration['loss_every']>=3 and configuration['delay_ns']>0
        (WORK/'model-input.json').write_text(json.dumps(configuration,indent=2))
        for window in (64,128,256):
            source=WORK/f'lab-{window}'
            shutil.copytree(WORK/'observation-source/carrier',source)
            shutil.copyfile(FIXTURE/'model_test.go',source/'tcpforward/credit_model_test.go')
            if window!=64:
                patch=f'*** Begin Patch\n*** Update File: {source}/tcpforward/mux_protocol.go\n@@\n-const MuxWindow = 64 << 10\n+const MuxWindow = {window} << 10\n*** End Patch\n'
                subprocess.run(['apply_patch',patch],check=True)
        print(json.dumps(configuration));return
    assert mode in ('run','regressions')
    configuration=json.loads((WORK/'model-input.json').read_text())
    for window in (64,128,256):
        env=environment()
        if mode=='run':env.update(MUX_CREDIT_MODEL='1',MUX_CREDIT_DELAY_NS=str(configuration['delay_ns']),MUX_CREDIT_LOSS_EVERY=str(configuration['loss_every']))
        output=WORK/f'lab-{window}-{mode}-{len(list(WORK.glob(f"lab-{window}-{mode}-*.jsonl")))+1}.jsonl'
        options=['-run','^TestCreditMeasuredModel$'] if mode=='run' else []
        with output.open('xb') as log:
            result=subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-json','-count=1','-timeout=480s',*options,'./tcpforward'],
                                  cwd=WORK/f'lab-{window}',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=540)
        print(json.dumps(dict(window=window,mode=mode,exit=result.returncode,log=str(output))),flush=True)
        if result.returncode:raise SystemExit(result.returncode)


if __name__=='__main__':main()
