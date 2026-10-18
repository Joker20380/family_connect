# Bootstrap cleanup race — deployment and owner acceptance, 2026-10-05

Superseding update: [server readiness correction05.10](2026-10-05-readiness-clock-skew.md)
is deployed13:55–13:56UTC, issuer5 renewed, unchanged owner65 fresh READY/ACK PASS.
Gateway executable remains05571644. New effective gateway ceiling17:52:14UTC today.
The following export12/13 decisions precede that resumed work; tester result remains pending.

Latest: [export13 mobile attempt](2026-10-05-field-export13-beta65.md) on current65
fails before restricted native startup after AWG/TCP NETWORK and FETCH_FAILED.
This does not exercise the new gateway recovery path. No further implementation or
deployment occurred after the user stopped development to run that one test.

Follow-up: [export12 diagnosis](2026-10-05-field-export12-beta65.md) confirms tester65
but native import fails before a session, with client/server clock-sensitive guards.
User explicitly defers that correction; keep working VPN for coordination and do not
request clock changes, screenshots or another mobile trial. Earlier gates below are
historical, not instructions to repeat the VPN-off preparation.

## Scope and delivery state

Continuation of the [beta65 failed recovery gate](2026-10-04-beta65-readiness-candidate.md).
Source prepared on HEAD `5263410`; user authorized scoped commit/push05.10.
Final sourcea813dc5 passes CI and gateway artifact verification (checkpoint below).
Follow-up10:13UTC deploys that gateway; owner65 runtime recovery/security acceptance
now PASS, detailed at the end. No product APK version change, rebuild, signing or
installation. Targeted publication of the previously accepted immutable65 and public
download verification completed10:27UTC. Unrelated dirty documentation is preserved. Original field DATA/ACK loss
remains unlocalized; this controlled acceptance is not a Krasnodar field-fix claim.

Last verified04.10: owner Redmi `0.1.18-beta65`/65; tester and targeted public64;
default/catalog/invitation60. Accepted APK65 source
`86fa1bae8b97ff34d3e8cbd5b3cfe923cb7d71a6`, four exact-source workflows PASS;
signed APK SHA256 `dfbdb5352b8c707fb77ff3d7392d8217f898aa8e999b6a0f52fad8172185778e`,
49671035bytes. Do not replace these bytes with a same-version rebuild.
Last gateway binary SHA256
`f71b7e7bb92d7f312d210d41ebf200cf4416ed73ca7fe3a33ae2e13d4d3f2ebf`;
PID4077612 at04.10 20:30UTC. This paragraph is historical; current readback is below.

## Evidence and limits

### Final CI and gateway artifact acceptance05.10

Source **`a813dc5c80b27025222f317a068d16c71d6dc64c`**:
- `phase0` run37291210868 and `Client builds` run37291211020 both **success**,
  attempt1, confirmed by exact-SHA API readback05.10 09:56:53UTC.
- Previously failing full carrier race step passed, as did Android emulator
  WG/AWG/TCP/Auto lifecycle, native build, release verification, Linux, Windows and
  Windows compatibility. Other path-filtered workflows did not run; not four CI PASS.
- Artifact11337447479, `FamilyConnect-Android-restricted-arm64`,58409367bytes,
  SHA256 `195e7575e0f3aae4d8a944533bcc6abc522af137d0ba7b4792ebbfcb1de29fe4`.
  Downloaded ZIP matches GitHub metadata, exact workflow/source and expected four
  entries. CRC, manifest version/package/source and contained APK hash/size checked.
- Extracted gateway17373323bytes, Linux/amd64 ELF,
  SHA256 `055716447a1fe4bd8859dc2877410e756a9dc60a81b0ae5203a23f99606326a0`;
  manifest hash and embedded VCS revision matcha813dc5.

