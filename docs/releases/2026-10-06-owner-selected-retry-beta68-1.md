# OWNER-SELECTED-RETRY-BETA68-1 — FAIL

## Resumed single physical experiment — 2026-10-06 UTC

User accepted private internal ACK-token matching backed by frozen beta68 source/CI;
raw token export is neither required nor performed. No timestamp-only substitution.
The earlier pre-arm pause below is historical and resolved.

Fresh preflight at20:54:53 PASS: owner beta68/code68 package
`com.familyconnect.app.friends`, UID10283/data inode601521, encrypted identity and
enrollment preserved; exact sealed APK and loaded gateway verified. Fresh READY/ACK,
Wi-Fi OFF/cellular ON, Android unarmed and gateway directory empty. Actual served
leaf expiry23:48:47 UTC; limiting headroom10433s. RU/NL directory generation
`2026-10-06T20:13:55.407645965Z`, SHA256
`2159d02f9d5cabe150ed206ba395b788cd346c9fba0037b8428aafa54655baa4`;
issuer/grants/CRL/hostname/signature validation passed. The earlier immediate
preflight rejected READY age before any arm; ordinary READY/ACK refresh resolved it.

Exactly one session/test launch20:56:54 UTC, one receiver prearm and one sender arm.
Session established Family TLS/gateway and baseline DNS/full HTTPS/TCP before arm.
Fresh128-bit generation and exact selected descriptor transferred via trusted USB/SSH,
not user traffic. One fault consumed DATA60 attempt0 at20:57:30.801 UTC; frozen source
drops before encode/lower-layer carrier allocation. Count stayed1, auto-disarmed.

### Direct pinned evidence

- Attempt1: carrier sender433208471/message2855051861; one fragment/one RTP packet,
  PictureID214, sender timestamp1671731102, RTP sequence20994. Actual `rtp_written`
  result `ok` at20:57:31.840 UTC, not merely WriteSample success.
- Sender ACK received and base advanced at20:57:32.023 UTC: base61/mask3;
  selected sender watch COMPLETE.
- Receiver candidate same carrier sender/message and PictureID214, reconstruction
  complete, sequence_known=true; remote timestamp635613 and RTP sequence220.
  These differ from the exact sender descriptor. Receipt remained BOUND and then
  OVERFLOW by20:57:32.513 UTC. No receiver COMPLETE and no exported pinned selected
  Reliable acceptance/consumption/ACK-generation/actual-ACK-write chain.
- This is a failed mandatory cross-peer evidence gate, not proof of failed healing.
  No ordinary ring substitution or weakened matching is accepted. The receipts show
  the RTP identity difference; its upstream cause is not established by this run.
- All three modest concurrent requests completed DNS, full HTTPS577-byte body and
  TCP response. All74 sender snapshots healthy, same session, no reliable terminal
  failure. This does not substitute for missing receiver callback proof.

### Cleanup and scope

Both correlation watches explicitly CLEANED; fault final count1/disarmed. Engine
closed, final native state UNAVAILABLE/unarmed with no generation. Independent
20:58:41 UTC readback PASS: identity/data/APK preserved, gateway directory empty,
PID1401423/NRestarts0, exact loaded hash/revision and service configuration unchanged.
Temporary test helper removed and USB forwarding removed. No second test, rebuild,
product install/deploy, renewal, impairment, soak, transport tuning or publication.
No raw private ACK token exported. Reverse cleanup journal was not collected;
there is no claim of independently proving absence of reverse cleanup exhaustion.

Runtime remains exact sealed beta68, source
`1abaa3a8a9ba8ad9fa2a71c126620175b713c321`, gateway SHA256
`3038888ae8abc585d159f9c0bec629ce59b0b2ac40b0a3d22e9bb73a92d9f717`.
Both sealed beta67/beta68 pairs remain hash-verified; rollback paths/Android downgrade
constraints remain as documented in the accepted deployment report. No rollback
performed: the failure is evidence completeness, with normal traffic successful.

Private local receipts:
`state-client-build/field65-export16/owner-selected-retry-beta68-1/resume1/`:
`immediate2/fresh-preflight.json`, `receiver-prearm.json`, `sender-armed.json`,
`sender-descriptor.json`, `receiver-pinned-1791320252177961026.json`,
`experiment-result.json`, `evidence-summary.json`, `cleanup-verified.json`,
`evidence-sha256.json`. Instrumentation `OK (1 test)` means helper lifecycle completed,
not that the cross-peer experiment passed; operator acceptance explicitly FAIL.

**Next step:** offline review of retained receiver RTP-identity mismatch and overflow;
do not consume another physical experiment under this authorization.

## Historical pre-arm pause

## No experiment consumed

Separately authorized owner Android→gateway physical task was opened after accepted
PINNED-EVIDENCE-DEPLOY-2 PASS. No restricted session started, no receiver prearm,
no sender fault arm, no traffic generation, no physical attempt, no runtime changes.
Immediate full live credential/identity/control preflight remains pending and must
be performed immediately before proceeding; prior deployment headroom is not reused.

## Narrow evidence-contract question

User requires mandatory ACK generation evidence including a unique ACK token.
Clean exact frozen source `1abaa3a8a9ba8ad9fa2a71c126620175b713c321` contains:

- `carrier/sessiontrace/receiver_diagnostic.go:76`: ReceiverACK.token is unexported.
- JSON exports base, mask, created_ns, sent_ns and result, not the token.
- `receiverACKSentLocked` compares the private token AND creation timestamp/base/mask
  before recording actual carrier-write outcome. Equal timestamps alone cannot match.
- Accepted PINNED-RELIABLE-CALLBACKS-1 explicitly says the token is not on wire/export.

Thus the accepted runtime implements unique-token correlation, but the physical
export cannot directly show the token value. This is NOT a callback defect or a
request to change privacy/wire/runtime behavior. Deployment's earlier clarification
covered schema capability reporting, not this distinct physical evidence field.
No timestamp-only, ordinary-ring or manifest-only substitute is claimed.

Before consuming the single authorized physical experiment, confirm whether the
exported token-matched callback proof plus accepted exact-source/CI linkage meets
the unique-ACK-token requirement without exposing the private token value.
No new endpoint or binary rebuild is proposed or performed.

Local receipt: `state-client-build/field65-export16/owner-selected-retry-beta68-1/contract-preflight.json`.
Prior deployment/freeze receipts remain accepted; unrelated dirty work unchanged.

**Next step:** clarify acceptance of internal unique-token matching without token export;
then resume the same task with fresh runtime preflight and at most one experiment.
