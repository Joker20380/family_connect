# MESH overnight checks — 5 November 2026

## Scope and retained delivery

Owner explicitly authorized unattended stability checks overnight. Selected scope is
the existing MESH incident: paired-DNS loss, disconnect/recovery, both-node equivalence,
weak-link tests and bounded sustained observations. No public rollout or unrelated PLAN
successor. Android118 remains the exact signed owner build from
[its qualification receipt](2026-11-05-android118-signaling-diagnostics.md); public113/
catalog7 and desktops are unchanged. Both NL nodes retain gateway70e6c0fc. No new version,
gateway binary, credential policy, timeout, retry limit or owner admission is changed.

Local evidence root is `state-client-build/mesh-overnight-20261105/`, ignored/private.
No private identifiers, profiles, product databases or raw journals are committed.
Existing unrelated dirty documentation and untracked work are retained.

## Initial observation and independently attributed maintenance interruption

A new30-minute diagnostic observation starts00:11:59UTC on the existing118/NL2 session.
This is a new characterization run, not a retry that erases the earlier7/8 DNS failure.
Its first round passes8 wire DNS,2 Android hostname HTTPS and2 exact-NL2 egress checks.
The initial session subsequently fails: phone first cause00:13:19.709UTC is
RELIABLE_FRAME_TIMEOUT/RELIABLE_EXHAUSTION. No preceding WebSocket/ICE failure is recorded.
VPN capture remains open; normal automatic recovery is observed CONNECTED on a new
session at00:14:40.897UTC, without an operator Connect/Disconnect or network mutation.
Sampled RESTORING starts00:13:24.548UTC; this is not uninterrupted stability.

Independent systemd and exact-session gateway records establish the immediate cause:

| Event | UTC |
| --- | --- |
| RU scheduled credential renewal starts | 00:12:30.836 |
| NL1 bootstrap stopping / stopped | 00:12:56.009 / 00:12:56.174 |
| NL2 bootstrap stopping / stopped | 00:12:58.548 / 00:12:58.579 |
| NL2 exact session parent cancellation | 00:12:58.555 |
| NL1 / NL2 new bootstrap start | 00:13:25.664 / 00:13:27.740 |
| RU renewal finishes, result COMMITTED | 00:13:37.042 |

New running PIDs are1436865/1252999, both executable hashes still70e6c0fc and systemd
NRestarts0. NRestarts0 alone is not proof of no stop/start; this scheduled operation is
not counted as an automatic crash restart. No assistant restart was issued. The existing
controller explicitly permits approved leaf/CRL scheduled maintenance with unknown
session inventory and zero_downtime=false, then quiesces the readers. Authentication,
expiry, revocation and coordinated publication must not be weakened to hide this outage.
No perpetual timer pause or unsafely extended credentials are introduced.

The broad bootstrap journal query reaches its3000-entry bound; it is not used to claim
an exhaustive historical restart inventory. Exact current-session evidence and the
separate RU renewal journal cover this interruption. The earlier117 WebSocket read error
and118 paired-DNS timeout are not reclassified as renewal failures without evidence.

## Checks still running at this checkpoint

- Thirty-minute observation continues across automatic recovery, retaining each failure
  and each session transition; subsequent traffic success cannot turn the original
  uninterrupted-session gate into PASS.
- Focused production/default-tag native race checks cover TCP/DNS mux, reliable stream,
  protected underlay, whole-device capture and safe diagnostic projection.
- Focused real-Pion/RTP/signaling checks and explicit paced-link qualification follow;
  optional skipped tests do not count as executed physical/provider tests.
- Paired-DNS timeout attribution, old WebSocket cause, physical weak-link and both-node
  sustained gates remain OPEN. No new correction is claimed merely from diagnosis.

## Rollback and cleanup

No product/server mutation needs rollback in this checkpoint. The ordinary-UID synthetic
probe is temporary and must be removed in the observation's finally path, including
failure or expired app consent. Do not uninstall/reset the product, reenroll, evict an
owner, disable expiry checks or change ordinary AWG/TCP services. Continue phone diagnostics
only while the normal in-app USB grant remains authorized; broad task permission is not
an access-control bypass. Source/documentation rollback is an ordinary non-force revert.
