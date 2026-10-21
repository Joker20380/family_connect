# Consolidated Android speed candidate — 21 October 2026

Signed97 installed owner-only; approved shared gateway transition complete.
Original96 P0, new97 P0a/P1a/P2a/P2b/P1b each delivered15/15 responses, total48.0703125MiB.
New P0 is slower beyond the frozen15% review threshold; integration review is saved,
live cause unresolved, original/new equivalence and product admission **not given**.
P0a later Android4/gateway3 errors exclude clean acceptance. First P1 is faster,
not repeated. Later P1 gateway3/exhaustion and P2 preload Android1 exclude clean
acceptance without negating body delivery. P2 post errors1→10 in664.356s include
load/background; first error stage/branch unknown, no terminal failure observed.
P2a later server terminal1/exhaustion retained. P2b post0 then later Android2/server1
and exhaustion: not clean acceptance. P1b delivered15/15, actual both-end P1/Q0,
initial errors0; post errors1 over831.678s including background, not clean acceptance.
P1b later gateway3/exhaustion retained. Final P0b both-end8/16/effective8/LEGACY64:
single and12 small complete, two parallel partial/curl18 during proven scheduled
renewal; TUN-route guard failed, no retry.103/105 complete across seven phases,
56.08203125MiB reserved (52.08203125MiB complete plus1.569685MiB partial received).
Raw windows single2.116×/2.024×; reverse aggregate unavailable. No added Q1 speed gain.
Final `(14)` confirms new P0 session at both ends, Android CONNECTED/READY with17
session protocol errors, cause unknown. Cycle closed with limitations; keep P0,
no more owner exports/actions or load. Post-renewal active route/DNS/HTTPS not run.
See the [integration report](../../../docs/releases/2026-10-21-android-speed-candidate.md)
and [machine evidence](../../../docs/releases/2026-10-21-android-speed-candidate.evidence.json).

## Source and replay contract

Work directory: `state-client-build/speed-candidate-20261021` (private/ignored).
Exact accepted inputs are beta96's `mobile-bootstrap-20261020/android-source` and
the installed734b6ca6… gateway's `rtp-pacing-20261020/candidate`, not GitHub main.
`baseline.json`, the original build manifests and `source-seal.json` pin inputs,
outputs and all changed files. The combined Android patch includes the dormant Q1
delta; **do not apply the Q1 patch and then the combined patch to the same tree**.

| Delta | Replay root | Scope |
|---|---|---|
| `android-q1-core.apply_patch` | A fresh copy of beta96 `carrier/` | Q1 core alone, no profile activation |
| `android96-to97.apply_patch` | A fresh copy of complete beta96 Android source | Complete code97, including gated Q1 |
| `gateway734-to-speed.apply_patch` | A fresh copy of accepted734 gateway source | Owner-targeted P0/P1/P2, existing dormant Q1 reused |

The `.patch` files are readable unified diffs; `.apply_patch` is the canonical
replay input (`apply_patch < …` from the specified **fresh** copy). All three
replays matched every source file, not only changed-file hashes. `seal.py` records
this and refuses existing replay destinations. Do not overwrite the accepted
capsules. `q1_core.py` preserves the minimal saved Q1 transplant recipe; sealed
patches, rather than an old development generator, define the final source.

## Implemented profiles

- P0: existing RS local send8/receive16, peer receive16 on the accepted pair,
  effective send8; LEGACY64/65536B Mux; Q0.
- P1: RS OPEN receive32, local send32, **actual peer receive checked separately**;
  CREDIT128/131072B via existing authenticated ALPN; Q0.
- P2: P1 plus local-media-write completion Q1. No remote-ACK wait in SendContext.
- Only new whole-device sessions use the Android preference. The gateway requires
  the existing protected operator directory and an exact authorized-peer key tag;
  all other peers stay P0. Neither setting grants access or mutates OPEN mid-session.
