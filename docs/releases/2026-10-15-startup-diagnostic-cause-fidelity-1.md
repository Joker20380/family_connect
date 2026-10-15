# STARTUP-DIAGNOSTIC-CAUSE-FIDELITY-1

**RESULT: IMPLEMENTED_AND_LOCALLY_VERIFIED.** Diagnostic correction on top of
the implemented chat/VPN handoff; real Family/TLS receive regressions, combined
handoff/race tests, native/JNI builds and full researchProvisioning assemble PASS.
The normal Android export serialization path retains the new safe facts in JVM
tests. No on-device execution or new support export was performed.

`PRODUCTION_ACCEPTANCE=FAIL`; `HISTORICAL_CAUSAL_BINDING=NOT_PROVEN`;
`DEVICE_ACCEPTANCE=NOT_RUN`. Historical UNKNOWN is not retrospectively reclassified.

## Base, delta and build identity

- Input review `4eb47111c85731262ebf9971cdf2fdb7706767a7`; exact retained research84
  base `f5240994869826c6a28f59e58e38256c688cf6eb` plus source delta
  `d7907697d71f119c21bced533f08abae06ae33ef9159c5fd9bd54cf031a481e7`.
- Reconstructed using the prior handoff `apply.py` and its source manifests;
  handoff patch SHA256 `a9be16b5be05788d0ad1c9c19497044a68f01e733a21739a33ba4ae507189c64`.
- [Diagnostic-only patch](../../research/startup-cause-fidelity-20261015/diagnostic.patch):
  SHA256 `bd3d3923a28e2bad405516d20dcb387f44586ff734e0432494934b682f5e146d`.
- [Before/after files and manifest](../../research/startup-cause-fidelity-20261015/source-manifest.json)
  bind twelve files; [reproduction and runners](../../research/startup-cause-fidelity-20261015/README.md).
- Exact cumulative source inventory digest:
  `a4d489079e3da0df7fdd01b7977962b20ddbbf8605fbf682a349703a88b916d5`.
  Reconstructing the published projection reproduced the working source byte-for-byte.
- Normal arm64 native SHA256:
  `2a974350c168913ca8a217d3fc73f452fdd709c3619d0c690abd5d884c54b88c`.
- Local unsigned researchProvisioning APK SHA256:
  `a2578412f8a3850e5f06aae838ddff0d1f4b04364b01885ffe3ea3b7dbe8ce3d`.
  Local build identity only, **not an accepted/release candidate or installed APK**.
  Publication SHA is neither frozen candidate source nor APK source identity.

## Diagnostic contract and implementation

1. Family `Recv` observes its original returned error and local context before its
   own stream cleanup. A bounded context observer feeds the existing startup
   recorder; `requestTransport` supplies the actual bootstrap stage. No error is
   wrapped differently, replaced or retried. Observations have no effect on I/O.
2. Existing top-level cause now explicitly recognizes `os.ErrDeadlineExceeded`
   as `IO_DEADLINE`, distinct from context `DEADLINE`. `io.ErrClosedPipe` becomes
   `CLOSED_PIPE`; an otherwise unclassified `Timeout()==true` is
   `TIMEOUT_UNQUALIFIED`, never automatically a context or budget deadline.
3. Optional `observation` contains allowlisted `point`, `error_category`,
   `context_state`, `stop_at_observation`, and monotonic-relative `elapsed_ms`.
   `FAMILY_RECEIVE` means observation before Family's read cleanup;
   `STARTUP_CALLER` means the existing startup failure call site. This timestamp
   is observation time, not an exact timestamp for every accumulated event.
4. Optional `local_stop` retains the first explicitly recorded local stop intent:
   `STARTUP_BUDGET`, `CONNECT_CANCEL`, or `CLEANUP`, with elapsed time. It is not
   a claim about the first physical bridge close, remote intent, or server cleanup.
   `stop_at_observation=NONE` means no such local intent had yet been recorded.
   Concurrent closed-pipe and context cancellation remain ambiguous.
5. The native budget callback records `STARTUP_BUDGET` before calling the same
   cancel function. Duration and timer stop behavior are unchanged. Successful
   startup stops this timer; it does not become a VPN lifetime deadline. Callback
   closures retain their original context/cancel, not the current global owner.
6. Native failure is recorded before `owned.cleanup()` calls `owned.cancel()`.
   A failed ownership wait uses the now end-to-end supported `OWNERSHIP_DRAIN`
   stage, never HELLO_RECEIVE. Existing explicit native stop can record STARTUP
   cancellation first, before the wait returns; first-failure order is preserved,
   not retrospectively overwritten with a more convenient stage.
7. Failure/Complete/Cancel keep the first failure; late cancellation does not
   replace invalid HELLO, certificate/auth/protocol categories, or turn successful
   startup into failure. New snapshot objects copy bounded observations rather
   than exposing mutable recorder pointers.

## Normal support export

Actual researchProvisioning uses `publicStartup` plus `provisioningResearch`, not
the ownerDiagnostic implementation. The normal path is still native stats
`owner_startup` → `Diagnostics.nativeStats` → `DiagnosticRing.startupStats` →
`RestrictedStartup.project` → saved ring/incident → `Diagnostics.share` JSON.

The allowlist retains the new categories, ownership stage and bounded optional
facts. Pure existing bundle-read/encode operations were extracted into
`DiagnosticRing.exportRecord/exportBytes`, called by the real share path and JVM
tests. URI grants, old-cache deletion, export rotation, Activity/UI behavior and
primary journal retention are unchanged. Record/export limits remain 256 KiB and
2 × 256 KiB + 1024. No arbitrary `err.Error()`, keys, payload or addresses are added.

