import argparse
import hashlib
import json
from pathlib import Path
import re


parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--run', type=Path, required=True)
args = parser.parse_args()
research = Path(__file__).resolve().parent
publication = research.parents[1]
output = args.run.resolve()
receipts = json.loads((output / 'receipts.json').read_text())
assert [(item['label'], item['count']) for item in receipts] == [
    ('candidate-normal', 2), ('previous-normal', 2), ('candidate-race', 1), ('previous-race', 1)]
assert all(item['exit'] == 0 and item['reason'] == 'command_exit' for item in receipts)
assert json.loads((output / 'source-unchanged.json').read_text())['selected_sources_unchanged']
inputs = json.loads((output / 'inputs.json').read_text())
for name, expected in inputs['fixtures'].items():
    assert hashlib.sha256((research / name).read_bytes()).hexdigest() == expected, name
gateway = args.repo.resolve() / 'state-client-build/transport-speed-cutover-1/gateway-source/carrier'
gateway_matches = {}
for name in ('tcpforward/mux.go', 'tcpforward/mux_stream.go', 'tcpforward/mux_dns.go', 'roombroker/lease_control.go'):
    actual = hashlib.sha256((gateway / name).read_bytes()).hexdigest()
    assert actual == inputs['sources']['candidate'][name], name
    gateway_matches[name] = actual
protocol_counters = {}
for receipt in receipts:
    logfile = output / (receipt['label'] + '.log')
    raw = logfile.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == receipt['log_sha256']
    text = raw.decode()
    assert '\nPASS\n' in text and 'FAIL' not in text and 'DATA RACE' not in text
    assert text.count('32 occupied: reused search=3/3') == receipt['count']
    assert text.count('31 TCP + 1 control fills mux;') == receipt['count']
    assert text.count('40 sequential verified HTTPS bodies;') == receipt['count']*3
    matches = re.findall(r'client_protocol_errors=(\d+) server_protocol_errors=(\d+)', text)
    assert len(matches) == receipt['count']*3
    modes = ['application_close', 'origin_close', 'application_reset'] * receipt['count']
    protocol_counters[receipt['label']] = [dict(mode=mode, client=int(client), server=int(server))
        for mode, (client, server) in zip(modes, matches)]
    (research / logfile.name).write_bytes(raw)
value = dict(
    result='LOCAL_ADMISSION_MECHANISM_REPRODUCED_ON_BOTH_SOURCES',
    owner_report='Search engine returns results; most sites/assets fail. UI observation, no HTTP receipt.',
    phone_export_sha256='bcc5a08d4638550c136b7c97243cb18a8a071eac1ff7022a8993c46b48a83c30',
    installed_apk_sha256='28543d4690327e29a6eb6a60e52fa50232a407663ed7e610f1434cd56f86193d',
    installed_native_sha256='f25124ba1c94a0c6f4258e8b67488e8febf9a1c9e88cb2073790564c3a1f4729',
    last_observed_gateway_sha256='5de40b9ce9c15aac85475df05c449bddf2ecfe61a1928fa3844b4a8446b33047',
    source_inputs=inputs, deployed_gateway_relevant_sources_match=gateway_matches,
    fixed_leaf_cases=30, verified_synthetic_https_bodies=1140,
    tests=receipts, selected_sources_unchanged=True,
    local_lifecycle_protocol_counters=protocol_counters,
    analysis_history='First summary rejected an incorrect all-zero protocol-counter assumption; corrected to retain observed counters. Go tests passed; no rerun or product change.',
    observations=dict(
        retained_32_tcp_search_and_existing_asset='PASS',
        new_tls_at_32='REFUSED_BEFORE_ORIGIN',
        release_one_new_https='PASS',
        dns_at_32=dict(udp='SYNTHETIC_QUERY_RESPONSE_PASS', tcp='REFUSED'),
        control_at_32='LOCAL_MUX_STREAM_LIMIT_BEFORE_SERVER_CALLBACK',
        data_at_31_plus_control='LOCAL_MUX_STREAM_LIMIT_WITHOUT_LIMIT_DENIED_OR_OPEN_ERRORS_INCREMENT',
        clean_tls_close_origin_close_and_abort='NO_LEAK_IN_40_SEQUENTIAL_REQUESTS_PER_CASE',
        phone_failed_request_to_quota_binding='NOT_PROVEN',
        ten_minute_termination_to_control_starvation='NOT_PROVEN',
        ten_owner_client_mux_protocol_errors='NOT_REPRODUCED_OR_EXPLAINED; LOCAL_SERVER_ORIGIN_CLOSE_COUNTERS_RECORDED_SEPARATELY',
        fast_retransmit_cause='NOT_PROVEN; SAME_ADMISSION_RESULT_BEFORE_AND_AFTER'),
    limits=['No Android TUN/gVisor or real browser in fixture',
            'No WebRTC/provider/cellular path, real-site DNS or HTTP/2/QUIC',
            'Distinct synthetic HTTP Host values and connections share one trusted local TLS origin',
            'Real Family TLS/reliable/mux/wholedevice code, default reliable parameters, no injected loss',
            'Control callback tests admission only, not authenticated lease renewal or live expiry'],
    actions=dict(local_test_batches=4, product_patches=0, apk_native_gateway_builds=0,
                 adb=0, ssh=0, connects=0, exports=0, restarts=0, rollback=0,
                 native_stats_pollers=0, emulator=0))
target = publication / 'docs/releases/evidence/2026-10-17-browser-admission-local-1.json'
target.write_text(json.dumps(value, indent=2)+'\n')
print(json.dumps(dict(result=value['result'], cases=30, https_bodies=1140,
                     peak_cpu_celsius=max(item['max_cpu_celsius'] for item in receipts)), indent=2))
