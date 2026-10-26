# L04.2-R2 — process containment versus authenticated drain

## Phase B continuation — current checkpoint

Input main `0aec7a1324a5457a0936ff5219f988491367e4fd`,26.10.
The source correction at `169aa687f497f8be690be5331879f994636135e1` is **DONE /
review accepted in source scope**. Exact affected native15, cleanup32, combined3,
desktop1306 and unchanged local36/phase0-Docker54 residual IDs remain accepted.
The previous control setup timeout and Client Linux setup hang are infrastructure
incomplete observations, no longer progression blockers. No overall CI PASS,
workflow timeout change or new top-level PLAN ID is claimed.

**Result: L04.2-R2 PARTIAL; Phase B BLOCKED at native build-test environment;
Phase C NOT_RUN. STOP. NEXT — final review L04.2-R2.**

### Entry and exact inputs

Read-only Git comparison confirms that169aa68→0aec7a1 changes only the two CI
receipt workflows and documentation. Product/runtime, locks, native sources,
Android106 references and package source bytes are unchanged, including the
working tree. No checkout back to the runtime commit occurred.

The fresh disposable builder reports Ubuntu26.04.1 and system Python3.14.4.
All four exact requirements locks match installed distributions; runtime wheel
RECORD verification covers630 files/17 distributions; pip check and accepted
Android106/native-reference verification PASS. Go is pinned1.26.0; Xray remains
`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`, with unchanged accepted patch/reference
pins. Native source digest remains
`cfcb7bae874765cfe6a66742fbeed55cb03399b7e32c13d5a5edcd212299df61`.
No locked dependency was unavailable or updated.

Generated output starts in a new empty ignored directory. No .9 system archive
or package member is used as build input. AWG/TCP inputs were independently
obtained from the current committed pinned Docker recipes (Go1.26.1, including
normal build-cache reuse), not extracted from .9. Both input-image builds finish;
they are not a matching MESH system, candidate or package acceptance result.

### First affected test failure and stop

The agent launched the native builder with `--network none` without first
providing the non-loopback test interface. The unchanged standard build command
uses `go test -race -count=1 -mod=readonly ... ./...` before producing its binary.
It exits1 with exactly this test failure:

```text
github.com/Joker20380/family_connect/desktopbridge/direct
TestProtectionFailureNeverConnectsAndProtocolIsBounded
direct_test.go:182: test requires one up non-loopback interface
```

The test enumerates interfaces and exits at that explicit fixture precondition,
before invoking the protection assertion or attempting its synthetic destination.
The supplied network-none namespace does not satisfy the recipe. This is an
agent build-environment configuration error, **not evidence of a product,
gateway, certificate, cleanup or protocol defect**. Seven other native test
packages pass; the command package has no tests. The failing test is not waived,
deleted, suppressed or counted as PASS, and is not added to the accepted
historical full-repository residual baseline.

The requested rule to stop if an affected/package test fails is applied here.
No native test replay, new candidate build, source patch, pin update or live
attempt follows. The parallel AWG/TCP input build had already completed; its
temporary extraction containers were removed. The native builder was `--rm`;
no installed system, service, VPN owner or TUN was created by this run.

Two earlier harness-only invocation errors are disclosed: the initial lock
auditor incorrectly matched across lines, then passed with line-wise parsing;
the local Docker legacy builder rejected an unsupported progress flag before
any build, then accepted the otherwise unchanged recipe without that flag.
Neither changes dependency pins, runtime code or test assertions. Unlike those
pre-test invocation corrections, the native test failure terminates Phase B.

### Unreached package/live gates and preserved state

Requested version **0.2.12~l03.2.10 NOT_BUILT**. The native output contains only
the failed test log; there is no new native binary, RNS delivery, matching system
manifest/build ID, candidate ID, DEB, AppImage or legacy archive. New artifact
sizes/hashes are therefore **N/A**, not inherited from .9. System source-reference
updates, inventory/imports/modes/polkit/root→UID checks, real systemd/pkexec setup,
tampered/old/mixed-build rejection, rollback to exact .9, candidate-check/status
and package regressions are **NOT_RUN**. Accepted source results are not relabelled
as new package results; the requested post-build full-suite comparison is NOT_RUN.

Installed entry, P0, P1, Auto, DNS/HTTPS, selected-next/active separation, refresh,
stale callback, lifecycle and AppImage sharing are **NOT_RUN**. No new first_reason,
cleanup_reason, process_contained, drain_acknowledged, attempt count or generation
was observed for a live session. Old .9 P0 was not repeated.

