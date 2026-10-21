"""Validate isolated observation source and the existing JNI/export projection."""

import json
import os
import shutil
import subprocess
import sys

from preserve import ROOT, WORK


def main():
    os.umask(0o077)
    target = WORK / 'validation/carrier'
    java_only = '--java-only' in sys.argv
    if not java_only:
        shutil.copytree(WORK / 'gateway-source/carrier', target)
    fixture = ROOT / 'tests/fixtures/mesh_receive_path'
    shutil.copyfile(fixture / 'receive_trace_test.go', target / 'sessiontrace/receive_path_test.go')
    shutil.copyfile(fixture / 'saved_head_test.go', target / 'telemost/saved_head_test.go')
    output = WORK / 'validation/results'
    output.mkdir(parents=True, exist_ok=java_only)
    tools = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
    environment = {key:value for key,value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    environment.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2',
                       GOPATH=str(tools / 'gopath'), GOCACHE=str(WORK / 'go-cache'),
                       RECEIVE_TRACE_OUTPUT=str(output), MESH_TRACE_OUTPUT=str(output), FC_EXPECT_SEED_OBSERVABILITY='1')
    result = []
    for label, tags in ([] if java_only else [('default', []), ('observation', ['-tags=fc_perf_diagnostic'])]):
        with (output / (label + '.jsonl')).open('xb') as log:
            run = subprocess.run([tools / 'go/bin/go', 'test', '-race', '-json', '-count=1', '-timeout', '180s', *tags,
                                  './sessiontrace', './telemost', './reliablestream', './familysession', './tcpforward', './sessiondiag', './cmd/bootstrap-broker'],
                                 cwd=target, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=600)
        result.append(dict(label=label,exit=run.returncode))
        print(json.dumps(result[-1]), flush=True)
        if run.returncode:raise SystemExit(run.returncode)
    java = WORK / 'android-source/clients/android/app/src/main/java/com/familyconnect/app'
    classes = WORK / 'validation/classes'
    previous = ROOT / 'state-client-build/tunnel-restart-20261019/android-build/android/app/intermediates/javac/privateBeta/compilePrivateBetaJavaWithJavac/classes'
    gson = next((tools / 'gradle-home/caches').rglob('gson-*.jar'))
    classpath = os.pathsep.join(map(str,(classes,previous,gson)))
    subprocess.run([tools / 'jdk/bin/javac', '-cp', classpath, '-d', classes,
                    java / 'PerformanceTrace.java', java / 'DiagnosticRing.java',
                    ROOT / 'tests/fixtures/mesh_throughput_trace/PerformanceExportProbe.java'],check=True,timeout=60)
    for prefix in ('receive', 'native'):
        source = output / ('receive-native.json' if prefix == 'receive' else 'native-snapshot.json')
        completed = subprocess.run([tools / 'jdk/bin/java', '-cp', classpath, 'com.familyconnect.app.PerformanceExportProbe',
                                    source, output / (prefix+'-export.json'), output / (prefix+'-java-chunks.jsonl')],
                                   check=True, text=True, capture_output=True, timeout=30)
        (output / (prefix+'-java.log')).write_text(completed.stdout+completed.stderr)
        print(completed.stdout.strip(),flush=True)
    sys.path.insert(0,str(ROOT / 'tests/fixtures/mesh_throughput_trace'))
    from correlate import reconstruct, android_export, correlate
    records, errors = reconstruct((output/'receive-java-chunks.jsonl').read_text().splitlines())
    assert not errors and len(records)==1
    received = records[0]['performance']['Trace']['receive']
    assert received['count']==400 and received['overwritten']==144 and len(received['incident'])==128
    exported = android_export(json.loads((output/'receive-export.json').read_text()))
    assert exported[0]['performance']['Trace']['receive']==received
    nodes={}
    for node, name in [('NL','nl-chunks.jsonl'),('Android','native-java-chunks.jsonl')]:
        nodes[node], errors = reconstruct((output/name).read_text().splitlines())
        assert not errors, errors
    joined = correlate(nodes)
    assert not joined['errors'], joined['errors']
    (output/'correlation.json').write_text(json.dumps(joined,indent=2))
    print('PASS_GO_JNI_SHAPE_JAVA_EXPORT_CHUNKS_CORRELATOR_RECEIVE_CONTEXT')


if __name__ == '__main__':
    main()
