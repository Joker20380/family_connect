# Restricted readiness — early refresh with retained cache, 2026-10-04

## Scope and observed failure

User authorized correcting the stale-directory refresh blocker after tester64 was
confirmed by authenticated ACK19:21:49UTC. Latest live readback19:23UTC remains the
[beta64 delivery/readiness checkpoint](2026-10-04-beta64-paired-candidate.md): owner64,
tester64, public targeted64, default/catalog/invitation60, gateway f71b7e7b. Source
baseline HEAD7088fb5, accepted release sourcece73ddf. This change is local source only;
no commit/push, version change, release APK build/sign/install/publication or live mutation.
Never overwrite published64 with these different source bytes.

`RestrictedCache.attempt` first enforced the persisted `next_attempt`, then rejected
refresh while a usable cached response had more than300 seconds remaining. A four-hour
response therefore prevented replacement of a retired gateway seed for hours.
`FriendsRestricted.prewarm` could revalidate/re-ACK that old cache with the new app
version, producing64/READY without a new challenge/fetch. This is distinct from the
original field DATA/ACK stall and from gateway certificate expiry.

## Change

Remove only the usable-cache/expiry suppression from the existing attempt gate.
Each eligible attempt still persists `next_attempt = now + 300` before network work.
The ordinary foreground prewarm loop and existing single-flight/lock/deadlines remain
unchanged. Process recreation retains the cooldown. An upgrade from the old state
requires no schema migration and no data deletion: if the last attempt is already
more than300 seconds old, the next ordinary prewarm may request fresh materials.
Otherwise it waits the remaining cooldown and foreground scheduling; not instant
or guaranteed connectivity. There is no new background service or per-minute fetch.

The cadence is now at most one attempt per300 seconds while prewarm is invoked,
including while cached credentials remain valid. This intentionally adds bounded
freshness checks for long-lived materials. The existing cache remains usable during
refresh and temporary fetch failures, subject to the unchanged native validation.
Explicit authorization rejection still marks it denied; retries do not resurrect it.
Issuer/revision/CRL/time/directory monotonic checks, equal-time conflict rejection,
atomic encrypted storage, identity, signing, receipt privacy and ACK behavior are unchanged.
This is not a change to reliable retries, transport RTO or authority TTLs.

## Regression coverage

Before the production change, the focused13-test run failed **5 tests** on the old
suppression condition. The red XML/logs are retained privately under ignored
`state-client-build/early-readiness-refresh/red/`. No pre-existing assertion was
relaxed except the assertion explicitly requiring the obsolete no-refresh policy.

New cache tests cover long-valid saved state and restart, exact300-second cooldown
boundaries, timeout-equivalent retained state/replay floors, explicit denial,
failed durable cooldown write and validation failure. `ReadinessRefreshTest` starts
with a serialized four-hour cache and previous receipt, recreates the cache as after
upgrade, and must pass **the production attempt gate** before authenticated challenge/
fetch. It imports the newer seed through `ReadinessProduct`, observes the validation
callback on the new bytes, reads the persisted cache and sends the normal signed
ACK with fresh correlation IDs and phase=import. It also tests challenge timeout and
native/bootstrap rejection without replacing the old bundle or reporting fresh READY.

The test uses a synthetic transport and validation callback, not actual JNI, Android
Keystore, foreground Activity or a physical phone. Identity proofs/protocol/cache/
import/ACK are production Java components. The new regression is included in both
Android unit tests and the standalone JVM readiness-contract CI source set.
Physical automatic-prewarm acceptance remains required; forced authenticated import
alone does not satisfy that gate.

### Local check results

- Android `:app:testFriendsUnitTest :app:lintFriends`: **254 tests**, zero failures/
  errors/skips; lint zero errors/37 warnings. Gradle deprecation warnings remain;
  no formatter or unrelated cleanup introduced.
- Standalone `clients/android/control-tests` `test goldenClasspath`: **171 tests**,
  zero failures/errors/skips, including the new scheduled-refresh regression.
- `tests/test_android_challenge_contract.py`, `tests/test_friends_restricted.py` and
  `tests/test_readiness_receipts.py`: **117 passed**, with golden Java classpath and
  locked Go toolchain supplied (the four native delivery cases were not skipped).
  First invocation passed116 and failed1 because the subprocess could not find `java`;
  the rerun adds the existing JDK to PATH and passes117 without code/assertion changes.
- Private red/green XML and logs retained under ignored
  `state-client-build/early-readiness-refresh/`. No live access data or signing material
  was used for these synthetic checks. Android/JVM counts overlap; they are separate
  suite executions, not a claim of425 distinct tests.
- Documentation check:474 files/2884 links, zero errors; `git diff --check` PASS.

## Remaining delivery gates and rollback

1. DONE local full Android unit/lint, standalone readiness JVM and Python HTTP/native
   contract checks; red/green and initial environment-failure evidence retained separately.
2. Prepare an immutable successor version (not a replacement64); obtain the scoped
   source commit/push authorization needed for exact-source hosted CI. Preserve
   unrelated working-tree documentation. Accept platform artifacts before offline signing.
3. Revalidate/renew the complete live material chain; prior gateway bound04.10
   22:57:31UTC must not be assumed valid at later execution time.
4. Owner in-place install and **ordinary foreground prewarm from still-valid old cache**,
   without clear/reenroll/test-forced fetch. Verify new authenticated fetch, native
   validation/readback/ACK, unchanged identity/Support, bounded retry and AUTH denial.
5. Only after owner acceptance distribute the successor, then verify tester fresh
   current-directory readiness before the single authorized Krasnodar mobile attempt.

No deployed rollback is needed for this source-only patch. Retain published64 bytes
and existing gateway/catalogs; reverse only this local source change if rejected,
without discarding the pre-existing dirty work. Any rollback after future installation
requires a higher-version forward-fix, not uninstall/data clear or APK downgrade.
