"""One paired small gate or one6MiB cell, using the existing phone-side meter."""

import json
import sys

from preserve import ROOT, WORK, digest


def main():
    assert sys.argv[1] in ('small','small-return','baseline')
    original=ROOT/'tests/fixtures/mesh_throughput_trace/measure.py'
    assert digest(original)=='17e76fb9f3d8c46b5e7e4b5c55fa0f8098b59aef63e0e66c94cbce81b2c2a5ef'
    source=original.read_text()
    replacements={
        "WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'":"WORK = ROOT / 'state-client-build/mesh-receive-path-20261020'",
        "== '89'":"== '91'",
        "'/data/local/tmp/fc-mesh-trace-' + mode + '-20261019'":"'/data/local/tmp/fc-receive-path-' + mode + '-20261020'",
        'for number in range(2):':'for number in range(1):',
        "and value['consumes'] == 1 and 'new' in value['receive_results']]":"and value['consumes'] == 1 and 'new' in value['receive_results'] and any(item['node']=='NL' and item['kind']=='submission_to_release_ns' for item in value['local_intervals'])]",
        'final_topology = topology()':"try:\n        final_topology = topology()\n    except Exception as failure:\n        final_topology = dict(error=type(failure).__name__, unexplained_tun_gap=True)",
    }
    for old,new in replacements.items():
        assert source.count(old)==1,old
        source=source.replace(old,new)
    sys.path.insert(0,str(original.parent))
    namespace=dict(__name__='bounded_receive_measure',__file__=str(original))
    exec(compile(source,str(original),'exec'),namespace)
    if '--check-only' in sys.argv:
        print('PAIRED_METER_COMPILES_NO_TRAFFIC')
        return
    from correlate_receive import receive_evidence
    from journal import reassemble, performance_lines
    original_correlate, original_reconstruct = namespace['correlate'], namespace['reconstruct']

    def joined(nodes):
        result=original_correlate(nodes)
        result['receive_path']=receive_evidence(nodes)
        result['errors']+=result['receive_path']['errors']
        return result

    def parsed(handle):
        if str(getattr(handle,'name','')).endswith('NL-raw.jsonl'):
            rows, errors=reassemble(handle)
            records, other=original_reconstruct(performance_lines(rows))
            return records,errors+other
        return original_reconstruct(handle)

    namespace['correlate'],namespace['reconstruct']=joined,parsed
    namespace['GATEWAY']=json.loads((WORK/'gateway-build.json').read_text())['sha256']
    signing=json.loads((WORK/'delivery/signing-receipt.json').read_text())
    adb=namespace['adb']
    path=adb('pm path com.familyconnect.app.friends').stdout.strip().removeprefix('package:')
    assert path.startswith('/data/app/') and not any(char.isspace() for char in path)
    assert adb('sha256sum '+path).stdout.split()[0]==signing['signed']['sha256']
    requested=sum(json.loads(line)['intended_bytes'] for path in WORK.glob('*/requests.jsonl') for line in path.read_text().splitlines())
    next_bytes=65536 if 'small' in sys.argv[1] else 6*1024*1024
    assert requested+next_bytes<=32*1024*1024
    namespace['main']()


if __name__=='__main__':main()
