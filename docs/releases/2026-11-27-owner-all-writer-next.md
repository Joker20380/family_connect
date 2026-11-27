# OWNER/all-writer NEXT — 27 November 2026

Selected task remains CONTROL-HA-20261123 / HA-02. Mandatory collector
owner-collectors-b7f4cbd2 and compatible maintenance tooling8b9355db are accepted,
not pending. Original192343eb and old panel01 plan/authority/receipts/capsule retain
their meaning and bytes. No completed Resume.run is used as a health check.

## Fresh availability and exact failure correlation

At02:14UTC real panel authentication, overview/subscriptions/payments/two existing
cards and logout pass without test messages or manual business-data changes.
Read-only observer8b9355db passes with supportPID240065/archive621009b8,
authorityb0c470dc and NL1 generationb75ef2a2 unchanged.

NL1 failed invocation `81d9b8d83b3641d9954c0dd8d9adeb80`, PID1990396, ends
01:32:57UTC. Application and systemd receipts match the invocation/PID. The first
cause is SIGNAL_READ at SEED_READ: WebSocket CONNECTION_RESET, context ACTIVE,
carrier not already closed, returned_error, exit1, empty Unix signal. Cleanup
completes; credential headroom11166s. Systemd subsequently restarts normally once.
Neither SIGTERM nor provider blocking is established; the reset initiator remains
unknown. Application receipt SHA256:
`8e5da01a2c42dfebf50c63f0d7fbd0ba17998b4f1b454453afcf7c1405b3be8b`;
systemd receipt `b67917a613e0cef3080efd4311d680990906b46b54865212edd1b9e3709cfaf3`.

The authorized retained FLEET_MESH_PROBE_1 identity is reused, never regenerated.
Fresh authenticated HTTPS readiness/native import provides the directory/profile;
traffic uses public MESH, with the normal broker disabled and no SSH tunnel.
NL1 at02:19UTC passes4 simultaneous HTTPS,3 DNS and expected NL1 egress.
NL2 at02:20/02:24UTC passes only3/4 and2/4 HTTPS: verified end-site TLS but
HTTP response parsing fails after remote FIN. DNS/egress are NOT_REACHED, not
separately failed tests. Identical direct HTTPS requests from NL2 pass4/4; an earlier
Python-default-User-Agent request gets403 and is retained separately. The gateway's
later dedicated-session idle timeout occurs after the probe failure, not proof of
its initiating cause. No underlying network/provider diagnosis is claimed.

One guarded stop/start of NL2 uses unchanged installed70e6c0fc/a597d2a bytes.
The node operation lock, absent renewal owner, exact old invocation, credential
headroom, protected files and disabled boot enablement are checked. The initial
runner import failure occurs before any operation; corrected invocation performs
one actual stop/start only. NL2 PID2786473/invocationd0f64ecd obtains READY;
protected files remain unchanged. New directory SHA256
`a3b2d66f3bc53fe844f1e716a08a5974e1161c46051e06a0a2fc42c3ebac0167`
is independently present on RU after normal directory sync success/0 at02:30:28UTC.
At02:31:53UTC the same probe passes4 HTTPS/3 DNS/expected NL2 egress. Probe children
are reaped, identity bytes unchanged. This is bounded traffic recovery, not durable
stability, a root-cause fix or an Android/phone acceptance result. NL1 is not restarted.

## Exact activation inputs and remaining gates

The retained archive SHA256
`42ffb2afbe8e0752507ecf6c9842c19a7e3ab1b308d568f9082320b71cf4b6d1`
and both12-file source closures independently match source
`7a91d1278eda8594e448e5794e183e313aed8440`.
Candidates: console `sha256:3af9fbf95b36b33f1c0414ac41b84687f502391e311ff0bc35658cbf50da5cb1`;
publisher `sha256:35158514371e2a321643dbfe4b64b9a87a9b85b32228a5184d2c95e3b8ac19e8`.
Fresh proposal preserves effective installed configuration except those images and
reviewed gate env/mounts. Baseline console5ce82415/publisher50de6f25 remain installed
at this checkpoint. PostgreSQL/support are not recreated or restored.

Console verification must include `/run/family-connect-support` ownership, mode,
actual host/container mount identity and IPC. The known boot-order dependency is
NOT repaired or qualified merely by a successful panel restoration.

One observed Docker exec is explicitly queried by ID and is terminal exit0; this
is not proof for all historical imports/remote dispatches. Installation still
requires bounded stop/readback, retained code-only rollback and loaded-code/HTTP/
scheduler/management/manual ORM/CLI/no-unit-environment checks. Full capture also
requires external-work settlement or reliable fencing and a fresh stopped-support
snapshot within all held barriers, independent verify and normal resume.

Root119, original inventory3, later12, additional6, probe14 and support33 remain
separate. No marker deletion, weakened Gate.drain, maintenance-as-capture permit,
common capture, custody approval or HA-03 cutover is claimed. e4eace1a is history.
Joker/NL2/KeePassXC and historical Family-Connect.kdbx are known; actual external
copy and laptop-loss access remain separate, with no secret record contents read.

Private evidence: `/mnt/data/fc-owner-next-20261127` and the scoped NL2 root operation
directory; no profiles, raw journals, database contents or private screenshots enter
Git. This checkpoint changes documentation only; rollback is a normal documentation
revert. Runtime recovery rollback does not replay stale directories or credentials.
