# L04.2-R1 — primary MESH failure and cleanup preservation

Date: 2026-10-26. Continuation of **L04.2**, not a new PLAN ID.
Input main: `36606eae3162b3c5e1d93397a05caab5118ccc74`.
Source correction: `9c6f867ea3e866df6a0ce65dbd311e1882336bb0` (pushed main,
remote SHA verified). **PARTIAL / STOP at mandatory source/CI gate. No new exact
candidate, system build or live PASS. NEXT — review L04.2-R1.**

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

## Mandatory gate result and CI

Complete local suite on Ubuntu26.04/Python3.14, with fresh80-file release fixtures
pinned to source9c6f867 and Go1.26.0: **36 FAIL / 3377 PASS / 99 SKIP**,7 passing
subtests,231.20s. No deselection, suppression or unchanged rerun. Its36 failure
IDs exactly match the recorded [CHAT-UX-2 failure list](2026-10-26-chat-ux-2/validation.json).
The earlier separate FD teardown error did not reproduce in this run; it is not
claimed fixed. Historical failures still fail this mandatory gate and are not waived.
They concern HTTP-route expectations, permission/root-execution assumptions,
native expiry and readiness socket reuse; none is relabelled as a MESH live cause.
The first fixture-preparation command stopped on container Git safe-directory
validation before producing the inventory; a container-local safe.directory entry
allowed preparation. No product sources or test selection changed for that repair.

Automatic push CI for the exact source commit (readback17:26UTC), not a new
installed .10 candidate:

| Gate | Result |
| --- | --- |
| [AWG](https://github.com/Joker20380/family_connect/actions/runs/40366892370) | PASS |
| [TCP](https://github.com/Joker20380/family_connect/actions/runs/40366892151) | build PASS; release jobs SKIPPED |
| [Client Linux](https://github.com/Joker20380/family_connect/actions/runs/40366892183/job/121726915514) | PASS |
| [Voice/encrypted messaging source tests](https://github.com/Joker20380/family_connect/actions/runs/40366892697) | PASS; not L05 or live voice acceptance |
| [Native bridge](https://github.com/Joker20380/family_connect/actions/runs/40366892046) | protocol jobs PASS; isolated-linux FAIL |
| [Linux control full suite](https://github.com/Joker20380/family_connect/actions/runs/40366892214/job/121726915996) | 54 FAIL / 3232 PASS / 226 SKIP;7 passing subtests |
| [phase0 Docker mandatory test layer](https://github.com/Joker20380/family_connect/actions/runs/40366892149/job/121726916075) | 54 FAIL / 3230 PASS / 228 SKIP;7 passing subtests; downstream failover NOT_RUN |
| [phase0 tests](https://github.com/Joker20380/family_connect/actions/runs/40366892149/job/121726915683) | IN_PROGRESS at local vault dependency setup; full tests not yet reached, not PASS |
| [Internal candidate CI](https://github.com/Joker20380/family_connect/actions/runs/40366892194) | IN_PROGRESS at supported Python/GI preparation; not the requested .10 package acceptance |

The isolated-linux failure is a **separate unaccepted regression observation**:
authenticated service-only lifetime selection **2 FAIL / 13 PASS**,112.24s:
`test_mesh_chat_lifetime_native.py::test_unconfirmed_authenticated_cleanup_retains_admission[cancel]`
and `[peer]`, at the assertion that the failed owner retains active admission.
It is not covered by the local three-case combined PASS and is not declared an
environment issue, known residual, gateway failure or accepted behavior change.
No rerun or further source patch follows this result. The gate does not establish
that all existing chat-binding/cleanup tests remain green. This source-level fixture
failure is separate from the untouched live delivery_unavailable observation.

No workflows were manually dispatched; the existing push matrix also starts
other-platform jobs automatically. Those jobs are not Windows/Android acceptance,
and no platform source, installed device or release is changed by this checkpoint.
Full CI PASS is **not** claimed. CI skip counts differ from the real-GTK local run
and are not interchangeable. Later package/system/live stages remain stopped even
if an already-running CI job finishes successfully.

## Stopped package gate and immutable artifacts

This source checkpoint is not a candidate, installed acceptance or release.
The mandatory source/CI failure stops progression to a new exact candidate and
live acceptance. No unrelated repairs or test weakening are performed.
New system inventory/imports, real systemd/pkexec setup, rollback, old/mixed-build
rejection, .10 DEB/AppImage coherence and candidate-check/status are **NOT_RUN**.
Historical .9 package PASS is not substituted for these gates.

Historical .9 and its system remain immutable, per the unchanged
[manifest](2026-10-26-chat-ux-2/candidate-delivery.json):

- Candidate `6f312d1e7c783ea42a39ca164d93d74b0ec4faf5bac53e24c12551cedd052a5b`.
- System `43266d97c6a9f8d4e7026727cbb4b5cb6aeea49db799f93bd798b67a8135198c`.
- DEB SHA256 `e79bca1bb70a1b8d6db1ba44436cb9216c8fa7bf769fb3d919a1f2c8c96eaf62`.
- AppImage SHA256 `dc790701321da9e63325bc097bf6eab81032ed7f46236e0ed2de39cc673d45d4`.
- System archive SHA256 `402affe5628da4ecd1df3e274f3c67848d5e59023a63374765c91419490b9a55`.

Expected next internal version .10 is **NOT_BUILT**, with no candidate/system ID
or DEB/AppImage hashes to report. Automatic CI build outputs are not promoted,
downloaded or installed as .10. The old system is not reused as a new build.
P0/P1/Auto and active GUI/AppImage lifecycle on a new candidate are **NOT_RUN**;
no new live primary_reason/cleanup_reason or attempt count exists.
Retained encrypted test snapshots and original protected home are not booted or
mutated by source tests. Owner workstation **NOT_USED** for acceptance.
L05/messages/voice/signing/publication/revoke/teardown NOT_RUN. No deployment or
installed rollback is performed. Unrelated VPN-health working changes are preserved.

Original protected home: all seven files compared with the retained pre-run
digests, byte-identical. Historical .9 DEB/AppImage/legacy/system hashes rechecked;
the manifest and previous L04.2 reports are unchanged. No identity/store/cache/
floor/settings changes, provisioning, registration, renewal or teardown in this run.

```json
{
  "task_id": "L04.2",
  "checkpoint": "R1",
  "result": "PARTIAL",
  "source_commit": "9c6f867ea3e866df6a0ce65dbd311e1882336bb0",
  "mandatory_source_gate": "FAIL",
  "new_candidate_id": null,
  "new_system_build_id": null,
  "new_deb_sha256": null,
  "new_appimage_sha256": null,
  "new_live_p0": "NOT_RUN",
  "new_live_p1": "NOT_RUN",
  "new_live_auto": "NOT_RUN",
  "new_installed_lifecycle": "NOT_RUN",
  "owner_workstation": "NOT_USED",
  "L05": "NOT_RUN",
  "publication": "NOT_RUN"
}
```

Sanitized source logs, fixture inventory and read-only CI receipts are retained
privately under `/var/tmp/fc-l042-r1-20261026`; no private test data is added to Git.
Secret scan **PASS**; report JSON and11 private receipt/inventory JSON files parse;
419 local links **PASS**; staged scope is exactly STATUS/PLAN/README/this report;
git diff --check and staged whitespace **PASS**. Source-log SHA256 receipts are
retained privately. Unrelated unstaged work is excluded. L04.1 remains DONE; parent L04 stays
IN_PROGRESS. **STOP. NEXT — review L04.2-R1**, not automatic continuation or L05.
