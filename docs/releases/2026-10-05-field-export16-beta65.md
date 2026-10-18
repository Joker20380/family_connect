# Export16 — real post-fix Telemost traffic, repeated uplink exhaustion

## Verdict

The post-renewal/post-RTP-fix cellular trial reached two authenticated Telemost
sessions and transferred data both ways. Both still failed after about20s of
UI-connected time. Automatic restoration after the first failure worked; the
second reached the existing bounded recovery guard. **Field stability FAIL**.
Gateway RTP timer correction7c6e1e11 is insufficient to resolve the field failure;
its local regression remains valid, but field causality was never established.
Do not ask for an identical retry, new clock settings or another readiness exercise.

## Source and retention

`FamilyConnect-diagnostics(16).json`,57491bytes, SHA256
`7e055fd4342075662c45328f7a025673df2884bbe3d8873fa93b8901fc2d7ac6`.
Tester FC-YHQB-9VJN, beta65/code65/API31. The new ring has only one READY event,
UNKNOWN network and no session; **the incident** preserves CELLULAR,73 events,
one current and one archived restricted session. Do not mistake the reset ring
for absence of a trial. Incident counters:15 DNS responses and13 TCP opens across
the two session snapshots; individual counts below, not sums of overlapping samples.
Neither session reports authorization denial or native protocol errors.

Allowlisted server journal20:12–20:18UTC contains202 trace records, of which162
match the two incident session tags. First session105 records, second57; no server
sequence gaps or missing required lifecycle stages. Client retained32/50 events,
three delivery samples dropped per session; archived first session also reports
18 archive drops. Thus server lifecycle is complete, not all client delivery history.
Support/connection/incident/session lookup assertions pass for both sessions.
Private evidence: `state-client-build/field65-export16/` (`correlation.json`,
`journal-receipt.json`, `summary.json`); no raw journal, credentials or profiles
are committed. Journal byte digest
`37123eb81f01966c3d5e82ce46995db1a4c09989c02a85cf97301c859548486a`.

## Timeline (UTC05.10; Krasnodar is UTC+3)

| Time | Event |
| --- | --- |
|20:12:39.428|Auto starts on the incident connection.|
|20:13:04.958 /20:13:27.217|AWG/TCP fail NETWORK.|
|20:13:31.486|Restricted cached readiness READY.|
|20:14:03.594|First Telemost CONNECTED; bootstrap, Family auth and session succeeded.|
|20:14:21.639|First native RELIABLE_RETRY_EXHAUSTED.|
|20:14:23.891|Android classifies NETWORK and starts restoration.|
|20:14:24.074|Cleanup complete.|
|20:14:33.083|Background FETCH_FAILED during restoration; cached material remains usable.|
|20:15:11.927|Restricted readiness READY again.|
|20:15:48.290 /20:15:48.337|New Telemost CONNECTED/restoration_succeeded,84.399/84.446s after RESTORING.|
|20:16:03.653|Second native RELIABLE_RETRY_EXHAUSTED.|
|20:16:08.665 /20:16:08.901|Second RESTORING then bounded guard FAILED, no third descriptor.|
|20:17:04.264|New ring READY after the incident; not a third successful data session.|

UI-connected to RESTORING durations20.297s and20.375s. Native first-failure times
precede UI detection and should not be conflated with those durations. Background
fetch failure is not the cause of the first data failure and does not prevent the
successful second session. Later FAMILY_TLS_ERROR follows carrier exhaustion,
not certificate rejection. Offline recovery projection uses UNKNOWN_INTERNAL for
Android NETWORK because its enum is narrower; raw Android recovery policy is NETWORK.

## Paired delivery evidence

