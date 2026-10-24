# D01.3 — public chat completion/admission

Date: **2026-10-24**. Bounded source checkpoint, **CI pending**.
**STOP. NEXT — review D01.3.** D01 remains open; D02.1-R PARTIAL/NOT_RUN.

Entry: clean current `main` and remote
`d448e99b55e594522c02234ac2a87575603a6bbb`; no checkout rollback.
L02.2 review accepted: the original local L02 authenticated SERVICE_ONLY → VPN
publication → EXISTING_EXIT → new SERVICE_ONLY criterion is complete for both
Manual and Auto, at source `dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`.
Its [historical report](2026-10-24-linux-chat-mesh-l02-2.md) and exact receipts are
preserved, not rewritten as D01.3 evidence. No installed/live/F-01 claim.

## Cause and deterministic red/green

Host wrote a successful probe/prepare reply before monitor cleanup, socket close
and removal from `active`. ChatBridge treated that reply as completion and opened
the next connection. With three live mailboxes, the completed-but-still-active
control operation occupied slot4; Host rejected the dependent open at cap4.
There was also a close→active-removal window outside the admission lock.

[New tests](../../clients/desktop/tests/test_chat_public_completion.py) use actual
Host, ServiceHost, ChatBridge and AF_UNIX/SCM_RIGHTS, with explicit events holding
the successful server response's return and active removal. A client recv barrier
distinguishes waiting for completion from starting another open. No random sleeps,
repeated attempts or HTTP retries. The native lane/material resolver are synthetic;
these tests do not replace the accepted15 authenticated, combined3 or kernel gates.

