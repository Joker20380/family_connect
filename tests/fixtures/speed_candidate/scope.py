"""Bind an owner-provided export to fresh readbacks; never infer applied limits."""

import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from prepare import ROOT, WORK, digest


def validate_export(document, profile):
    ring = document['ring']
    assert ring['version_code'] == 97 and ring['app_version'] == '0.1.18-beta97-speed'
    assert ring['state'] == 'CONNECTED' and ring['vpn_capture_open'] and ring['restricted_readiness'] == 'READY'
    diagnostic = ring['restricted_session']
    assert re.fullmatch('[0-9a-f]{64}', diagnostic['session_tag'])
    assert diagnostic['speed_profile'] == profile
    assert diagnostic['terminal_reason'] == 'NONE' and 'terminal_observed_at_ms' not in diagnostic
    expected = dict(local_send=8,local_receive=16,peer_receive=16,effective_send=8,local_write_completion=False) if profile == 'P0' else dict(local_send=32,local_receive=32,peer_receive=32,effective_send=32,local_write_completion=profile == 'P2')
    assert diagnostic['reliable_limits'] == expected
    assert diagnostic['mux_profile'] == ('LEGACY64' if profile == 'P0' else 'CREDIT128')
    assert diagnostic['mux_window'] == (65536 if profile == 'P0' else 131072)
    return diagnostic


def main():
    os.umask(0o077)
    assert len(sys.argv) in (4,5)
    phase, export_file, label = sys.argv[1:4]
    assert phase in ('P0a','P1a','P2a','P2b','P1b','P0b')
    assert re.fullmatch('[a-z0-9-]+', label)
    destination = WORK / ('scope-' + phase + '.json')
    assert not destination.exists()
    source = Path(export_file)
    assert source.stat().st_size <= 525312
    document = json.loads(source.read_text())
    android = validate_export(document, phase[:2])
    for previous_path in WORK.glob('scope-P*.json'):
        previous = json.loads(previous_path.read_text())
        assert previous.get('session_tag') != android['session_tag'], 'New manual session required; do not reuse an earlier phase connection'
    export_age = time.time() - android['observed_at_ms'] / 1000
    assert -60 <= export_age <= 300, 'Fresh export required; age is a staleness guard, not one-way latency'
    saved = WORK / ('android-' + label + '.json')
    assert not saved.exists()
    shutil.copyfile(source, saved)
    subprocess.run([sys.executable, ROOT/'tests/fixtures/speed_candidate/readback.py', label], check=True)
    subprocess.run([sys.executable, ROOT/'tests/fixtures/speed_candidate/observe.py', label, *sys.argv[4:]], check=True)
    readback = json.loads((WORK/(label+'-readback.json')).read_text())
    observation = json.loads((WORK/('observation-'+label+'.json')).read_text())
    assert len(readback['vpn']) == 1
    assert observation['identity']['beta97_readiness']['result'] == 'READY'
    gateway = observation['gateway']
    assert not gateway['parser_errors']
    tag = android['session_tag']
    matched = [row for row in gateway['records'] if row.get('diagnostic',{}).get('session_tag') == tag]
    assert len(matched) == 1 and matched[0]['event'] == 'session_profile', 'Missing startup or terminal session'
    server = matched[0]['diagnostic']
    for key in ('speed_profile','reliable_limits','mux_profile','mux_window'):
        assert server[key] == android[key]
    trace = gateway['latest_trace'][tag]
    assert -60 <= time.time() - int(trace['journal_epoch_us']) / 1e6 <= 30, 'No recent same-session activity'
    assert trace.get('state') not in ('FAILED','CLOSED')
    meter = ROOT/'tests/fixtures/mesh_throughput_trace/measure.py'
    assert digest(meter) == '17e76fb9f3d8c46b5e7e4b5c55fa0f8098b59aef63e0e66c94cbce81b2c2a5ef'
    helpers = [node for node in ast.parse(meter.read_text()).body if isinstance(node,ast.FunctionDef) and node.name in ('adb','topology')]
    namespace = dict(subprocess=subprocess,re=re)
    exec(compile(ast.Module(body=helpers,type_ignores=[]),str(meter),'exec'),namespace)
    scope = dict(phase=phase,owner_verified=True,gateway_verified=True,observed_epoch=time.time(),
                 android_diagnostic=android,gateway_diagnostic=server,session_tag=tag,
                 android_export_sha256=digest(saved),android_export_age_seconds=export_age,
                 fresh_gateway_same_tag_trace=trace,topology=namespace['topology'](),
                 vpn_network=re.search(r'network\{(\d+)\}',readback['vpn'][0])[1],
                 phone_apk_sha256=readback['phone']['apk_sha256'],gateway_sha256=readback['gateway']['sha256'],
                 gateway_pid=readback['gateway']['state']['MainPID'],gateway_invocation=readback['gateway']['state']['InvocationID'],
                 readback=readback,gateway_journal_since_utc=gateway.get('since_utc'),scope_note='Android applied export up to300s; immutable session limits; fresh same-tag gateway trace and TUN readback. incident/history not used as current.')
    with destination.open('x') as output:
        json.dump(scope, output, indent=2)
    print(json.dumps(dict(scope=str(destination),profile=phase[:2],both_applied_limits_verified=True,android_protocol_errors=android['protocol_errors'])))


if __name__ == '__main__':
    main()
