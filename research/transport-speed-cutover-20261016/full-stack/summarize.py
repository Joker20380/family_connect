import hashlib
import json
from pathlib import Path
import re
import sys


root = Path(__file__).resolve().parent
output = root / sys.argv[1]
rows = []
pattern = re.compile(r'STACK_RESULT client=(\w+) server=(\w+) scenario=(\w+) traffic=(\{.*?\}) client_result=(\{.*\}) server_result=(\{.*\})$')
for mode, repetitions in [('normal', 2), ('race', 1)]:
    log = (output / ('matrix-' + mode + '.log')).read_text()
    assert 'WARNING: DATA RACE' not in log and '\nFAIL' not in log
    for line in log.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        client, server, scenario, traffic, client_result, server_result = match.groups()
        rows.append(dict(mode=mode, client=client, server=server, scenario=scenario,
                         traffic=json.loads(traffic), client_result=json.loads(client_result),
                         server_result=json.loads(server_result)))
    selected = [row for row in rows if row['mode'] == mode]
    assert len(selected) == 12 * repetitions
    for client in ('baseline', 'candidate'):
        for server in ('baseline', 'candidate'):
            for scenario in ('clean', 'loss', 'reorder'):
                assert len([row for row in selected if (row['client'], row['server'], row['scenario']) == (client, server, scenario)]) == repetitions
for row in rows:
    assert row['traffic']['traffic_complete'] is True
    assert row['traffic']['bulk_echo_bytes'] == 1048576
    for side in ('client', 'server'):
        result = row[side + '_result']
        assert result['rtp_received'] > 0 and result['rtp_written'] > 0
        assert result['mux']['DNSErrors'] == result['mux']['DNSTimeouts'] == result['mux']['ProtocolErrors'] == 0
        assert result['mux']['DNSResponses'] == 8
        if row['scenario'] != 'clean':
            assert result['fault']['injected'] is True
        if row['scenario'] == 'loss':
            assert result['fault']['target_retransmissions'] >= 1
receipts = json.loads((output / 'receipts.json').read_text())
assert len(receipts) == 6 and all(receipt['exit'] == 0 for receipt in receipts)
assert all(receipt['reason'] == 'command_exit' for receipt in receipts)
input_files = json.loads((root / 'input-carrier-files.json').read_text())
fixture_names = {'telemost/full_stack_test.go', 'telemost/full_stack_credentials_test.go', 'tcpforward/fixture_dns.go'}
for variant, inventory in input_files.items():
    source = root / variant / 'carrier'
    actual = {str(filename.relative_to(source)): hashlib.sha256(filename.read_bytes()).hexdigest()
              for filename in source.rglob('*') if filename.is_file()}
    assert set(actual) == set(inventory) | fixture_names
    assert all(actual[name] == checksum for name, checksum in inventory.items())
gateway = root.parent / 'gateway-transport-progress-burst-candidate-1/source/carrier'
gateway_differences = []
checked_gateway_files = {}
for package in ('reliablestream', 'familysession', 'telemost', 'tcpforward'):
    for filename in sorted((root / 'baseline/carrier' / package).glob('*.go')):
        if filename.name.endswith('_test.go') or filename.name == 'fixture_dns.go':
            continue
        name = str(filename.relative_to(root / 'baseline/carrier'))
        gateway_file = gateway / name
        expected = hashlib.sha256(filename.read_bytes()).hexdigest()
        found = hashlib.sha256(gateway_file.read_bytes()).hexdigest() if gateway_file.is_file() else None
        checked_gateway_files[name] = dict(client=expected, gateway=found)
        if expected != found:
            gateway_differences.append(name)
summary = dict(result='PASS_LOCAL_FULL_STACK', scenarios=len(rows), fixed_normal_repeats=2,
               fixed_race_repeats=1, rows=rows, thermal_max_celsius=max(receipt['max_cpu_celsius'] for receipt in receipts),
               original_carrier_sources_unchanged=True, extra_fixture_files=sorted(fixture_names),
               gateway_relevant_differences=gateway_differences, gateway_relevant_bindings=checked_gateway_files,
               limitations=['local Pion peer-to-peer, not provider signaling/relay/mobile path',
                            'Family TLS and production mux; DNS upstream is a synthetic local adapter',
                            'FRS1 frame drop/delay before VP8 encoding, not on-the-wire RTP loss',
                            'compiled test peers, not existing installed APK or gateway executable',
                            'no bootstrap/admission/maintenance or real download speed claim'])
(root / 'results.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps({key: value for key, value in summary.items() if key not in ('rows', 'gateway_relevant_bindings')}))
for row in rows:
    print(row['mode'], row['client'], row['server'], row['scenario'], row['traffic']['elapsed_ms'],
          [row[side+'_result']['fault'] for side in ('client','server')])
