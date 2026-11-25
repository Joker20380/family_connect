# 25 November 2026 — HA-02 support stabilization, not handoff acceptance

## Exact f6c6171e CI outcome and coverage correction (22:20UTC)

Native workflow45709174045 at `f6c6171e022fbf2b671e7c950671a556a7fdeb79` actually passed214 tests,
zero skips. Artifact15068030347 SHA256 `055d07dc98a814c3156acbaece0c4a991788b14b174faffaca61138835bee082`
is retained privately. Windows control conformance and readiness golden also PASS. Full phase0
45709173975 and Linux control45709173914 FAIL, not accepted: execution contexts pass but final
coverage audit refuses native314 inventory. The retained log proves exactly64 extra cases: mailbox
fence26, links13, startup25. Explicit native selection included these files while default pytest.ini
testpaths excluded messenger. Corrected full-suite discovery includes those same three files; no
assertion or accepted hash is removed/rewritten. The audit still rejects missing, extra and duplicate
cases, now retains sanitized collection inventories and bounded differences.20 scoped regressions PASS.

Host artifact15068910400 SHA256 `a26b2fc72d9da2b13e782d4e7f6c61b807acba1116c8ef636bf452dcd99779f6`
and Docker artifact15068505853 SHA256 `d020f376d193197de8b6a8934dbaaf037f3dfdfc4e90d26bc97fcc37496cedb1`
are retained privately. Host execution:9448 passed/915 skipped/602 deselected; root258 passed;
snapshot31498 passed; native314187 passed/123 skipped. Those skips are not native acceptance:
the separate214-case native workflow requires zero skips. New exact-SHA full CI remains required.
Combined executor and working installation remain incomplete; no production change or rollback.

## Scope and starting point

Remote feature `595acebe72bc486ec9661bb68bc493a09e9863f8` and main
`17d3b32ab7384bdeb680f3a389408f25b2e78559` matched the owner checkpoint; both worktrees
were clean. Work remains on `feature/device-technical-metadata-20261115`. No working
support replacement, mailbox opening, capture permission, HA-03 cutover or release is claimed.
The selected result is the **combined OWNER ↔ NL1 handoff/reclosure/recovery**, not a helper PASS.

## WORKERS_REMAIN: evidence and limits

The original failed fixture and JUnit remain untouched. A private second copy of its13 JSON
receipts and failed JUnit is retained under `/tmp/fc-ha02-stabilize-20261125/retained-failure`.
The original failed JUnit SHA256 remains
`40fe8c267b11496ea2d85a4d66745015888a5f95b19b24c3b7afbf28d6d77c78`.
It proves irreversible WORKERS_REMAIN, not the identity of the extra task. **The historical
specific cause cannot be recovered from these artifacts.** A subsequent PASS is not an explanation.

The three `only_main()` boundaries now retain bounded, private census files: phase, last completed
step, fixed owner roles, Python identifiers, native TIDs and set differences. Thread names, messages,
keys, frames and arbitrary locals are excluded. Partial/read-failed/changing/over-limit snapshots
are explicitly incomplete and refuse progress. Samples are not described as atomic.

A controlled native-tail counterexample removes an owned thread from Python's active registry,
then holds its native lifetime with a pipe. Python enumeration is already main-only while the native
TID remains. No sleep, timeout extension or repeated attempt is used to make the check pass.
CPython3.14 joins the OS thread, but Linux distinguishes pthread completion from task detachment:
pidfd readable exit and pidfd HUP/reaping are different boundaries. The legacy bridge now retains
PIDFD_THREAD handles **before irreversible commit**, joins owned Python workers, and waits for their
kernel HUP before its unchanged native-task exclusion check. Unsupported pidfd setup refuses before
commit. Final-persistence starts and their descendants retain explicit ownership even after Python
enumeration loses them; they too are joined/reaped before persistence completion.

This establishes and fixes a concrete completion gap; it does **not** establish that this was the
original20:35UTC failure. Unknown native tasks still refuse; none are ignored or killed by the bridge.

## Terminal reconciliation

