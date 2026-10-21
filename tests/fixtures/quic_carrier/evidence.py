import copy
from lab import *

analysis=json.loads((WORK/'analysis.json').read_text())
verification=json.loads((WORK/'verification.json').read_text())
phases=copy.deepcopy(analysis['phases'])
for name,phase in phases.items():
    phase['manifest_sha256']=digest(WORK/name/'reservation.json')
    phase['result_sha256']=digest(WORK/name/'phase-result.json')
    phase['logs']={path.name:digest(path) for path in (WORK/name).iterdir() if path.suffix in ['.json','.jsonl','.stderr']}
    for endpoint in phase['endpoints'].values():
        mux=endpoint['mux_final']
        if mux:
            endpoint['mux_final']={key:value for key,value in mux.items() if not isinstance(value,(list,dict))}
        endpoint['trace']={key:value for key,value in (endpoint['trace'] or {}).items() if not isinstance(value,(list,dict))}
build=json.loads((WORK/'build.json').read_text())
local_logs={path.name:digest(path) for path in WORK.glob('*.log') if not path.name.endswith('-operator.log')}
fixture_inventory={name:value for name,value in inventory(FIX).items() if '__pycache__' not in name and not name.endswith('.pyc')}
result=dict(schema='family-connect-quic-carrier-lab-v1',capsule=str(WORK.relative_to(ROOT)),scope='isolated lab; production/Android/public artifacts unchanged; not product admission',build=build,earlier_build=json.loads((WORK/'build-v1.json').read_text()),fixture_inventory=fixture_inventory,local_logs=local_logs,local_tests='local memory/bound-Pion/loopback only, not charged as live traffic',source_reserved_live=analysis['source_reserved_live'],media_charged_live=analysis['media_charged_live'],budget=dict(source_limit=64*2**20,media_limit=128*2**20,transfer_seconds=180,source_semantics='conservative reservation including complete failed workloads, not fictitious delivered bytes',media_semantics='observed conservative media bytes plus64KiB per endpoint shutdown allowance; IPv6/SRTP16 upper, no local test charge'),preexecution=json.loads((WORK/'preexecution-AO.json').read_text()),external_change=json.loads((WORK/'external-state-change.json').read_text()),repairs={name:json.loads((WORK/name).read_text()) for name in ['controller-line-repair.json','startup-gate-repair.json','controller-proof-repair.json','A1G-causal-review.json']},replay=json.loads((WORK/'replay-v2.json').read_text()),extra_local=json.loads((WORK/'extra-validation.json').read_text()),phases=phases,verification=verification,interpretation=dict(datagram_adapter='local/race and live short/complete-body QN PASS; no reliability layer below QUIC',packetization='1200B datagram; L24B+VP8 17B, RTP1200 MTU,12B header+1/3/4B VP8 descriptor: two RTP; exact cipher tag not observed',cadence='original2ms/frame measured410.39 datagrams/s; common normalized1MiB/s with2ms earned credit measured750.81/s; no fixed sleep;33ms nominal timestamp inherited',authentication='ephemeral mutual CA/DNS role/TLS1.3/lab ALPN; no0RTT; not Family admission',main_acceptance='no repeatable clean A/QN/QN/A contrast; preserve all phase and post-delivery failures',loss_counters='QUIC loss declaration/repeated STREAM bytes, RS retries and RTP repeats are different quantities; lower ring gaps never zero-filled',closure='QN1 all17 bodies/receipts verified before idle/phase timeout during controller log fetch; not download failure; QN2 publisher disconnect before bulk, no further QN retry',next='close this bounded experiment; no automatic tuning, product admission or further live load'))
result['interpretation']['local_write_timing_scope']='WriteNS begins after serialized adapter slot acquisition; earlier slot wait and library8-entry queue residence not timed; exact pre-send/ACK causal attribution unavailable, not zero'
destination=ROOT/'docs/releases/2026-10-21-quic-carrier.evidence.json'
write(destination,json.dumps(result,indent=2)+'\n')
print(destination.relative_to(ROOT),destination.stat().st_size)
