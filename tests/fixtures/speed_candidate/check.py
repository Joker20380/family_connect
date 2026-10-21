"""Local-only correctness gates, bounded logs; no SSH, ADB or Telemost joins."""

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from prepare import ROOT, WORK, TOOLS, environment, digest


def main():
    scope = sys.argv[1]
    assert scope in ('focused', 'suite', 'queue')
    python = ROOT / 'state-client-build/field65-export16/telemost-admission-ownership-1/build/venv/bin/python'
    with tempfile.TemporaryDirectory(prefix='check-identities-', dir=WORK) as temporary:
        fixture = Path(temporary) / 'fixture'
        subprocess.run([python, '-m', 'pilot.telemost_family_fixture', '--out', fixture], cwd=ROOT, check=True, timeout=30)
        run(scope, fixture)


def run(scope, fixture):
    results = []
    for side, source in [('android', WORK / 'android-source/carrier'), ('gateway', WORK / 'gateway-source')]:
        runs = [('normal', ['-run', 'TestSpeed'], ['./tcpforward', './roombroker'])]
        if scope == 'suite':
            runs = [('normal', [], ['./localwrite', './reliablestream', './familysession', './tcpforward', './telemost', './wholedevice', './restrictedowner', './sessiondiag', './bootstrap', './roombroker', './cmd/bootstrap-broker'])]
            if side == 'gateway':
                runs[0][2].remove('./restrictedowner')
        if scope == 'queue':
            runs = [(mode, ['-run', '^TestQueueRetryHeldLocalWriter$'], ['./telemost']) for mode in ('Q0', 'Q1')]
        for mode, filters, packages in runs:
            env = environment()
            env['FC_EXPECT_SEED_OBSERVABILITY'] = '1'
            env['FC_FAMILY_TEST_FIXTURES'] = str(fixture)
            env['FC_QUEUE_COMPLETION_EXPECTED'] = '1' if mode == 'Q1' else '0'
            log = WORK / (side + '-' + scope + '-' + mode + '-' + str(time.time_ns()) + '.jsonl')
            started = time.monotonic()
            with log.open('x') as output:
                tags = ['-tags=fc_perf_diagnostic'] if side == 'gateway' else []
                result = subprocess.run([TOOLS / 'go/bin/go', 'test', '-p=1', '-race', '-json', '-count=1', '-timeout=180s', *tags, *filters, *packages], cwd=source, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=900)
            record = dict(side=side, mode=mode, scope=scope, exit=result.returncode, seconds=time.monotonic()-started, log=log.name, sha256=digest(log))
            results.append(record)
            (WORK / ('checks-' + scope + '.json')).write_text(json.dumps(results, indent=2))
            print(json.dumps(record), flush=True)
    if any(record['exit'] for record in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
