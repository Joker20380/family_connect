# Historical Android unit inputs

These are public source snapshots, not APKs, identities, runtime state or
new acceptance evidence. `scripts/ci_android_fixture.py` checks literal SHA256
before loading any snapshot. A mismatch fails; current Android source is not used
as an unverified replacement for an older boundary.

- `bridge95.py.txt`: exact beta95 frozen Python bridge, hash
  `6dc08e65f7b60d77a1f8a6a4d05afdaadbaad547382a1c7c966365957a517c4b`,
  recorded in the [bootstrap receipt](../../../docs/releases/2026-10-20-volgograd-mobile-bootstrap.evidence.json).
- `bridge96.py.txt`: exact beta96 bridge, hash
  `2c895a3728eb1d93e4121c8c9526960e544a947417738823a4e714c7475e250d`.
  A regression applies the existing `mobile_bootstrap/beta95-to-beta96.patch`
  to the pinned beta95 Python file and compares the complete result byte-for-byte.
- The deadline103 bridge uses `clients/rns/fc_rns_transport.py`, pinned to
  `70593713d1d915904d10cf0cac0eb21ca41b11b4dedcdb7973d0da236579ada0`
  in the [RNS source receipt](../../../docs/releases/2026-10-24-rns-reference-d02-2.md).
- The health89 fixture pins `health89.java.txt` (exact `VpnHealth.java` from
  main09f1aae5, before per-app carrier health) to
  `bbab99f2cfbc527c19e378c37b78f7ec53be96bdafb2bcd2915666ce8013f19b`,
  also recorded in the [earlier source inventory](../../../docs/releases/2026-10-03-canary57-provenance.json).

The tests use synthetic callbacks, loopback DNS and the CI JDK, never private
build directories or connected phones. This does not repeat Android runtime QA.
