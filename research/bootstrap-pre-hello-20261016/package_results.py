import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
for name in ('task', 'retained', 'gateway'):
    parser.add_argument('--'+name, type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
source = args.task/'source'
changes = ['carrier/bootstrap/protocol.go', 'carrier/startupdiag/enabled.go', 'carrier/startupdiag/result.go',
           'carrier/startupdiag/bootstrap_test.go', 'clients/android/app/src/main/java/com/familyconnect/app/Diagnostics.java',
           'clients/android/app/src/main/java/com/familyconnect/app/RestrictedStartup.java',
           'clients/android/app/src/test/java/com/familyconnect/app/BootstrapCorrelationTest.java',
           'clients/android/app/src/test/resources/bootstrap-deadline-native.json']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


manifest = {'input_review': 'a63d446acc788d791d76fa938a8575d115b5e411',
            'input_cumulative': 'c2dc3dd860044b31696893244995cbc5cc8eb805ee34319df99cce085cf40d08', 'files': {}}
patch = []
for name in changes:
    before, after = args.retained/name, source/name
    manifest['files'][name] = {'before': digest(before), 'after': digest(after)}
    for directory, path in (('before', before), ('changed', after)):
        if path.is_file():
            target = root/directory/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    patch.extend(difflib.unified_diff(before.read_text().splitlines(True) if before.exists() else [], after.read_text().splitlines(True),
                                      fromfile='a/'+name if before.exists() else '/dev/null', tofile='b/'+name))
(root/'source.patch').write_text(''.join(line if line.endswith('\n') else line+'\n\\ No newline at end of file\n' for line in patch))
(root/'source-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
bindings = {}
for name in changes+['carrier/bootstrap/carrier.go', 'carrier/roombroker/ownership.go',
                     'carrier/cmd/bootstrap-broker/ownership.go', 'carrier/cmd/bootstrap-broker/main.go',
                     'carrier/familysession/session.go', 'carrier/familysession/receive_observer.go',
                     'carrier/sessiontrace/trace.go', 'carrier/startupdiag/stop.go',
                     'pilot/android-restricted/native/startup_owner.go', 'pilot/android-restricted/native/main.go',
                     'pilot/android-restricted/native/chat_owner.go', 'pilot/android-restricted/native/bridge.c',
                     'clients/android/app/src/main/java/com/familyconnect/app/NativeRestricted.java',
                     'clients/android/app/src/main/java/com/familyconnect/app/DiagnosticRing.java',
                     'clients/android/app/src/publicStartup/java/com/familyconnect/app/StartupDiagnostics.java',
                     'clients/android/app/build.gradle']:
    bindings[name] = {label: digest(base/name) for label, base in (('C_NEW', args.retained), ('diagnostic', source), ('gateway', args.gateway))}
(root/'exact-bindings.json').write_text(json.dumps(bindings, indent=2)+'\n')
results = root/'results'
results.mkdir(exist_ok=True)
for name, path in [('go-runs.json', args.task/'local-final/runs.json'),
                   ('compiled-inputs.json', args.task/'local-final/bindings.json'),
                   ('native-build.json', args.task/'native-build/receipt.json'),
                   ('gradle-build.json', args.task/'gradle-native-export-final/receipt.json'),
                   ('cumulative-source.json', args.task/'gradle-native-export-final/cumulative-source.json'),
                   ('deadline-native.json', args.task/'local-native-export/deadline-native.json'),
                   ('native-export-compiled-inputs.json', args.task/'local-native-export/bindings.json'),
                   ('preliminary-fixture-failure.json', args.task/'local-v1/runs.json'),
                   ('preliminary-jvm-compile-failure.json', args.task/'gradle-build/receipt.json'),
                   ('sandbox-build-failure.json', args.task/'gradle-build/sandbox-receipt.json')]:
    shutil.copyfile(path, results/name)
summaries = []
for path in sorted((args.task/'gradle-native-export-final/android/app/test-results/testResearchProvisioningUnitTest').glob('TEST-*.xml')):
    suite = ET.parse(path).getroot()
    summaries.append(dict(suite.attrib, sha256=digest(path)))
(results/'jvm-tests.json').write_text(json.dumps(summaries, indent=2)+'\n')
for mode in ('normal','race'):
    for variant in ('client','gateway'):
        shutil.copyfile(args.task/f'local-final/{variant}-{mode}.log', results/f'{variant}-{mode}.log')
    shutil.copyfile(args.task/f'local-native-export/native-{mode}.log', results/f'native-export-{mode}.log')
print('Packaged eight-file client delta and local-only safe test receipts')
