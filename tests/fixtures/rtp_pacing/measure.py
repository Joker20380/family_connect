"""One phase using the accepted TUN meter and bounded Mux/RS collector unchanged."""

import json
import re
import subprocess
import sys
import time

from prepare import ROOT, WORK, APK, digest


def select_records(records):
    selected = [record for record in records if record['performance'].get('PacketPacing') is not None]
    if not selected:
        return []
    assert len({record['session_tag'] for record in selected}) == 1, 'AMBIGUOUS_OWNER_SESSION_NO_BULK'
    for record in selected:
        performance = record['performance']
        assert performance['Mux']['Profile'] == 'LEGACY64' and performance['Mux']['Window'] == 65536
        assert performance['PacketPacing']['RateBytesPerSecond'] == rate, 'ACTUAL_PACING_MODE_MISMATCH'
    assert -2 <= time.time() - selected[-1]['observed_epoch'] <= 8, 'OWNER_SESSION_STALE_STOP'
    return selected


def scope_receipt(records, session):
    receipt = dict(phase=phase, mode=mode, session_tag=session, window=65536,
                   observed_epoch=records[0]['observed_epoch'],
                   protocol_errors_first_observed=records[0]['performance']['Mux']['ProtocolErrors'],
                   protocol_errors_at_establishment=None, vpn_network=vpn, vpn_created=created,
                   gateway_pid=readback['gateway']['state']['MainPID'],
                   gateway_invocation=readback['gateway']['state']['InvocationID'],
                   phone_apk_sha256=APK, gateway_sha256=artifact['binary_sha256'],
                   both_sides_window=dict(android=65536, nl=65536,
                       basis='Actual authenticated Family TLS/Mux runtime plus exact pinned shared ALPN mapping; not an independent Android live counter export'),
                   attribution='Only the authenticated owner key is selected for PacketPacing; one fresh tagged session in this invocation has the expected mode',
                   topology=initial_topology)
    with (WORK / ('session-scope-' + phase + '.json')).open('x') as output:
        json.dump(receipt, output, indent=2)
    print(json.dumps(dict(gate='ACTUAL_OWNER_LEGACY64_MODE_VERIFIED', phase=phase, mode=mode,
                         session_tag=session, window=65536, protocol_errors=receipt['protocol_errors_first_observed'])), flush=True)


phase, readback_name = sys.argv[1:]
assert phase in ('A1', 'B1', 'B2', 'A2') and re.fullmatch('[a-z-]+', readback_name)
mode = 'OBSERVE' if phase.startswith('A') else 'FIXED4M'
rate = 0 if mode == 'OBSERVE' else 500000
readback = json.loads((WORK / (readback_name + '-readback.json')).read_text())
artifact = json.loads((WORK / 'build-result.json').read_text())
assert readback['phone']['apk_sha256'] == APK and readback['gateway']['sha256'] == artifact['binary_sha256']
assert len(readback['vpn']) == 1
vpn = re.search(r'network\{(\d+)\}', readback['vpn'][0])[1]
created = re.search(r'created=(\S+)', readback['vpn'][0])[1]
previous = json.loads((WORK / 'manual-a1-preparation.json').read_text())
assert vpn not in previous['previous_vpn_networks']
for existing in WORK.glob('session-scope-*.json'):
    assert json.loads(existing.read_text())['vpn_network'] != vpn, 'REUSED_PHASE_VPN'
assert not (WORK / phase).exists()

original = ROOT / 'tests/fixtures/mux_credit/measure.py'
assert digest(original) == 'a936409c318246edcfaf15c7cfbee2b8b030091e8ab147da690748718d57ed67'
source = original.read_text()
replacements = {
    'from prepare import ROOT, WORK, APK, digest': '',
    "target=WORK/'matrix'": 'target=WORK/phase',
    "(WORK/'observation-build.json').read_text())['sha256']": "(WORK/'build-result.json').read_text())['binary_sha256']",
    "'/data/local/tmp/fc-mux-credit-matrix-20261020'": "'/data/local/tmp/fc-rtp-pacing-'+phase+'-20261020'",
    "output.append(row)": "output.append(dict(row,observed_epoch=int(record['__REALTIME_TIMESTAMP'])/1e6))",
    '    return output': '    return select_records(output)',
    'initial=topology()': "initial=topology()\n    global initial_topology\n    initial_topology=initial\n    assert 'network{'+vpn+'}' in adb('dumpsys connectivity').stdout",
    "(target/'preflight.json').write_text": "assert gateway['MainPID']==readback['gateway']['state']['MainPID'] and gateway['InvocationID']==readback['gateway']['state']['InvocationID']\n    (target/'preflight.json').write_text",
    "session=observed[-1]['session_tag']": "session=observed[-1]['session_tag']\n        scope_receipt(observed,session)",
    "reserved=WORK/'traffic-matrix-reservation.json'": "reserved=WORK/('traffic-'+phase+'-reservation.json')",
    'intended_bytes=24*1024*1024': 'intended_bytes=8*1024*1024+65536',
    'reserved.write_text(json.dumps(': "assert sum(json.loads(path.read_text())['intended_bytes'] for path in WORK.glob('traffic-*-reservation.json'))+8*1024*1024+65536<=64*1024*1024\n        reserved.write_text(json.dumps(",
    'enumerate((1,2,4,4,2,1))': 'enumerate((1,1,2))',
    '4*1024*1024//flows': '(65536 if number==0 else 4*1024*1024//flows)',
    'assert not stop.is_set() and topology()==initial': "assert not stop.is_set() and topology()==initial\n            assert 'network{'+vpn+'}' in adb('dumpsys connectivity').stdout,'OWNER_VPN_CHANGED_STOP'",
    "final_topology=topology()": "final_topology=topology(),phase=phase,mode=mode,profile='LEGACY64',window=65536,vpn_unchanged=('network{'+vpn+'}' in adb('dumpsys connectivity').stdout)",
}
for old, new in replacements.items():
    assert old in source, old
    source = source.replace(old, new)
compile(source, str(original), 'exec')
initial_topology = None
namespace = dict(globals(), __name__='__main__', __file__=str(original))

def record_scope(records, session):
    global initial_topology
    initial_topology = namespace['initial_topology']
    scope_receipt(records, session)

namespace['scope_receipt'] = record_scope
try:
    subprocess.run([sys.executable, str(ROOT / 'tests/fixtures/rtp_pacing/policy.py'), mode, 'ON', phase+'start'], check=True, timeout=75)
    exec(compile(source, str(original), 'exec'), namespace)
finally:
    subprocess.run([sys.executable, str(ROOT / 'tests/fixtures/rtp_pacing/policy.py'), mode, 'OFF', phase+'end'], check=True, timeout=75)
