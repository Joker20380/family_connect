import difflib
import hashlib
import json
import os
from pathlib import Path
import zipfile

os.umask(0o077)
root = Path(__file__).resolve().parents[3]
out = root / 'state-client-build/mesh-perf-3b'
fixtures = root / 'tests/fixtures/mesh_perf3b'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


baseline_api = root / 'state-client-build/field65-export16/warm-start-collector-rebase-1/preservation/deployed-api.pyz'
assert sha(baseline_api) == '12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed'
changed_api = ['control/friends/restricted.py', 'control/friends/owner_handoff.py']
api_patch = []
with zipfile.ZipFile(baseline_api) as original, zipfile.ZipFile(out/'friends-http-owner-candidate.pyz', 'x') as candidate:
    for info in original.infolist():
        raw = original.read(info.filename)
        if info.filename == changed_api[0]:
            new = (out/'api'/info.filename).read_bytes()
            api_patch.extend(difflib.unified_diff(raw.decode().splitlines(True), new.decode().splitlines(True),
                                               fromfile='a/'+info.filename, tofile='b/'+info.filename))
            raw = new
        candidate.writestr(info, raw)
    added = (out/'api'/changed_api[1]).read_text()
    api_patch.extend(difflib.unified_diff([], added.splitlines(True), fromfile='/dev/null', tofile='b/'+changed_api[1]))
    info = zipfile.ZipInfo(changed_api[1], (1980, 1, 1, 0, 0, 0))
    info.external_attr = 0o100644 << 16
    candidate.writestr(info, added.encode())
with (fixtures/'api-overlay.patch').open('x') as handle:handle.write(''.join(api_patch))
with zipfile.ZipFile(baseline_api) as original, zipfile.ZipFile(out/'friends-http-owner-candidate.pyz') as candidate:
    assert set(candidate.namelist()) == set(original.namelist()) | {changed_api[1]}
    assert all(original.read(name) == candidate.read(name) for name in original.namelist() if name != changed_api[0])
    assert all(candidate.read(name) == (out/'api'/name).read_bytes() for name in changed_api)

base = root/'state-client-build/mesh-perf-3/source/carrier'
source = out/'source/carrier'
inventory = {str(path.relative_to(source)): sha(path) for path in source.rglob('*') if path.is_file()}
base_inventory = {str(path.relative_to(base)): sha(path) for path in base.rglob('*') if path.is_file()}
delta = sorted(name for name in set(inventory) | set(base_inventory) if inventory.get(name) != base_inventory.get(name))
assert delta == ['bootstrap/owner_handoff_auth_test.go', 'roombroker/control.go', 'roombroker/owner_guard_off.go',
                 'roombroker/owner_guard_on.go', 'roombroker/owner_guard_test.go']
gateway_patch = []
for name in delta:
    old = (base/name).read_text().splitlines(True) if (base/name).exists() else []
    new = (source/name).read_text().splitlines(True)
    gateway_patch.extend(difflib.unified_diff(old, new, fromfile='a/'+name if old else '/dev/null', tofile='b/'+name))
with (fixtures/'gateway-owner-overlay.patch').open('x') as handle:handle.write(''.join(gateway_patch))
accepted = json.loads((root/'state-client-build/mesh-perf-3/accepted-source.json').read_text())
accepted_path = root/'state-client-build/transport-write-batching-1/gateway-source/carrier'
assert all(sha(accepted_path/name) == expected for name, expected in accepted['files'].items())
assert sha(root/'state-client-build/mesh-perf-3/diagnostic-broker-final') == '04886384ce0bfa80568aea7e6d6fd2fec6ee0ed300a071ea806a8ef6a29a033b'
record = dict(status='LOCAL_CANDIDATES_NOT_DEPLOYED', api_baseline_sha256=sha(baseline_api),
              api_candidate_sha256=sha(out/'friends-http-owner-candidate.pyz'), api_overlay_sha256=sha(fixtures/'api-overlay.patch'),
              api_modules={name:sha(out/'api'/name) for name in changed_api},
              accepted_gateway_sha256='4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7',
              perf3_candidate_sha256=sha(root/'state-client-build/mesh-perf-3/diagnostic-broker-final'),
              owner_candidate_sha256=sha(out/'diagnostic-broker-owner-final'), gateway_delta_sha256=sha(fixtures/'gateway-owner-overlay.patch'),
              gateway_source_inventory=digest(inventory), changed_from_perf3=delta,
              accepted_source_files_rechecked=len(accepted['files']), perf3_observer_hot_path_unchanged=True,
              receipts={path.name:sha(path) for path in (out/'receipts').iterdir() if path.is_file()})
with (out/'receipts/seal.json').open('x') as handle:json.dump(record,handle,indent=2)
with (root/'docs/releases/2026-10-18-mesh-perf-3b-evidence.json').open('x') as handle:json.dump(record,handle,indent=2)
print(json.dumps({key:value for key,value in record.items() if key.endswith('sha256') or key=='gateway_source_inventory'}, indent=2))
