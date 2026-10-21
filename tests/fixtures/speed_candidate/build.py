"""Reuse pinned native/Gradle build, ordinary diagnostics, beta96 recovery inputs."""

import json
import os
import subprocess
import sys
import time
from prepare import ROOT, WORK, TOOLS, ANDROID, digest, environment, write


def main():
    mode = sys.argv[1]
    assert mode in ('android', 'gateway')
    if mode == 'gateway':
        binary = WORK / 'gateway-speed'
        assert not binary.exists()
        with (WORK / ('gateway-build-' + str(time.time_ns()) + '.log')).open('x') as output:
            subprocess.run([TOOLS / 'go/bin/go', 'build', '-p=1', '-trimpath', '-buildvcs=false', '-tags=fc_perf_diagnostic', '-o', binary, './cmd/bootstrap-broker'], cwd=WORK / 'gateway-source', env=environment(), stdout=output, stderr=subprocess.STDOUT, check=True, timeout=600)
        (WORK / 'gateway-build.json').write_text(json.dumps(dict(binary=str(binary), sha256=digest(binary), deployed=False, defaults='unchanged', tags=['fc_perf_diagnostic']), indent=2))
        print('BUILT_GATEWAY', digest(binary))
        return
    original = ROOT / 'tests/fixtures/mesh_throughput_trace/build.py'
    assert digest(original) == '4ed782e6d77748d1cc0e7342c9d15d4486b5a9459b19018d623da929022e9a58'
    source = original.read_text()
    os.environ['GIT_DIR'] = str(ROOT / 'state-client-build/mux-profile-20261020/android-source/.git')
    os.environ['GIT_WORK_TREE'] = str(WORK / 'android-source')
    replacements = {
        'ROOT = Path(__file__).resolve().parents[3]': 'ROOT = Path(' + repr(str(ROOT)) + ')',
        "WORK = Path(os.environ.get('MESH_TRACE_OUT', STATE / 'mesh-throughput-trace-20261019'))": 'WORK = Path(' + repr(str(WORK)) + ')',
        "version_code=89, version='0.1.18-beta89-mesh-trace'": "version_code=97, version='0.1.18-beta97-speed'",
        "parent = STATE / 'beta87-product-fix-20261019/android88-source'": 'parent = Path(' + repr(str(ANDROID / 'android-source')) + ')',
        "'-tags=fc_perf_diagnostic', ": '',
        "build_tags=['fc_perf_diagnostic']": 'build_tags=[]',
        "actual_build_receipt='mesh-throughput-trace-20261019/build/receipt.json'": "actual_build_receipt='speed-candidate-20261021/build/receipt.json'",
        "parent.parent / 'android88-build/research-assets'": "parent.parent / 'build/research-assets'",
        "parent.parent / 'android88-build/android.init.gradle'": "parent.parent / 'build/android.init.gradle'",
        "parent.parent / 'android88-build'": "parent.parent / 'build'",
        "parent.parent / 'delivery/FamilyConnect-0.1.18-beta88-recovery.apk'": "parent.parent / 'delivery/FamilyConnect-0.1.18-beta96-bootstrap.apk'",
        "'ControlOperationsTest', 'ControlStartupTest', 'ControlTransactionTest')": "'ControlOperationsTest', 'ControlStartupTest', 'ControlTransactionTest', 'MobileBootstrapTest', 'SpeedProfileTest', 'SpeedReceiptTest', 'RestrictedDeliveryTest', 'RestrictedTraceTest')",
    }
    for old, new in replacements.items():
        assert source.count(old) == 1, (old, source.count(old))
        source = source.replace(old, new)
    runner = WORK / 'executed-android-build.py'
    write(runner, source)
    exec(compile(source, str(runner), 'exec'), dict(__name__='__main__', __file__=str(runner)))


if __name__ == '__main__':
    main()