Historical .9 candidate/system/artifact hashes are rechecked against the unchanged
manifest. Original protected seven files remain byte-identical. Retained encrypted
derived snapshots are not booted or modified; no identity/store/cache/floor/settings
change, certificate renewal, registration, provisioning or teardown occurs.
Private continuation evidence is retained under
`/var/tmp/fc-l042-r2-package-20261026`; partial generated input output remains
ignored under `state-client-build/linux-l042-r2-20261026`.

Owner workstation **NOT_USED**. L05/messages/voice acceptance, Android106 changes,
wire/schema/policy changes, signing and publication **NOT_RUN**.
STATUS/PLAN retain the same L04.2 ID; parent L04 remains IN_PROGRESS.
Secret/JSON/link/staged-scope/whitespace checks PASS; unrelated pre-existing
working-tree changes remain unstaged and preserved. No installed rollback or
remote deployment is needed or performed.

## Prior source checkpoint — preserved evidence, now review accepted

Date: 2026-10-26. Same PLAN **L04.2**, no new top-level ID.
Input main `e3cc0348ad8ee87631b83f78b8f9618876f57138`;
R1 source `9c6f867ea3e866df6a0ce65dbd311e1882336bb0`.
**PARTIAL / STOP before package build: mandatory source verification BLOCKED.**
The two isolated product regressions are fixed and their exact selection passes.
Control CI exceeded its15-minute setup budget before pytest; its complete
failure-ID comparison is unavailable. This is not a new product failure finding
or a claim that the historical54-ID residual set grew. Client Linux CI was still
in dependency preparation at the stop readback. **NEXT — review L04.2-R2.**

The [R1 primary/cleanup correction](2026-10-26-linux-mesh-failure-preservation-l04-2-r1.md)
is retained. The accepted historical .9 live P0 failure is not repeated.
Owner workstation **NOT_USED**; no private state or live gateway in source tests.
Chat delivery_unavailable remains uninvestigated L05 backlog, not a VPN gate.

## Localization: both causes, separately evidenced

The exact CI selection (lifetime, terminal, status native), root/private network
namespace, FC_L021_WORKER and the same test-only native overlay recipe reproduce
**2 FAIL / 13 PASS** on R1. The original two tests and their8s joins/assertions
are unchanged. A read-only pytest observer records only lifecycle booleans,
relative monotonic timestamps, signal counts and return codes, never materials.

Times relative to cleanup_entered; each case has one stop RPC attempt:

| Observation | R1 cancel | R1 peer | Corrected cancel | Corrected peer |
| --- | --- | --- | --- | --- |
| cleanup_entered since test origin | 2345ms | 2352ms | 2318ms | 2331ms |
| stop timeout | 4004ms | 4003ms | 4004ms | 4004ms |
| terminate calls | 2 | 2 | 1 | 1 |
| kill calls by existing join boundary | 0 | 0 | 1 | 1 |
| watcher at8s join | alive | alive | finished at6020ms | finished at6020ms |
| failed / gate.active | false / true | false / true | true / true | true / true |
| process poll/returncode | running/null | running/null | -9 | -9 |
| reap / reader stopped / descriptors closed | no / yes / no | no / yes / no | yes / yes / yes | yes / yes / yes |
| stop acknowledged / cleaned observed | no / no | no / no | no / no | no / no |

**A:** the original assertions fail because the watcher has not finished within
the existing8s boundary: stop4s, terminate2s, duplicate terminate2s, then kill.
No timing assertion or join timeout is increased.

**B:** a separate controlled source red using real NativeWorker subprocess/IPC
and real ServiceOwner with an admission spy proves that R1 releases admission
after force containment without an acknowledged drain. Invalid/negative/EOF stop
replies do not raise CLEANUP_UNCONFIRMED on that old source. This is independent
of the8s observation; a later test-fixture teardown is not presented as native
proof at the original boundary. Corrected9-case old-red selection: **9 FAIL**.
Together these establish **C: both defects**, without attributing either to the
unlocalized historical live .9 Connect failure.

## Contract and scope

- Frozen, memoized internal NativeCleanup exposes process_contained,
  drain_acknowledged, cleanup_reason and admission_release_safe. No wire change.
- Containment requires reaped process, closed stdin/stdout/chat descriptor and
  stopped reader. Nonzero exit alone is not incomplete packet cleanup.
- A drain ACK requires the existing validated stop reply, ok=true and
  state=DISCONNECTED, plus no forced termination. Schema/ID reject booleans.
  EOF, malformed reply, ok=false, STOPPING, exit0 without ACK and forced exit
  cannot release authenticated admission.
- Existing Go ServeWithOwner sends the stop reply only after Server.Close waits
  for the packet lifecycle and chatOwner.Close drains ownership. That existing
  proof is sufficient; no Go, public IPC schema or network protocol modification.
- Stop RPC retains its4s deadline and graceful process exit retains its2s wait.
  There is at most one terminate and one kill, no duplicate initial wait. A7s
  shared cleanup budget bounds containment/reap/reader checks; no synchronization
  sleeps are introduced.
