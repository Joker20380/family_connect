"""Reuse the accepted small Android-TUN control, not a throughput rerun."""

import json
import os
import sys

from prepare import ROOT, WORK, GATEWAY, digest


def main():
    os.umask(0o077)
    receipt=WORK/'final-post-readback.json'
    if not receipt.exists():receipt=WORK/'final-readback.json'
    before=json.loads(receipt.read_text())
    assert before['gateway']['sha256']==GATEWAY and before['phone']['code']==90
    label=sys.argv[1] if len(sys.argv)>1 else 'final-control'
    assert label in ('final-control','final-control-ready','final-control-confirmed')
    baseline=WORK/(label+'-baseline.json')
    with baseline.open('x') as output:json.dump(dict(nl=dict(service=before['gateway']['state']),phone=dict(process=before['phone']['pid'])),output)
    helper=ROOT/'state-client-build/beta87-product-fix-20261019/physical_probe88.py'
    assert digest(helper)=='d06aa28bbe8365ab3f3c6df244d1a935b3bf340c64407e0c1e3813388154da9d'
    source=helper.read_text().replace('beta88 in-place update production control only; no bulk or recovery claim',
        'current1011 exact rollback and unchanged90 control; no speed or overnight acceptance')
    source=source.replace("metrics.get('remote_ip','INVALID')+':443' in entry", "bool(metrics.get('remote_ip')) and metrics['remote_ip']+':443' in entry")
    namespace=dict(__name__='accepted_small_control',__file__=str(helper))
    exec(compile(source,str(helper),'exec'),namespace)
    namespace.update(ROOT=ROOT,OUT=WORK/label,REMOTE='/data/local/tmp/fc-queue-'+label+'-20261020')
    namespace['main'](baseline,'queue-'+label+'-20261020')
    result=json.loads((WORK/label/'result.json').read_text())
    assert result['control_pass'],'FINAL_CONTROL_FAILED_RETAIN_EVIDENCE'


if __name__=='__main__':main()
