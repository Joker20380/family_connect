"""Reproducible public projection; no credentials, private profiles or room URLs."""
import json

from prepare import ROOT, WORK, patch_file


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(str(value) for value in row)+' |' for row in rows])


def main():
    summary=json.loads((WORK/'summary.json').read_text())
    verification=json.loads((WORK/'verification.json').read_text())
    build=json.loads((WORK/'build.json').read_text())
    phases=summary['phases']
    assert verification['status']=='COMPLETED_WITH_P816_PROTOCOL_WARNING_NOT_PRODUCT_ADMISSION'
    kit=json.loads((WORK/'kit.json').read_text())
    raw=[];loss=[];reliable=[];product=[];windows=[];resources=[];paths=[];public={}
    for name,item in phases.items():
        config=item['config'];server=item['endpoints']['server'];client=item['endpoints']['client']
        sender=client if config['Reverse'] else server
        receiver=server if config['Reverse'] else client
        state=sender.get('reliability') or {};perf=state.get('Performance') or {}
        received=item['received'] or {}
        assembly=receiver['carrier']['Delivery']['assembly']
        rtt=item.get('loaded_rtt_median_s')
        if config['Mode']=='C':
            raw.append([name,config['Rate']*8/1e6,item['sent']['offered_bytes'],item['sent']['count'],f"{sender['carrier']['Media']['SamplesWritten']}/{sender['wire']['rtp_packets']}",sender['wire']['rtp_bytes'],f"{received['count']}/{received['expected']}",received['useful_bytes'],f"{item['during_offered_interval_mbit_s']:.6f}",f"{item['received_mbit_s_observation']:.6f}"])
            loss.append([name,receiver['carrier']['Media']['RTPReceived'],assembly['rtp_gaps'],receiver['carrier']['Media']['FramesReceived'],assembly['fragments'],assembly['completed'],assembly['expired'],assembly['capacity'],received['late_after_offer_seconds'],f"{received['last_seconds']:.6f}/{received['observation_seconds']:.6f}",f"{rtt:.3f}"])
        elif config['Mode']!='P':
            reliable.append([name,config['Mode'],received['useful_bytes'],f"{received['count']}/{received['expected']}",f"{received['last_seconds']:.6f}",f"{item['received_mbit_s_to_last']:.6f}",state['RetransmittedBytes'],f"{sender['waits_seconds']['ReadyFullNS']:.6f}",'-' if rtt is None else f'{rtt:.3f}'])
        else:
            single=next(row for row in item['requests'] if row['name']=='single')
            product.append([name,f"{config['SendWindow']}/{config['ReceiveWindow']}",f"{single['full_seconds']:.6f}",f"{single['goodput_mbit_s']:.6f}",f"{item['parallel']['seconds']:.6f}",f"{item['parallel']['goodput_mbit_s']:.6f}",f"{sender['waits_seconds']['ReadyFullNS']:.6f}",state['RetransmittedBytes'],'5/5',max(row['mux_after']['ProtocolErrors'] for row in item['requests'])])
        if name in ['R816a','R832a','R1632a','R3232a','R3232b','R1632b','R832b']:
            pair=f"{config['SendWindow']}/{config['ReceiveWindow']}"
            windows.append([name,pair,pair,perf['EffectiveWindow'],f"{item['received_mbit_s_to_last']:.6f}",f"{sender['max_retained']}/{sender['max_unconfirmed']}/{sender['max_sacked']}",f"{sender['max_sampled_head_age_seconds']:.3f}",f"{receiver['max_sampled_assembly_pending']}/{assembly['capacity']}"])
        gc=server.get('gc_resources',[])
        last_gc=gc[-1] if gc else {}
        cpu=server['cpu_user_s']+server['cpu_system_s']
        resources.append([name,f"{cpu:.3f}/{server['resource_seconds']:.3f}",f"{server['thread_peak_cpu_one_core_percent']:.2f}",f"{server['cgroup_delta']['throttled_usec']/1000:.3f}",f"{server['host_steal_percent']:.3f}",server['max_rss_kib'],f"{last_gc.get('gc_pause_total_ns',0)/1e6:.3f}",f"{server['max_send_queue']}/{client['max_receive_queue']}"])
        selected={side:[dict(connection=pair['connection'],local=pair.get('local'),remote=pair.get('remote')) for pair in endpoint['selected_paths']] for side,endpoint in item['endpoints'].items()}
        sfu=sorted({pair['remote']['ip'] for endpoint in item['endpoints'].values() for pair in endpoint['selected_paths'] if pair.get('remote')})
        paths.append([name,', '.join(sfu),f"{item['result']['seconds_including_setup_drain_confirmation_cleanup']:.3f}",item['reservation']['application_reserved'],item['result']['wire_charged']])
        public[name]=dict(config_both_ends=config,source_binary_sha256=item['reservation']['binary_sha256'],room_id_sha256=json.loads((WORK/name/'room-receipt.json').read_text())['id_sha256'],sfu_ips=sfu,result=item['result'],received=received,sent=item['sent'],goodput_mbit_s=item.get('received_mbit_s_to_last'),during_offered_interval_mbit_s=item.get('during_offered_interval_mbit_s'),parallel=item.get('parallel'),requests=[{key:row[key] for key in ['name','size','received','passed','full_seconds','goodput_mbit_s']} for row in item['requests']],endpoints={side:{key:endpoint.get(key) for key in ['wire','histograms','waits_seconds','max_retained','max_unconfirmed','max_sacked','max_sampled_head_age_seconds','max_sampled_assembly_pending','cpu_user_s','cpu_system_s','resource_seconds','cgroup_delta','max_rss_kib','max_send_queue','max_receive_queue']} for side,endpoint in item['endpoints'].items()})
        public[name]['protocol_counters']=[dict(request=row['name'],before=row['mux_before']['ProtocolErrors'],after=row['mux_after']['ProtocolErrors']) for row in item['requests']]
    long=phases['R32sustain'];long_received=long['received']
    outcome=f"""# MESH capacity investigation — phases1–2,20 October2026

**COMPLETED WITH P816 PROTOCOL WARNING: bounded Linux findings; NOT product admission.**
19 independent NL sessions,38 closed peers. No live Android interaction, production
binary/configuration/identity/credentials/floors/directory/routing mutation, push,
publication or RU matrix. The previous host-comparison budget remains closed.

## Conclusions, individually classified

| Question | Classification | Finding |
|---|---|---|
| CARRIER_DELIVERY_ENVELOPE | CONFIRMED at tested points; higher raw rates NOT_CHECKED | C0.5 delivers70/75; two C1 runs134/151 and133/151 after32s. No corruption. Partial-message delivery is not reliable VPN capacity. Rates2/4/8 were not escalated after repeated incomplete delivery. |
| RELIABLESTREAM_COST | CONFIRMED recovery/wait cost; exact causal layer percentage LIMITED by sessions/shape | At matched carrier DATA size and nominal new-DATA rate, Rmatch delivers151/151 with606304 retry bytes; C1b loses18/151. Default full-record R8/16 delivers1.258819Mbit/s completely. This is not a simple “RS subtracts X%” result. |
| TLS_MUX_INCREMENTAL_EFFECT | CONFIRMED record-shape effect; one clean P pair only; pure TLS CPU overhead NOT_ESTABLISHED | T8/16=0.498142; clean P8 single0.584762. Earlier P816 has a protocol warning and is excluded. T creates many22/34-byte RS DATA blocks; P has its existing loopback TCP/Mux batching shape. P32 single0.764793, two-stream aggregate1.367101: not the~3x R-layer gain. |
| WINDOW8_16_32_EFFECT | CONFIRMED in bounded repeated R comparison | Effective8:1.262439/1.331633;16:2.245900/1.607627;32:3.642117/3.643658Mbit/s, all256/256. Same payload/RTO/retry/framing;8/32 is an experimental receive-cap control, not production8/16. |
| REASSEMBLY_CAPACITY_INTERACTION | CONFIRMED local overlap hazard; overflow NOT_OBSERVED physically | Ordered32 messages complete with cap16.32 deliberately incomplete overlapping messages produce32 capacity-rejected fragments and only16 completions. Every physical capacity counter remains0; caps were not raised. |
| CPU_OR_SCHEDULER_LIMIT | NOT_SUPPORTED in tested conditions | Generator/verifier22Gbit/s; full copy/read/verify/counter calibration2.07Gbit/s under race. Owned process CPU, GC and cgroup throttling are small relative to window waits; no basis for blaming1vCPU or moving to RU. |
| BEST_RELIABLE_RESULT | CONFIRMED for the finite tested transfer, not a technology ceiling | R32sustain: {long_received['count']}/{long_received['expected']}, {long_received['useful_bytes']} useful bytes in{long_received['last_seconds']:.6f}s = **{long['received_mbit_s_to_last']:.6f}Mbit/s**, no corruption/capacity overflow. |
| PRODUCTION_UNCHANGED | CONFIRMED gateway readbacks; phone not operated | Same734b6ca6…/PID4126720/invocationc24eee95…/profile hash/OFF/LEGACY64/export-OFF throughout and postflight. No product artifact was installed or distributed. |

The unused-capacity hypothesis has a **specific supported component**: the shared
RS slot window and record shape limit this workload before all available delivery
in the tested media path is used. This does **not** measure a universal carrier
maximum, a precise percentage of unused bandwidth, or Android speedup.

## A — independent carrier messages

C input is16448bytes/message, including32-byte diagnostic envelope. Target rates
are **carrier-input**, not RTP/UDP wire rates. Send schedules last19.738/19.475/
19.738s for finite151/75/151 messages; declared offered observation interval20s.
Local write columns are **whole-peer** WriteSample/RTP-attempt counters including
controls, keepalives and lower retransmits, not falsely relabeled useful messages.

{table(['Phase','Target Mbit/s','Offered carrier B','Enqueued messages','Samples/RTP writes','TX RTP B','Unique messages','Useful received B','Useful by20s Mbit/s','Whole32s observation Mbit/s'],raw)}

All C source/receiver sampled queues end empty, sampled send/receive queue peaks0;
duplicates0, corruption0, CRC failures0, capacity rejects0. Final count uses the
sender's predetermined total, not merely a receiver-reported denominator.

{table(['Phase','RTP reader packets','Sequence-gap events','VP8 frames','Carrier fragments','All complete carrier msgs','Expired partials','Capacity rejects','Late after20s msgs','Last arrival / observation s','Loaded32B RTT median s'],loss)}

Gap events are not lost-packet counts. Carrier totals include32-byte diagnostic
controls; useful-message counts come from independent ID/content validation.
TX/RX differences cannot localize loss to wire versus SFU versus unexported reader/
reorder/VP8 categories. Absence in bounded metadata is not a network-loss verdict.
The12s raw drain exceeds the10s reassembly lifetime; missing IDs mean **not delivered
within this observation contract**, not a claim about arbitrarily late network data.
Late bytes are never added to the20s numerator. Last-arrival goodputs are separately
0.804015/0.420460/0.802386Mbit/s, not reliable completion rates.

C1 missing-group starts on the **planned sender schedule** are0.395,2.369,4.342,
6.316,8.290,10.264s; C1b starts0.526,2.500,4.605,6.579,8.553,10.527s.
Repeated spacing is~1.974–2.105s. Source also emits a decodable keepalive every2s.
This is a discriminating **phase3 hypothesis**, not proof that keepalives cause loss:
exact per-frame send/receive timebase correlation was not exported in this phase.

## B — reliable completion, TLS and product-like workload

R/T goodput uses useful bytes excluding32-byte envelope and receiver-monotonic
start-request→last verified byte. Full controller elapsed times including setup,
drain, confirmation and cleanup are retained below. No clocks of different machines
are subtracted.32-byte probes measure the entire stack round trip, not pure wire RTT.
Retry and ready-full counters are **whole-peer lifetime** counters, including setup
and final control; they are not request-local allocations or additive wall times.

{table(['Phase','Mode','Useful B','Verified messages','Receiver s','Mbit/s','RS retry B','Ready/full s','Loaded32B RTT median s'],reliable)}

Rmatch uses151×16384-byte inputs at124513B/s, yielding151×16448-byte original
carrier DATA at nominal1Mbit/s, matching C1b's carrier work. R's32-byte envelope
leaves16352 useful bytes versus C's16416; reported numerators account for this.
Retransmissions/ACKs are extra wire work, not hidden in original offered rate.
Initial C1→R816a is followed by the **reverse-order** matched Rmatch→C1b contrast;
R816a is uncapped and is not falsely described as the matched offered-rate run.

Rmix repeats[88,556,556,7980,7980,8492,16384]100times, representative of actual
P816 DATA sizes rather than only full16KiB blocks. Its4,181,200 useful bytes take
66.577367s (0.502417Mbit/s); sampled retained peak58420B versus131072B for full
R8. These are representative weights, not an exact replay of P's frequency histogram.
Reverse is a64KiB **direction/correctness control**, not sustained upstream capacity.

### P: Mux64 + Family TLS + ReliableStream

Every phase has complete64KiB echo,4MiB download,2×2MiB parallel download,64KiB
reverse upload plus verified digest receipt. Echo is bidirectional application
latency, **not network RTT**. Main throughput rows are pure NL→client downloads.

{table(['Phase','RS S/R both ends','Single4MiB s','Single Mbit/s','Parallel4MiB common s','Aggregate Mbit/s','Phase ready/full s','Phase RS retry B','Bodies','Max client protocol errors'],product)}

**P816 is excluded from the clean comparison.** Postflight found its client counter
0 at echo completion,1 before the single download, then1 throughout bulk/reverse.
All bodies match, but that does not erase a protocol warning. Exact error category
is not exported; neither a harmless close race nor network loss is established.
The new wrapper omitted the previous operator's protocol stop gate, so discovery
was late, after subsequent independent sessions. This workflow failure is retained
in `P816/postflight-protocol-warning.json`; the original operator is preserved in
`operator-used/run.py`. Future runs now fail on any nonzero P counter and this
experiment is closed. No binary/transport fix, hidden rerun or counter reset occurs.

Clean P3232→P816b gives single+30.79%, aggregate+21.60%, with0 throughout both.
This is one bounded clean pair, not a repeated3x single-flow claim or Android
admission. The contaminated earlier comparison is visible but not acceptance.
Ready/full falls markedly at P32,
while application goodput does not follow R32 proportionally: limitation remains
above/alongside the larger RS window. **Server Mux zero-credit counters were not
exported by this adapter**, so pure Mux-credit attribution is not claimed.

### Record and packetization accounting

Exact defaults: Payload16384, SendWindow8, ReceiveWindow16, MaxWindow32, SACK32bits,
RTO1s, MaxRetries8, MaxAge20s. Carrier payload fragment8192B +24B header;
maxPendingMessages16, receive queue64, sendQueue256, reassembly lifetime10s.
No framing/packetizer/timebase/cap/RTO/retry/A0/pacer changes.

Pion4.2.15 actually uses MTU1200: RAW16384 →2 fragments/2 VP8 frames/**14 RTP**;
FRS DATA16384+64 or RAW16448 →3/3/**15 RTP** before lower retransmits.
The previous local framed-loss helper uses payloader1100 and yields16/17; that is
**not** the physical packetization. `actual-packetization.log` verifies real Pion.

T816's outbound unique TLS histogram includes251×16406B and251×34B records.
The large TLS record crosses RS as16384+22; the small remaining record consumes
another34-byte RS DATA slot. All-attempt RS histogram includes302×16384,290×22,
279×34. Sampled retained peak62410B despite eight occupied slots. P816's actual
DATA distribution includes556,88,7980,8492,16384 and many intermediate sizes.
Full TLS/RS/carrier histograms and actual RTP counters are preserved per endpoint.
Therefore T/P differences cannot be called pure cryptographic CPU overhead.

## C — effective windows, not Mux credit

Notation S/R = configured local send / advertised local receive. The other end's
receive32 permits effective32; no32/16 case is misrepresented as window32.
Configuration is emitted at both ends; unchanged OPEN code advertises that receive
cap and live Performance.EffectiveWindow confirms the negotiated send limit.
All rows below deliver256/256,4,186,112 useful bytes, same fixed full DATA size.

{table(['Phase','NL S/R','Client S/R','Effective NL','Mbit/s','Sampled retained/unconfirmed/SACKed B','Sampled max head age s','RX sampled pending/capacity rejects'],windows)}

Order8→16→32 then32→16→8.32/8 gains+188.50% and+173.62%;16 gains vary materially
with path/recovery. Exact8/16 versus8/32 control1.258819 versus1.262439 does not
show a meaningful receive-cap-only speed change in this one comparison.
4MiB R32 runs are~9.2s, **not sustained capacity claims**. Additional10MiB completes
in16.994586s; the final20MiB control above extends the observation, separately scoped.
Retained/unconfirmed/SACKed bytes are overlapping sampled states, **not physical
bytes in flight**. Head ages are sampled lower bounds; engine MaxRecoveryMS and
head-blocked counters are retained in raw data. Overlapping waits must not be summed.

Local fault checks cover loss/reorder/duplicates/head gaps/late recovery/ACK loss,
slow consumer/backpressure/cancel/close and bitmap bit31 for all four pairs. Actual
RTP→reorder→VP8→reassembly→RS recovery delivers64/64 at each pair after two missing
head attempts, capacity rejects0. Deliberately interleaving32 incomplete assemblies
produces16/32 completions,32 rejected fragments,16 pending; contiguous32 completes
32/32. That controlled hazard is real but is not observed in these physical runs.
Memory/waits stay bounded; validation and limits remain enabled.

## Resources and measurement calibration

NL remains1logical CPU with the existing test-only50%-of-one-core quota,
MemoryMax220MiB/no swap/TasksMax96/Nice10; no assumption that1vCPU is insufficient.
The previous Linux client remains on its Wi-Fi path; no RU control is warranted by
the observed compute utilization. Whole-host counters include unrelated work and
are not attributed to this test. Local cgroup is shared; owned PID/thread counters
and getrusage, not its aggregate cgroup usage, establish test-process CPU.

{table(['Phase','NL process CPU / sampled lifetime s','Peak thread % one core','Cgroup throttled ms','Host steal %','NL max RSS KiB','GC pause ms through last sample','Sampled server send/client receive queue'],resources)}

Per-core `/proc/stat`, per-owned-thread schedstat, scheduler wait, cgroup counters,
memory and GC samples are retained. No profiler touches production. Independent
generator/full-byte verifier calibration before media:22,003.62Mbit/s under race;
additional generation/copy/read/verify/counters calibration after the window round:
2,068.97Mbit/s. The latter is not falsely described as pre-matrix. Neither supports
a generator bottleneck. Initial lab-only compile/type errors and an OS-suffix test
filename omission were repaired and rerun **before any media**; failure logs remain.
The missing-callable test was renamed before all four pairs passed. This is not a
production MESH fix. One local packetization validation compile overlapped T's run;
owned test CPU is separate, but the machine was not an exclusive benchmark host.

## Session comparability and budgets

One source capsule and one test binary for every endpoint. Separate fresh media
sessions, no runtime switching protocol and no reused user/bootstrap room. Each
phase fully closes before the next. All use VP8/RTP/IPv4 with unchanged Pion lower
NACK/retransmission. SFU differences limit precise causal percentages; repetitions
support only the stated bounded comparisons, not a universal host/channel maximum.
Per-phase client network/rules/routes and nominated local/remote ICE candidates are
in the raw kit; postflight route readbacks are in verification.json.

{table(['Phase','Selected SFU IPs','Controller total s incl setup/drain/confirm/cleanup','Source reserved B','Conservative outgoing media charge B'],paths)}

Source reservation **{verification['application_reserved']}B = {verification['application_reserved']/2**20:.6f}/128MiB**.
Outgoing RTP+RTCP attempts **{verification['outgoing_rtp_rtcp_bytes']}B**;
conservative wire charge **{verification['conservative_wire_charge']}B = {verification['conservative_wire_charge']/2**20:.6f}/256MiB**.
The first Pion interceptor counts **both processes' outgoing packets only**, including
NACK retransmits; no receiver-RX double counting. Guard reserves RTP/RTCP length+64B
per packet/compound for IPv4/UDP/SRTP/SRTCP. Closed endpoints also retain64KiB tail
margin; unclosed ones would charge their full reservation. Every write is guarded
atomically before emission; no budget stop occurred. Signaling/SSH/source uploads
are administrative traffic outside this explicitly defined media boundary.

## Provenance, cleanup and rollout/rollback

- Production gateway SHA256 `734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e`.
- Last accepted product remains beta96-bootstrap/A0/LEGACY64/65536/OFF/Q0;
  bootstrap96/gateway1011 retained. Prior manifest APK07a90f03… /native66a9d18d…;
  no phone read/write/reconnect was performed in this experiment.
- **Different test binary** SHA256 `{build['binary_sha256']}`;
  Go1.26.1 linux/amd64,fc_perf_diagnostic, pinned dependencies, no upgrades.
- Parent host-comparison build manifest SHA256 `{build['base_build_sha256']}`.
- Current build manifest SHA256 `{verification['build_manifest_sha256']}`;
  canonical source inventory SHA256 `{verification['source_inventory_sha256']}`.
- Test-only patch SHA256 `{build['lab_patch_sha256']}`: workload adapters, read-only
  histograms/candidate projection, outgoing budget guard; no accepted transport
  optimization and no production file edits. No reset to old main or push.
- Built and run: this isolated laboratory executable only. Installed product,
  public installer/APK/catalog/invitation-page versions: **unchanged**. No release
  signing, public distribution, routing, authority, floors or credential operations.
- All{verification['closed_peers']} peers closed; owned local/remote processes and NL
  stages absent; fresh test identities/DB/profile/room inputs removed. Normal leave
  is confirmed; provider-side conference metadata deletion is **not established**.
- Production rollback is neither needed nor invoked. Test rollback is stopping only
  `family-connect-capacity-20261020-<phase>` and its owned worker, then removing only
  its isolated stage after process exit; RuntimeMax510s also bounds abandoned units.
  Never replace production with this binary or restore an obsolete gateway/main.

Reproducible source/binary/raw logs/configurations/calculations/manifests:
`state-client-build/mesh-capacity-20261020/`.
Kit `mesh-capacity-kit.tar.gz`, SHA256 `{kit['sha256']}`.
[Operator scope](../../tests/fixtures/mesh_capacity/README.md),
[machine-readable public projection](2026-10-20-mesh-capacity.evidence.json).

## Next discriminating work — recorded, not implemented

Phase3 first: record RTP/RTCP timebase and actual data/keepalive frame cadence,
correlate the~2s missing-message groups across reader/reorder/VP8/reassembly, and
measure the cost of losing one fragment of a message. Keep a known baseline;
timestamp changes and packetization changes must be separate experiments.
Exact provider/SFU discard classification remains missing, not assumed network loss.

Phase4 separately: alternate fragmentation **without FEC**, then the same choice
with bounded FEC at equal total sending budget including parity, group delay and
burst losses; no assumption of arbitrary SFU FEC support. Phase5 separately: QUIC
over carrier datagrams, not ReliableStream; check MTU, queues and lower carrier HOL,
and do not collapse all independent flows into a single QUIC stream. Prototypes
still need compatible Family identity/authorization/revocation integration and
must never create a plaintext fallback. None of these mechanisms is implemented here.

Remaining product checks: Android/mobile/TUN and window32 production admission are
**NOT_RUN**; CPU-host migration is not indicated; raw rates above1Mbit/s remain
unmeasured. No further load, phone action or deployment is pending in this task.
"""
    public_receipt=dict(verification={key:value for key,value in verification.items() if key not in ['fixture_inventory','routes_postflight']},build_pins={key:build[key] for key in ['binary_sha256','base_build_sha256','lab_patch_sha256','rs_defaults']},phases=public,kit=kit)
    patch_file(ROOT/'docs/releases/2026-10-20-mesh-capacity.md',outcome)
    patch_file(ROOT/'docs/releases/2026-10-20-mesh-capacity.evidence.json',json.dumps(public_receipt,indent=2))


if __name__=='__main__':main()
