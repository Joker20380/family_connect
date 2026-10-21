# Negotiated64/128KiB compatibility capsule

This implements the missing compatibility contract, not another RTP/RS tuning
experiment. See `docs/adr/2026-10-20-negotiated-mux-credit.md` and the continuation
of `docs/releases/2026-10-20-mesh-mux-credit.md`.

## Exact sources

Accepted old client: `state-client-build/rtp-deadline-20261020/normal94/android-source`.
Accepted old server: `state-client-build/tunnel-restart-20261019/gateway-source/carrier`.
Private current capsule: `state-client-build/mux-profile-20261020` (no production
credentials in this fixture directory). `prepare.py` pins old manifests before
copying. Never replace accepted sources with current Git main.

- `complete-functional.patch`: b9→negotiated implementation and all extra tests.
- `complete-gateway.patch`: b9→deployed implementation plus bounded counters.
- `complete-android.patch`: accepted94→built95, including dedicated client opt-in
  and versionCode; Android ordinary build has no fc_perf_diagnostic tag.
- `negotiated-profile.patch`: earlier core-only checkpoint, retained as evidence;
  it is not the complete final patch. Do not apply both patches cumulatively.

Apply the appropriate complete patch to a **fresh copy** of its stated base with
`git apply`, not to the active accepted capsule. `seal_final.py` inventories all
deltas; `final-source-seals.json` and `negotiated-build.json` pin the actual inputs.
All three complete patches passed fresh-base `git apply --check`.

## Validation

`check.py suite|delta|observed` runs affected race tests with pinned offline tools.
`cross_process.py` compiles actual94 client, actualb9 server and new code and runs
five real TLS/RS/Mux interoperability cases. `--resume` uses the existing compiled
executables after the sandbox socket restriction; it does not emulate old peers.
`lease_checks.py`/`lease_retry.py` add/run128 persistent-lease and fresh-floor denial
counterparts using disposable ProductStore fixtures from
`pilot.telemost_family_fixture`, never production enrollment or keys.

Retain failed logs. Initial sandbox loopback/Gradle failures, a missing test import,
fixture dependency/opt-in issues, UI automation failures and the repaired null
Streams evidence parser are not successful checks. Passing reruns are listed in
the report. Synthetic byte-exact is not origin-byte-exact physical acceptance.

## Build and operator workflow

`build_android.py`, `sign.py`, `build_gateway.py`, `rollout.py`, `upgrade.py` reuse
pinned established build/sign/current-material guard workflows. Sign only through
the existing protected vault UI; never pass passwords as arguments or print them.
The installed95 is owner-only; tester remains94. No public release or push.

`policy.py LEGACY64|CREDIT128 ON|OFF LABEL` writes only two protected local operator
files atomically; a profile change affects **new sessions only**. Gateway rollback
uses fresh guards and exactb9; new client then negotiates legacy, no downgrade.
Do not rerun a saved transition intent or reuse a receipt label blindly.

`measure.py` reuses the exact phone HTTP/1.1 TUN request and bounded collector.
Each physical phase reserves8MiB bulk+64KiB control before requests; all task
reservations count toward64MiB,150s/request, no retries. A session/profile/counter
gate runs first. `B1` stopped before traffic on a profile mismatch; it is **not** a
candidate result. `return95` stopped before traffic on ambiguous session tags.
`control.py` is the one final64KiB counters-off phone health request, not a speed
sample and not an attribution to a specific server media session.

Manual B1 continuation uses `session-scope-B1m.json` from fresh owner APK/network
and gateway/session readbacks. `session_scope.py` selects only that validated tag
for analysis; raw capture still preserves other peers. Missing/stale owner samples,
profile/window mismatch, changed gateway invocation or owner VPN stop the phase.
Five local attribution tests cover mixed peers, missing/stale owner and mismatched
profile/window; no transport/HTTP meter or binary change. `evidence.py` uses the
same scope, while RSS/CPU remain whole-process metrics. Do not attribute another
peer's errors or the old64 session's errors to the new128 session.

`OwnerUi.java`/`ui_read.py` are shell UIAutomator helpers, not an installed APK or
transport API. Read-only UI works with continuous animation; touch injection is
denied by MIUI (`INJECT_EVENTS`). After that denial no other injection route was
used. `session.py` is therefore not currently usable on this owner device without
an explicit change by the user. `await_manual.py` only watches network IDs for a
user-operated ordinary Disconnect/Connect. Its120s wait expired without a restart.
No lockscreen bypass, developer-security setting change or data reset is performed.

The first checkpoint ended LEGACY64/counters OFF; the later B1 preparation selected
CREDIT128 for new sessions only. Consult the latest report/STATUS and fresh
readback rather than interpreting an old receipt as current policy. For paired work,
the owner must perform ordinary UI Disconnect/Connect at the profile boundaries;
read fresh actual session/profile receipts before traffic. Do not interpret the
unfinished comparison as physical rejection of128 or as speed acceptance.
On this device do not invoke `session.py`, inject input, or start another120s
manual wait. Finish each authorized step with no collectors left running, then
continue after the owner's next message.