An irreversible error is durably latched as `MANUAL_RECONCILIATION_REQUIRED`, with its original
reason and receipt/diagnostic hashes. The CLI exits78, matching the existing supervisor
`RestartPreventExitStatus=78`; only genuine pending work returns WAITING/75. Re-entry, recovery
and direct rollback cannot install a candidate or restart the old writer after this latch.
Witness sampling refuses, and the receipt explicitly denies witness/open/capture permission.
Reservation guards remain in force, including dangling markers. No reservation removal is added.

A real user-systemd synthetic service injects `SYNTHETIC_FINAL_FAILURE` after READY. Its supervisor
exits78 with zero restarts, while the original process remains parked, no candidate/witness/rollback
intent is produced, and uncertainty remains. Fixture teardown is scoped to its synthetic unit only.

## Qualification through21:14UTC

| Check | Result | JUnit SHA256 |
| --- | --- | --- |
| Exit/terminal/replacement/witness, CPython3.14 GIL | 65 passed,0 skipped;462.45s | `5055ffef222fe99cbf3fc4cd411ace1ab1c6ecfc576c52d414dab687e063cbe5` |
| Native systemd terminal behavior | 1 passed,0 skipped;18.99s | `766b5e38d4ae874c8feb18f64dbfb8773c42b86f7cb42a1c4942067a2ef11ff6` |
| Actual fc-support UID/systemd replacement/witness | 3 passed,0 skipped;53.59s | `2b7e03445accf4af2754b684321119bd224dd983f5b7d9342dce24152c662303` |
| CI context/native-diagnostic regressions | 21 passed;1.50s | `041284a2b88d36dc3a4e4df7f5ea5cf49f3ef50307a4112a139ae5434b550bbd` |

An earlier preparation run stopped after51 passes and one newly introduced reservation-order
regression; its JUnit is retained as `initial-diagnostics.xml`. Reservation precedence was restored
before the complete final run. Preliminary and overlapping runs are not added to the final count.
The actual-root run21:13:45–21:14:40UTC independently verifies the working OWNER before and after:
same PID2022541,0 restarts,19 source pins, unit files and interpreter digest. These are isolated tests,
not working installation. Private evidence remains outside Git.

## CI integration: still open

The original CI artifacts are retained locally, not inferred from workflow names:

- a39c74b9: phase0 run45693050426, Linux control45693051031, messenger45693050885,
  notifications45693050692, panel45693051038 and voice45693050487 fail. Golden and Linux internal
  candidate pass; conditional Android/support workflows are skipped, not accepted.
- Exact595acebe: phase0 run45697240725 and Linux control45697240234 fail; golden45697240931 passes.
  Other path-filtered workflows did not run at this SHA and are not claimed successful.
- phase0 standard context at595acebe:72 failed,8957 passed,1009 skipped,521 errors. Root258 and
  snapshot31498 pass. All593 failed/error lines match the preceding artifact after normalizing
  temporary diagnostic paths; the earlier artifact additionally has the queue-descendant lifecycle
  failure. Docker failover also fails its full-suite build gate, not a working failover exercise.

Concrete corrections in this checkpoint: route native mailbox/remote-exec tests to a distinct
CPython3.14 **GIL-enabled**, unprivileged context while retaining Python3.13 desktop coverage;
install the existing HA PostgreSQL lockfile in test environments; provision messenger dependencies
for314; run messenger/notification/support-contract jobs on314; restore the actual migration graph
leaves after the payment migration test instead of leaving later console tables removed; preserve
bounded native-fixture stderr, including timeouts, in uploaded always-run diagnostic artifacts.
Fixture stdout/input containing synthetic custody material is not included in these logs.

No contract hashes or assertions are relaxed. Full CI is **not reconciled yet**: native-image/daemon
availability and internal errors, launcher executable permissions, historical overlay inputs,
runtime-package closure and the announcement-source contract still need exact-source resolution.
The migration change also requires panel CI, not just the context unit tests. New-source CI must be
observed after publication; a workflow that did not run is NOT_RUN.