The temporary verifier initially required `vcs.modified=false`, which this build
does not claim. Readback shows **vcs.modified=true**, also present in accepted64.
The workflow creates untracked root logs/summary before Go build; these are not
ignored. The committed packaging gate separately runs `git diff --exit-code HEAD`
over carrier/client/native source and passed in exact-source job111701775294.
Acceptance uses that existing source guard plus immutable artifact digest, source
manifest and embedded revision, not a fictitious clean-worktree flag. This flag and
the verifier's rejected assumption are retained in the receipt/documentation.

Initial Python download got HTTP403; same unexpired URL with the established curl
User-Agent succeeded. No artifact was substituted or rebuilt. Subsequent verification
reused the saved ZIP rather than redownloading. Gateway receipt and ZIP are retained
under `state-client-build/bootstrap-cleanup-ci/a813dc5-artifact/`; file
`gateway-verification.json` records all hashes and provenance checks.

The ZIP contains a **new unsigned same-version65 CI APK**, not a new distributable
release. It was not extracted as an installable delivery, signed, installed or
published. Existing signed owner65 `dfbdb535...` stays immutable. Read-only ADB
metadata confirms installed `0.1.18-beta65`/65 and UID10283, without modifying data.

At the CI-only checkpoint no deployment, renewal or public-route change had occurred.
Local disk-quota failures remain real failed local validation
attempts; the now-successful remote CI provides independent full-build evidence.
The subsequent deployment and owner gates are recorded below; a Krasnodar mobile
retry still requires the tester's own fresh current-directory READY/ACK.

### Earlier new-source/live readback checkpoint05.10

User-authorized source `a813dc5c80b27025222f317a068d16c71d6dc64c` committed/pushed
from parenta5acb73. Exactly six scoped files (two tests/four documents), no production
TCP changes; ten unrelated dirty files remain local. Source guard1761 entries/0
blocked; documentation476/2898 before checkpoint updates.

New exact-source `phase0` run37291210868 **PASS**, attempt1. `Client builds`
run37291211020 is still **in_progress**, attempt1. Android job111701775294 has
already passed `Restricted carrier race regression`; its emulator lifecycle stage
is running. Linux, Windows and Windows compatibility passed. This removes the
observed earlier carrier-test blocker on CI but is not full artifact acceptance.
Status receipts are persisted in
`state-client-build/bootstrap-cleanup-ci/a813dc5-ci-status.json`.

Read-only05.10 **09:47UTC** RU/NL/device check:
- Owner Redmi is connected over ADB. Both existing admissions remain non-revoked;
  no identity/grant changes. Owner's last ACK is65 from04.10; tester latest05.10
  readiness fetch has no ACK and does not establish its installed version.
- Neither device currently has usable readiness. Previous READY receipts have
  expired and must not be mistaken for current readiness.
- NL bootstrap is active/PID254601/NRestarts3 with unchanged loaded binary
  `f71b7e7bb92d7f312d210d41ebf200cf4416ed73ca7fe3a33ae2e13d4d3f2ebf`.
  The certificate actually served on the existing control listener matches the
  profile and still expires04.10 **22:57:31UTC**. This task did not restart/renew it.
- Last recorded issuer4 expiry is05.10 **13:28:47UTC**, less than4h after this
  readback. A future leaf renewal must respect the verified current issuer/grant
  bound; it cannot silently promise4h or weaken floors to bypass expiry.

Safe live receipts `readiness-*.json` and `loaded-gateway-*.json` are in the same
private CI evidence directory. No profile/key/database or raw transport URL is
included in repository documentation. Gateway-only artifact verification is prepared;
no signing, APK installation, renewal, server update or public publication occurred.

### Overall problem progress05.10

1. Original export11 classification defect: fixed in the beta63/64 line. Beta64
   owner acceptance demonstrated genuine native retry exhaustion → NETWORK →
   bounded new-session recovery, not merely an injected policy failure.
2. Retained-valid-cache refresh defect: fixed in accepted signed owner beta65.
   Ordinary foreground refresh over retained valid cache passed04.10; beta65 public
   delivery remains held by the separate recovery gate.
