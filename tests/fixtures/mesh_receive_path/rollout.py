"""Fresh observation-only transition; exact b9 rollback and current credentials."""

import sys

from preserve import ROOT, digest


if __name__=='__main__':
    assert sys.argv[1]=='a'
    original=ROOT/'tests/fixtures/queue_retry/rollout.py'
    assert digest(original)=='92c6a08e38de0de80180b5df443740bcc6ce5157b29d059f26e2278629be9d67'
    source=original.read_text()
    replacements={
        'from prepare import ROOT, WORK, GATEWAY, digest': 'from preserve import ROOT, WORK, digest\nGATEWAY="b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba"',
        "label='observation-queue' if variant=='a' else 'candidate-observed'":"label='observation'",
        "WORK/(label+'-build.json')":"WORK/'gateway-build.json'",
        "WORK/'tests'/('observation-suite-1.jsonl' if variant=='a' else 'candidate-observed-suite.jsonl')":"WORK/'validation/results/observation.jsonl'",
        "'.queue-retry-'+variant+'-20261019-stage'":"'.mesh-receive-'+variant+'-20261020-stage'",
        "queue-retry-'+variant+'-20261019-":"mesh-receive-'+variant+'-20261020-",
    }
    for old,new in replacements.items():
        assert old in source,old
        source=source.replace(old,new)
    exec(compile(source,str(original),'exec'),dict(__name__='__main__',__file__=str(original)))