## Installation, recovery and one next result

### Source publication and following CI corrections

Checkpoint `762f2d658360946ba2d07b15c335e6c39cd5fb90` was ordinarily pushed and the remote
feature SHA independently matched. This publishes source only, not working deployment.
The next bounded CI correction uses the exact metadata-overlay source
`430278008af38943de51cab8454614cb60b5837f`, rather than reversing an old patch against moving HEAD.
Both original baseline hashes were independently reproduced and remain unchanged. The closed
Docker source export now includes that exact Git object; its strict inventory assertion is extended
accordingly. The paid-boundary builder reads the committed graceful-stop template required by its
HTTP packager, without adding runtime configuration/private state to the bundle. The route fixture
now explicitly models the local enrollment-repository context. Lifecycle assertion failures retain
their synthetic diagnostic result instead of hiding it behind only a thread-count comparison.

Metadata-overlay/source-export/paid-bundle regression:10 passed in7.43s, no skips. A first run
correctly exposed the newly required Git object missing from the exact expected inventory; its
failed JUnit is retained. Assertions and contract hashes are not removed or replaced.
The four transport-overlay candidates likewise use their original source commits299b4845,
80b38d55,1cc6c510 and5eb8cec5 in disposable local checkouts; production packagers still refuse
unrelated policy/gateway deltas.13 transport/export tests pass in6.60s and33 route/context/diagnostic
tests pass in0.99s. These are overlapping scoped selections, not an inflated aggregate count.

CI on exact762f2d658360946ba2d07b15c335e6c39cd5fb90: panel45703107722,
messenger45703107736, notifications45703107887 and golden45703107911 PASS. Their conditional
support-contract/Android jobs remain skipped. At21:27UTC phase045703107732 and Linux control
45703107743 are still in progress, not accepted. Voice did not run at this SHA.
NL1 independent read-only readback21:21:56UTC confirms PID3705,0 restarts, no pending daemon reload,
and unchanged relay/server/codec/membership source hashes. No NL1 operation is performed.

Installed support remains the original19-source OWNER runtime; candidate archive
`9d7bf840f3455d0ef2e7653dc9289aac2f0d77c9f2a0a8e305c786f7ddb80489` is **NOT installed**.
No working NL1 unit, mailbox, notification queue, product database or client version changes occur.
The seven historical UNKNOWN outcomes are neither cleared nor replayed. No code rollback may restore
old data. Existing reservation markers remain mandatory and may not be removed or bypassed.

**One next result:** reconcile applicable CI and qualify the single resumable, authenticated
OWNER ↔ NL1 handoff/reclosure/recovery, including live closed/drained mailbox verification,
old exit/candidate verification, reservation-bound witness consumption, confirmed opening,
identity-specific notice-queue pause, reclosure/drain/permit invalidation before code-only recovery,
and interrupted/lost-response/controller-death/mailbox-restart/candidate-restart boundaries; then
perform authorized working installation and independent readback. This combined executor and
working gate are not delivered by the shutdown correction. No renewed operational authorization
is requested, but unqualified working activation is not performed.

The same three HA-02 criteria remain partial: current approved inputs/trust and journals; coherent
installed schemas/all-writer capture; complete independent custody/final recovery. Replication
remains PASS in isolation. FLEET-PRODUCTION-ONBOARDING-1 remains mandatory and unimplemented:
VPS → IP/access/roles → ordinary enrollment → verified active node. Support migration alone cannot
close that requirement or all of HA-02.

## 21:48UTC — native CI root cause and bounded environment correction

Checkpoint `a6f7c730f26cc8ca5092376cb00af4e4f374be5b` was ordinarily pushed and the remote
SHA matched. Its phase0 tests45705013013 FAIL; no full-CI acceptance is inferred. The prior
762f2d65 phase0 artifact15064657864 now contains the actual native fixture stderr:
Docker exit125, **No such image sha256:89598610ee266cf1efa164092d1193479069784f1c94493c46fcff82f5a6736f**.
That local-only image dependency accounts for the common native-fixture failures on this exact SHA;
the old a39/595 logs had no retained internal stderr, so this is not retroactively claimed as direct
observation on those historical runners.762 phase0 standard context:39 failed,9009 passed,521 errors;
root258 passed; snapshot31498 passed; native31485 passed/123 skipped. Linux control was CANCELLED,
not PASS. Public unauthenticated API hit rate403 during later inspection; authenticated job reads
were used instead, never interpreting an empty combined-status list as success.

