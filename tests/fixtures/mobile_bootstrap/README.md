# Volgograd mobile bootstrap — exact beta95 derivative

The capsule is `state-client-build/mobile-bootstrap-20261020/`. Source baseline is
the verified installed95/A0 source inventory, not checkout main. Relevant94 and95
readiness Java/Python files are byte-identical; all twelve native libraries in96
equal95. Gateway/1011 and LEGACY64 remain unchanged. No production fault injection.

`prepare.py` verifies the two supplied exports, deduplicates events and creates an
isolated source copy once. Do not rerun it over an existing capsule. Product delta
is `beta95-to-beta96.patch`; apply only to that exact accepted95 source tree.
`build.py` seals the delta, reuses native95 and runs the affected/recovery JVM suites.
It binds the existing immutable Git metadata to the isolated work tree for the
existing provenance verifier; it neither creates a branch nor alters the accepted
source. Retained failed build logs must not be deleted or counted as passing.

Tests:
- `python3 -m unittest discover -s tests/fixtures/mobile_bootstrap -p 'test_*.py' -v`.
- `build.py`:175 JVM cases including valid/expired/denied cache, recovery and JSON
  export through the actual DiagnosticRing serializer.
- `network_fixture`: compile these stubs plus actual candidate ChatNetworkAndroid
  with the existing JDK, then run `com.familyconnect.app.NetworkProbe`. This checks
  per-call underlay selection/handoff/TUN exclusion without connecting any sockets;
  it is not Android kernel/Volgograd cellular acceptance.

`api_readback.py` runs read-only on authorized RU. It looks up only the specified
Support ID, never uses that ID for authorization and never copies device keys,
nonces or proof. Server receipt retention and journal gaps limit historical attribution.

`sign.py --check-only` verifies unsigned96, exact native reuse, package/alignment
and previous signer pin. `sign.py` uses the existing offline GUI vault workflow;
the owner must enter the vault password in the protected dialog, never chat/shell.
Do not start it unattended or leave a prompt waiting in the background. No signing
secret is persisted/exported. Signed destination is
`delivery/FamilyConnect-0.1.18-beta96-bootstrap.apk`; successful signing receipt and
SHA25607a90f03… are retained. Do not sign again to reproduce an existing artifact.
Do not send or install the unsigned APK, and do not present beta95 as a bootstrap fix.

`upgrade.py check/install/identity-after` reuses the pinned existing guarded updater
with fresh pre/post identity comparison, never a stale identity snapshot. Owner update
95→96 completed14:48:37UTC while VPN/service were already absent; do not rerun install.
For any future update, a fresh version/signer/identity readback and ordinary manual
disconnect are prerequisites. Never replay a saved install intent, clear data,
downgrade or reactivate. Candidate must keep LEGACY64/128 OFF. Owner's manual Connect
and new96 READY/device proof are pending; server-row equality is not that proof.
One targeted tester cellular Connect+diagnostic export is useful only after that
ordinary same-key update; FIELD_PASS stays NOT_RUN until actual evidence arrives.
No new API, invitation, root enrollment, gateway restart, speed test or public push.