- PacketSession/Supervisor retain R1 first_reason, separate cleanup stage,
  all-stage binding/worker/detach cleanup, retry fencing and generation safety.
  Force-contained worker without drain ACK can still permit packet retry after
  confirmed network detach; no general stop-RPC-failed⇒CLEANUP_PENDING rollback.
- ServiceOwner invalidates current/binding, attempts worker containment even if
  binding close fails, and releases admission only for a strict safe result.
  Otherwise failed is sticky, gate/transport.lock remain chat-owned, new admission
  is OWNER_BUSY, no bootstrap/new worker occurs and close is CLEANUP_UNCONFIRMED.
  Retained admission does not keep a child, reader or descriptor alive.

## Source evidence and stop gate

Initial corrected focused selection: **237 PASS / 2 SKIP** (explicit native
artifact skips). Final added case also refuses forced exit after a valid reply.
Final R1/R2 cleanup selection: **32 PASS / 0 FAIL**, including that case.
Exact authenticated lifetime/terminal/status: **15 PASS / 0 FAIL**. Full desktop
with privileged disposable kernel and real GTK/Xvfb: **1306 PASS / 82 SKIP**.
Final combined/manual/Auto root→UID: **3 PASS / 78.90s**.
Runtime source commit `169aa687f497f8be690be5331879f994636135e1` is pushed and
remote main verified. Full local repository: **36 FAIL / 3387 PASS / 99 SKIP**,
7 passing subtests; all36 failure IDs exactly match CHAT-UX-2 and R1, zero new
failure/error IDs. No suppression, deselection or new xfail is used.

Automatic source CI: native bridge (including exact15/combined), AWG, TCP and
voice source jobs PASS. The evidence-only commit
`ca8c7108f2cc891379533355985554259c297ac4` is pushed/remote verified and does not
change runtime sources or test selections from169aa68. It adds narrow workflow
receipts retaining the full pytest command and nonzero pipeline exit, uploading
only source SHA, outcome, completion, summary and sorted failure/error IDs as
JSON. Both generators validate against the local36-ID log and an incomplete-log
case; pipefail preserves a synthetic nonzero exit17. Raw logs are not uploaded by
the new receipt step. No blanket CI or complete source-gate PASS is claimed.

