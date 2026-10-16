import argparse
import hashlib
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
for name in ('client', 'gateway', 'out'):
    parser.add_argument('--'+name, type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
args.out.mkdir(parents=True, exist_ok=False)
canonical = 'github.com/Joker20380/family_connect/carrier'
bindings = {}
for variant, original in (('client', args.client), ('gateway', args.gateway)):
    stage = args.out/variant
    shutil.copytree(original/'carrier', stage)
    bindings[variant] = {str(path.relative_to(stage)): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in sorted(stage.rglob('*.go')) if not path.name.endswith('_test.go')}
    if variant == 'gateway':
        for path in list(stage.rglob('*.go'))+[stage/'go.mod']:
            path.write_text(path.read_text().replace(canonical, 'fixture.invalid/gateway'))
client = args.out/'client'
native = client/'nativeexport'
native.mkdir()
native_source = args.client/'pilot/android-restricted/native/startup_owner.go'
(native/'startup_owner.go').write_text(native_source.read_text().replace('package main', 'package nativeexport', 1))
shutil.copy2(root/'native_export_adapter.go', native/'adapter.go')
bindings['native_export'] = {'pilot/android-restricted/native/startup_owner.go': hashlib.sha256(native_source.read_bytes()).hexdigest()}
with (client/'go.mod').open('a') as output:
    output.write('\nrequire fixture.invalid/gateway v0.0.0\nreplace fixture.invalid/gateway => '+str((args.out/'gateway').resolve())+'\n')
for name in ('correlation_test.go', 'tls_fixture_test.go'):
    shutil.copy2(root/name, client/'bootstrap'/name)
shutil.copy2(root/'capture_test.go', args.out/'gateway/cmd/bootstrap-broker/correlation_capture_test.go')
(args.out/'bindings.json').write_text(json.dumps(bindings, indent=2)+'\n')
