# L04.2-R1 — primary MESH failure and cleanup preservation

Date: 2026-10-26. Continuation of **L04.2**, not a new PLAN ID.
Input main: `36606eae3162b3c5e1d93397a05caab5118ccc74`.
**Source checkpoint; system/package/full-suite gate still pending. No live PASS.**

The [accepted core report](2026-10-26-linux-installed-mesh-auto-l04-2-core.md)
records one .9 P0 Connect returning NETWORK_SETUP_FAILED at attempt1/60835ms.
That action was not repeated. Its underlying live cause remains unlocalized;
the deterministic diagnostic-collapse reproduction below is not proof of that
particular incident's native root cause. Chat delivery_unavailable remains an
uninvestigated L05 observation, not a VPN prerequisite.

## Old red / new green

Added controlled source tests using real Supervisor, PacketSession and NativeWorker
cleanup, real local child processes and real ChatLane readers. No private state,
live gateway, server policy or owner identity. Typed session replies and failures
are injected only at controlled dependency boundaries, not via transition().

Against the input commit's exact mesh_service.py/backend.py, the corrected20-case
red selection gives **18 FAIL / 2 PASS**. In particular, WORKER_EXITED and
NETWORK_TIMEOUT both collapse into NETWORK_SETUP_FAILED when the already-reaped
nonzero child makes the old stop RPC/close fail. Genuine reap/reader/detach/binding
cleanup failures and an unexpected body exception reproduce the same overwrite.
Old repeated close also detaches the next simulated generation. Setup-attempt0
and cancellation ordering controls pass; they are not falsely described as red.

Current source focused regression selection: **213 PASS / 2 SKIP**; the two skips
require an explicitly built native binary and are not claimed exercised by this
selection. The final22 regression cases additionally cover final network fail-safe
failure and repeated unsuccessful close without touching a replacement.
Full desktop on Ubuntu26.04/Python3.14: **1296 PASS / 82 SKIP**, no deselection.
Isolated authenticated combined manual/Auto root→UID and release-control gate:
**3 PASS / 81.03s**, using updated Python sources and the retained test-only native
fixture (unchanged Go boundary), not the old installed system as a new candidate.

The first desktop invocation had four authorization fixture failures because its
Docker /tmp was mounted noexec. A direct fixture-only executable probe confirmed
rc126/Permission denied. Correcting only the mount to /tmp:exec produced the full
result above; no test, skip or product authorization behavior was changed.
An initial new synthetic failed-reply fixture omitted ok=True; that fixture was
corrected before the retained old-red/new-green comparison. A misspelled test
selection path collected no tests and is not counted as validation.

## Semantics and scope

- NativeWorker.close no longer treats a nonzero return code or an unavailable
  stop RPC as proof of incomplete cleanup. It still requires acknowledged reap,
  closed stdin/stdout, terminated chat reader and closed chat descriptor, within
  its10s budget. Signal/RPC errors are tolerated only when subsequent lifecycle
  checks confirm cleanup; they never turn a failed session into a successful one.
- PacketSession.close attempts binding, worker and detach independently, records
  the first sanitized cleanup stage and confirmation, and memoizes its result
  under a lock. Repeated close cannot detach a replacement generation.
- Supervisor records the primary failure before close. first_reason is retained;
  a cleanup-stage event follows it, then final FAILED/CLEANUP_PENDING. No retry or
  ownership release follows unconfirmed cleanup, including explicit Disconnect.
- Complete cleanup permits the existing cancel-aware transient backoff. A real
  second controlled attempt proves it starts only after reap/reader shutdown/
  detach. The session reference is always cleared under lock. Final network
  cleanup remains a fail-safe and cannot erase a primary reason.
- NETWORK_SETUP_FAILED is limited to pre-session setup at attempt0; unexpected
  session-body failure becomes PACKET_OR_IPC_FAILED; worker disappearance remains
  WORKER_EXITED. No raw exception strings are exported.
- Existing IPC schema and service events are retained. Strict desktop diagnostic
  allowlists add CHAT_BINDING_CLEANUP_FAILED, WORKER_REAP_FAILED,
  WORKER_READER_FAILED, WORKER_DESCRIPTOR_FAILED, WORKER_CLEANUP_FAILED,
  NETWORK_DETACH_FAILED and NETWORK_CLEANUP_FAILED; export tests preserve them.

Source scope: [supervisor/session/worker](../../clients/linux/mesh_service.py),
[desktop diagnostics](../../clients/desktop/backend.py), and
[regressions](../../clients/desktop/tests/test_mesh_failure_cleanup.py).
No network protocol, Android106, identity/store, certificate, policy or underlay
IPv6 changes. The prior mngtmpaddr observation remains supplementary; no manual
underlay correction is performed.

## Remaining gate and immutable artifacts

This source checkpoint is not a candidate, installed acceptance or release.
Mandatory complete suites, CI and isolated/package gates must complete before
live continuation. No full-suite failures may be suppressed or waived here.
The first non-fixture source/package failure stops progression to a new candidate
and live acceptance; it does not authorize unrelated repairs.

Historical .9 and its system remain immutable, per the unchanged
[manifest](2026-10-26-chat-ux-2/candidate-delivery.json):

- Candidate `6f312d1e7c783ea42a39ca164d93d74b0ec4faf5bac53e24c12551cedd052a5b`.
- System `43266d97c6a9f8d4e7026727cbb4b5cb6aeea49db799f93bd798b67a8135198c`.
- DEB SHA256 `e79bca1bb70a1b8d6db1ba44436cb9216c8fa7bf769fb3d919a1f2c8c96eaf62`.
- AppImage SHA256 `dc790701321da9e63325bc097bf6eab81032ed7f46236e0ed2de39cc673d45d4`.
- System archive SHA256 `402affe5628da4ecd1df3e274f3c67848d5e59023a63374765c91419490b9a55`.

Expected next internal version .10 is **not built or assigned an ID** in this
source checkpoint. The old system must not be reused for its eventual build.
P0/P1/Auto and active GUI/AppImage lifecycle on a new candidate are NOT_RUN.
Retained encrypted test snapshots and original protected home are not booted or
mutated by source tests. Owner workstation **NOT_USED** for acceptance.
L05/messages/voice/signing/publication/revoke/teardown NOT_RUN. No deployment or
installed rollback is performed. Unrelated VPN-health working changes are preserved.
