"""One cell per phase through the existing meter; no new instrumentation."""

import json
import sys

from deadline import WORK
from late_arrival import ROOT, digest


def main():
    assert sys.argv[1] in ('small', 'baseline')
    phase = next((value.split('=', 1)[1] for value in sys.argv if value.startswith('--phase=')), 'A1')
    assert phase in ('A1', 'B', 'A2')
    code = dict(A1=92, B=93, A2=94)[phase]
    expected = '1e73167c8bfdba68f96249088cf08ea3dfb9d3614d5bedb8a0a7bdd8716e4e7b'
    if phase != 'A1':
        receipt = json.loads(((WORK if phase == 'B' else WORK/'normal94')/'delivery/signing-receipt.json').read_text())
        expected = receipt['signed']['sha256']
    sys.argv = [sys.argv[0], sys.argv[1]]
    original = ROOT / 'tests/fixtures/mesh_throughput_trace/measure.py'
    assert digest(original) == '17e76fb9f3d8c46b5e7e4b5c55fa0f8098b59aef63e0e66c94cbce81b2c2a5ef'
    source = original.read_text()
    replacements = {
        "WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'": 'WORK = ROOT / '+repr(str(WORK.relative_to(ROOT)/('physical-'+phase))),
        "== '89'": "== '"+str(code)+"'",
        "'/data/local/tmp/fc-mesh-trace-' + mode + '-20261019'": "'/data/local/tmp/fc-deadline-"+phase+"-' + mode + '-20261020'",
        'for number in range(2):': 'for number in range(1):',
        "assert gate_result['small_gate_pass'] and gate_result['source_gateway'] == gateway": "assert gate_result['requests'] == 1 and gate_result['application_bytes'] == 65536 and gate_result['topology_stable'] and gate_result['matched_requests'] == 1 and gate_result['source_gateway'] == gateway\n        assert all(json.loads(line)['valid'] for line in (WORK / gate / 'requests.jsonl').read_text().splitlines())",
        'final_topology = topology()': "try:\n        final_topology = topology()\n    except Exception as failure:\n        final_topology = dict(error=type(failure).__name__, unexplained_tun_gap=True)",
    }
    for old, new in replacements.items():
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    sys.path.insert(0, str(original.parent))
    namespace = dict(__name__='deadline_physical_a1', __file__=str(original))
    exec(compile(source, str(original), 'exec'), namespace)
    namespace['GATEWAY'] = 'b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba'
    sys.path.insert(0, str(ROOT / 'tests/fixtures/queue_retry'))
    from journal import reassemble, performance_lines
    reconstruct = namespace['reconstruct']
    def parsed(handle):
        if str(handle.name).endswith('NL-raw.jsonl'):
            rows, errors = reassemble(handle)
            records, other = reconstruct(performance_lines(rows))
            return records, errors + other
        return reconstruct(handle)
    namespace['reconstruct'] = parsed
    namespace['WORK'].mkdir(mode=0o700, exist_ok=True)
    requested = sum(json.loads(line)['intended_bytes'] for path in namespace['WORK'].glob('*/requests.jsonl') for line in path.read_text().splitlines())
    assert requested + (65536 if sys.argv[1] == 'small' else 6*1024*1024) <= 7*1024*1024
    total = sum(json.loads(line)['intended_bytes'] for path in WORK.glob('physical-*/*/requests.jsonl') for line in path.read_text().splitlines())
    assert total + (65536 if sys.argv[1] == 'small' else 6*1024*1024) <= 64*1024*1024
    adb = namespace['adb']
    path = adb('pm path com.familyconnect.app.friends').stdout.strip().removeprefix('package:')
    assert path.startswith('/data/app/') and not any(char.isspace() for char in path)
    assert adb('sha256sum '+path).stdout.split()[0] == expected
    namespace['main']()


if __name__ == '__main__':
    main()
