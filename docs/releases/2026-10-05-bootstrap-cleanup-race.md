# Bootstrap cleanup race — source correction, 2026-10-05

## Scope and delivery state

Continuation of the [beta65 failed recovery gate](2026-10-04-beta65-readiness-candidate.md).
Source prepared on HEAD `5263410`; user authorized scoped commit/push05.10.
Final sourcea813dc5 passes CI and gateway artifact verification (checkpoint below).
No version change, local APK signing, installation, gateway
mutation or public rollout in this step. Unrelated dirty
documentation is preserved. This is a locally verified server-side correction,
not evidence that installed beta65 recovery now works against production.

Last verified04.10: owner Redmi `0.1.18-beta65`/65; tester and targeted public64;
default/catalog/invitation60. Accepted APK65 source
`86fa1bae8b97ff34d3e8cbd5b3cfe923cb7d71a6`, four exact-source workflows PASS;
signed APK SHA256 `dfbdb5352b8c707fb77ff3d7392d8217f898aa8e999b6a0f52fad8172185778e`,
49671035bytes. Do not replace these bytes with a same-version rebuild.
Last gateway binary SHA256
`f71b7e7bb92d7f312d210d41ebf200cf4416ed73ca7fe3a33ae2e13d4d3f2ebf`;
PID4077612 at04.10 20:30UTC. This report does not assert a new live state readback.

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

No remote deployment, credential renewal, ordinary-service restart or public-route
change in this task. Local disk-quota failures remain real failed local validation
attempts; the now-successful remote CI provides independent full-build evidence.
Next gate is verified gateway05571644 deployment with fresh valid credentials and
owner recovery/security acceptance, not a Krasnodar mobile retry yet.

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

There is no production rollback to perform now. A later gateway rollback restores
the saved f71b7e7b binary/configuration with **fresh valid credentials**, not the
expired04.10 profile, and then revalidates service/loaded chain. Keep issuer floors,
admission, private state and unrelated services intact. A client fix requires a
higher-code successor, never uninstall/data clear/downgrade or immutable-byte replacement.