3. Server old-session cleanup/admission race: correction source3ba5270 committed and
   pushed, locally tested, but not deployed. Old journal has generic rejection only;
   exact historical `device_busy` is not claimed observed.
4. Release-gate TCP reset fixture race: reproduced on previous accepted source,
   corrected only in test files,1500 repetitions per case passed. Sourcea813dc5
   pushed; new exact-source CI and gateway artifact now PASS on attempt1. Local
   quota failures retained; this is not a third unchanged retry of failed3ba5270.
5. Original restricted-network DATA/ACK stall: loss location and RKN involvement
   remain unknown. Neither a local test fix nor successful CI proves field stability.
   Next runtime sequence is accepted gateway artifact → valid loaded credentials →
   owner recovery/security acceptance → targeted65/tester fresh READY/ACK → one
   Krasnodar trial with paired evidence. No percentage-complete or end-to-end fix claim.

### Authorized test-only correction05.10

After the baseline failure was reported, the user authorized fixing synchronization
of these two fixtures without changing production TCP. Local code scope is exactly
`carrier/tcpforward/forward_test.go` and `integration_test.go`; there is no new
commit/push or CI result at the local checkpoint. Subsequent05.10 user approval
authorizes scoped source delivery; exact-source CI receipt is still pending.

`startResetFixture` uses real loopback TCP. The accepted socket waits for a signal
sent only after `tcpDial` returns successfully; it then writes the existing optional
prefix, applies zero linger and closes. The injected test dialer waits for the
actual close before handing the socket to the production forwarding loop. This
retains reset-before-OPEN_OK processing instead of weakening the test by delaying
RST until the client receives OPEN_OK. Context cancellation releases waits and test
cleanup cancels the fixture even if opening fails. No sleeps or timer extensions.

The authenticated test still uses real ReliableStream/Family TLS and `OpenTCP`,
normal `gatewayPolicy` and checked `ClaimTCP(true)` before calling the existing
internal `serve` dialer seam. The public `Serve` wrapper and all production code
are unchanged; separate authentication/policy tests continue to cover that wrapper.
Both reset cases require a successful OPEN and exact `ErrReset`, not arbitrary
non-nil error or EOF. Added assertions require one OPEN_OK, zero OPEN errors and
zero remaining sockets. Other cancellation/half-close cases remain in the suite.

Validation: focused `go test -race ./tcpforward` with both reset cases,
`-count=500 -cpu=1,2,4` PASS49.755s (1500 repetitions of each case).
Receipt `/tmp/fc-reset-synchronized-stress.log`. Initial full parallel and serial
race runs failed linking cmd/telemost-binary with `disk quota exceeded`; the other
test packages passed, but neither command is a full-suite PASS. Moving temporary
output to /tmp alone did not resolve linking. Rebuildable scoped Go cache was then
cleared with approval, but the clean-cache run then failed compiling runtime and
dependencies with the same quota error, before test execution. This did not repair
the environment. Parallel/serial full attempts passed tcpforward16.736s/16.446s;
neither is full-suite acceptance. All three full-run failures are retained and no
full-suite PASS is claimed for this fixture patch. No unrelated files/keys/APKs were
deleted. No tests were skipped and no assertions or transport code changed to bypass
the quota failure. Documentation476 files/2898 links, gofmt and diff checks PASS.

No APK/signing/installation, credentials, gateway deployment or public rollout in
this step. Existing accepted APK65 bytes remain immutable, and failed CI3ba5270
cannot be treated as accepted because local fixture checks now pass.

### CI blocker and baseline reproduction05.10

`phase0` run37284062182 completed **success** on source3ba5270.
`Client builds` run37284062212 is **failure**, attempt2. Linux, Windows and Windows
compatibility jobs passed; Android failed before native gateway/release APK build,
and release was skipped. No accepted matching gateway artifact exists from these runs.

