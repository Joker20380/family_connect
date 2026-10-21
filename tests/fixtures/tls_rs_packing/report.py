"""Append one raw-derived packing section; preserve all earlier attempts."""
import json
import statistics
from prepare import ROOT,WORK,FIX,digest,patch_file

MARKER='## TLS→RS packing — 21 October2026'

def request(phase,name):return next(row for row in phase['requests'] if row['name']==name)
def change(baseline,candidate):return (candidate/baseline-1)*100
def number(value):return '—' if value is None else f'{value:.6f}'
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers)]+['| '+' | '.join(str(value) for value in row)+' |' for row in rows])
def log_objects(path):
    result=[]
    for line in path.read_text().splitlines():
        if '{' not in line:continue
        try:result.append(json.loads(line[line.index('{'):]))
        except ValueError:continue
    return result

def main():
    analysis=json.loads((WORK/'analysis.json').read_text());phases=analysis['phases']
    verification=json.loads((WORK/'verification.json').read_text());kit=json.loads((WORK/'kit.json').read_text());build=json.loads((WORK/'build.json').read_text())
    tnames=['T8A','T8B','T32A1','T32B1','T32B2','T32A2']
    pnames=['P32A1r','P32B1','P32B2','P32A2','P8Ar','P8B','P8A3','P8B3']
    pairs=[('T8','T8A','T8B'),('T32 forward','T32A1','T32B1'),('T32 reverse','T32A2','T32B2')]
    ppairs=[('P32 forward (shutdown warning)','P32A1r','P32B1'),('P32 reverse','P32A2','P32B2'),('P8 v2 (shutdown warning)','P8Ar','P8B'),('P8 v3 clean','P8A3','P8B3')]
    gains={label:change(phases[base]['received_mbit_s_to_last'],phases[candidate]['received_mbit_s_to_last']) for label,base,candidate in pairs}
    pgains={label:dict(single=change(request(phases[base],'single')['goodput_mbit_s'],request(phases[candidate],'single')['goodput_mbit_s']),parallel=change(phases[base]['parallel']['goodput_mbit_s'],phases[candidate]['parallel']['goodput_mbit_s'])) for label,base,candidate in ppairs}
    body_stream_exact=all(all(item['accepted_equals_ordered_peer'] and item['accepted_equals_submitted'] for item in phases[name]['packing'].values()) and not any(phases[name]['protocol_errors'].values()) for name in tnames+pnames)
    assert body_stream_exact
    assert all(phases[name]['clean_acknowledged_completion'] for name in ['P8A3','P8B3'])
    for _,baseline,candidate in pairs+ppairs:
        assert phases[baseline]['reservation']['production_before']==phases[candidate]['reservation']['production_before']
    repeated=False
    source=analysis['application_reserved']/1024**2;wire=analysis['wire_charged']/1024**2
    text=f'''{MARKER}

**COMPLETED LABORATORY COMPARISON; no production admission or deployment.**
{len(phases)} isolated attempts, including retained failed attempts; all owned peers
and collectors closed. Source reservations{source:.6f}/128MiB, conservative outgoing
media{wire:.6f}/256MiB. Failed attempts are not removed or refunded from this ledger.
Original phase1–3 results, long R32 controls and excluded old P816 remain unchanged.

### Contract, provenance and common controls

Pinned parent is phase3 exact source/binaryb95110c5…; original media A/phase0 in every
packing run. The monotonic timebase B remains separate and disabled. No pacer,
SACK-hole, queue-retry, read-alignment, finite-deadline, fragmentation, FEC, QUIC,
Mux128, hosting or library change. FRS1, Family prefix, TLS configuration, AEAD and
ALPN unchanged. 8 means both ends S8/R16, effective8;32 means both ends S32/R32,
effective32. Payload16384, RTO1s, MaxRetries8, MaxAge20s and SACK32 remain unchanged.

Packing is in the existing outbound Family TLS byte-stream adapter, before
ReliableStream.SendContext and before sequence/pending/window allocation. It never
combines already encoded FRS1 messages. The receiving ordered pipe is unchanged.
A uses the old net.Pipe reader→RS boundary. B0 copies into a finite FIFO and sends
available bytes without a coalescing timer. Selected B2 adds at most2ms intentional
tail waiting, timed from its oldest byte, not reset by later arrivals. Full blocks
have no intentional delay. The deadline fires without another Write. A blocked RS
window can delay actual dispatch beyond2ms; this is explicitly NOT a2ms network
timeout. No priority inference from22/34 and no ciphertext deletion/reordering.

One existing outbound worker plus the unchanged inbound worker, no per-Write worker.
Four16KiB copied FIFO blocks + one16KiB worker buffer =81920B owned payload storage;
the replaced A reader buffer is65536B, so data-buffer increment is16384B/session.
Only the active Write copies bytes; blocked caller slices remain caller-owned until
their Write returns, with no additional per-call payload copy or internal job queue.
Caller goroutines/stacks and one timer per waiting caller are not disguised as free
memory; the adapter cannot bound the number of concurrent callers created externally.
In the actual Family TLS path, Go TLS serializes ciphertext Write/alerts with its
outbound mutex, so only one such adapter writer is active; no new internal workers
are created for application writers waiting on the existing Family/TLS locks.
Three diagnostic histograms have at most256 distinct keys plus overflow(-1), three
incremental SHA256 states, four ages/lengths, mutex/channels and fixed connection
metadata. Metadata/map/runtime overhead is additional, not included in81920B;
the post-local report records the concrete connection struct size. Shared media
trace storage is unchanged A/B and is reported separately from coalescer memory.

Write success is local copied acceptance, not a carrier write or ACK. FIFO-full
writers wait on deadlines/cancellation; terminal send failures wake waiting calls.
No common lock spans RS SendContext. Explicit LabDrain(ctx) flushes accepted bytes
and waits for existing RS send depth zero, with a finite caller deadline; it is not
proof of application consumption. Ordinary Close is abortive, as in the old bridge.
Application completion is established by receiver counts/body hashes and the
within-run accepted→submitted→opposite ordered-receive SHA256 equality, not Close.
Explicit drain is the end-of-workload flush; shutdown itself performs no hidden
flush. Handshake and close_notify are covered locally, with dynamic TLS sizing on.

T pairs share binary`{json.loads((WORK/'build.json.v1').read_text())['binary_sha256']}`.
Initial P pairs share binary`{json.loads((WORK/'build.json.v2').read_text())['binary_sha256']}`. The only non-test v1→v2 source change
allows32B E in the already loopback-only synthetic fixture; packing/Family/RS/media
sources are byte-identical. P32A1(v1) rejected the new32B idle probe before any bulk:
CLIENT_FAILED,0/32B, TCP reset, both ProtocolErrors0. It is excluded, retained with
its reservation, and repeated as P32A1r(v2). No successful T trial was substituted.

Common P harness uses FIN/EOF/Close and includes completion in full_seconds, with
32B idle and one32B concurrent-single control. Both A/B use exactly this workflow.
An initial local abrupt-close test saw a late ProtocolErrors increment; it remains
in local-6.log. It was not classified as a clean pass or hidden by counter reset.
The fixed orderly test passes with both endpoint counters0. The first snapshot did
not retain that failed local increment's category, so exact category is not invented.
Local-2 loopback restriction and build-8 duplicate instrumentation insertion are
also retained; corrected race/loopback tests and successful build-10 precede v2 live.

P8A(v2, unpacked baseline) is separately excluded: after complete64KiB echo body,
NL RS terminated recovery_exhausted. Sequence22/DATA44 had retries1..8, nine local
RTP writes, no matching carrier identity at the client's valid-RTP input; head age
~9.1s. Both Mux ProtocolErrors stayed0. No encrypted Mux kind is inferred from44B
and no exact SFU/lower-path drop owner is claimed. This is NOT the32B fixture bug
or a clean baseline. One fixed-parameter retry P8Ar is retained alongside it, not
used to erase the failed session or restore its budget. No retry/age limits changed.

Late review also found shutdown warnings in P32B1 and P8Ar: all seven bodies and
ALL accepted ciphertext bytes reached the opposite ordered bridge, but NL retained
its last DATA awaiting ACK and later reached recovery_exhausted during teardown.
P32B1 sent882/released881; P8Ar sent1161/released1160. Each last DATA has nine local
writes and one matching received/ordered/assembled frame; this is unlike P8A's
absent data. These are body-complete performance observations, NOT clean shutdown
acceptance; the table retains them explicitly rather than silently selecting them.

The helper LabDrain incorrectly treated terminal-reset SendDepth0 as successful
drain. A local regression reproduced this false success. V3 checks terminal status
even at depth0, drains before (not after) P abort and gives BOTH A/B a fixed finite2s
passive ACK settlement with the reader alive. It does not change the coalescer
worker, RS limits, media policy, ALPN or ciphertext. New clean P8A3/P8B3 use binary
`{build['binary_sha256']}`; both policies use this same common teardown.
Final gates check ReleasedBlocks==DataSent on both peers, not just empty reset
state. These2s are in the controller's complete-phase duration, not smuggled into
per-request useful bytes. Request timing already includes body/FIN/EOF/stream Close.
The v3 strict-helper test and physical P8 pair validate the repair; old outcomes
and hashes remain unchanged. No application speed claim is based on this helper fix.

### Local correctness and formation

Real Family TLS tests: A/B0/B2 with8/16 and32/32,200 sequential16KiB application
Writes each direction plus mixed1/22/34/16383/16384/16385/32768/65536/7B bodies.
Each body is byte-exact and SHA256 checked; concatenated TLS input is compared to
unique ordered RS payload and opposite bridge bytes inside the SAME session.
No deterministic TLS randomness or comparison between independent ciphertexts.
Local full pattern: A~627–628 DATA versus B0~211–213 and B2~211–212, including
handshake/mixed tails; B2 chosen for the bounded lone-tail guarantee with repeatable
full-block formation, not selected from a live timer sweep. B0 also flushes a lone
tail without a future Write. Local legacy B2↔A passes both directions at both windows.
Loss/reorder/duplicate, ACK loss, slow consumer/full window, copied slice ownership,
partial n/deadline, late underlying failure, close/cancel/write/timer races, idle
request-response, handshake failure and bidirectional TLS close_notify pass.
Real authenticated Mux WINDOW_UPDATE releases a stopped bulk producer with no new
application Write; exact body and small subsequent response pass, counters0.
In-memory small idle request→response medians under race: A0.335289ms,
B0=1.363090ms, B2=4.807704ms (eight per policy, local-10.log). B2 costs
about4.472415ms versus A here, consistent with two directions of bounded tail
coalescing, not evidence of a zero-latency optimization. These are not live RTTs.

'''
    local=[item for item in log_objects(WORK/'local-11.log') if 'unique_data' in item]
    text+=table(['Policy','Effective window','Legacy peer','Direction','TLS Writes','TLS records','Unique DATA','B/slot','DATA<16KiB','Flush causes'],[[item['policy'],item['window'],item['legacy'],item['direction'],item['packing']['Writes'],sum(item['packing']['Records'].values()),sum(item['unique_data'].values()),number(sum(int(size)*count for size,count in item['unique_data'].items())/sum(item['unique_data'].values())),sum(count for size,count in item['unique_data'].items() if int(size)<16384),str(item['packing']['Flush'])] for item in local])+'\n\n'
    post=log_objects(WORK/'post-local-3.log')
    text+='### Local post-enqueue stall, calibration and memory\n\n'
    text+='The first post-local fixture wrongly blocked SendContext for2.2s, exceeding the existing2s enqueue deadline; all four cases failed, retained in post-local-1.log/post-local-source.v1. It was repaired to model a bounded256-message queue accepting immediately, then pause its first bulk **actual write** for2.2s. This is a controlled post-enqueue boundary, not a complete RTP/fragment-queue emulator. Corrected post-local-2/3 pass with byte-exact delivery and bounded staging at both windows. No queue-retry patch was added.\n\n'
    rows=[]
    for item in post:
        if 'before_first_actual_carrier_write' not in item:continue
        stats=item['before_first_actual_carrier_write'];rows.append([item['policy'],item['window'],stats['SendDepth'],stats['BufferedBytes'],stats['Retransmissions'],stats['RetransmittedBytes'],item['packing']['MaxQueueBytes'],item['complete']])
    text+=table(['Policy','Window','Retained slots','Retained B','Retries before first bulk write','Retry payload B','FIFO max B','Exact completion'],rows)+'\n\n'
    text+='**A real remaining risk:** packing does not increase the observed pre-write retry attempts (16 at window8,64 at32), but larger occupied slots multiply queued retry bytes. Thus the requested no-amplification condition is NOT confirmed for bytes. Per-message retries/age and queues remain bounded, but this is a product-admission blocker, not a hidden queue-retry fix. The controlled2.2s pause is longer than normal dispatch and does not establish physical-loss causality.\n\n'
    text+=table(['Calibration policy','TLS-shaped input B','Seconds','Mbit/s'],[[item['policy'],item['bytes'],number(item['seconds']),number(item['mbit_s'])] for item in post if 'mbit_s' in item])+'\n\n'
    text+='Calibration includes incremental SHA256/counters and512 repetitions of16406+34B, no per-block disk logging; these in-memory figures are not network throughput.\n\n'
    memory=[item for item in post if 'memory_policy' in item]
    text+=table(['Policy','Owned payload B','Conn struct B','Three SHA states B','Measured retained heap B/session'],[[item['memory_policy'],65536 if item['memory_policy']=='A' else 81920,item['connection_struct_bytes'],3*item['sha_state_bytes_each'],number(item['retained_heap_bytes_per_session'])] for item in memory])+'\n\n'
    text+='Memory accounting models128 simultaneously retained sessions, all three diagnostic histograms at cap, both pipe ends and two timers/session (coalescing plus one waiting writer), after GC. It includes allocated metadata and map overhead, not just payload; B−A is about16KiB/session. It is a measured retained Go heap model, not a hard RSS bound: existing worker stacks, allocator/GC transient space, unchanged inbound bridge/RS/carrier storage and caller-owned waiting input must also fit the process budget. Actual TLS serializes the adapter Write; arbitrary externally-created waiting callers are not bounded by this adapter. Physical RSS and retained-RS observations below include those broader effects.\n\n'
    text+='''### T — reliable application delivery and slot use

Each successful T trial has256/256 messages,4186112 useful B excluding the32B
diagnostic envelope per message, no corruption. Timing is receiver-monotonic from
requesting the transfer to the final useful message; whole controller duration is
recorded separately and includes setup, drain, confirmation and cleanup.
DATA counts below are whole-session unique DATA, including handshake/control, not
ACK/OPEN/RESET or retransmission attempts. A counts are derived by exact16384-byte
segmentation of successful bridge submissions; B submissions already fit one slot.

'''
    rows=[]
    for name in tnames:
        phase=phases[name];slot=phase['packing']['server'];endpoint=phase['endpoints']['server'];stats=slot['stats'];rs=endpoint['reliability']
        rows.append([name,phase['config']['Packing'],phase['config']['SendWindow'],number(phase['received']['last_seconds']),number(phase['received_mbit_s_to_last']),stats['Writes'],sum(stats['Records'].values()),slot['data_count'],number(slot['bytes_per_slot']),slot['short_count'],slot['small_256_count'],rs['RetransmittedBytes'],number(endpoint['waits_seconds'].get('ReadyFullNS'))])
    text+=table(['Phase','Packing','Effective','Seconds','Mbit/s','TLS Writes','TLS records','Unique DATA','B/slot','DATA<16KiB','DATA≤256B','Retry payload B','Ready-full s'],rows)+'\n\n'
    text+=table(['Contrast','B/A goodput change %'],[[label,number(value)] for label,value in gains.items()])+'\n\n'
    text+='### P — Mux64 + Family TLS, separate windows\n\n'
    text+='Each body-complete P trial: single4MiB download, parallel2×2MiB download,64KiB echo,64KiB reverse and two32B controls; all seven bodies/checks complete. P32B1/P8Ar retain shutdown warnings and are excluded from clean completion acceptance. Parallel time is the union from first start to last completion, not summed per-stream time. Every endpoint is monitored from Mux creation through final Close; Mux ProtocolErrors stay0.\n\n'
    rows=[]
    for name in pnames:
        phase=phases[name];slot=phase['packing']['server'];single=request(phase,'single')
        rows.append([name,phase['config']['Packing'],phase['config']['SendWindow'],number(single['full_seconds']),number(single['goodput_mbit_s']),number(phase['parallel']['seconds']),number(phase['parallel']['goodput_mbit_s']),slot['data_count'],number(slot['bytes_per_slot']),slot['short_count'],slot['small_256_count']])
    text+=table(['Phase','Packing','Effective','Single s','Single Mbit/s','Parallel s','Aggregate Mbit/s','NL unique DATA','B/slot','DATA<16KiB','DATA≤256B'],rows)+'\n\n'
    text+=table(['Contrast','Single B/A %','Aggregate B/A %'],[[label,number(value['single']),number(value['parallel'])] for label,value in pgains.items()])+'\n\n'
    text+=table(['Phase','Client terminal/sent/released','NL terminal/sent/released','Final ACK proof'],[[name,str(phases[name]['reliable_final']['client']),str(phases[name]['reliable_final']['server']),phases[name]['shutdown_ack_proven']] for name in tnames+pnames])+'\n\n'
    text+='Rows cancelled with outstanding ACKs prove peer byte receipt through matching ordered-stream hashes, but not full sender acknowledgement before abort. Recovery-exhausted rows additionally fail clean session completion. Only the v3 P8 pair is claimed as validation of the repaired explicit-drain/ACK gate. P32 performance is not repeated after that repair; it already showed no repeated gain.\n\n'
    text+='Final clean P8 single/aggregate improves in one matched pair, but the aggregate baseline also varies substantially between v2 and v3 sessions. It is an observation, not repeatable product acceptance. P32 ready-window pressure falls sharply while application throughput barely improves or regresses; Mux64/product-like supply/credit is the next distinguishing boundary. Exact per-stream credit-ready duration is not exported, so no precise fraction of time is assigned to it.\n\n'
    text+='T is intentionally a different source shape from the product-like P writer, which already batches plaintext. Gains are not transferred between these tables and are not claimed as TLS CPU savings. No A8→B32 comparison is used as a packing-only effect.\n\n### Small-message latency and queues\n\n'
    rows=[]
    for name in tnames:
        phase=phases[name];rows.append([name,number(phase['idle_rtt_median_s']),number(phase['loaded_rtt_median_s']),phase['received'].get('unanswered_probes'), '32B probe medians; no one-way inference'])
    text+=table(['T phase','Idle RTT s','Loaded RTT s','Outstanding at end','Boundary'],rows)+'\n\n'
    rows=[]
    for name in pnames:
        phase=phases[name];idle=request(phase,'small_idle');loaded=request(phase,'small_loaded')
        rows.append([name,number(idle['first_byte_seconds']),number(idle['full_seconds']),number(loaded['first_byte_seconds']),number(loaded['full_seconds'])])
    text+=table(['P phase','Idle first B s','Idle completion s','Loaded first B s','Loaded completion s'],rows)+'\n\n'
    text+='P has one idle and one loaded small request per phase, not a latency distribution. Separate SFU sessions and startup effects limit attribution of these differences to2ms alone.64KiB echo is retained as a workload/control, never renamed pure network RTT.\n\n'
    rows=[]
    for name in tnames+pnames:
        phase=phases[name];endpoint=phase['endpoints']['server'];stats=phase['packing']['server']['stats']
        rows.append([name,stats['MaxQueueBytes'],number(stats['MaxAgeNS']/1e6),number(stats['CoalescingWaitNS']/1e9),number(stats['RSWaitNS']/1e9),number(stats['WriteBackpressureNS']/1e9),number(stats['MaxEligibleDispatchDelayNS']/1e6),endpoint['max_send_queue'],endpoint['max_sampled_assembly_pending'],str(stats['Flush'])])
    text+=table(['Phase','FIFO max B','Oldest max ms','Timer wait s','RS call wait s','FIFO Write wait s','Eligible dispatch max ms','Carrier sampled queue','Assemblies sampled','Flush causes'],rows)+'\n\n'
    text+='Oldest age can include earlier RS backpressure. DeadlineOvershoot is NOT pure scheduler delay. Eligible-dispatch delay excludes the preceding blocked RS call. Different waits overlap and must not be added. Retained/SACKed bytes are not physical bytes in flight. Queue/assembly maxima are sampled, not asserted continuous maxima. Limits256 carrier send queue/16 incomplete assemblies are unchanged.\n\n'
    rows=[]
    for name in tnames+pnames:
        phase=phases[name];endpoint=phase['endpoints']['server'];rs=endpoint['reliability']
        rows.append([name,endpoint['max_retained'],endpoint['max_unconfirmed'],endpoint['max_sacked'],rs['MaxBufferedBytes'],rs['RetransmittedBytes'],number(endpoint['waits_seconds'].get('ReadyFullNS')),phase.get('mux_final',{}).get('server',{}).get('FlowStalls','—')])
    text+=table(['Phase','Sampled retained B','Unconfirmed B','SACKed B','RS buffer high-water B','Retry payload B','RS ready-full s','NL Mux flow-stall count'],rows)+'\n\n'
    text+='Packing can increase actual retained/retry BYTES per slot even with unchanged slot and retry limits. Existing RS maxima remain S8×16384=128KiB/R16×16384=256KiB, or S32/R32×16384=512KiB each; these are additional existing transport bounds, not included in the80KiB coalescer storage. The table exposes observed buffering rather than calling the buffer increase free. Mux flow-stall counts are exported; precise NL per-stream credit-ready duration was not exported in this harness and is not invented. The separate controlled pre-local-write stall test is retained in post-local logs; queue-retry semantics were not changed.\n\n'
    text+='### Resources, paths and limits\n\n'
    rows=[]
    for name in tnames+pnames:
        phase=phases[name];endpoint=phase['endpoints']['server'];paths=phase['endpoints']['client']['selected_paths'];remote=sorted({value.get('remote',{}).get('ip','?') for value in paths});rows.append([name,','.join(remote),number(endpoint.get('cpu_user_s')),number(endpoint.get('cpu_system_s')),endpoint.get('max_rss_kib'),number(endpoint.get('thread_peak_cpu_one_core_percent')),endpoint.get('cgroup_delta',{}).get('throttled_usec'),number(endpoint.get('host_steal_percent'))])
    text+=table(['Phase','Linux selected SFU IP','NL user CPU s','NL sys CPU s','NL max RSS KiB','Peak thread %core','Cgroup throttle µs','Host steal %'],rows)+'\n\n'
    text+='Same NL host and Linux network; every phase has its own media session/room. Full selected publisher/subscriber ICE paths, both configurations, source inventory, hashes, resources and monotonic boundaries are retained. CPU includes setup/drain/export, not pure TLS processing. No RU migration or host CPU ceiling is inferred. The wire ledger counts each peer outgoing RTP/RTCP including retransmits plus conservative packet/tail allowance, not receiver RX again; STUN/signaling are not media bytes.\n\n'
    text+='### Decisions and next product gate\n\n'
    decisions=[
        ['BYTE_STREAM_PRESERVED','CONFIRMED for completed bodies / local fault tests','Both-direction same-session SHA256 accepted=submitted=ordered peer; failed attempts remain separate.'],
        ['BOUNDED_FLUSH_AND_BACKPRESSURE','CONFIRMED within tested contract; retry-byte risk remains','64KiB FIFO +16KiB worker; finite lone-tail flush, deadlines/cancel/failure;2ms coalescing only.'],
        ['RS_SLOT_EFFICIENCY','CONFIRMED','Measured whole-session DATA/bytes per slot, including new small tails; no deletion of22/34.'],
        ['T_STACK_GAIN','CONFIRMED in tested pairs',str({key:round(value,3) for key,value in gains.items()})],
        ['P_SINGLE_AND_AGGREGATE_GAIN','NOT_CONFIRMED as repeatable P32 gain; one positive clean P8 pair',str({key:{field:round(value,3) for field,value in values.items()} for key,values in pgains.items()})],
        ['SMALL_REQUEST_LATENCY','LOCAL cost confirmed; LIVE attribution limited','Local B2 RTT median +4.472415ms. Sparse separate-SFU idle/loaded controls do not prove non-regression.'],
        ['LEGACY_COMPATIBILITY','CONFIRMED local protocol/byte-stream interop','B2↔unpacked A,8/16 and32/32, both directions; no new FRS1/ALPN. Installed Android interop NOT_RUN.'],
        ['PRE_WRITE_RETRY_AMPLIFICATION','CONFIRMED for bytes, not attempt count','At2.2s post-enqueue stall, denser slots increase queued retry bytes; product gate remains blocked.'],
        ['PRODUCTION_UNCHANGED','BINARY/FLAGS confirmed; whole-run runtime/profile equality NOT confirmed','No lab production mutation. Each phase stable, but process/invocation/profile hash changed between v2 and v3; cause not established.'],
    ]
    text+=table(['Criterion','Classification','Evidence / limit'],decisions)+'\n\n'
    text+='**Not ready for product admission.** The adapter is usable for the next isolated P-writer/credit and latency experiment; slot efficiency and T gain alone do not justify enabling it. Before product integration: (1) establish graceful admission-stop/drain/error and net.Conn conformance gates; (2) resolve or explicitly bound the observed pre-write retry-byte amplification in a separate one-mechanism experiment; (3) repeat P single/parallel and enough small controls with strict final ACK/protocol checks, synchronized ready-data/credit observations and a prespecified latency threshold. Only after those gates, factor this as per-session policy selected before TLS, default OFF, unchanged peer/ALPN/FRS1 and RS8 defaults. Android/native/mobile interop and revocation/expiry require separate authorization. RS32 remains independently lab-only. No APK, production binary/config or public release is produced here.\n\n'
    text+='### Production readback and all-attempt ledger\n\n'
    text+=table(['First phase','First observed UTC','Last phase','Last observed UTC','PID','Invocation','Profile SHA256'],[[item['first_phase'],item['first_observed_utc'],item['last_phase'],item['last_observed_utc'],item['state']['MainPID'],item['state']['InvocationID'],item['state']['profile']] for item in verification['production_epochs']])+'\n\n'
    text+='Fresh full preflight/final equality is **'+str(verification['production_equal'])+'**; binary/flags equality is true, every phase start/end equality is true, and each displayed A/B pair stays within one observed production epoch. The runtime/profile transition happened between series, outside an active lab phase. Its cause is not established by this evidence; the profile was hashed on its host only; its contents were not inspected/exported, and keys, identity or security state were not copied/reverted. The operator only reads production metadata and starts/stops its namespaced test units. The task made no production deployment, restart or config change; it cannot claim external global state stayed unchanged. Do not compare v2/v3 as if runtime background and teardown were identical.\n\n'
    text+=table(['Attempt','Result/error','Shutdown outcome','Whole controller s','Source reserved B','Media charged B'],[[name,phase['result'].get('error') or 'bodies completed',phase['shutdown_warning'] or 'all DATA ACKed',number(phase['result']['seconds_including_setup_drain_confirmation_cleanup']),phase['reservation']['application_reserved'],phase['result']['wire_charged']] for name,phase in phases.items()])+'\n\n'
    text+=f'''Final readback `{verification['utc']}`: production binary/flags equality; local/remote owned peers,
collectors, units and stages absent; isolated keys/room inputs removed. Provider room
metadata deletion is not supported by this workflow; normal media closure verified.
Client network equality: `{verification['client_network_equal']}`. Full raw results,
failed attempts, all three source revisions, patches, calculations and local tests:
`state-client-build/tls-rs-packing-20261021/`. Private kit SHA256
`{kit['sha256']}`. No push, publication, purchase, migration or user switching.
FEC, carrier fragmentation and QUIC remain later conditional work, not this candidate.
'''
    report=ROOT/'docs/releases/2026-10-20-mesh-capacity.md';previous=report.read_text().split(MARKER)[0].rstrip();patch_file(report,previous+'\n\n'+text)
    evidence=ROOT/'docs/releases/2026-10-20-mesh-capacity.evidence.json';public=json.loads(evidence.read_text());public['tls_rs_packing']=dict(verification=verification,kit=kit,T_gains_percent=gains,P_gains_percent=pgains,criteria=decisions,source=source,wire=wire,attempts=[dict(phase=name,config=phase['config'],completed=phase['result'].get('completed'),error=phase['result'].get('error'),binary=phase['reservation']['binary_sha256']) for name,phase in phases.items()]);patch_file(evidence,json.dumps(public,indent=2)+'\n')
    patch_file(WORK/'report-calculations.json',json.dumps(dict(T=gains,P=pgains,repeated_P32=repeated,completed_body_stream_exact=body_stream_exact,source_MiB=source,wire_MiB=wire),indent=2))
    print(json.dumps(dict(T=gains,P=pgains,repeated_P32=repeated,source_MiB=source,wire_MiB=wire)))

if __name__=='__main__':main()
