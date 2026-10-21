"""Fresh guarded counter-only transition; never replay an earlier intent."""

import sys
from prepare import ROOT, WORK, GATEWAY, digest

original=ROOT/'tests/fixtures/queue_retry/rollout.py'
assert digest(original)=='92c6a08e38de0de80180b5df443740bcc6ce5157b29d059f26e2278629be9d67'
source=original.read_text()
replacements={
    "label='observation-queue' if variant=='a' else 'candidate-observed'":"assert variant=='a'\n    label='observation'",
    "'observation-suite-1.jsonl' if variant=='a' else 'candidate-observed-suite.jsonl'":"'checks-final.jsonl'",
    "suite=WORK/'tests'/":"suite=WORK/",
    "'.queue-retry-'+variant+'-20261019-stage'":"'.mux-credit-'+variant+'-20261020-stage'",
    "'\".queue-retry-'+variant+'-20261019-\"+mode'":"'\".mux-credit-'+variant+'-20261020-\"+mode'",
}
for old,new in replacements.items():
    assert old in source,old
    source=source.replace(old,new)
exec(compile(source,str(original),'exec'),dict(__name__='__main__',__file__=str(original)))