- Attempt1 job111678656030: `TestAuthenticatedImmediateResetPreservesOpen`,
  `integration_test.go:234`, `OPEN_OK lost during reset: TCP OPEN: connect_failed`.
  Artifact11334056990,1015bytes, SHA256
  `75ab2b0b8583ac30aaf844c495f304a20c7b72736f8fdad4d9b9caa5a84a7753`.
- After the initial log was preserved and local200 repeats passed, one unchanged
  failed-job rerun was requested. Attempt2 job111685041292 failed instead at
  `TestImmediateCloseResetCancellation/reset`, `forward_test.go:235`,
  `TCP OPEN: connect_failed`. Artifact11334327672,993bytes, SHA256
  `4762f5d928e3e42ec2a3440b33249e9203cd1b75425a3920c29b04ab8e79dbbf`.
- Both downloaded ZIP digests match GitHub metadata and both logs retain passing
  bootstrap/room-broker packages. These are real gate failures, not a successful
  release and not evidence for changing production TCP or increasing timeouts.
- Default local200 repeats of the authenticated immediate-reset test PASS7.645s.
  With `GOMAXPROCS=1`, both selected reset tests over200 iterations reproduced
  7 failing test cases in6.783s. The same unchanged command against a separate
  export of accepted baseline86fa1ba reproduced9 failing test cases in6.277s.
  `carrier/tcpforward` has no diff between that baseline and3ba5270.
- One earlier local command had an invalid slash-separated Go subtest selector;
  it executed no tests. The corrected selector retained every original assertion.

Evidence directory `state-client-build/bootstrap-cleanup-ci/` retains both ZIPs,
extracted carrier logs and default/current/baseline reproduction logs. No third CI
rerun, test weakening, transport changes, signing, installation, server renewal,
deployment or live device acceptance followed these failures.

The immediate-reset fixtures close accepted TCP sockets with zero linger before
synchronizing with completed connection establishment. `connect_failed` is the
pre-OPEN_OK dial failure path, not proof that an emitted OPEN_OK was lost. The exact
raw OS dial error was not recorded. The reproduction on the baseline establishes
that this release blocker predates the bootstrap correction. Next work should be
separately scoped to synchronizing these fixtures without sleeps or weakened
OPEN_OK/reset checks; production forwarding and the original field DATA/ACK stall
are not claimed fixed. Accepted gateway build, valid credentials and owner recovery
remain mandatory before the Krasnodar trial.

### Source delivery checkpoint05.10 08:31UTC

User-authorized commit `3ba52709253dba05a780aaa06d858a1a51f4ca5d` contains only the14
scoped code/test/contract/state/report files. Push to `origin/main` succeeded from
parent5263410. Ten unrelated dirty files remain local and unstaged; no keys/runtime
state or APK assets are included. Public source index guard:1761 entries,0 blocked.
Committed-source export documentation:476 files/2883 links, zero errors (working-tree
count differs because unrelated documentation edits were intentionally excluded).
First archive-doc check lacked Git metadata; rerun supplied the unchanged index as
read-only inventory with the exported worktree, without altering documents/assertions.

GitHub exact-source readback: `Client builds` run37284062212 and `phase0`
run37284062182 are **in_progress**, not PASS. Readiness/Linux control workflows do
not trigger for the carrier/docs-only path set; earlier beta65 four-workflow PASS
belongs to86fa1ba, not this correction. No CI results are borrowed across SHAs.
CI may build new same-version APK artifacts: do not sign, install or publish them
as immutable65. Existing accepted signed65 stays unchanged; the deliverable being
considered here is the matching gateway binary, after CI/artifact acceptance.

### Correlated original failure