| Metric | First session657e5f21150e | Second session27af3c64f6c2 |
| --- | --- | --- |
|Client sent/received bytes|32085 /17026|80151 /41837|
|DNS responses/errors|7 /0|8 /0|
|TCP open successes/errors|4 /0|9 /0|
|Missing client DATA head|48|58|
|Client send_next/pending|56 /8|66 /8|
|Head retries at first failure|8|8|
|Last ACK age at first failure|7ms|910ms|
|No ACK-base progress|8008ms|8108ms|
|Gateway receive_next /mask|48 /254|58 /70|
|Gateway later DATA buffered|7|3|
|Final gateway RTP gap events|9|5|

Both heads are absent in gateway receive state while later DATA is buffered. This
is not merely a missing return ACK for already-consumed uplink data. Full tags:
`657e5f21150e5ce89100a8ac9ac65ef874238f7ef65383415327dcb07bdb4d5a` and
`27af3c64f6c27cc3d08be29e63ffe1e76704d2c564f7ac609636dd6addd8a825`.
The second session's opposite-direction head59 is already consumed by the client
in the later sampled view; asynchronous final snapshots do not establish order
or a separate primary downlink failure.

Client written-boundary samples for DATA48 show two distinct carrier message IDs,
each total1/mask1. This counter advances only after successful Pion WriteSample:
the samples rule out those messages remaining solely in the application queue,
but do not prove UDP delivery. DATA58 has one retained written sample total3/mask1;
it proves only the first fragment's handoff, not completion of all three fragments.
Neither has a matching receiver fragment observation in retained samples.

Gateway carrier reassembler final fragments/completed are180/180 and229/229,
with zero expired/malformed/duplicate/conflict/capacity/CRC failures and no pending
message. These counters cover fragments that reached that layer, not missing VP8
frames. RTP gap counters are measured **after local reorder**, not a packet capture
at socket ingress. Consequently the evidence narrows the path to carrier media
delivery/processing before complete reliable DATA, but cannot distinguish sender
packetization, network/SFU loss, local reorder or VP8 assembly for the missing head.
It does not prove RKN interference. The first server eventually exhausts at
20:15:22.426, after the client's shutdown; do not report it as the initial trigger.

## Runtime, checks and next engineering gate

Read-only20:19:41UTC confirms the same installed accepted source8d04632 gateway
SHA256 `7c6e1e11208e167309cbe83dac0f5f1f1bb306f4e41628180367aa6fa5e9aa50`,
PID652351/NRestarts0, profile/served certificate match,12802s headroom and unchanged
ordinary-service/admission invariants. Leaf bound remains05.10 23:53:04UTC /
06.10 02:53:04 Krasnodar. Tester admitted/non-revoked, grant1/CRL7377, latest
ACK20:17:06 READY. Runtime receipts remain under `state-client-build/rtp-gap-20261005/`.
No build, installation, renewal, restart, timeout/policy change or deployment in
this analysis. Installed/targeted APK65 SHA dfbdb535 and default/catalog/invitation60
remain unchanged, not re-published or newly download-verified.

NEXT use the paired head sequences to investigate multi-packet VP8 delivery:
reproduce packetization/reorder/assembly loss locally, then close the specific
observability gap between gateway pre-reorder RTP receipt and VP8 frame discard
with bounded metadata only. Retain message/frame/sequence boundaries, not payloads,
subscriber identifiers or credentials. Do not declare a sender, SFU or receiver
fix without a red/green reproduction or matched boundary evidence. Any later
gateway/client candidate needs exact-artifact acceptance before another field trial;
do not promise a server-only remedy or raise retries/timeouts without evidence.
Tester can stop and retain the working VPN. No background monitor remains.

Rollback remains the accepted05571644 executable at
`/opt/apps/family_connect/restricted-materials-stage-20261001/rtp-gap-8d04632-20261005/bootstrap-broker.previous`;
rollback was not performed: the earlier binary also failed and current local fix
is valid. Preserve issuer5/current valid material/CRL floors and resync the new
directory after any restart; never restore the expired profile/retired seed.

Validation: existing correlation suite30 tests PASS; input/schema/privacy and
four-ID correlation checks PASS. See validation receipt for documentation checks.