Before production edits, both probe and prepare cases failed deterministically:
**2 failed / 0.77s**, dependent open raised **ConnectionResetError(104)** with
active4 and only three operation leases (plus the service generation lease).
Red log SHA256: `50d48f976b55f83f4732bb590c9de9b641d98a1c05522854b55099b0a8eabfd1`.
This proves the race class, not the precise scheduling of the historical
[Client Linux failure](https://github.com/Joker20380/family_connect/actions/runs/40129362261/job/120977564976)
on `dac0f6b45be6ed8703d3de93ff5fdbc67462eabe` (BrokenPipeError at sendall).
The original failing test and every assertion remain unchanged.

## Completion contract

- Client waits for control EOF after a validated success, within the original
  deadline and max4s. Cancellation/client close interrupt it; timeout is DEADLINE;
  unexpected bytes are DENIED. Typed terminal replies do not wait or get replaced.
- Server retains active accounting through monitor/lease cleanup. Socket close
  and active removal share the admission lock; the next accept cannot reject for
  the just-completed slot. No early removal of a handler to make room.
- Host shutdown stops admission before early socket shutdown and joins handlers;
  held cleanup stays tracked. Client completion is not a capacity reservation
  against unrelated demand, and no open/request/HTTP retry is introduced.
- Both sides of the completion contract are tested together; wire schema1 and
  response fields stay unchanged. An older client does not wait, and an older
  host does not serialize EOF/removal: mixed versions are not claimed race-free.
  This is a source checkpoint, not an installed mixed-version upgrade acceptance.
- Public4, native CONTROL4/MAX_JOBS, generation pin/refcount, UID/device/profile,
  native drain ordering and VPN publication are unchanged. No SYSTEM fallback.

After: fourth mailbox passes, fifth live mailbox rejected, both halves closing
returns capacity; prepare behaves identically. Actual cancel/client-close/deadline/
Host-close during held completion stay bounded; retained handler blocks Host.close.
Tests count native-fixture leases, opens, exactly one HTTP send, connections,
descriptors and live handler/monitor threads. EOF/slot-removal barrier additionally
checks admission-lock ownership while the next request waits.
During test development, two assertions initially awaited mailbox cleanup without
closing the synthetic peer's half; corrected the test to finish both halves, not
product half-close semantics. This intermediate failure is not hidden as a PASS.

## Checks and source receipt

Local locked Python3.13: initial addressed Host/ServiceHost/status/error set
**121 passed / 14.62s**; final24 regressions plus lane/manual/Auto/mailbox/error
dependencies **266 passed / 38.89s**. Native code is unchanged; existing standard
and authenticated workers from L02.2 are reused, not newly claimed builds.
On source **`23e3c5513ab9c37e919f228066c0e23f733a997e`**, ordinarily pushed and
remote-verified: original15 authenticated **15 passed / 109.34s**, combined3
**3 passed / 79.20s** (Manual/Auto real OFF→ON→OFF plus CONTROL release), actual
root→UID/process **13 passed / 0.86s**. `scripts.verify_desktop_reference`:
**175 pins PASS**. No native source/pin/Coordinator changes or new native build.
The original failing test file is byte-for-byte unchanged from entry.

Reproduction: `python -m pytest -q clients/desktop/tests/test_chat_public_completion.py`
inside the locked Linux test environment (all24 cases). The broader266 selection
adds `test_mesh_chat{,_host,_service,_status}.py`, `test_mesh_service.py`,
`test_auto_mesh.py`, `test_auto_platform.py`, `test_chat_service.py`,
`tests/test_chat_bridge_http.py`, `messenger/tests/test_resilient.py` and
`messenger/tests/test_chat_client.py`. Existing native fixtures use the documented
[lifetime](../../tests/fixtures/mesh_lifetime/README.md) and
[combined](../../tests/fixtures/mesh_combined/README.md) runners, unchanged.

| Local evidence | SHA256 |
|---|---|
|266 addressed/dependent|`a121b6a7ad81316e97cf89aadc7dcc1e04a33539868b6687ed1a7e3b4b501502`|
|15 authenticated|`48fa770bd69badc414df51087d9b24690f7fc35c3d6401053a1cbf6f017c99ca`|
|13 root→UID/process|`65d9d40c8e08cc3c0b019401fa3b2477b38093bee9d8e9b249852f5fa9a5580b`|
|combined3|`273bae942acd37d85a57b0b8555757593c23746821364b52d21bc081fc562e24`|

Follow-up only hardens the new test barrier: publish the held handler before
sending response bytes, so the cancellation assertions cannot overtake that
publication. **24 passed / 6.23s**, log SHA256
`79cc04e9231e8d69d6328e3da67fa59232c6a84328e2b015dc8316e4cc41742d`.
No production changes follow `23e3c55`. This is an explicit test-ordering change,
not a retry to obtain green; final follow-up source/CI is recorded separately.

CI for production source **`23e3c5513ab9c37e919f228066c0e23f733a997e`**:

| Suite | Exact run/job | Result |
|---|---|---|
|Client Linux, including mandatory desktop pytest|[40131682971 / 120984525484](https://github.com/Joker20380/family_connect/actions/runs/40131682971/job/120984525484)|PASS; both pytest steps and whole Linux job success|
|isolated-linux|[40131682996 / 120984525274](https://github.com/Joker20380/family_connect/actions/runs/40131682996/job/120984525274)|PASS; original15, combined3, root→UID/process, Auto/DIRECT kernel and native race retained|
|native protocol Linux|40131682996 / 120984525228|PASS|
|phase0/tests|[40131682943 / 120984525008](https://github.com/Joker20380/family_connect/actions/runs/40131682943/job/120984525008)|3056 passed / 54 failed / 138 skipped, errors0, 183.37s|
|control|40131682940 / 120984524983|IN_PROGRESS at20:58UTC; not PASS|
|Docker|40131682943 / 120984524829|IN_PROGRESS at20:58UTC; not PASS|
|voice|40131683016 / 120984525157|PASS, without a voice code change or rerun; earlier holding failure remains separately recorded|
|AWG / TCP|40131682989 / 120984524985; 40131682949 / 120984525214|PASS; TCP release jobs skipped|

Client Linux mandatory desktop pytest must also PASS on the follow-up source
before final completion. Full CI remains enabled; no overall CI PASS is claimed.

Previous source `dac0f6b45be6ed8703d3de93ff5fdbc67462eabe`, separate results:
control **3032/54/138**, phase0/tests **3032/54/138**, Docker **3030/54/140**
(passed/failed/skipped), errors0; Client Linux **1003/1/94**; voice pointer/holding
failure. Isolated-linux15+combined3/root→UID/Auto/DIRECT/race and AWG/TCP PASS.
These54 residual failures and voice failure are out of scope, not fixed/disabled.
New source SHA/jobs and content/link/diff checks: pending source commit and CI.

No version/install/deployment change; rollback is an ordinary source revert,
not a catalog or server operation. Identity/WG keys/activation/Support ID/history/
settings/signed floors/Android106 and reference pins remain unchanged.
L03, installation, live, publication, Windows, fleet and iOS **NOT_RUN**.