Original owner test injected a NETWORK policy cause after real restricted HTTPS200;
it was not a genuine native retry-exhaustion injection. Client cleanup occurred at
04.10 **20:21:16.631UTC**. New bootstrap family authentication succeeded at
**20:21:24.725749UTC**, followed by generic exchange failure at
**20:21:24.726987UTC**, before descriptor delivery. The old server session remained
alive until `RELIABLE_RETRY_EXHAUSTED` at **20:21:35.103UTC** (8 retries, one pending
block, ACK/progress age18460ms); final cleanup at **20:21:35.113UTC**.

The server slot therefore remained occupied18.482s after client cleanup, and was
released approximately10.386s after the new exchange failed. The original session
has67 gap-free server trace events. Strict projection reports zero changed/invalid
trace records. Private evidence is retained in
`state-client-build/bootstrap-exchange-diagnosis/original-session-server-inventory.json`,
alongside the earlier `state-client-build/field65-owner/` snapshots. No profiles,
keys, room URLs or product database are committed.

The old journal does **not** expose the rejection code. Code inspection and a red
deterministic regression reproduce immediate `device_busy` rejection during this
active-slot overlap; that demonstrates a cleanup race, not retrospective proof of
the exact historical error. Original field DATA/ACK loss location and RKN involvement
remain unproven. Earlier empty journal selections were a diagnostic selector error;
the corrected retrieval supplies the67-event record, not evidence of absent logs.

## Correction and security

- BOOT-1 waits for the exact previous active/closing setup's `done`, then requests
  a fresh challenge through the original admission path. Gateway close precedes
  `done`. It neither cancels the old session nor creates a parallel dedicated room.
- The existing120s total exchange deadline and any earlier parent deadline bound
  waiting. No transport timer, retransmission count or retry budget was increased.
- Family/device/public key are pinned and rechecked at the broker's existing
  authorization interval and after cleanup. Revocation, identity changes,
  cancellation and expiry stop admission. Deadline/cancel errors take precedence
  over a concurrent authorization-poll error caused by that cancelled context.
- Non-active unfinished duplicate setups and global limit violations still reject
  immediately. HTTP `Challenge`, replay checks and one-device slot limits remain.
- Server event `bootstrap_exchange_rejected` contains UTC and fixed stage/reason
  enums only. Unknown/raw errors map to `unknown`; generic on-wire ERROR and the
  existing `bootstrap_exchange_failed` event remain. No client protocol change.

## Validation and retained failures

1. RED before wait correction: active old gateway caused immediate ERROR instead
   of bounded waiting (`/tmp/fc-bootstrap-cleanup-red.log`).
2. Initial full Go race suite and94 Python tests PASS04.10. Python selection:
   `test_bootstrap_acceptance`, `test_nl_bootstrap_acceptance`,
   `test_telemost_family_fixture`, `test_restricted_correlation`;
   `/tmp/fc-bootstrap-python-checks.log` records94 passed in6.84s.
3. A20-repeat stress run exposed three deadline/auth polling races. The fix preserves
   exact `context.DeadlineExceeded`/`context.Canceled` assertions; it does not accept
   either error interchangeably. Initial failure log retained.
4. Overnight50-repeat run failed only the real-TLS busy test: disposable leaf/CRL
   expired04.10 21:44:44UTC, CA22:44:44UTC. At05.10 08:22UTC these were expired.
   No expiry checks or assertions were disabled. New isolated ProductStore-backed
   fixtures were generated under a separate ignored private directory.
5. Final05.10 fresh-fixture **50 repeats PASS** in10.640s: active cleanup wait,
   deadline, cancellation, authorization loss/identity change, immediate admission
   refusal, malformed request and real-TLS busy-reason observation.
   Receipt `/tmp/fc-bootstrap-repeat-race-20261005.log`.
6. Final05.10 **`go -C carrier test -race -count=1 ./...` PASS** with fresh fixtures,
   no cached test results. Receipt `/tmp/fc-bootstrap-full-race-20261005.log`.
   Full suite retains wrong-Family, revoked/unknown identity, provider/gateway failure,
   successful handoff, room broker, TCP, ReliableStream and privacy regressions.
