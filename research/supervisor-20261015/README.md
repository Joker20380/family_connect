# Supervisor research source snapshots — reading only

These are copies of **existing work**, not new product patches or a new candidate.
The publication commit is not a frozen executable's source revision. Root source
outside this directory remains the public main checkpoint8d046321; it is not
silently upgraded to the experimental gateway. No build or test is run here.

- [Identities](source-identities.json): authoritative source/binary IDs projected
  from the existing local manifests; original isolated Git histories are not imported.
- [File inventory](source-inventory.json): origin, size and SHA256 for every copied
  source/provenance file. It describes publication contents, not a new sealed audit.
- [Baseline](baseline/carrier): complete carrier subtree of preserved snapshot
  471d1d62e1385a9ffc5ff6a16a5a7e9fe043fae2, representing a4087e0 plus its recorded
  classifier delta. This is the source of the recorded21f0a0fd…70509a baseline.
- [Frozen candidate](frozen-candidate/carrier): complete carrier subtree at
  134083d87773dacc038c9593afdaff0c57ea951d, recorded binary53beb661…5138f.
- [Local-stack overlay](local-stack-overlay/carrier): exactly seven existing files
  differing from the frozen carrier tree, including the local Pion provider,
  metadata/TLS/dial hooks and continuity tests. Conceptually this overlays
  frozen-candidate/carrier to recover the retained validation/carrier source tree.
  **It requires compilation with fixture hooks; it does not run the exact binaries.**
- [Research84](research84): selected existing Java startup/orchestrator/readiness
  classes and tests, native attachment, packet adapter and wholedevice source.
  This is not a complete Android build or a change to the installed APK.
- [Provenance](provenance): original behaviour/observability diffs, acceptance matrix,
  reproduction notes and trigger validation script. Historical scripts retain their
  original capsule/path assumptions and are published for reading, not execution.
- [Receipts](receipts): small existing production/rootcause result projections and
  historical test differential. They are not raw support exports or freshly run tests.

Use the [publication index](../../docs/releases/2026-10-15-supervisor-publication-index.md)
for the reports, source availability and evidence exclusions. Local artifact paths
inside unchanged historical documents do not make those artifacts available on GitHub.

No private keys/profiles, live room URLs, binaries, APKs, archives or raw journals are
included. Synthetic invalid URLs and placeholder userinfo in validation tests are
test inputs, not live provider credentials. No release/deployment scripts are invoked.
