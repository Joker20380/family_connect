# L04.2-R2 — process containment versus authenticated drain

Date: 2026-10-26. Same PLAN **L04.2**, no new top-level ID.
Input main `e3cc0348ad8ee87631b83f78b8f9618876f57138`;
R1 source `9c6f867ea3e866df6a0ce65dbd311e1882336bb0`.
**Source checkpoint / remaining source gate IN_PROGRESS. Not an installed PASS.**

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

## Source evidence and remaining gates

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
voice source jobs PASS. phase0 Docker: **54 FAIL / 3240 PASS / 228 SKIP**,
7 passing subtests; its54 IDs exactly match the retained R1 Docker artifact,
zero new failure/error IDs. CI is not generally green. Client Linux is pending.
Control/phase0 full-suite jobs fail; their exact-ID comparison is pending, not
inferred from counts or truncated logs. Narrow workflow evidence changes retain
the full pytest command and nonzero pipeline exit, and upload only source SHA,
outcome, completion, summary and sorted failure/error IDs as JSON. Both receipt
generators validate against the local36-ID log and an incomplete-log case;
pipefail preserves a synthetic nonzero exit17. Raw logs are not uploaded by this
new receipt step. No source/package acceptance is claimed before all required
source results and failure-ID checks.

The automatic internal-candidate preview rejects changed system source hashes
against the historical pinned candidate contract before sealing. It is not a
.10 build or acceptance; reference/inventory updates belong to the gated new
system/package phase, not a bypass of historical .9 integrity checks.

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

New .10 candidate and system **NOT_BUILT**, IDs/hashes not assigned. Package
inventory/setup/rollback/mixed/old-build/coherence gates and new live P0/P1/Auto/
lifecycle are **NOT_RUN** until the complete source gate passes.
The historical [exact .9 manifest](2026-10-26-chat-ux-2/candidate-delivery.json),
system and retained encrypted test bases are not modified or booted in this phase.
No identity/store/cache/floors/settings, provisioning, policy or underlay IPv6 edits.
No deployment, installed rollback, owner-workstation operation, Android106,
Windows/iOS acceptance, L05/messages/voice, signing, publication or teardown.
Private source evidence is retained under `/var/tmp/fc-l042-r2-20261026`.