Tests persist synthetic ring and incident separately, reload them through the same
bundle serialization, and check attempt/connection separation, old-schema missing
fields, preserved UNKNOWN, first failure after cleanup, malformed-code filtering
and size limits. The ten selected JVM tests pass. This does not execute Android
AtomicFile, Share UI, JNI callbacks or a real installed application's export.

## Before/after and regression results

[Raw synthetic test receipts](../../research/startup-cause-fidelity-20261015/results/)
are public; no owner diagnostic exports were used or published.

| Scenario | Before on handoff | Combined derivative |
|---|---|---|
| Real Family/TLS I/O deadline, local context live | UNKNOWN; no observation | IO_DEADLINE + LIVE, original `os.ErrDeadlineExceeded` retained |
| Parent deadline while HELLO read waits | UNKNOWN for deadline/closed-pipe variants | actual IO_DEADLINE or CLOSED_PIPE + observed context; no forced causal attribution |
| Cancel during blocked receive | UNKNOWN closed pipe | CLOSED_PIPE + CANCELLED context; not asserted to be a user action |
| Peer close, then late local cancellation | UNKNOWN close | original CLOSED_PIPE + LIVE remains unchanged |
| Invalid HELLO then cleanup | PROTOCOL_REJECTED | PROTOCOL_REJECTED preserved |
| Successful real HELLO/exchange, then stop | success | SUCCEEDED, no startup failure |
| Known auth/certificate/protocol errors, then cleanup | existing categories | category/unit preservation tests PASS; no runtime policy change |
| Unknown error without facts | UNKNOWN | UNKNOWN remains valid |
| Real coordinator drain + budget/manual/cleanup | no explicit stop provenance | supported stage and separate stop intent; budget cancellation stays CANCELLED, not invented I/O deadline |
| Stopped budget / old attempt callback | handoff timer | production budget helper tests: working/new context survives |
| Normal Java projection/export bundle | drops new categories/facts | safe facts retained, old schema/incident separation PASS |

Receive tests invoke the real `requestTransport` and Family TLS/Reliable path using
the existing in-memory synthetic fixture. I/O deadline uses a test context exposing
a read deadline without cancelling its parent. Parent deadline tests accept every
observed legitimate error/closure variant; there is no required variant quota.
Known category/unknown/budget tests additionally exercise the actual recorder and
production coordinator/helper, not a replacement classifier model.

Fixed final matrix: one normal + three race suite repetitions. All six existing
coordinator tests run: chat-first, VPN-first, opening, cancellation/recovery,
simultaneous acquire, compatibility/expiry/failure. Real broker handoff records
old release sequence 15 → new grant 17 → HELLO; broker A–D remain unchanged.
No standalone chat open bypass, cleanup ordering or security policy is modified.

Unexpected intermediate failures are retained, not erased: an old immutability
test compared new pointer addresses rather than their values (changed to deep
equality); initial sandbox Gradle could not open its local daemon socket; the new
JVM test used unavailable `Files.writeString` (changed to compatible `Files.write`).
Only after these specific fixes were final fixed-count checks run; no retry-until-pass.

## Build and runtime compatibility

- Native/JNI compile/link PASS: normal tags `[]`, `fc_owner_diagnostic`,
  `fc_messenger_lab`, arm64, Go 1.26.1, NDK 28.2.13676358. Existing budget JNI
  signature checks PASS. Native build metadata retains commands/hashes.
- Full offline Gradle 8.11.1 `assembleResearchProvisioning` and selected
  `testResearchProvisioningUnitTest` PASS, 65 executed tasks; 10 tests, no failures.
  New normal native bytes exactly match the library embedded in the unsigned APK.
  DEX contains IO_DEADLINE, CLOSED_PIPE, OWNERSHIP_DRAIN and the new observation fields.
- Existing input-verification tasks were not bypassed. Local metadata explicitly
  binds original Git base plus cumulative source delta and newly built native.
  No signing, permissions/debuggable, version, wire/Mux/framing, retries, timeout
  duration, protect/underlay or authentication decision changes.
- Diagnostic consumers inspected: native error decisions still use `Legacy(err)`;
  Java orchestrator uses native state/event outcomes, not the new observation fields.
  `startupdiag.Preserve/Legacy` and unwrap identities remain unchanged and tested.

## Limits and production unchanged

This fixes independently demonstrated **diagnostic information loss**, not the
historical owner failure's causal mechanism. No historical ring/incident record is
rewritten. No full VPN/DNS/HTTPS, server cleanup, Android runtime or device acceptance
is inferred from host/JVM compilation and tests. Real TLS auth rejection still has
its existing coarse runtime identity; this task does not redesign authentication.

Original dirty checkout is unchanged; source reconstruction, build trees, APK/native
binaries and caches remain local. Frozen snapshots and handoff evidence are untouched.
Publication consists only of safe review source/tests/receipts/docs; no main merge,
workflow change, release or binary distribution. Deployment-capable workflow path/
branch gates do not match this docs/research-only push; ordinary CI is permitted.

CONNECT/reconnect, ADB/SSH runtime access, owner export/native poll, APK install,
gateway/process restart, deployment, provider actions, real rooms, credential
mutations and recovery triggers: **all 0**. Product change is diagnostic-only;
ownership policy remains the previously tested handoff. DEVICE_ACCEPTANCE stays
NOT_RUN and PRODUCTION_ACCEPTANCE stays FAIL.
