# Bounded cold field delivery preparation — 7 November 2026

Status: local build/package work in progress; NOT a deployable field APK or rollout.

## Accepted baseline

- F checkpoint `867ba7f7bc2869f41468c12495a2e929e4dc3f33`; application
  `9bf02724deacf1c5e4293bea1bfdc6fc4f7fcacc`, native source
  `6eb61a9faa659b6b07ac16bf9f4bac46a41cd2a7`, harness
  `252c87e367e59cdad1b29f8245d2db618125ad40`.
- F/API28/emulated CELLULAR-only cold DROP/READY/DNS/verified HTTPS/egress stays
  accepted, not repeated. E's two DNS timeouts/two ProtocolErrors remain unexplained;
  F is not a retrospective fix or physical-phone acceptance.
- Original FAILs and A–F evidence remain untouched. Production, G4, paid/cohort,
  public updater/catalogs and user phones are outside this operation.

## Native and package checkpoint

Standard `pilot/android-restricted/build.py` from a detached6eb source capsule builds
arm64-v8a with NDK28.2.13676358, pinned Xray
`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`, no diagnostic build tags.
The builder's required packet boundary race check passes (count3); no old JNI/JVM
matrix or emulator gate is repeated. JNI SHA256:
`773d760dc8f5a7894ed7008b5f6c30b830bd663f66a8935d470f5262ebc50d26`.
Private output: `state-client-build/cold-field-delivery-20261107/native-arm64`.

Reserve unpublished versionCode119 / `0.1.18-beta119`, not a replacement118.
Package gate now supports a pinned native-source commit and generated-artifact directory;
it still requires clean tracked sources, exact native/manifest match and verifies that
carrier runtime/native/build closure did not change. Application source is independently
recorded. Existing release-preservation pins are advanced only to already accepted9bf
classes, not to new untested application changes.

No final locator has been issued, no signature produced, no APK installed or published.
The ARM64 managed build and unit tests complete; release lint identifies `WrongConstant`
in the accepted API27 compatibility helper (numeric18 is FOREGROUND on that API).
A method-scoped source-only `SuppressLint` annotation documents that deliberate numeric
compatibility path; the expression and network-selection behavior remain unchanged.
Release lint and bytecode equivalence are rechecked before packaging, not waived globally.
The release/packaging checks, bounded server package and handoff procedure remain pending.
Rollback is to stop only the prospective new entry; existing services and public
beta113/catalog7 remain unchanged. No new public download link/checksum is advertised.