7. Documentation checker:476 files/2896 links, zero errors; `git diff --check`
   and `gofmt -l` on all changed Go files are clean. This checks repository links,
   not public rollout or availability of download URLs.

No physical owner acceptance or Krasnodar mobile trial was repeated in this step.

## Next gates and rollback

1. DONE scoped bootstrap3ba5270 and test-fixturea813dc5 delivery; successful exact-source
   CI and matching gateway05571644 artifact provenance. Existing accepted APK65 can be used for this
   wire-compatible server correction; do not rebuild/re-sign it under the same version.
2. Before hardware testing, renew/revalidate material: last actually loaded gateway
   leaf bound **04.10 22:57:31UTC has expired**. Later directory bound22:59:29UTC did
   not extend it. Verify loaded TLS chain/hostname/leaf and RU/NL directory generation
   consistency, issuer/security floors and device admission preservation.
3. Deploy only the verified gateway correction through the restricted runbook,
   preserving old binary and service configuration. Pass owner65 immediate recovery,
   auth/denial/cancellation and ordinary VPN/privacy gates with saved paired evidence.
4. Only then publish immutable targeted65, download/verify hash/signer, obtain tester
   fresh authenticated fetch/native READY/ACK and run one authorized Krasnodar trial.
   Default/catalog/invitation60 remain unchanged; no readiness from cached READY alone.

At the earlier predeployment checkpoint no production rollback was needed. A gateway rollback restores
the saved f71b7e7b binary/configuration with **fresh valid credentials**, not the
expired04.10 profile, and then revalidates service/loaded chain. Keep issuer floors,
admission, private state and unrelated services intact. A client fix requires a
higher-code successor, never uninstall/data clear/downgrade or immutable-byte replacement.

## Server execution05.10 — owner acceptance PASS

Preflight10:10UTC verified issuer4 cryptographically and unchanged owner3/tester1
grants. Only11891s of authority headroom remained. Renewal used the existing issuer
machinery and same gateway key, capped at `min(now+14400, issuer, grants)` rather
than extending authority. Issued CRL6326 and gateway lifetime11808s; issuer and grants
unchanged. Publication10:12:11UTC passed native positive/negative authority checks,
atomic publisher metadata/fsync/readback checks, UID/GID979,0600 and actual service
readability. Existing unit/wrapper/configuration were not replaced. Loaded TLS
certificate matched the profile, chain/hostname verified, stable35s observation PASS.
**Actual gateway expiry05.10 13:28:47UTC** is authoritative even though the published
directory expires14:13:47UTC. RU sync timer restored on exit.

Accepted binary deployment10:13:54UTC PASS; loaded SHA25605571644…6326a0 equals the
verified Linux/amd64 CI artifact at sourcea813dc5. PID353567/NRestarts0, fresh validated
directory, unchanged gateway binding. Before/after RU device/invite/grant/audit DB,
admission, ordinary HTTP/AWG/TCP service and binary invariants equal. No product APK
signing/install, public version or invitation/catalog change.

Private receipts: `state-client-build/bootstrap-cleanup-server/` (preflight, issued,
publication, loaded certificate, deployment and invariants). Protected remote renewal
stage on both authorized hosts:
`/opt/apps/family_connect/restricted-materials-stage-20261001/cleanup-renewal-a813dc5-20261005`.
NL binary rollback directory:
`/opt/apps/family_connect/restricted-materials-stage-20261001/cleanup-binary-a813dc5`.
Its `bootstrap-broker.previous` is f71b7e7b. Roll back only the executable while
preserving renewed credentials, monotonic CRL/floors and admission; revalidate loaded
hash/chain/READY, synchronize the replacement directory to RU before client refresh.
Never restore the expired old profile or decrement security state.

### Unchanged owner65 runtime acceptance

