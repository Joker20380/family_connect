"""Append phase 3 to the single capacity report; preserve parent history."""
import json
from prepare import ROOT, WORK, FIX, patch_file, digest


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(value) for value in row)+' |' for row in rows])


def main():
    summary=json.loads((WORK/'summary.json').read_text()); phases=summary['phases']
    verify=json.loads((WORK/'verification.json').read_text());kit=json.loads((WORK/'kit.json').read_text())
    analyses={name:json.loads((WORK/name/'media-analysis.json').read_text()) for name in phases}
    raw=[]; reliable=[]; product=[]; resources=[]; paths=[]; clocks=[]
    for name,phase in phases.items():
        server=phase['endpoints']['server'];client=phase['endpoints']['client'];analysis=analyses[name]
        mode=phase['config']['Mode'];policy=phase['config']['MediaPolicy']
        assembly=client['carrier']['Delivery']['assembly'];wire=server['wire']['rtp_bytes']
        reports=analysis['sender_reports']
        clocks.append([name,policy,sum(row['rtp_elapsed']<0 for row in reports),f"{max(abs(row['elapsed']-row['rtp_elapsed']) for row in reports):.6f}"])
        if mode=='C':
            received=phase['received'];bounds=analysis['bulk_boundaries']
            raw.append([name,policy+('/phase+1s' if phase['config']['KeepalivePhaseMS'] else ''),f"{analysis['bulk_locally_written_messages']}/151",f"{received['count']}/151",received['useful_bytes'],f"{phase['during_offered_interval_mbit_s']:.6f}",f"{phase['received_mbit_s_observation']:.6f}",f"{bounds['rx']}/{bounds['ordered']}/{bounds['assembled']}",assembly['expired'],f"{phase['loaded_rtt_median_s']:.3f}",server['max_send_queue']])
        if mode=='R':
            reliable.append([name,policy,phase['received']['count'],f"{phase['received']['last_seconds']:.9f}",f"{phase['received_mbit_s_to_last']:.6f}",server['reliability']['RetransmittedBytes'],f"{server['waits_seconds']['ReadyFullNS']:.6f}",server['max_retained'],server['max_sacked'],f"{server['max_sampled_head_age_seconds']:.3f}",f"{phase['loaded_rtt_median_s']:.3f}",f"{assembly['pending']}/{assembly['capacity']}"])
        if mode=='P':
            requests={row['name']:row for row in phase['requests']}
            counters={side:max(row['mux']['ProtocolErrors'] for row in analysis['mux'][side]) for side in ['client','server']}
            assert len(requests)==5 and all(row['passed'] for row in requests.values()) and not any(counters.values())
            product.append([name,policy,f"{requests['single']['full_seconds']:.9f}",f"{requests['single']['goodput_mbit_s']:.6f}",f"{phase['parallel']['seconds']:.9f}",f"{phase['parallel']['goodput_mbit_s']:.6f}",f"{requests['control_echo']['full_seconds']:.3f}",f"{requests['reverse_control']['full_seconds']:.3f}",'5/5;0/0',server['reliability']['RetransmittedBytes'],f"{server['waits_seconds']['ReadyFullNS']:.3f}"])
        resources.append([name,f"{server['cpu_user_s']+server['cpu_system_s']:.3f}/{client['cpu_user_s']+client['cpu_system_s']:.3f}",f"{server['max_rss_kib']/1024:.1f}/{client['max_rss_kib']/1024:.1f}",f"{server['thread_peak_cpu_one_core_percent']:.2f}",f"{server['cgroup_delta']['throttled_usec']/1000:.3f}",f"{server['host_steal_percent']:.3f}",f"{server['max_send_queue']}/{client['max_receive_queue']}",client['max_sampled_assembly_pending']])
        paths.append([name,','.join(sorted({item['remote']['ip'] for item in client['selected_paths']})),f"{phase['result']['seconds_including_setup_drain_confirmation_cleanup']:.3f}",phase['reservation']['application_reserved'],phase['result']['wire_charged']])
    old=json.loads((WORK/'parent-recalculation.json').read_text())
    oldrows=[[name,old[name]['bytes'],f"{old[name]['receiver_seconds']:.9f}",f"{old[name]['mbit']:.9f}"] for name in ['R816a','R832a','R1632a','R3232a','R3232b','R1632b','R832b','T816','R32long','R32sustain']]
    t8=json.loads((ROOT/'state-client-build/mesh-capacity-20261020/summary.json').read_text())['phases']['T816']['endpoints']['server']['histograms']['rs_data_attempts']
    tiny_count=t8['22']+t8['34'];all_count=sum(t8.values());tiny_bytes=22*t8['22']+34*t8['34'];all_bytes=sum(int(size)*count for size,count in t8.items())
    section=f'''## Phase3 — media timebase and periodic loss,20–21 October2026

**COMPLETED:14 isolated NL→Linux sessions,28 closed peers. B is a validated laboratory
clock correction, NOT an accepted speed fix or production configuration.** Main C,
R32 and P32 comparisons all use one binary
`b95110c5413d5af7e99a25072a2bb655775d159c0092aad69d4efc990061e3ce`.
CA1 is a retained instrumentation pilot with an earlier trace-label revision, not a
clean paired acceptance row. No production binary/config/APK, authority, credentials,
floors, revocation, routing, directory, release, push or RU migration was performed.

### Phase3 decisions, separately classified

| Question | Classification | Finding |
|---|---|---|
| PERIODICITY_REAL_OR_SAMPLING_ARTIFACT | CONFIRMED transient periodic structure, not an export artefact | Known missing IDs form groups~2s apart; packet-level monotonic observations place losses near the end of actual media-keepalive cycles. Main C losses occur in the first~11s of20s input, not indefinitely throughout a steady channel. |
| KEEPALIVE_CAUSAL_EVIDENCE | Phase coupling observed; exclusive causal attribution LIMITED | A+1s first-keepalive shift moves missing ID groups while the2s interval remains. All main missing-message first writes occur about1.61–1.98s after the previous actual keepalive. Different rooms/SFUs and load-start phase prevent an exact causal percentage; ICE consent also has a2s timer and is not in the media trace. Do not call keepalive suppression a fix. |
| RTP_RTCP_TIMEBASE | CONFIRMED inconsistency in A; corrected in B | A advances2970 ticks per sample regardless of idle/burst timing. Outgoing SR mapping has backwards steps and large jumps. B uses monotonic elapsed-before-sample; observed SR interval error is~0.07–1.03ms, with no backwards step. |
| FRAME_BOUNDARY_OR_REASSEMBLY_DEFECT | Local keepalive corruption hypothesis REFUTED in tested cases | Complete packet sets reassemble byte-exactly. Main C has40–42 bulk fragments without a first packet at the reader and5–6 partial frames; none has an equal complete payload packet multiset but fails assembly. The confirmed gap is after local RTP writes and before complete valid-RTP input, not a demonstrated local frame reset. |
| ONE_TARGETED_FIX | Correctness validated; NOT_ACCEPTED as speed fix | B changes only sample timestamp advancement using the same Pion packetizer. Keepalive2s, packetization, sequence/PictureID, NACK, A0, Q0, TLS, CRC and windows are unchanged. No second mechanism is combined with it. |
| C_AND_R32_EFFECT | C loss-fix hypothesis REFUTED; reliable speed attribution LIMITED | C A/B/B/A=134/133/133/133 of151. R32 delivers256/256 in every row; B/A gains+15.423% then+0.469%, with different SFUs. No repeatable sizeable R gain is established. |
| P_STACK_EFFECT | Repeatable application speedup REFUTED in these pairs | Single B/A +3.652% then−3.954%; parallel +3.770% then−6.659%.20/20 bodies byte-exact, both-end ProtocolErrors0 from creation through final close. |
| SHORT_RS_DATA_ORIGIN | CONFIRMED by byte-exact local boundary correlation | Application16384 + Family frame12 → TLS plaintext16396 → records16406 and34 → RS DATA16384,22,34.195/200 steady-state writes reproduce this in each direction; old T8 has251 such record pairs. No packing patch implemented. |
| PRODUCTION_UNCHANGED | CONFIRMED fresh gateway readbacks; phone not operated | Binary734b6ca6…/PID47501/invocation27e2c972…/profileabda003f… and OFF/LEGACY64/export-OFF are constant throughout this task. This process/profile already differed from the previous task before testing and was not rolled back. |

### Parent results rechecked, not rerun or overwritten

All19 original attempts remain in `parent-recalculation.json`, including excluded
P816 (client0→1 between echo and bulk, category unavailable). The clean original
P3232/P816b pair remains separate; phase3 does not relabel P816 as clean or invent its
error category. Original window experiments and promising RS32 are not production
admission. The10MiB `R32long` and20MiB `R32sustain` retain their exact distinct names.

{table(['Parent phase','Verified useful B','Receiver monotonic s','Recomputed Mbit/s'],oldrows)}

The20MiB source run is1280/1280; its useful20930560B excludes32B diagnostic envelopes.
Its29.935789880s and5.593454546Mbit/s are not directly compared with a short4MiB A/B.

### Timers, observation boundaries and source audit

Exact dependencies: Pion WebRTC4.2.15, RTP1.10.2, interceptor0.1.45, ICE4.2.7;
individual relevant file hashes are in `dependency-audit.json`.

| Event | Exact configured timing | Evidence / limitation |
|---|---|---|
| VP8 media keyframe keepalive |2s; diagnostic first deadline+1s only in CShift | Actual TX/RX frames recorded, no application ID assigned to keepalive. |
| ICE selected-pair consent |2s, connecting checks200ms | `checkKeepalive` actually calls PingCandidate; do not rely on its stale idle-only comment. STUN not captured by RTP/RTCP interceptor. |
| RTCP SR/RR |1s per interceptor/stream | Outgoing SR and available incoming/outgoing RR retained. Incoming subscriber/SFU SR is not exported here; absence is not proof that SFU sends none. |
| NACK feedback / configured TWCC |100ms | Actual feedback packet types retained; configured TWCC is not proof of negotiated or emitted feedback. |
| Reassembly prune / lifetime |1s cleanup plus ingest-triggered prune /10s TTL | Expiry is later detection/cleanup, not the instant a fragment disappears. Exact expiry event times were not separately instrumented. |
| A0 reorder deadline |100ms checked on new packet arrival | Unchanged; no finite-deadline candidate enabled. |
| Capacity/resource sampler; CLI metrics |1s /1s;5s | These export counters, not packet-loss instants. |
| Signaling JSON ping / WebSocket control ping |5s /20s | Distinct from VP8 keepalive and ICE consent. |

Prior C1/C1b group intervals1.973760/2.105344s came from missing IDs and the offer
schedule, not2s snapshots. Their original trace did not identify individual RTP
packets: no retrospective exact loss boundary is invented. New media events have
`entry.ns`, a process-local monotonic timestamp. The outer JSON `utc` is **post-run
export time**, not packet time. Endpoint clocks are never subtracted for one-way
latency. Up to100000 metadata events stay in memory; every physical trace reports
overflow0. No per-packet disk logging occurs during the transfer.

`media-analysis.json` correlates sender/message/fragment headers and payload-body
hashes. SFU changes SSRC, sequence and timestamps: constant rewrite offsets are
learned from matching fragments within each session, not assumed. Timestamp-only
joins for missing first fragments are explicitly labelled inferred. Successful local
writes do not establish remote delivery; absence before the valid-RTP reader does
not locate the loss specifically inside SFU, network, SRTP or an unexported lower
boundary. All parsed incoming RTP, ordered RTP and assembled frames are retained.

### A/B implementation and correctness

A/0 keeps the exact33ms sample policy and2s ticker. Pion `WriteSample` ignores sample
wall time and passes duration ticks to `Packetize`; that packetizer assigns its
**current** timestamp to all packets of this frame, then advances the next timestamp.
Thus an idle2s still advances only2970 ticks; bursts can advance media time faster
than real time. Pion SR extrapolates from the first packet of the last new timestamp
at90000Hz, so the next synthetic sample can reset that mapping backwards. Merely
comparing33ms duration with2ms writer sleep was not used as proof of delivery loss.

B advances an empty sample by elapsed monotonic time before the actual zero-duration
sample. Empty packetization consumes neither RTP sequence nor PictureID and emits
no packet. Long elapsed intervals are split into safe1h clock advances; fractional
tick remainder remains Pion-owned. All fragments of one VP8 frame retain one timestamp.
Cached NACK retransmissions keep original headers; RS retransmission remains a new
carrier message as before. One writer serializes data and keepalive complete samples.
Insertion between fragments of a carrier message is legal and locally tested.

Local race checks cover byte-exact fragmented delivery with interleaved keepalives,
loss/reorder/duplicate/late retry, partial close, cancel, slow consumer, actual bound
Pion/RS32 with pacing OFF, fresh/rebound tracks, fractional ticks and25h simulated
clock wrap, sequence wrap, and PictureID wrap. Exact Pion omits optional PictureID
when its value is0, including wrap; it is not a new defect or a reason to change
packetization. The final local suite passes outside the sandbox where loopback TCP
is allowed. Initial wrong test assumptions (one TLS record per handshake Write,
mandatory PictureID at0) and a local observation-hook compile error are retained
with corrected retests. Sandbox socket-denial logs remain too. No media implementation
change was needed for these corrected test assumptions.

### C — same16448B carrier input,20s at target1Mbit/s

Each row offers/enqueues151 messages,2483648B including32B diagnostic envelope per
message. All151 are locally written as3 VP8 frames and15 unique RTP packets each:
2265 bulk RTP packets. No offered-rate escalation. Receive observation32s includes
12s drain; late bytes are **not** added to the20s numerator. No corruption/duplicate
application delivery. RX/ordered/assembled counts below are bulk fragments out of453,
not all controls/keepalives. Queue is the sampled sender depth, not an exact peak.

{table(['Phase','Policy','Local full msgs','Unique full msgs','Useful received B','By20s Mbit/s','Full observation Mbit/s','RX/ordered/assembled frags','Expired builds','Loaded32B RTT p50 s','Sample queue'],raw)}

CA1 is a pilot: optional RS trace-label discriminator was corrected before all main
pairs (no C payload effect), and local TLS-test compilation overlapped its tail.
CShift is diagnostic, not a capacity fix. Its actual first-bulk-write phase after
keepalive is1064ms versus CA1=1782ms and CA2=1531ms; the requested first-ticker+1s
does not imply an exactly1s shift relative to load, because probes/startup also vary.
Separate sessions/SFUs limit exclusive causal attribution; no runtime switch was added.

In CA2,40 bulk fragments have no first packet at the valid-RTP reader and6 have only
a partial frame. B1/B2/A3 have42 and5. Inferred complete-window RTP counts are2077,
2074,2074,2074 of2265 locally written packets. No complete matched payload packet
multiset fails local assembly. Consequently the missing messages are not invented
by reassembly TTL or a statistics sampler. Partial assembly expiry6 per main row is
not the same as17–18 missing messages: entire missing messages never create a build.

For complete multi-packet fragments in the first30 source messages, median local TX
span is0.11–0.16ms while raw-reader span is60.64–62.63ms across the main pairs. In the
last30 it is14.11–27.45ms at the reader. These are within-endpoint durations for
matched packets, **not one-way delay**; survivor-only samples are labelled as such.
This locates substantial spacing before reorder/reassembly and shows startup/path
service evolution. It does not prove a specific proprietary SFU discard algorithm.
The corrected B clock leaves both this pattern and periodic missing groups intact.

### R32 — same4MiB source in A/B/B/A

Both ends are Send32/Receive32; effective32 is observed, not32 against peer16.
Payload16384, RTO1s, retries8, age20s, SACK32, A0, Q0 and carrier limits stay fixed.
Every row delivers256/256,4186112 useful bytes, without corruption or duplicate
application data. These8–11s transfers are not sustained-capacity ceilings.

{table(['Phase','Policy','Messages','Receiver s','Mbit/s','NL retry B','Ready-window s','Peak retained B','Peak SACKed B','Sample head age s','32B RTT p50 s','Final pending/cap rejects'],reliable)}

Forward B/A +15.422799%; reverse +0.469052%. Different SFUs and startup/path evolution
prevent claiming the first percentage as a reproducible clock speedup. Retained,
unconfirmed and SACKed bytes are not physical bytes in flight; overlapping wait
counters are not summed. The source inventory retains all original RS32 work.

### P — Mux64 + Family TLS + RS32 only

Same single4MiB, parallel2×2MiB,64KiB echo and64KiB reverse-upload controls. Echo is
not pure network RTT; reverse time includes the verified32B hash acknowledgment.
All20 bodies match. Both endpoints export Mux counters at creation,100ms samples
and after Close; every counter remains0, including all six diagnostic error categories.
Any new error would cancel the phase rather than accepting a partial goodput result.

{table(['Phase','Policy','Single s','Single Mbit/s','Parallel common s','Parallel Mbit/s','64KiB echo s','Reverse control s','Bodies; errors C/S','NL retry B','Ready-window s'],product)}

Paired B/A single +3.652% /−3.954%, parallel +3.770% /−6.659%: signs reverse.
No repeatable P speed or latency gain is accepted. P/RS8 remains the separate parent
control, not a simultaneous8→32 plus clock change. Mux128 is absent. Actual TLS/RS
size histograms are saved; record-shape differences are not renamed TLS CPU overhead.

### Outgoing SR consistency, resources and budget

SR interval error is `RTP delta/90000 − local monotonic report interval`, wrap-aware.
It is not a cross-host latency estimate. Available NTP/RR values remain in raw events.

{table(['Phase','Policy','Backwards SR steps','Max absolute interval error s'],clocks)}

{table(['Phase','CPU NL/client s','Max RSS NL/client MiB','NL sampled peak thread % core','NL throttle ms','NL steal %','Sample send/recv queue','Sample pending assemblies'],resources)}

CPU values cover the whole test process, including setup/drain/post-run trace export,
not pure encryption cost. Thread scheduling waits are nonzero and retained in raw
resources; sparse cgroup throttle intervals are not hidden. No evidence supports a
compute ceiling requiring RU/2vCPU. GC, per-core load and per-thread scheduling are
saved; only test processes are sampled. Trace+hash calibration exceeds877Mbit/s under
race, with bounded100000 records and explicit overflow. Local memory-only regression
and calibration loops are separate from the network-source budget and emit no media.

{table(['Phase','Selected SFU IPv4','Controller total s incl setup/drain/cleanup','Source reserved B','Conservative outgoing media B'],paths)}

New phase3 total **{summary['application_reserved']}B = {summary['application_reserved']/1048576:.6f}/128MiB** source;
**{summary['wire_charged']}B = {summary['wire_charged']/1048576:.6f}/256MiB** outgoing-media charge.
The first interceptor counts outgoing RTP/RTCP attempts at both test endpoints,
including NACK retransmissions, plus64B per packet and a bounded final tail allowance.
Receiver RX is not counted again. STUN/signaling are not media bytes. Reservations
include controls and all attempts, including CA1; no failed attempt is deleted to
restore budget. Per-phase limits, both configurations, session scope, IPv4 paths and
source/binary hashes are retained. No user room, production private key or public
proxy was used. Every next phase started after prior owned processes were closed.

### Short RS DATA22/34 — proved origin, no packing patch

The local observation-only copy uses the exact Family implementation and in-memory
test certificates. Both directions perform200 application Writes of16384B without
echo or benchmark envelopes. A Family Send builds one16396B plaintext Write including
its12B prefix. After TLS dynamic-record warmup (first5 writes),195/200 calls each
produce ciphertext Writes16406 and34B. Bridge `net.Pipe.Read` preserves those writes
with its65536B buffer; RS segmentation produces16384+22 and34. Concatenated ciphertext
is byte-exact across TLS Write → bridge Read → unique ordered RS DATA in each direction.
TLS1.3 AES128-GCM record overhead is22B. The34B record holds the **last12 application
bytes** of the16396B plaintext, not a standalone Family header. The22B RS tail contains
required encrypted bytes/type/authentication data; neither block is disposable.

Handshake is analysed separately: one underlying Write may contain several TLS
records, which caused the retained first local-test assertion failure. Controls in
old T8 include66B records; the client-to-NL control direction has no22/34 steady bulk
pair. Old NL→client T8 has251×16406 and251×34 unique records. Its all-attempt RS DATA
counts22={t8['22']},34={t8['34']}: **{tiny_count}/{all_count}={100*tiny_count/all_count:.3f}%** of
DATA attempts but **{tiny_bytes}/{all_bytes}={100*tiny_bytes/all_bytes:.3f}%** of DATA payload bytes.
Retries are included in those historical attempt fractions; unique TLS record counts
are separate. In steady local bulk, two of three RS slots carry only56 of16440
ciphertext bytes. This is structural slot pressure, not a measured pure CPU tax.

This is not the rejected socket read-alignment patch and not the existing batching
before TLS: the reproduced boundary is TLS ciphertext Write → RS segmentation.
No ciphertext is removed/reordered or acknowledged early. A packing fix is a new,
separate experiment, including finite flush/control-latency and integrity checks.

### Cleanup, provenance and next decision

Final readback: `{verify['utc']}`; production equality confirmed. Baseline binary
`{verify['production_after']['binary']}`, profile hash
`{verify['production_after']['profile']}`, PID{verify['production_after']['MainPID']},
invocation`{verify['production_after']['InvocationID']}`. All28 peers, collectors and
owned systemd units are gone; remote stages and local ephemeral issuer/room/credential
files are removed. Provider room-metadata deletion is not supported by this workflow:
normal media closure is verified, not an unperformed metadata deletion. Phone/beta96,
directory/floors/revocations were not operated. No production rollback is needed.

Capsule: `state-client-build/mesh-capacity-phase3-20261020/`; exact inventories,
bounded raw traces, per-phase manifests, resources, calculations, failure logs and
cleanup receipts retained. Private kit `{kit['file']}` SHA256
`{kit['sha256']}`. The operator refuses further load after final verification.
Parent kit and source inventory are unchanged, including the P816 warning.

**Next:** close this media speed experiment and separately test TLS→RS block
formation, keeping one known A0/OFF/Q0/Mux64 baseline and RS32 only as a lab choice.
Test exact ciphertext concatenation, bounded buffering/flush, small-control latency,
then T and P; do not promise that a gain below Mux improves a single application flow.
Fragmentation without FEC, then equal-wire-budget bounded FEC, remains conditional on
remaining burst-loss evidence. QUIC later, if needed, must run over carrier datagrams,
not ReliableStream or one re-collapsed Mux stream, with compatible Family admission.
No FEC, new fragmentation, QUIC, Android rollout or migration is implemented here.
'''
    report=ROOT/'docs/releases/2026-10-20-mesh-capacity.md'
    text=report.read_text()
    marker='## Phase3 — media timebase and periodic loss,20–21 October2026'
    if marker in text:text=text[:text.index(marker)].rstrip()+'\n'
    text=text.replace('# MESH capacity investigation — phases1–2,20 October2026','# MESH capacity investigation — phases1–3,20–21 October2026')
    if 'Phase3 follow-up is appended' not in text:
        text=text.replace('\n\n**COMPLETED WITH P816', '\n\nPhase3 follow-up is appended below with its own budget and fresh production readback.\nThe following original sections retain the closed phases1–2 history and P816 warning.\n\n**COMPLETED WITH P816',1)
    text=text.replace('## Next discriminating work — recorded, not implemented','## Parent handoff — historical, superseded by phase3 below')
    patch_file(report,text.rstrip()+'\n\n'+section)
    projection=ROOT/'docs/releases/2026-10-20-mesh-capacity.evidence.json'
    value=json.loads(projection.read_text())
    value['phase3']=dict(verification={key:verify[key] for key in ['status','utc','phases','failures','source_reserved','conservative_outgoing_media_charged','production_before','production_after','production_equal','local_peers','local_collectors','remote','client_network_equal']},binary_sha256=json.loads((WORK/'build.json').read_text())['binary_sha256'],C=raw,R32=reliable,P32=product,clocks=clocks,resources=resources,paths=paths,kit=kit)
    patch_file(projection,json.dumps(value,indent=2))
    patch_file(WORK/'report-calculations.json',json.dumps(dict(C=raw,R32=reliable,P32=product,SR=clocks,resources=resources,paths=paths,short_rs=dict(attempt_count=tiny_count,total_attempts=all_count,bytes=tiny_bytes,total_bytes=all_bytes)),indent=2))
    print('report updated',digest(report))


if __name__=='__main__':main()