The new CI recipe builds from only six explicit public recipe/lockfiles, verifies Python3.13.15 and
cryptography46.0.7, and supplies an immutable built image ID. The original local fixture image pin
and all native assertions remain. On host runners, execution retains network-none/read-only source,
root UID, capability/resource restrictions and bounded stderr. Inside the existing full Docker build,
where a sibling Docker daemon is unavailable, a single fixed sudo command runs an immutable root-owned
source snapshot in a network-none build step, a fresh `/run` lab and a bounded child process. It rejects
the wrong installed path, non-root or any network interface other than loopback. It is a CI-only fixture,
not a host maintenance entrypoint or a production deployment. The complete Docker test gate remains.

Local portable-image run of all ten affected test families: **592 passed,31 skipped in208.03s**.
The31 explicit PostgreSQL qualification skips are not PG acceptance. Native helper separately passes
actual UID0/network-none/settled-vs-pending and all twelve existing maintenance behavior assertions.
Private evidence: `ci-native-image.xml`, `maintenance-helper.json` under the retained session root.
The launcher tests move to the existing root-owned CPython3.14/GIL context because Actions' toolcache
executable fails the unchanged LAUNCH_RUNTIME_PERMISSIONS contract; no ownership assertion is removed.
Launcher/context/diagnostic tests131 PASS; final context/preparation tests29 PASS after the build guard
adjustment. Full new-SHA CI and the actual full Docker pipeline are still required.

Announcement reference review identifies only the already-existing HA server-authority changes:
transactional repository adapter, fail-closed canonical-file refusal, paired durable exports and
operator capture admission. Original Android106 hashes, wire actions/bounds and fresh proof/admin
checks remain. A separate source-only delta pins the two reviewed current modules and must reverse
byte-for-byte to the original accepted hashes. Reference/authorization/publication regressions:
83 PASS/40 explicit PG skips, not client rollout or complete PG acceptance. No new runtime logic is
introduced by this contract bookkeeping. The combined executor, queue-pause qualification and working
installation remain part of the **same single next result**, not displaced by these CI corrections.

## 21:57UTC — required native support CI, not a skipped-test PASS

Checkpoint `1c24d595ee729b8be6fb9cf7494a059fcec1f3cb` was pushed and remote-SHA verified.
Its full phase0 run45707883397 is still in progress at this checkpoint. To prevent the missing
installed baseline from silently skipping the selected shutdown/replacement/witness tests, a dedicated
HA-02 native workflow reconstructs exactly19 public files from
`61b00409e24b92651678b817d2a6f5d4796948f9`; every original deployed-source hash independently matches.
The deterministic candidate remains9d7bf840, not a new binary or changed contract. No private installed
state or source capsule is uploaded. The historical object joins the closed CI source export.

This workflow explicitly provisions root-owned CPython3.14/GIL, pinned packages and a disposable
runner user-systemd manager. It requires **zero skipped, failed or errored cases** in the selected
legacy admission/quiescence/exit/replacement/witness/terminal/archive/native mailbox tests and records
the exact SHA. Missing XML is NOT_RUN, not PASS. Docker's non-systemd context does not substitute for
this job. A test-only portable PR_SET_PTRACER exec wrapper replaces dependence on the host util-linux
`setpriv --ptracer` option; production units and global host ptrace policy are unchanged.
Source reconstruction/export10 PASS in3.83s; actual isolated user-systemd acceptance/code-only rollback
and irreversible terminal2 PASS in24.09s, no skips. The new workflow itself must still run and pass;
neither these local results nor its mere addition closes CI or the combined OWNER/NL1 result.