- Carrier L, A0/33ms timebase, original2ms/frame, packing/FEC/pacing OFF. No QUIC,
  SACK-hole/read-alignment or experimental dependency changes.

## Local commands and scope

Run from repository root. Commands use pinned offline Go/NDK/Gradle tools; Pion and
loopback tests may require ordinary outside-sandbox execution. These are local
tests, not Telemost traffic. Do not re-run `prepare.py` over the existing workdir.

```sh
python3 tests/fixtures/speed_candidate/check.py focused
python3 tests/fixtures/speed_candidate/check.py queue
python3 tests/fixtures/speed_candidate/compatibility.py
python3 tests/fixtures/speed_candidate/head32.py
python3 tests/fixtures/speed_candidate/security.py
python3 tests/fixtures/speed_candidate/final_checks.py
python3 tests/fixtures/speed_candidate/sign.py --check-only
```

`security.py` uses disposable certificates, unchanged lease/revocation production
logic, and a test-only bounded wait for the prior control stream to close before
another immediate exchange. `head32.py` adapts the existing full-window head-loss
fixture to32, including its bitmap expectation. Both changes and earlier failures
are retained. Broad Android bootstrap assertions are **not all green**; see the
report's paired accepted96/candidate97 reproductions. A successful Q0 reproducer
test means it reproduced the bug, not that Q0 recovered successfully.

`build.py android` reuses the ordinary bootstrap96 build and produces unsigned97;
`build.py gateway` builds the same existing gateway diagnostic tag. Neither deploys.
The sealed native/source inventory is authoritative; a version string is not proof
that a binary was installed. `sign.py` without `--check-only` invokes the existing
protected vault dialogue; never supply/store/print its password. Do not invoke it
until the actual installed version and code97 suitability have been rechecked.

## Owner continuation — installed, P0 controls done

Do not rerun install/deploy/signing blindly: read `upgrade-receipt.json`,
`delivery/signing-receipt.json` and `transitions/private/deploy-NL.jsonl` first.
Final installed97 APK SHA is `d7c02ef5e947733702490c2bf5b6afc0d17dbcb5f19b44eca478d621dfcf928f`.
The first unused signed UI build is under `superseded-ui`, never installed. Final
launcher is FriendsActivity;190 JVM tests pass and native is unchanged. The shared
restart12:30UTC was explicitly approved; exact734 rollback is staged but not run.
The first startup publication gate failed before ordinary startup published its
new catalog; `candidate-ready` passed the identical gate, no second restart.

1. Final closure is in `owner-p0-final-receipt.json`; `(14)` matches new gateway
   sessiond0ca9226… actual P0 both ends, Android errors17 (not interrupted P0b).
   No more owner actions/exports/load. The following procedures are retained for
   provenance, not a request to repeat them. All planned phases have been attempted; do not rerun `scope.py`/`measure.py` for
   P0b or rename a retry. Current policy is P0. Gateway sessiond0ca9226… advertises
   effective8/LEGACY64 after renewal; Android receipt still pending. Request a
   current export without disconnect/profile switch, then read-only
   `readback.py UNIQUE_LABEL` / `observe.py UNIQUE_LABEL 2026-10-21T14:11:30Z`.
2. Reconcile interrupted P0b history using `post_export.py P0b SAVED_EXPORT LABEL`.
   The old-epoch terminal is in `phase-P0b/phase-analysis.json`, not the new-epoch
   journal. Keep this provenance separate; do not invent a zero final Android count
   or merge different sessions. P1b closure is already saved in
   `post-P1b-p0b-preflight.json` (gateway3/exhaustion after completed bodies).
3. Verify current97 `ring`, P0 actual8/16/peer16/effective8/LEGACY64/Q0 via
   `validate_export`, same-tag new gateway receipt/activity and actual TUN route.
   READY and VPN object presence alone are insufficient. No new traffic gate/sweep.
   Do not interpret clocks across hosts as one-way latency or exact outage duration.
