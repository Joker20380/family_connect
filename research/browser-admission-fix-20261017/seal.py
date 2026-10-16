import difflib
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
parent = root.parent/'transport-speed-cutover-1'
def digest(filename):
    return hashlib.sha256(filename.read_bytes()).hexdigest()
def inventory(folder):
    return {str(filename.relative_to(folder)):digest(filename) for filename in folder.rglob('*')
            if filename.is_file() and not any(part in ('.git','__pycache__') for part in filename.relative_to(folder).parts)}
def fingerprint(values):
    return hashlib.sha256(json.dumps(values,sort_keys=True,separators=(',',':')).encode()).hexdigest()

before, after = inventory(parent/'source'), inventory(root/'source')
changed = sorted(name for name in before.keys()|after.keys() if before.get(name)!=after.get(name))
allowed = {'carrier/tcpforward/admission.go','carrier/tcpforward/admission_test.go','carrier/tcpforward/mux.go','carrier/tcpforward/mux_stream.go','carrier/tcpforward/mux_protocol.go','carrier/wholedevice/session.go','carrier/wholedevice/session_test.go','carrier/sessiondiag/report.go','carrier/sessiondiag/report_test.go','carrier/roombroker/lease_mux_test.go','pilot/android-restricted/xray-packet-boundary.patch','pilot/android-restricted/packet/engine_test.go','clients/android/app/build.gradle',*[f'clients/android/app/src/main/java/com/familyconnect/app/{name}.java' for name in ('Diagnostics','DiagnosticRing')],'clients/android/app/src/test/java/com/familyconnect/app/AdmissionDiagnosticsTest.java'}
assert set(changed)==allowed,(set(changed)-allowed,allowed-set(changed))
original = json.loads((parent/'build/cumulative-source.json').read_text())
assert original['source_delta_sha256']=='211b127d545af5c129acc93bf0ff78cac3af93707aad8def27bb6da830e2ae86'
assert all(before[name]==value for name,value in original['files'].items())
cumulative = original['files'] | {name:after[name] for name in changed}
manifest = dict(base=original['base'],parent_inventory=original['source_delta_sha256'],source_delta_sha256=fingerprint(cumulative),files=cumulative)
(root/'cumulative-source.json').write_text(json.dumps(manifest,indent=2)+'\n')
patch = []
for name in changed:
    old = (parent/'source'/name).read_text().splitlines(True) if name in before else []
    new = (root/'source'/name).read_text().splitlines(True)
    patch.extend(difflib.unified_diff(old,new,fromfile='a/'+name if name in before else '/dev/null',tofile='b/'+name))
(root/'candidate.patch').write_text(''.join(patch))
gateway_before = inventory(parent/'gateway-source/carrier')
gateway_after = inventory(root/'gateway-source/carrier')
gateway_delta = sorted(name for name in gateway_before.keys()|gateway_after.keys() if gateway_before.get(name)!=gateway_after.get(name))
assert set(gateway_delta)=={name.removeprefix('carrier/') for name in allowed if name.startswith('carrier/tcpforward/')}|{'sessiondiag/report.go'}
for name in gateway_delta:
    assert gateway_after[name]==after['carrier/'+name]
gateway = dict(parent_inventory='3693f70552d27365a56eb9f625f8afe03c01f7e513acdc04cb31e107f52d837e',source_inventory=fingerprint(gateway_after),files=gateway_after)
(root/'gateway-source.json').write_text(json.dumps(gateway,indent=2)+'\n')
xray_before = inventory(root.parent/'field65-export16/native-packet-tests/xray')
xray_after = inventory(root/'xray')
assert set(xray_before)==set(xray_after)
assert [name for name in xray_before if xray_before[name]!=xray_after[name]]==['proxy/tun/stack_gvisor.go']
(root/'boundary.json').write_text(json.dumps(dict(client_delta=changed,gateway_delta=gateway_delta,
    source_inventory=manifest['source_delta_sha256'],gateway_inventory=gateway['source_inventory'],
    xray_changed_file_sha256=xray_after['proxy/tun/stack_gvisor.go'],
    product_patch_sha256=digest(root/'candidate.patch'),parent_sources_preserved=True,
    transport_reliable_media_security_unchanged=True,ui_unchanged=True,jni_contract_unchanged=True),indent=2)+'\n')
print(json.dumps(dict(source=manifest['source_delta_sha256'],gateway=gateway['source_inventory'],files=len(changed))))
