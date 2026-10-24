# D01.3-R — DIRECT public completion/admission

Date: **2026-10-24**. Bounded checkpoint; local PASS, mandatory new-source CI pending.
**STOP. NEXT — review D01.3-R.** D01 remains open; D02.1-R PARTIAL/NOT_RUN.

Entry: clean current `main` = remote `68e4029f58d54384471576c623b08e89752f2c94`.
No checkout rollback. Review accepts D01.3 ChatBridge and Host/ServiceHost;
D01.3 remains PARTIAL per review until this DIRECT correction is accepted.
The [D01.3 report](2026-10-24-desktop-chat-admission-d01-3.md), exact historical
SHA/jobs/counts and accepted L01/L01-R, local L02/L02.2, D03/D04/D05 are preserved.

## Cause and red/green

DirectBridge inherits ChatBridge's successful probe→EOF completion wait, but
DirectHost overrides `_serve` and closed its socket outside the admission lock.
EOF could reach the client while the completed probe still occupied public slot4.

[Regression](../../clients/desktop/tests/test_chat_direct_completion.py) reuses
`test_chat_direct.integration/enroll`: real DirectHost, DirectBridge, Authority,
authenticated registration validation, AF_UNIX and SCM_RIGHTS. Only native backing
is synthetic: controlled socketpairs, no peer4s timeout/thread or external network.
Three authorized live mailboxes persist until explicit teardown. Events hold the
probe handler **after real socket.close**, assert fd=-1 and actual client EOF, then
observe the dependent open's admission attempt. A lock observer retains the same
underlying mutex and distinguishes acquire from waiting; proof is the actual
public exchange, not just lock state. No sleeps/retry or repeated-until-green runs.

Before the product edit: **1 failed / 0.56s**, ConnectionResetError104 after EOF,
active4, native opens3, API sends2 (challenge/register only). Red log SHA256:
`491dfe788a7be64f10e5235e3ea7ac1c76212a86fca1c91b4a8aab8e55462ed7`.
This does **not** establish the exact cause/schedule of historical Client Linux
BrokenPipeError on `dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`.

Fix: move DirectHost connection.close into the existing lock enclosing active.pop.
Monitor/native/mailbox cleanup still precedes it; handler accounting remains until
cleanup. No client/protocol/native Coordinator/refcount/authority/endpoint changes.
Public4, native CONTROL4/MAX_JOBS, UID/device/profile, expiry/revocation, typed
terminal errors, cancellation/deadline and no SYSTEM fallback/replay are unchanged.

After: fourth mailbox waits at admission and succeeds, bidirectional bytes pass,
fifth live mailbox is rejected, explicit closure restores capacity. Only one
dependent open, no additional API sends; backing opens/accounting are asserted.
Cancel/client-close/deadline and shutdown while post-close completion is held are
bounded; shutdown stops admission before releasing the test barrier. The inherited
open reply timeout remains its existing budget+4s; no new retry/deadline policy.
Active handlers persist while cleanup is held; teardown checks active/native counts,
FDs and thread sets including DIRECT disconnect monitors and mailbox writers.

## Checks and provenance

- Focused green: **30 passed / 12.34s** (five DIRECT + unchanged24 public completion
  + unchanged original bounded-mailbox test and all its assertions).
- Root→UID/process: **13 passed / 0.84s**, locked Python3.13 disposable container,
  actual trusted native worker; no host network/DNS modifications.
- Dependent DIRECT/public IPC/error/lifecycle selection: **326 passed / 56.93s**,
  locked Python3.13 container, including `test_chat_direct`, both completion suites,
  mesh_chat/host/service/status, mesh_service, Auto mesh/platform, chat_service,
  ChatHTTP terminal/no-replay and messenger resilient/client tests.
- Mandatory Client Linux desktop pytest, authenticated15, combined3, Auto/DIRECT
  kernel, root→UID and full CI gates remain enabled and unchanged. New-source
  SHA/jobs/results will be recorded separately after ordinary commit/push; NOT_RUN
  here until observed. Old green results are not assigned to new source.
- Historical54 residual failures and voice holding-state failure remain separate;
  no fixes, disabled tests or reruns to obtain green in this scope.

Source/tests/docs form one logical checkpoint. Content/local-link checks,
`git diff --check` and staged secret/artifact review precede commit. Logs and
worker binaries stay outside Git. No version/install/deployment changes; rollback
is an ordinary source revert, not a catalog/server operation. Identity/WG keys,
activation/Support ID/history/settings/signed floors/Android106/reference pins stay
unchanged. L03/install/live/publication/Windows/fleet/iOS **NOT_RUN**.