4. Original/new P0 speed divergence triggered the frozen15% review. `p0_audit.py`
   records unchanged P0 configuration/protocol/core paths and actual limits, but
   cause remains unresolved. Do not mark that baseline pair clean/comparable or
   waive the criterion. Remaining new-pair contrasts are measurements, not admission.
5. Keep P0; no automatic profile changes/retry/tuning. The existing owner-targeted
   policy workflow remains the only profile path if a later authorized change is
   required. Full8MiB+12KiB per attempted phase remains debited (including failed
   P0b); common64MiB budget,150s deadline. Do not refund or hide partial responses.
6. Preserve pre/post same-session counters, raw requests and terminal reports.
   `phase_results.py original96 P0a` summarizes retained intervals and resource scope;
   `after_original.py` uses the existing bounded journald continuation parser.
   Original late closures are not incomplete downloads; historical nonzero counters
   are not new errors. Missing coverage is unknown. `measure.py` intentionally leaves
   `clean_acceptance=false` for final review; terminal reset never becomes success.
7. Finally set both next-session profiles P0, manually reconnect once, verify actual
   send8/receive16/peer16/effective8 and LEGACY64 at both ends, stop all collectors.
   No Android/security downgrade, tester distribution, push or public release.

The HTTP meter records body bytes/SHA256, HTTP/TLS checks, TTFB and full time. Its
observed SHA256 is **not** a pre-known origin hash for the external test body.
The local integration tests provide deterministic byte-exact contracts. Do not
upgrade the physical meter's contract in prose. Setup/closure errors and raw
attempts stay in evidence; terminal reset is never successful LabDrain.

Actual97 signing/install, READY97 and original/new P0 delivery are verified.
Repeated P1/P2 contrasts, final P0 return and whole-wire/Android phase CPU cost remain unmeasured;
automatic network-loss recovery and overnight stability NOT_RUN. `evidence.py`
indexes existing receipts only and refuses unreviewed additional phase directories.
It does not run tests, network requests, signing or deployment.

Supplementary observation13:48 failed once by SSH30s timeout and once by the
32MiB raw-journal guard; both attempts are retained. `observe.py LABEL [SINCE_UTC]`
and the optional final argument of `scope.py` can narrow the journal interval.
Use a known UTC boundary before the required session startup/previous close;
the successful13:45Z filter retains P2b closure and P1b startup,5,061,871B,parser0.

P0b interruption is independently explained by the existing scheduled renewal
`scheduled-1792591872-28bb9be0fa02eed7`: COMMITTED, gateway stop14:11:24/restart
14:11:33UTC, exact archived profile changes certificate/revocations only. The
read-only `state_change.py` receipts and `profile-delta` comparison neither
construct a renewal controller nor trigger recovery. First profile probe failed
because active-owner state had already been archived; failure retained. Do not
repeat these immutable receipt calls. Earlier11:41 change remains unexplained.
Offline `phase_results.py` preserves raw partial byte-rate but qualifies completed
goodput as null for incomplete cells; existing bounded journal parser recovers the
split terminal. Original two parse errors retained, nine helper tests pass, meter
and failure handling unchanged. All seven collectors stopped.
The4000-entry/32MiB/20s journal and30s SSH limits, exact invocation, parser checks,
actual startup/new-tag/fresh-trace gates remain unchanged. Earlier receipts are
retained separately, not assumed absent from the filtered interval. This changes
readback selection only, not product code, traffic, counters or phase instrumentation.

`post_export.py PHASE SAVED_EXPORT LABEL` binds later current/history snapshots to
that phase's exact tag; it never substitutes the old incident. Archives alone are
not terminal receipts. P0 Android4 occurred after its clean immediate post-load
snapshot; gateway3 is whole-session with unknown first-error time. Neither late
error is deleted or turned into incomplete HTTP delivery. Later readbacks include
bounded phone memory/CPU point observations outside load, not reconstructed earlier
phase CPU/peak. The bulk collector/instrumentation itself is unchanged.
