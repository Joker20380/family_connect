# Startup diagnostic cause fidelity — cumulative research84 derivative

This is a **diagnostic delta above the implemented handoff**, not an accepted APK,
historical root-cause attribution, or a replacement for the ownership fix.
Read the [report](../../docs/releases/2026-10-15-startup-diagnostic-cause-fidelity-1.md).

## Source identities

- Input review: `4eb47111c85731262ebf9971cdf2fdb7706767a7`.
- Retained research84: base `f5240994869826c6a28f59e58e38256c688cf6eb` plus
  delta `d7907697d71f119c21bced533f08abae06ae33ef9159c5fd9bd54cf031a481e7`.
- Handoff patch SHA256:
  `a9be16b5be05788d0ad1c9c19497044a68f01e733a21739a33ba4ae507189c64`.
- Diagnostic-only patch SHA256:
  `bd3d3923a28e2bad405516d20dcb387f44586ff734e0432494934b682f5e146d`.
- Cumulative Git-base-relative file inventory digest:
  `a4d489079e3da0df7fdd01b7977962b20ddbbf8605fbf682a349703a88b916d5`.
  Algorithm and full inventory: `results/gradle-final/cumulative-source.json`
  and `build_gradle.py`. This is **not a Git commit SHA**.

`source-manifest.json` binds the twelve changed/new files to the handoff derivative.
`before/` contains exact affected handoff files; `changed/` contains complete updated
files. `diagnostic.patch` applies only after handoff. Archived namespaces are unchanged.

## Reconstruct and test

Use the retained source containing the exact Git base and eight research overlays;
the private full source/build inputs are not replaced by root main. The published
slice is reviewable without them, but full reproduction requires them.

```sh
python3 research/startup-cause-fidelity-20261015/apply.py \
  --retained "$RETAINED_RESEARCH84_SOURCE" --out /tmp/fidelity-cumulative
python3 research/startup-cause-fidelity-20261015/run_host.py \
  --source /tmp/fidelity-cumulative --review "$REVIEW_ROOT" \
  --tools "$RESUME_TOOLS" --out /tmp/fidelity-host
```

The runner stages the actual cumulative carrier and reuses the existing real
Broker/Family-TLS fixtures and handoff integration test. It never creates a live
provider session. Final repetitions are fixed: one normal suite and three race
suites. The `--before` option runs the same receive assertions against an unmodified
handoff reconstruction; failure is expected, not retried. No new dependencies.

Native/JNI build: invoke the unchanged
`research/chat-vpn-handoff-20261015/build_check.py` with `--source` pointing to the
cumulative tree, cached `--tools`, patched `--xray`, retained `--reference-classes`,
and a fresh `--out`. It builds normal, owner-diagnostic and messenger-lab arm64 JNI
and checks existing Java/native budget signatures. Reference-class javac is only
an additional contract check, **not** the full application build.

Full build and actual research variant JVM tests:

```sh
python3 research/startup-cause-fidelity-20261015/build_gradle.py \
  --source /tmp/fidelity-cumulative --retained "$RETAINED_RESEARCH84_SOURCE" \
  --tools "$RESUME_TOOLS" --native "$NATIVE_BUILD_OUTPUT" \
  --out /tmp/fidelity-gradle --awg "$RETAINED_AWG_GENERATED" \
  --radio "$RETAINED_AUDIO_NATIVE" --python "$RETAINED_PYTHON310"
```

The build uses a separate local clone at the research base, overlays the cumulative
source, records every delta hash, and retains existing verification tasks. Metadata
explicitly pairs the base revision/tree with the cumulative delta; the library is
newly compiled, not the research84 frozen native. Producer/patch contract fields
come from retained metadata; actual compilation commands are in the native receipt.
Unsigned output remains local. No permission, debuggable, signing, workflow or
APK-version change. Gradle's local daemon socket needs normal host permissions.

## Evidence and compatibility

- `results/before/`: expected receive regression failure on handoff.
- `results/after-1/`: retained unexpected test failure: an old test compared pointer
  addresses after Result acquired optional copied observations. Corrected to deep
  value equality; no product invariant removed. This preliminary selection omitted
  two handoff tests; the final selection includes all six coordinator tests.
- `results/after-final/`: final normal/race tests, including broker A–D and handoff.
- `results/native-build/`: native/Java/JNI compile/link receipts (no binaries).
- `results/gradle-1/`: sandbox Gradle socket failure, before compilation.
- `results/gradle-2/`: assemble succeeded; new JVM test failed compilation because
  Android's compile API lacks `Files.writeString`. Replaced only with `Files.write`.
- `results/gradle-final/`: final full assemble and ten selected JVM tests PASS.
- `results/verification.json`: observed error/closure variants, JUnit totals,
  embedded native byte identity and new diagnostic markers in the packaged DEX.

Schema remains 1 with optional `observation` and `local_stop`. Old records and
historical UNKNOWN remain unchanged. Context at observation and first recorded
local stop are independent facts, **not proof that a closed pipe was caused by
that stop**. No arbitrary error text or new identifiers are exported.

Local binaries, APKs, generated JNI headers/classes, caches, full retained source
and real support exports are excluded. No device execution, share UI/cache rotation,
TUN/HTTPS/DNS acceptance, or historical-cause claim is made.
