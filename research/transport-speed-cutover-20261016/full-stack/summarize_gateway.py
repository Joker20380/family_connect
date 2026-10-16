import hashlib
import json
from pathlib import Path
import re
import sys


root = Path(__file__).resolve().parent
output = root/sys.argv[1]
rows = []
pattern = re.compile(r'STACK_RESULT client=(\w+) server=(\w+) scenario=(\w+) traffic=(\{.*?\}) client_result=(\{.*\}) server_result=(\{.*\})$')
for mode in ('normal', 'race'):
    log = (output/('matrix-'+mode+'.log')).read_text()
    assert 'WARNING: DATA RACE' not in log and '\nFAIL' not in log
    for line in log.splitlines():
        match = pattern.search(line)
        if match:
            client, server, scenario, traffic, client_result, server_result = match.groups()
            rows.append(dict(mode=mode,client=client,server=server,scenario=scenario,
                             traffic=json.loads(traffic),client_result=json.loads(client_result),server_result=json.loads(server_result)))
    selected = [row for row in rows if row['mode'] == mode]
    assert len(selected) == 12
    assert len({(row['client'],row['server'],row['scenario']) for row in selected}) == 12
for row in rows:
    assert row['traffic']['traffic_complete'] and row['traffic']['bulk_echo_bytes'] == 1048576
    for side in ('client', 'server'):
        result = row[side+'_result']
        assert result['rtp_received'] > 0 and result['rtp_written'] > 0
        assert result['mux']['DNSResponses'] == 8
        assert result['mux']['DNSErrors'] == result['mux']['DNSTimeouts'] == result['mux']['ProtocolErrors'] == 0
        if row['scenario'] != 'clean':
            assert result['fault']['injected']
        if row['scenario'] == 'loss':
            assert result['fault']['target_retransmissions'] >= 1
receipts = json.loads((output/'receipts.json').read_text())
assert len(receipts) == 6 and all(receipt['exit'] == 0 and receipt['reason'] == 'command_exit' for receipt in receipts)
before = json.loads((root/'gateway-input-files.json').read_text())
manifest = json.loads((root.parent/'owner-cumulative-client-acceptance-1-resume/review-publication/research/gateway-transport-progress-20261016/source-manifest.json').read_text())
assert before == manifest['candidate_files']
fixtures = {'telemost/full_stack_test.go','telemost/full_stack_credentials_test.go','tcpforward/fixture_dns.go'}
for variant in ('baseline','candidate'):
    directory = root/('gateway-'+variant)/'carrier'
    after = {str(filename.relative_to(directory)):hashlib.sha256(filename.read_bytes()).hexdigest()
             for filename in directory.rglob('*') if filename.is_file()}
    assert set(after) == set(before)|fixtures
    expected = dict(before)
    if variant == 'candidate':
        expected['reliablestream/engine.go'] = hashlib.sha256((root/'candidate/carrier/reliablestream/engine.go').read_bytes()).hexdigest()
    assert all(after[name] == checksum for name,checksum in expected.items())
result = dict(result='PASS_EXACT_PEER_SOURCES', scenarios=24, fixed_normal_repeats=1,fixed_race_repeats=1,
              gateway_parent_inventory=manifest['candidate_inventory_sha256'],gateway_product_delta=['reliablestream/engine.go'],
              rows=rows,thermal_max_celsius=max(receipt['max_cpu_celsius'] for receipt in receipts),
              production_changes=False, compiled_test_peers_not_production_executables=True)
(root/'gateway-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({key:value for key,value in result.items() if key!='rows'}))
for row in rows:
    print(row['mode'],row['client'],row['server'],row['scenario'],row['traffic']['elapsed_ms'],
          [row[side+'_result']['fault'] for side in ('client','server')])