| CI gate / exact run | Result at stop readback,18:40UTC |
| --- | --- |
| [Native bridge](https://github.com/Joker20380/family_connect/actions/runs/40374958486) | PASS, including exact authenticated15 and combined root→UID |
| [AWG](https://github.com/Joker20380/family_connect/actions/runs/40374958436) | PASS |
| [TCP](https://github.com/Joker20380/family_connect/actions/runs/40374958412) | PASS; publication jobs skipped |
| [Voice/encrypted source](https://github.com/Joker20380/family_connect/actions/runs/40374958304) | PASS, not L05/live voice acceptance |
| [Client Linux](https://github.com/Joker20380/family_connect/actions/runs/40374958403/job/121755378905) | IN_PROGRESS in Python3.12/dependency preparation; source/package steps not yet reached, not PASS |
| [phase0 full pytest](https://github.com/Joker20380/family_connect/actions/runs/40377384729/job/121764050147) | 54 FAIL / 3242 PASS / 226 SKIP,7 subtests; exact54 IDs match R1 retained CI baseline; no new IDs/errors |
| [phase0 Docker](https://github.com/Joker20380/family_connect/actions/runs/40377384729/job/121764049239) | 54 FAIL / 3240 PASS / 228 SKIP,7 subtests; exact54 IDs match R1 Docker; downstream failover not reached |
| [Control exact receipt](https://github.com/Joker20380/family_connect/actions/runs/40377384751/job/121764050127) | CANCELLED at Local HTTP contract proxy dependency setup; annotation: maximum execution time15m0s exceeded; pytest SKIPPED |

Control setup ran18:24:10–18:39:20UTC; the job finished18:39:24UTC. The retained
receipt has outcome=skipped, completed=false, summary=null. Empty failure/error
lists in that incomplete receipt are **not** zero-failure acceptance. The earlier
[169aa68 control run](https://github.com/Joker20380/family_connect/actions/runs/40374958594)
failed its full suite, but available truncated logs are not an exact54-ID proof.
No manual CI retry, timeout increase, apt workaround or source repair follows
this stop. Later asynchronous CI completion cannot retroactively authorize .10
build/live progression in this checkpoint.

### Exact residual-ID accounting

Local36 IDs match both the recorded CHAT-UX-2 and R1 lists. phase0 and Docker54
IDs match the full retained R1 Docker build log (artifact12670228037), not merely
its count. Each completed comparison has new_failure_ids=[], missing_failure_ids=[]
and error_ids=[]. Control comparison remains **NOT_PROVEN**, rather than borrowing
phase0's result. Affected cleanup/lifetime tests are absent from all completed
failure sets and separately pass the exact native selection.

Canonical sorted ID-list SHA256 (UTF-8 JSON with compact separators):

- Local36: `e8e3d06b12a79058aefbcd7c653627e7b71eeee5a20d9a8ed7751f316713f549`.
- R1/R2 CI54: `066830f3630ee7caa5ccd8d956c8861f13b459a7eca3ffd4b48bc03382bd5a60`.

Download/readback-verified sanitized evidence artifacts:

| Evidence | Artifact ID | ZIP SHA256 |
| --- | --- | --- |
| R1 Docker baseline | 12670228037 | `6b93e382aff386bfdfeaa99b71411633f902a542fb26b681b29c1073cc45a28c` |
| phase0 receipt | 12676791295 | `281afb35d88db5aeb5479287c870f307df0c4a0349634e87d28671e5d6b6edc5` |
| phase0 Docker | 12676921545 | `dd9631cffd5d1adcaaaac75505f2fa93cd6b64272aab4ac04e868518f1e4ef98` |
| Control incomplete receipt | 12677746129 | `8a5d7dd2fbaf2fd885dbf59b546771b284c00ab464c70c74ca982554a71bbcfb` |

The automatic internal-candidate preview rejects changed system source hashes
against the historical pinned candidate contract before sealing. Readback of
both R1 job121726914811 and R2 job121755378779 confirms the same rejection at
linux_candidate.embed, not a new pytest failure ID. Push CI built a temporary
preview system and passed its smoke, but no preview output is promoted or reused.
It is not the requested .10 build or acceptance; reference/inventory updates belong
to the gated new system/package phase, not a bypass of historical .9 integrity.

Fixture-only corrections are retained, not hidden: initial test import order and
unsafe temporary root-ownership fixture were corrected before the retained red
comparison; standalone tests use an admission spy while exact isolated tests keep
real root ownership/OWNER_BUSY. Two typed fake workers explicitly return the new
cleanup result. The combined observer initially discarded super().close's result;
it now returns it unchanged, without changing assertions, timing or product proof.
Initial non-privileged desktop skipped two TUN preflight tests; the final proper
kernel run exercises them. Fixture compilation first needed container Git
safe.directory and missing pinned Go dependencies; those were corrected without
changing source pins. The resulting fixture is never a release/system artifact.

Review policy: exact historical failure IDs may remain only with no additional
failure/error IDs and no suppression/xfail/deselection. This is not an overall
green-CI claim. The local reference is the36 IDs in
[CHAT-UX-2 validation](2026-10-26-chat-ux-2/validation.json) and R1; control/phase0/
Docker are compared to their corresponding recorded baseline, not local counts.

## Candidate, state and boundaries

Requested exact .10 candidate and matching system **NOT_BUILT**, IDs/hashes not
assigned. Package inventory/imports/setup/rollback/tampered/mixed/old-build/
coherence/AWG/TCP gates and new live P0/P1/Auto/lifecycle are **NOT_RUN**. The stop
is before Phase B, not a failed installed .10 scenario. No .10 DEB/AppImage or
system archive hash is fabricated; rollout/installed rollback are NOT_RUN.
The historical [exact .9 manifest](2026-10-26-chat-ux-2/candidate-delivery.json),
system and retained encrypted test bases are not modified or booted in this phase.
Old candidate `6f312d1e7c783ea42a39ca164d93d74b0ec4faf5bac53e24c12551cedd052a5b`
and system `43266d97c6a9f8d4e7026727cbb4b5cb6aeea49db799f93bd798b67a8135198c`
remain historical inputs, not R2 outputs. All three .9 artifact hashes/sizes and
the system archive hash match that manifest. Original protected seven files are
byte-identical; derived encrypted snapshots remain unbooted. No live Connect,
renewal, chat registration, identity creation or teardown receipt change occurred.
No identity/store/cache/floors/settings, provisioning, policy or underlay IPv6 edits.
No deployment, installed rollback, owner-workstation operation, Android106,
Windows/iOS acceptance, L05/messages/voice, signing, publication or teardown.
Private source evidence is retained under `/var/tmp/fc-l042-r2-20261026`.
It includes old/new timelines, full local log/ID comparisons, exact CI receipts
and archive digests; no materials or private fixture values enter the report.
Secret scan, JSON validation, local links, staged scope and git diff --check PASS.
Unrelated existing working-tree changes are preserved and excluded from commits.
L04.2 remains PARTIAL; parent L04 IN_PROGRESS, L04.1 DONE, L05 NOT_RUN and
L06/L07/L08 unchanged. **STOP. NEXT — review L04.2-R2.**
