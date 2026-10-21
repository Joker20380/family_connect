"""Build only B125 from pinned92, with ordinary diagnostics and unchanged recovery."""

import difflib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from deadline import WORK
from late_arrival import ROOT, SAVED, FIXTURE, digest


def main():
    os.umask(0o077)
    if sys.argv[1] == 'prepare':
        patch = ''
        for name in ('rtp.go', 'rtp_reader.go', 'signaling.go', 'rtp_gap_test.go'):
            baseline = SAVED / 'normal92/android-source/carrier/telemost' / name
            candidate = WORK / 'carrier/telemost' / name
            patch += ''.join(difflib.unified_diff(baseline.read_text().splitlines(True) if baseline.exists() else [],
                candidate.read_text().splitlines(True), fromfile='a/telemost/' + name if baseline.exists() else '/dev/null', tofile='b/telemost/' + name))
        subprocess.run(['apply_patch', '*** Begin Patch\n*** Add File: '+str(FIXTURE/'finite-deadline.patch')+'\n'+
                        ''.join('+'+line+'\n' for line in patch.splitlines())+'*** End Patch\n'], check=True)
        shutil.copytree(SAVED / 'normal92/android-source', WORK / 'android-source', ignore=shutil.ignore_patterns('.gradle', '__pycache__'))
        subprocess.run(['git', 'apply', str(FIXTURE/'finite-deadline.patch')], cwd=WORK/'android-source/carrier', check=True)
        gradle = WORK / 'android-source/clients/android/app/build.gradle'
        subprocess.run(['apply_patch', '*** Begin Patch\n*** Update File: '+str(gradle)+
            "\n@@\n-            variant.outputs.all { versionCodeOverride = 92; versionNameOverride = '0.1.18-beta92-stability' }\n"+
            "+            variant.outputs.all { versionCodeOverride = 93; versionNameOverride = '0.1.18-beta93-rtp-deadline' }\n*** End Patch\n"], check=True)
        return
    original = ROOT / 'tests/fixtures/mesh_throughput_trace/build.py'
    assert digest(original) == '4ed782e6d77748d1cc0e7342c9d15d4486b5a9459b19018d623da929022e9a58'
    source = original.read_text()
    replacements = {
        "ROOT = Path(__file__).resolve().parents[3]": 'ROOT = Path('+repr(str(ROOT))+')',
        "WORK = Path(os.environ.get('MESH_TRACE_OUT', STATE / 'mesh-throughput-trace-20261019'))": 'WORK = Path('+repr(str(WORK))+')',
        "version_code=89, version='0.1.18-beta89-mesh-trace'": "version_code=93, version='0.1.18-beta93-rtp-deadline'",
        "'-tags=fc_perf_diagnostic', ": '',
        "build_tags=['fc_perf_diagnostic']": 'build_tags=[]',
        "actual_build_receipt='mesh-throughput-trace-20261019/build/receipt.json'": "actual_build_receipt='rtp-deadline-20261020/build/receipt.json'",
    }
    for old, new in replacements.items():
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    runner = WORK / 'executed-build.py'
    with runner.open('x') as output:
        output.write(source)
    exec(compile(source, str(runner), 'exec'), dict(__name__='__main__', __file__=str(runner)))


if __name__ == '__main__':
    main()
