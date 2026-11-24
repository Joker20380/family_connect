# Accepted read-only snapshot fixture

This is the explicit public-source contract for the retained generic snapshot archive
`0120dad028ead353b8b83a600538f3e578b2b46ddf871bf16e97529f9449f450` (26,854 bytes).
Its complete18-member inventory is recorded in
`docs/releases/2026-10-28-android106-beta-0-canary-nl-readonly.json`.

`sources.json` pins each Python member to an exact historical Git commit or a reviewed
source-only text fixture. The two text snapshots match that recorded inventory and the
retained accepted archive byte-for-byte; those member versions are not in the available
Git history. No private state, profiles, keys or operational configuration is included.
They are test inputs, not deployable source replacements.

`scripts/ci_release_fixtures.py` reconstructs the original archive with its original
member ordering, ZIP metadata and entrypoint. It checks every member and the unchanged
whole-archive SHA256 before exposing `FC_TEST_SNAPSHOT_ARCHIVE`. It does not normalize
the expected hash to today's sources. The current unbound credential-renewal package
is built separately by the real package builder and supplied as `FC_TEST_RENEWAL_PACKAGE`.