RU sync run succeeded; post-deployment RU/NL directory bytes and generation equal,
issued10:13:50.834616272UTC, SHA256
`6bf514cd90d55af8256e86d2fdbb7175cf6185383fa65914f29f725fb9e9e53d`.
Only the existing matching signed private instrumentation package was installed.
Ordinary FriendsActivity foreground obtained a fresh authenticated fetch/native
READY/ACK65 after expired cache; no forced fetch, cooldown bypass or cache edit.
This is an expired-cache case; retained-valid-cache ordinary refresh was already
accepted04.10 and is not relabeled as a new retained-cache test here.

`OwnerRecoveryTest#realSessionsWithInjectedPolicyLoss` now PASS against the new live
gateway on exactly the previously installed signed65. It injects the NETWORK policy
cause; it does **not** induce native eight-retry exhaustion or emulate RKN loss.
Real original/restored native sessions have different handles/tags, HTTPS200 before
and after, and the old handle is gone. The second-loss bounded guard and explicit
disconnect cleanup remain. Separate startup AUTH denial, connected AUTH denial
without another descriptor, and pre-start cancellation all PASS (local denial
injection, not revocation of an actual user's access).

Paired client/server evidence PASS: original59 and restored67 server events, no
sequence gaps, complete descriptor/join/carrier/Family TLS/gateway session/cleanup
stages. Client32/36 events with7/8 bounded delivery samples; server13/17 delivery
samples. Old server cleanup10:18:11.285UTC precedes new descriptor10:18:15.034UTC
by3.749s; no bootstrap exchange rejection in this bounded window. These timestamps
prove ordering, not the duration of the specific busy-slot wait. Initial all-journal
read failed (protected error receipt retained); reading the known active journal
file completed and supplied the gap-free evidence. No runtime test was rerun to hide
that observer failure.

AWG/TCP ordinary product transport, existing enrollment, provider/protocol/update
security suite, restart/Support, diagnostics/share and final cleanup PASS. Diagnostic
export8937bytes matches the reported SHA/size, event bounds and forbidden-field scan;
no share recipient selected/upload performed. Final pulled APK SHA256dfbdb535…5778e
and original signer67a90d1b match; UID10283, data inode/first install, identity,
enrollment, activation and Support remain unchanged. Readiness may legitimately
refresh. The private test package was removed and its absence verified.

Final10:22:43UTC actual loaded gateway05571644 still PID353567/NRestarts0; certificate
matches and has11163s headroom. RU invariants equal pre-renewal state. Verified HTTPS
status200 and expected400 for unauthenticated ordinary challenge/chat and malformed
restricted request; both public update catalogs byte-identical, default60 unchanged.
Private receipts: `state-client-build/bootstrap-cleanup-owner/` and the server folder.
### Targeted public65 delivery — verified05.10 10:27UTC

Owner/runtime gates above allowed delivery of the **existing** signed source86fa1ba
APK65, not the unsigned same-version artifact from gateway CI. Source's four workflow
successes and saved signed-artifact verification were rechecked. No rebuild/resign.
Only a separate immutable download and exact nginx route were added; syntax check and
reload of `family-connect-product-https` PASS10:25:54UTC. Existing downloads, catalog,
invitation/landing bytes, admission/Support/enrollment and ordinary service processes
unchanged. Full HTTPS download10:27:01UTC, certificate verification enabled, no redirect:

- [FamilyConnect-Test-0.1.18-beta65.apk](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta65.apk),
  HTTP200, ARM64/package `com.familyconnect.app.friends`, code65,49671035bytes.
- Downloaded SHA256 `dfbdb5352b8c707fb77ff3d7392d8217f898aa8e999b6a0f52fad8172185778e`.
- Verified original signer SHA256
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Signed catalog/discovery/default APK/invitation remain60, with previous hashes;
  old64 and all other downloads unchanged. No GitHub APK publication or new signed catalog.

Private delivery receipts and downloaded APK:
`state-client-build/field65-direct-delivery/`. RU publication/route backup:
`/opt/apps/family_connect/release-beta65-recovery-20261005`, with nginx config backups
and `publication.json`. Route rollback restores those configs after checking for
later changes, runs nginx syntax check/reload, and retains immutable APK bytes.
No client uninstall/downgrade/identity reset; a future client correction needs a
higher versionCode. Gateway executable rollback is documented separately above.

Read-only RU observation10:25:59UTC: owner65 fresh fetch/READY/ACK usable, both devices
admitted/non-revoked. Tester latest05.10 fetch has no ACK and is expired; last confirmed
installed version remains64. Public availability is not evidence of tester installation.
NEXT tester updates over Wi-Fi in place, confirms65 and unchanged Support, opens with
VPN off; operator verifies fresh current-directory native READY/ACK65. Only then one
authorized Krasnodar mobile Auto trial; export JSON before manual reconnect on failure.
Current material bound **05.10 16:28:47 Krasnodar/13:28:47UTC**; later trial requires
fresh authority/material validation and renewal, not accepting expired cached READY.
Original field DATA/ACK loss location and RKN involvement remain unproven.

Documentation updated in STATUS/PLAN, documentation index, release overview,
beta65 report and RU/EN installation/download guides, preserving pre-existing dirty
work. Final local documentation check:476 files/2905 links, zero errors;
`git diff --check` PASS. These edits are local/uncommitted in this continuation;
the published APK and deployed gateway are verified separately above. No new source
commit, APK version or claim of published GitHub documentation is made here.

### Tester availability update

User clarified the tester unavailable before **14:00 Brussels (CEST/UTC+2),
15:00 Krasnodar (UTC+3),12:00UTC on05.10**. This replaces the initial provisional
Krasnodar-time assumption. No tester action/mobile trial before availability.
The currently verified material bound16:28:47 Krasnodar leaves1h28m47s from15:00,
but actual gateway health, authority headroom and fresh native READY/ACK must be
rechecked at test time. No automatic schedule, background monitoring or tester
contact was created.

### Krasnodar availability and live preflight12:26UTC

User reports tester ready after a communication interruption. Read-only check05.10
12:26:15UTC confirms actual loaded05571644, PID353567/NRestarts0, active service,
served leaf/profile match and issuer/CRL signature validation. RU/NL directory hash
6bf514cd…9e53d and generation10:13:50.834616272UTC match; RU sync timer active.
Effective material headroom3751s; expiry13:28:47UTC/16:28:47 Krasnodar unchanged.
Owner65 retained READY is not evidence of tester readiness. Tester admitted and
non-revoked, with new fetch12:22:14UTC/revision1/minimumCRL6565 but no ACK/native READY;
installed65 cannot be inferred from this request. No mobile trial authorized to
start before the missing gate: confirm/update65 in place over Wi-Fi, open VPN-off,
then verify fresh native READY/ACK. No server mutation/restart/renewal or client
operation was performed by this preflight. Private timestamped receipts retained
under `state-client-build/field65-krasnodar/`. STATUS/PLAN updated; diff check PASS.

### Setup reported complete; READY absent12:38UTC

User says preparation is done. Recheck12:38:40UTC: same gateway05571644/PID353567,
NRestarts0, loaded leaf/profile match and RU/NL directory equality, headroom3006s.
Tester latest challenge/fetch remains12:22:14UTC with no ACK; the user's completion
message alone is not server-side code65/native READY proof. No new fetch or ACK is
observed. This does not locate the fault or establish that the client is defective.
Rather than repeat setup blindly, request a screenshot of Settings → «Готовность
подключения» (FriendsReadiness.inspect, local inspection, no forced fetch/activation
or access change). It reports activation/identity/provisioning/cache/refresh status
without private identity bytes. Keep Wi-Fi and VPN off; mobile trial remains gated.
Timestamped read-only receipts retained in the same ignored evidence directory;
no server mutation/client reset/reinstall/test started. STATUS/PLAN and diff checked.
