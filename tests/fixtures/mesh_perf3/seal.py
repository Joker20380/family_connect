import collections
import difflib
import hashlib
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'state-client-build/mesh-perf-3'
SOURCE = OUT / 'source/carrier'
BASE = ROOT / 'state-client-build/transport-write-batching-1/gateway-source/carrier'
TARGET = ROOT / 'docs/releases/2026-10-18-mesh-perf-3-evidence.json'
PATCH = Path(__file__).with_name('accepted-overlay.patch')
assert not TARGET.exists() and not PATCH.exists()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(path):
    return {str(item.relative_to(path)): digest(item) for item in path.rglob('*') if item.is_file()}


def seal(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


base = inventory(BASE)
assert base == json.loads((OUT / 'accepted-source.json').read_bytes())['files']
assert digest(OUT / 'baseline-broker') == '4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7'
current = inventory(SOURCE)
changed = {name: dict(before=base.get(name), after=current.get(name)) for name in sorted(base.keys() | current.keys()) if base.get(name) != current.get(name)}
assert all(current[name] == base[name] for name in ('reliablestream/protocol.go', 'telemost/rtp.go', 'telemost/session.go', 'tcpforward/mux_protocol.go', 'sessiontrace/schema_default.go', 'sessiontrace/schema_diagnostic.go', 'sessiontrace/delivery.go'))
chunks = []
for name in changed:
    original = (BASE / name).read_text().splitlines(keepends=True) if name in base else []
    revised = (SOURCE / name).read_text().splitlines(keepends=True) if name in current else []
    chunks.extend(difflib.unified_diff(original, revised, fromfile='a/'+name if name in base else '/dev/null', tofile='b/'+name if name in current else '/dev/null'))
with PATCH.open('x') as handle:
    handle.write(''.join(chunks))

receipts = {}
for file in sorted((OUT / 'receipts').glob('*.json')):
    value = json.loads(file.read_bytes())
    receipts[file.stem] = {key: value[key] for key in ('exit', 'seconds', 'log_sha256', 'source_before', 'source_after', 'toolchain_sha256') if key in value}
tests = {}
layers = collections.defaultdict(list)
for file in sorted((OUT / 'receipts').glob('*.log')):
    if file.stem.startswith('layer-') or file.stem.startswith(('suite-', 'race', 'compare-flakes', 'regression-')):
        events = [json.loads(line) for line in file.read_text().splitlines() if line.startswith('{')]
        counts = collections.Counter((row.get('Test'), row['Action']) for row in events if row['Action'] in ('pass','fail','skip') and row.get('Test'))
        tests[file.stem] = [dict(test=key[0], action=key[1], count=count) for key,count in sorted(counts.items())]
        text = ''.join(row.get('Output', '') for row in events)
        for line in text.splitlines():
            if 'MESH_PERF {' in line:
                row = json.loads(line.split('MESH_PERF ', 1)[1])
                layers[file.stem].append({key:row[key] for key in ('case','byte_exact','synthetic','payload_bytes','duration_s','goodput_mbps','cpu_one_core_percent','allocations','allocated_bytes','one_way_ms')})
benchmarks = {}
for file in sorted((OUT/'receipts').glob('bench-*.log')):
    rows = []
    for line in file.read_text().splitlines():
        match = re.match(r'(BenchmarkPerformanceWindow\w+)-\d+\s+\d+\s+([\d.]+) ns/op\s+[\d.]+ MB/s\s+(\d+) B/op\s+(\d+) allocs/op',line)
        if match:
            rows.append(dict(name=match[1], ns=float(match[2]), bytes=int(match[3]), allocations=int(match[4])))
    benchmarks[file.stem] = rows
wire = {file.stem:sorted(set(re.findall(r'WIRE_SHA256=([0-9a-f]{64})',file.read_text()))) for file in sorted((OUT/'receipts').glob('bench-*.log'))}
assert all(value == ['9798fa9ce79950fa2126ab348854afdb443e7f738acd070bfd1ca63088e04211'] for value in wire.values())
record = dict(task='MESH-PERF-3', result='PARTIAL', physical_canary='BLOCKED_NO_SUPPORTED_OWNER_HANDOFF',
              baseline_inventory=seal(base), candidate_inventory=seal(current), files=changed,
              baseline_binary_sha256=digest(OUT/'baseline-broker'), candidate_binary_sha256=digest(OUT/'diagnostic-broker-final'),
              overlay_sha256=digest(PATCH), build_tags=['fc_perf_diagnostic'], receipts=receipts, tests=tests,
              layer_measurements=dict(layers), benchmarks=benchmarks, wire_transcripts=wire,
              live_payload_bytes=0, live_processes_created=0, production_mutations=0,
              runtime={name:json.loads((OUT/'receipts'/f'{name}.json').read_bytes()) for name in ('initial','final','api-process-readback','isolation-readback','rotation')},
              evidence_files={str(file.relative_to(OUT)):digest(file) for file in sorted((OUT/'receipts').iterdir()) if file.is_file()},
              limitations=['No physical canary; no diagnosis of current Android window bytes or Mux credit.',
                            'Local synthetic measurements are not carrier capacity or physical acceptance.',
                            'Default non-race regression failures reproduced on exact accepted source; no unrelated runtime fix.'])
with TARGET.open('x') as handle:
    json.dump(record, handle, indent=2)
print(json.dumps(dict(evidence_sha256=digest(TARGET), overlay_sha256=digest(PATCH), candidate_binary_sha256=record['candidate_binary_sha256'], candidate_inventory=record['candidate_inventory'], changed_files=len(changed)), indent=2))
