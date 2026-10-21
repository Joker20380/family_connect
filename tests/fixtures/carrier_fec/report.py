import collections
import importlib.util
import json
import re
import tarfile
from lab import ROOT, FIX, WORK, SOURCE, digest, inventory, save, write
spec=importlib.util.spec_from_file_location('fec_analyze',FIX/'analyze.py')
analyze=importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)


def main():
    analyze.main()
    analysis=json.loads((WORK/'analysis.json').read_text())
    verification=json.loads((WORK/'verification.json').read_text())
    build=json.loads((WORK/'build.json').read_text())
    phases=analysis['phases']
    assert len(phases)==12 and all(phases[name]['clean'] for name in ['R0','RL','RS','RSF','PL1','PS1','PSF1','PSF2','PS2','PL2'])
    public_phases={}
    for name,row in phases.items():
        endpoints={}
        for side,prefix in [('client',''),('server','server-')]:
            endpoint=row['endpoints'][side]
            events=analyze.prior.records(WORK/name/(prefix+'peer.jsonl'))
            media=[event['entry'] for event in events if event.get('event')=='media']
            transmitted=[event for event in media if event['stage']=='tx']
            control=[event for event in media if event['stage']=='rtcp_tx' and event.get('kind')!='RRblock']
            assert endpoint['trace']['overflow']==0
            assert endpoint['rate']['max_rtp_header']==12
            full_clear=sum(event.get('size',0)+12 for event in transmitted)+sum(event.get('size',0) for event in control)
            ipv6_upper=full_clear+64*len(transmitted)+68*len(control)
            assert ipv6_upper<=row['result']['wire_details'][side]['charged'],(name,side)
            capacity=next(event for event in events if event.get('event')=='capacity_config')
            assert capacity['reliability_config']['SendWindow']==capacity['reliability_config']['ReceiveWindow']==32
            endpoint_keys=['wire','fragment','rate','retry','waits_seconds','max_retained','max_sacked','max_unconfirmed','max_sampled_head_age_seconds','cpu_user_s','cpu_system_s','max_rss_kib','host_busy_percent','host_steal_percent','cgroup_delta','queue_samples','observed_parts','matched_parts','matched_fec_groups','rtp_retransmitted_observed','protocol_errors','trace','small']
            compact={key:endpoint[key] for key in endpoint_keys if key in endpoint}
            compact['all_outgoing']=dict(clear_rtp_rtcp=full_clear,rtp_packets=len(transmitted),rtcp_packets_upper=len(control),ipv6_srtp16_srtcp20_upper=ipv6_upper,accounting_charged=row['result']['wire_details'][side]['charged'])
            compact['actual_config']=capacity
            compact['paths']=[dict(connection=path['connection'],local_type=path['local'].get('candidateType'),remote_type=path['remote'].get('candidateType'),remote_ip=path['remote'].get('ip'),protocol=path['remote'].get('protocol'),rtt=path['pair'].get('currentRoundTripTime')) for path in endpoint['selected_paths']]
            compact['completion']=[event for event in events if event.get('event') in ['p_drained','packing_closed']]
            if row['config']['Mode']!='P':compact['capacity_events']=endpoint['capacity_events']
            endpoints[side]=compact
        public_phases[name]=dict(config=row['config'],clean_complete=row['clean'],source_reserved=row['reservation'],result=row['result'],single_seconds=row['single_seconds'],single_mbit_s=row['single_mbit_s'],parallel_seconds=row['parallel_seconds'],parallel_mbit_s=row['parallel_mbit_s'],small=row['small'],requests=row['requests'],endpoints=endpoints)
    comparisons={}
    for first,second in [('PL1','PS1'),('PL2','PS2'),('PS1','PSF1'),('PS2','PSF2'),('PL1','PSF1'),('PL2','PSF2')]:
        comparisons[second+'-vs-'+first]={key:(phases[second][key]/phases[first][key]-1)*100 for key in ['single_mbit_s','parallel_mbit_s']}
    files={str(path.relative_to(ROOT)):digest(path) for path in FIX.rglob('*') if path.is_file() and '__pycache__' not in path.parts}
    archive=WORK/'carrier-fec-kit.tar.gz'
    assert not archive.exists()
    with tarfile.open(archive,'w:gz') as bundle:
        for name in sorted(files):bundle.add(ROOT/name,arcname=name)
    kit=dict(sha256=digest(archive),files=files)
    save(WORK/'kit.json',kit)
    evidence=dict(status='CLOSED_LAB_NO_PRODUCT_SPEED_ADMISSION',binary_sha256=build['binary_sha256'],parent_binary='c97d4192f3c54396677da09896cd16784c60445ebd9ada633713787eb595148a',build_manifest_sha256=digest(WORK/'build.json'),source_inventory=build['source_inventory'],patch_sha256=build['patch_sha256'],kit=kit,phases=public_phases,comparisons_percent=comparisons,verification={key:value for key,value in verification.items() if key!='network_after'},local_budget=json.loads((WORK/'local-budget.json').read_text()),mtu_readback=json.loads((WORK/'mtu-readback.json').read_text()),local_logs={name:dict(sha256=digest(WORK/name),top_level_passes=len(re.findall(r'^--- PASS:',(WORK/name).read_text(),re.M))) for name in ['local-1.log','local-2.log','admission.log','extra-bounds.log','all-lengths.log']},replay=json.loads((WORK/'replay-final.json').read_text()),preexecution_failure=dict(stage='argument parsing before room/process',source=0,media=0,log='CL-operator.log.preexec'),limitations=['Negotiated SRTP profile is not populated by pinned Pion stats; actual permitted tags are10 or16B, all size/budget bounds use16. SRTCP explicit index adds4B. No guessed cipher.','Endpoint fragment matching, not a physical-network packet-loss attribution; includes closure tails. Every media ring overflow=0.','RS retry event rings are incomplete in P. FCF2 media does not export RS sequence. Pre-local-write/post-ACK causality unknown outside retained subset; no zero substituted.','Six latency samples per condition, no p99/non-regression conclusion.','Separate room/SFU per phase and background host load; no unsynchronized one-way latency.','Common additional media ceiling and retained2ms/frame/33ms nominal timestamp are explicit artificial limits, not optimized construction.','No new binary, deployment, routing, production identity/floor change, public release or push. Lab binary is temporary private code only.'])
    evidence['limitations'][-1]='No new product binary/APK, production deployment, routing, identity/floor change, public release or push. The separately hashed lab binary was temporary private code only.'
    save(ROOT/'docs/releases/2026-10-21-carrier-fec.evidence.json',evidence)
    table=[];controls=[];costs=[];losses=[]
    for name in ['PL1','PS1','PSF1','PSF2','PS2','PL2']:
        row=phases[name];sender=row['endpoints']['server'];receiver=row['endpoints']['client']
        table.append(f"| {name} | {row['config']['FragmentMode']} | {row['single_seconds']:.6f} | {row['single_mbit_s']:.6f} | {row['parallel_seconds']:.6f} | {row['parallel_mbit_s']:.6f} | {row['result']['seconds_including_setup_drain_confirmation_cleanup']:.3f} |")
        idle=row['small']['small_idle']['full_seconds'];loaded=row['small']['small_loaded']['full_seconds']
        controls.append(f"| {name} | {idle['median']:.6f} / {idle['maximum']:.6f} | {loaded['median']:.6f} / {loaded['maximum']:.6f} | 0 / 0 |")
        fragment=sender['fragment'];queue=fragment.get('QueueAgeMaxNS');queue_text=f'{queue/1e6:.3f}' if queue is not None else 'not instrumented'
        costs.append(f"| {name} | {row['result']['wire_charged']} | {sender['retry']['attempts']} / {sender['retry']['retry_bytes']} | {fragment.get('RepairBytes',0)} / {fragment.get('PaddingBytes',0)} | {sender['queue_samples']['max_frames']} / {queue_text} | {receiver['max_rss_kib']/1024:.2f} / {sender['max_rss_kib']/1024:.2f} |")
        match=sender['matched_parts'];metrics=receiver['fragment'];legacy=metrics.get('assembly',{}).get('assembly',{})
        losses.append(f"| {name} | {match['source_not_assembled']} / {match['repair_not_assembled']} | {metrics.get('RecoveredSymbols',0)} / {metrics.get('RecoveredGroups',0)} | {metrics.get('Expired',legacy.get('expired',0))} |")
    contrasts='\n'.join(f"| {name} | {value['single_mbit_s']:+.3f}% | {value['parallel_mbit_s']:+.3f}% |" for name,value in comparisons.items())
    report=f'''

## Carrier fragmentation and FEC — 21 October 2026

**Closed isolated lab: S and SF implemented and physically tested; neither is a
product speed fix.** No further size/k/r/window sweep. The next separate stage is
QUIC **instead of the common ReliableStream**, not over it; no QUIC code here.
Prior T packing gains, non-repeatable additional P packing benefit, credit result
and separate dormant Q1 correctness candidate remain unchanged.

### Exact base, implementation and budget

Parent P-interaction binary `c97d4192f3c54396677da09896cd16784c60445ebd9ada633713787eb595148a`;
new lab binary `{build['binary_sha256']}`.
One binary for all12 physical sessions, no in-series transport patch. Exact source
replay including final gofmt matches the frozen inventory. Source/patch/config,
raw events and receipts: `state-client-build/carrier-fec-20261021/`.
Replay code: [carrier_fec](../../tests/fixtures/carrier_fec/README.md);
kit SHA256 `{kit['sha256']}`.
[Machine evidence](2026-10-21-carrier-fec.evidence.json) preserves every attempt.

Both peers' emitted configs are SendWindow32/ReceiveWindow32; the pinned OPEN
advertises that receive window and checks peer consistency, so effective window
is min(32,32)=32, not a send-only32 claim. P is Family TLS/Mux128, packing OFF,
Q0, payload16384, RTO1s, retries8, MaxAge20s. Existing negotiated CREDIT128 and
plaintext batching are unchanged. This is **not production RS8/LEGACY64**.
No Q1, timebase fix, rejected FIXED4M, new ALPN or provider is silently activated.

Live source reservations **{verification['source_reserved_live']}B / 50.273193MiB**,
outgoing media charge **{verification['media_charged_live']}B / 82.704313MiB**.
Including conservative local reservations64MiB source/128MiB in-memory media gives
114.273193/128MiB source and210.704313/256MiB media. Known newly generated local
test source upper bound57.087365MiB; the local reservation also covers inherited
small regressions. Verification copies are not additional transmitted source.
48MiB P-bulk was reserved before smoke; all six main phases ran without expansion.
Per-transfer180s, request150s, final RS drain10s, worker250s/unit280s limits remain.

### FRAGMENT_WIRE_AND_PACKETIZATION

L retains original24B carrier header and8192B parts. S/SF use explicit incompatible
FCF2 v1:64B header,1024B source symbols. Header contains16B per-phase epoch,
direction, sender/message IDs, original length/CRC, group/symbol position, actual
source count, fixed symbol size and symbol/header CRC. Every part is independently
locatable without part0 or RTP SSRC/sequence stability. No new RS DATA sequence;
only a fully assembled, whole-CRC-checked original message reaches RS/TLS.

Pinned Pion outbound clear-RTP MTU1200; fixed RTP header12, VP8 descriptor1/3/4B,
fake VP8 interframe17B. Payload capacity is1188 before descriptor,1184 at the
largest descriptor. Live observed RTP header12 (no extensions), S/SF full packet
1121B including descriptor4; L max1200B. A16448B RS carrier message produces:

| Variant | Source/repair parts | RTP count | Carrier bytes before VP8 | Mandatory frame pauses |
|---|---:|---:|---:|---:|
| L |3/0|15 =7+7+1|16520|6ms|
| S |17/0|17|17536|34ms|
| SF |17/6|23|24064|46ms|

The exact negotiated SRTP cipher is **not exposed/populated** by pinned Pion
transport stats. Supported profiles use10B SHA1-80 or16B AEAD tags; no cipher is
invented. Size/budget safety uses16B. With observed no RTP extensions, IPv4/UDP
sizes are at most1165B S/SF and1244B L; IPv6 bounds1185/1264B. SRTCP adds its4B
explicit index. Post-series route/link readback for every selected IPv4 SFU shows
MTU1500 at both ends. This establishes packet-size margin, not a claim of measured
path-MTU discovery or a kernel IP-fragmentation trace. RTP MTU was not raised.

### FRAME_RATE_AND_ARTIFICIAL_LIMITS

Original2ms sleep after **every** frame and33ms nominal RTP duration (2970 ticks)
remain in all modes. No S-only pause removal. Thus500 frames/s is an ideal ceiling,
before scheduler/write/queue overhead: full1024B S symbols imply at most4.096Mbit/s
source; full8+2 groups at most3.277Mbit/s, worse for short final groups. S/SF also
advance the nominal timestamp more times per original message. These are explicit
construction limitations, not proof of an optimized fragmentation/FEC transport.

All main L/S/SF additionally share a conservative outgoing byte-service ceiling
1,048,576B/s, including repair, RTP retries and RTCP. This is not FIXED4M. Existing
2ms frame pacing remains the tighter S/SF limiter. R0 disables only this new
ceiling to retain a short original-L bridge.128KiB R0/RL complete8/8, receiver
last-byte times1.214118/1.239959s; sender-confirmed intervals1.640424/2.869691s on
their own clocks. Different SFUs and one pair preclude attributing all difference
to this ceiling. Do not subtract inter-host timestamps or compare to an old best P.

### S_CORRECTNESS and FEC_PROFILE_AND_RECOVERY_BOUNDS

Local real Pion packetization proves one RTP/part for S/SF. Tests cover byte-exact
0..65536B boundary/sample sizes, with allocation-free geometry checked for **every
one of65537 lengths**; no unsupported giant payload. First/middle/last loss,
reorder, identical/conflicting duplicates, invalid length/index/profile, corrupt
symbol/whole CRC, wrong epoch/direction, silence/expiry, cancel/close and race pass.
The legacy duplicate-poisons-build behavior is unchanged in L. S's separate
duplicate-idempotence rule is explicit, tested, and not credited as a size-only
speed improvement; live duplicate-conflict counters are zero.

Bounds:16 pending messages,80 symbols/message,1,310,720 held symbol bytes,4096
recent/pending IDs,10s lifetime; no legacy bitmap used for S completion. Max-size
pressure test holds16 incomplete messages at1,032,192B S /917,504B SF, refuses the
17th, and releases all on expiry/close. Header validation/CRC are bounded before
large allocations/decode. No memory credit or flow control is disabled.

SF uses verified MIT `klauspost/reedsolomon v1.12.4` plus cpuid/v2 v2.2.8, not custom
cryptography. [License/sums](../legal/DEPENDENCY_LICENSE_AUDIT.md#isolated-carrier-fec-laboratory--2026-10-21).
One shortened systematic up-to8+2 profile, one codec worker. Groups never cross
messages/epochs/directions or wait for future input. Last group uses its actual
1..8 source count plus2 repairs, with zero-padding only for coding. Messages of
0..1024B bypass repair, so small ACK/control never waits for group fill. Source
delivery does not wait for repair once complete. All one/two erasure combinations
of10-symbol groups,0..2 erasures at multiple message sizes,3+ erasures, repair
loss, whole absent groups, short tails and corrupt reconstruction are tested.
Insufficient FEC leaves normal RS recovery; CRC does not replace Family TLS.

Nine bound-Pion RS32 tests (L/S/SF × fast/one-RTP-loss/slow consumer) pass under
race with196608B each. One-loss retries are12/1/0 for L/S/SF in that fixture,
not claimed comparable live loss probabilities. Independent seeded model uses
seeds11/29/47,1.5% packet Bernoulli loss and a separately named packet-triggered
6ms burst model, common1MiB/s serialization plus2ms/frame.24 messages/mode/seed:
iid L19/18/22, S18/16/21, SF24/24/24 completed; burst L16/14/16, S16/14/16,
SF22/22/23. SF consumes more modeled time/media. These are recovery-model results,
not an SFU replay or P speedup. Raw loss and residual missing messages are retained.

### Physical attempts: smoke, R32 and P

Pre-execution CL argument error created no room/process and sent0B; retained as
`CL-operator.log.preexec`. Actual C smoke L18/20, S19/20 complete bodies, corrupt0;
missing IDs L[10,11], S[7]. Observation deadline expires normally, but these are
**partial raw delivery**, not clean full-message acceptance. S showed141/141
identified outgoing parts in one RTP each. R0/RL/RS/RSF all deliver8/8 exact128KiB;
S/SF receiver last-byte times2.217346/2.677176s, sender confirmed2.975111/2.254888s.
Repair transport via ordinary VP8 is observed, not assumed from local tests.

Main order L→S→SF→SF→S→L, one4MiB stream and two2MiB streams per phase:

| Phase | Mode | Single s | Single Mbit/s | Parallel s | Aggregate Mbit/s | Whole phase s |
|---|---|---:|---:|---:|---:|---:|
{chr(10).join(table)}

| Paired contrast | Single | Aggregate |
|---|---:|---:|
{contrasts}

**S loses to L in both orders. SF single is lower than S in both orders; its
aggregate sign reverses. No repeatable useful P benefit is established.**

### P_SINGLE_AGGREGATE_AND_LATENCY

Identical six32B idle and six32B loaded sequential echoes,100ms gaps, loaded start
1s into single bulk. All six loaded probes are wholly inside bulk in every phase.
All72 small responses succeed. Median / observed maximum, seconds; **not p99**:

| Phase | Idle median/max | Loaded median/max | Errors idle/loaded |
|---|---:|---:|---:|
{chr(10).join(controls)}

Latency is mixed; non-regression is not accepted. All17 application operations
per P phase have exact sizes/SHA256 and corresponding both-end stream byte counts.
Both RS drains have empty terminal state, all DATA acknowledged, matching ordered
ciphertext, Mux128 on both ends, no protocol errors through final closure.

### MEDIA_COST_AND_RAW_LOSS; resources

Whole-phase outgoing charge includes both directions, controls, repair and all
retries, not equal source-rate plus unbudgeted parity. Complete rings permit
independent full clear RTP/RTCP sums and IPv6+SRTP16/SRTCP20 upper bounds; each is
below the charged value. The inherited64B allowance slightly undercounts individual
AEAD SRTCP by4B, but explicit recomputation fits the reserved closing margin by
over60kB/endpoint in P; no budget overrun or hidden zero overhead. Logical coding
padding is reported separately, not added again to repair-inclusive wire bytes.

| Phase | Charged media B | NL RS retries / bytes | NL repair / coding padding B | Peak queue frames / max age ms | RSS Linux/NL MiB |
|---|---:|---:|---:|---:|---:|
{chr(10).join(costs)}

SF sends3,688,448/3,506,176B repair from NL, plus reverse-direction repair, while
recovering only2 missing source symbols in each P phase (1/2 groups). Shortened
tails make real parity overhead materially greater than a blanket25% assumption.
For example16448B needs6144 repair bytes (37.35%) plus headers and960 coding-pad
bytes. No changing source rate is disguised as equal bandwidth.

| Phase | NL source/repair parts not assembled at Linux | Recovered source symbols/groups | Linux expired partial messages |
|---|---:|---:|---:|
{chr(10).join(losses)}

These are whole-session endpoint-ID matches, including shutdown tails, not a
claim that a physical network dropped that many packets. For S/SF one part maps
to one RTP. L part loss may follow any one of several RTP losses. All media trace
overflows are0; no clock subtraction used. In each SF phase **90 fully transmitted
protected groups with missing source exceeded two absent symbols**; only1/2
source-missing groups fit the two-erasure budget. Complete group histograms are
retained. This explains why local erasure repair is real but has little useful
opportunity under these observed clustered erasures. No reordering/interleaving,
larger r, or alternate size is silently tried.

NL encode CPU is50.7–58.0ms per S/SF whole phase; actual recovered decode CPU is
21.9/26.3 microseconds at Linux. Whole-process CPU Linux/NL: PL1 5.299/5.649s,
PS1 5.792/6.275s, PSF1 6.748/6.912s, PSF2 6.031/6.693s, PS2 6.021/6.280s,
PL2 4.921/5.953s. NL queue peaks hit256 frames in SF, age660/664ms; finite and
drained, not a reason to increase offered load. Ready-window waits and head stalls
remain in evidence and overlap other waits; they are not summed as elapsed time.
NL background busy28.18–34.63%, steal0.219–0.312%, throttling0–57.4ms. Each phase
uses another SFU; selected UDP/host paths and resource samples are retained.

### RETRY_ACCOUNTING and closure

Q0 stays common throughout. No Q1 correctness transition was needed/activated.
Repair overhead is explicit, and NL RS attempts/bytes decrease in SF, but **lower
retries with lower goodput is not a speed fix**. Only2 repaired symbols/phase do
not causally explain the entire retry-count difference across independent SFUs.
Maximum observed S/SF frame queue age remains below1s RTO; this alone is not proof
of no premature retries. Incomplete RS rings and missing FCF2 physical-to-RS
sequence export prevent exhaustive pre-first-write/post-ACK attribution. Retained
subsets show no retry scheduled after first ACK; early-local/late-ACK causes remain
unknown where unobserved. No retry limit or payload of assigned RS sequences changed.
Actual repeated RTP identities are1 per endpoint in P except PL1 NL3, separate
from RS re-encodings and FEC repair. Their timestamps/body hashes match.

At the two-end completion barrier PS1 Linux still held2 obsolete partial carrier
attempts/7168B and PSF1 NL1/13312B; all application/RS contracts were already
confirmed. They are reported, not silently called zero, and normal final close
purges them; final S/SF Held/Pending0 and Closed=true. All carrier send queues0.
All P `packing_closed: use of closed network connection` warnings occur **after**
the valid two-end barrier; no terminal reset is turned into LabDrain success.
No protocol-error attempt is used for acceptance, and raw partial smokes remain
partial in the common table/evidence rather than disappearing from statistics.

Final readback `{verification['utc']}`:24 owned peers,12 isolated units/stages/
collectors and ephemeral identity sets removed. Normal peer/WebSocket closure;
provider room-metadata deletion is not supported/claimed. Addresses/rules/routes
match after removing only DHCP lifetime countdowns. Production PID429617,
invocation9922c6ee79f64e94aa87e8ec47313f5c, binary734b6ca6…/profile66096048… and
OFF/LEGACY64 flags match every before/after readback. No renewal/timer action,
reset, rollback, production keys/floors/routing edit, APK, publication or push.
Bootstrap96/gateway1011/A0 and public/invitation/catalog versions remain unchanged.

| Requested decision | Result |
|---|---|
| FRAGMENT_WIRE_AND_PACKETIZATION | Explicit FCF2,1024B S, one RTP/part locally and live; exact clear sizes, bounded encrypted/IP sizes; negotiated cipher unknown. |
| FRAME_RATE_AND_ARTIFICIAL_LIMITS | Same2ms/frame,33ms nominal clock and common1MiB/s ceiling; original-L bridge separate. |
| S_CORRECTNESS | Local bounds/race/byte-exact PASS; physical R/P complete; raw C partial preserved. |
| FEC_PROFILE_AND_RECOVERY_BOUNDS | Shortened up-to8+2 RS verified; all two-erasure combinations; beyond-r falls back to RS. |
| S_VS_L_EFFECT | P single and aggregate lower in both orders. |
| SF_VS_S_EFFECT | Tiny real live recovery; single lower, aggregate sign mixed; higher wire cost. |
| P_SINGLE_AGGREGATE_AND_LATENCY | Six complete P phases;72 small responses; no P speed or latency non-regression admission. |
| MEDIA_COST_AND_RAW_LOSS | Repair/padding/headers/retries separate; erasures preserved; clustered groups mostly exceed r. |
| RETRY_ACCOUNTING | Q0 unchanged; full attempts/bytes known, complete causal timing unavailable; no hidden Q1. |
| PRODUCTION_UNCHANGED | Verified read-only snapshots and cleanup; no product admission. |

**Close this size/profile, preserve the negative result.** Next separate stage:
QUIC replacing the common ReliableStream, not layered on it. Do not implement it,
expand hosting, change Android/users or tune RS/Mux windows in this task.
'''
    path=ROOT/'docs/releases/2026-10-20-mesh-capacity.md'
    assert '## Carrier fragmentation and FEC — 21 October 2026' not in path.read_text()
    write(path,path.read_text()+report)
    status='''## Carrier S/SF,21.10 — completed lab; no P speed admission

Exact P-interaction parent c97d4192…; one lab cdb583b6… binary, source replay exact.
RS32/32 + Mux128, packing OFF/Q0; L legacy8192, S1024/FCF2, SF shortened8+2.
Original2ms/frame and33ms nominal clock retained; common1MiB/s media ceiling,
with separate short original-L bridge. S/SF each one RTP, clear max1121B.
Local byte-exact/bounds/race,0..65536 geometry, erasure/duplicate/corruption/close
and actual Pion/RS tests pass. FEC implemented, not deferred; new MIT deps lab-only.
12 live sessions: raw C L18/20,S19/20 partial retained; four R128KiB8/8 complete;
six P phases L/S/SF/SF/S/L all exact body/ACK/ciphertext/terminal proof, protocol0.
Single Mbit/s1.326/1.254/1.220/1.216/1.264/1.451; aggregate
2.666/1.900/2.032/1.999/2.140/2.270. S loses both orders; SF single loses to S,
aggregate +6.910/−6.584%, not repeatable.72 small replies succeed; no p99 or
latency non-regression. SF repairs2 symbols/phase, but90 groups/phase exceed r;
3.69/3.51MB NL repair and greater queue/wire cost do not yield useful P speed.
Q0 unchanged; RS retries drop but timing classification remains incomplete,
not a hidden Q1 fix or packet-loss-rate claim. Minor RTP retransmissions separate.
Live50.273193MiB source/82.704313MiB media; with conservative local reservations
114.273193/128 and210.704313/256MiB. All24 peers/12 units/stages/collectors and
ephemeral profiles gone.08:17:22UTC readback stable production PID429617,
734b6ca6…/66096048…/OFF/LEGACY64; client routes/addresses unchanged except DHCP
lifetimes. Normal session close, provider room-metadata deletion not claimed.
Bootstrap96/gateway1011/A0/public/invitation artifacts unchanged; no APK/deploy/
push/renewal/reset/rollback/user migration. Historical renewal cause still unknown.
Closed tested fragmentation/FEC profile; NEXT separate QUIC instead of common
ReliableStream, not over it. No QUIC or more tuning/load started in this task.
[Full result](releases/2026-10-20-mesh-capacity.md#carrier-fragmentation-and-fec--21-october-2026),
[evidence](releases/2026-10-21-carrier-fec.evidence.json), capsule carrier-fec-20261021.

'''
    path=ROOT/'docs/STATUS.md';text=path.read_text();heading,rest=text.split('\n\n',1);write(path,heading+'\n\n'+status+rest)
    path=ROOT/'docs/PLAN.md';text=path.read_text();marker='## Current engineering priority / Текущий critical path\n\n'
    plan='''### Fragmentation then FEC — closed; separate QUIC replacement next,21.10

- DONE: L/S/SF implemented on pinned local P baseline, effective32/32/Mux128,
  packingOFF/Q0; independently assembled1024B FCF2 parts and shortened8+2 FEC.
  Fixed2ms/frame/33ms clock retained, common media budget includes parity.
- PASS: bounds/invalid/duplicate/expiry/cancel/close/race, full-length geometry,
  real Pion/RS, two-erasure recovery, ordinary RS fallback and strict LabDrain.
- COMPLETE:12 isolated physical sessions; raw18/20 and19/20 partial smokes
  preserved, R8/8 all modes, six exact P phases in forward/reverse order.
- NEGATIVE: S below L in both P contrasts; SF single below S, aggregate sign
  changes.2 symbols recovered per SF phase,90 groups beyond r; extra wire/queue
  cost, no repeated useful P speed gain.72 small probes are not p99/non-regression.
- CLOSED: all processes/stages/profiles removed, production96/1011/A0/LEGACY64
  unchanged. No APK, deployment, public release, push, renewal action or migration.
- NO MORE SWEEP: do not continue fragment-size/k/r/flush/window selection here.
  Next independently authorized stage is QUIC **instead of** the common
  ReliableStream, not on top of it. No QUIC implementation in this task.
- LIMITATIONS retained: exact negotiated SRTP tag unavailable (safe bound16B),
  incomplete causal RS retry timing, per-phase SFU/background changes; no product
  admission. Q1 remains a separate correctness candidate, inactive in all modes.
  [Report/evidence](releases/2026-10-20-mesh-capacity.md#carrier-fragmentation-and-fec--21-october-2026).

'''
    assert marker in text;write(path,text.replace(marker,marker+plan,1))
    path=ROOT/'docs/README.md';text=path.read_text();heading,rest=text.split('\n\n',1)
    write(path,heading+'\n\n[Carrier fragmentation/FEC,21.10](releases/2026-10-20-mesh-capacity.md#carrier-fragmentation-and-fec--21-october-2026): implemented L/S/SF, local and forward/reverse NL→Linux P completed; no repeatable useful speed gain, production unchanged; next separate QUIC replacement.\n\n'+rest)
    print('REPORT SAVED',kit['sha256'])


if __name__=='__main__':main()
