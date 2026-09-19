# Security

Family Connect is an actively developed pilot. There is no independent security audit
or long-term supported production release declared here. Public source and passing tests
are useful evidence, not a security guarantee.

## Reporting a vulnerability

A dedicated private reporting contact and response-time policy have not yet been established.
If GitHub shows **Security → Report a vulnerability**, use that private channel. Its availability
must be confirmed by the repository owner; this document does not claim it is enabled.
If it is unavailable, ask the maintainer for a private channel without disclosing the flaw publicly.
Do not put exploit details, credentials, invitation tokens or personal data in a public issue.

## Boundaries to review

- [Architecture map](docs/architecture.md): distinguish the live clients, provisioning,
  control channel and separate relay laboratory.
- [Identity and provisioning trust model](docs/adr/001-identity-provisioning.en.md):
  separate device identities, recipient binding and pinned signing anchors.
- [Stage 5 verification and recovery design](docs/stage5-architecture.ru.md): signed
  revisions, expiry, durable state and rollback; dated platform limitations need STATUS.
- [Windows key custody](docs/windows-native.en.md): privileged broker and DPAPI boundaries.
- [Privacy notes](docs/privacy.md): data and metadata exposure, including limitations.
- [Desktop release verification](docs/updates.en.md): offline catalog signing, increasing
  sequence numbers and artifact hashes. Catalog signing is not Windows Authenticode.
- [Android beta19 checks](docs/releases/2026-09-19-beta19-download.ru.md): immutable APK
  and checksum. Android friends updates are manual and use a consistent beta signing key.

The operator, signing authority, gateway and device OS remain trust boundaries. Compromised
administrator access, traffic correlation and a compromised gateway are not solved by a VPN.
The QUIC laboratory threat model in [architecture.en.md](docs/architecture.en.md) applies to
that laboratory, not automatically to every released client.

## Handling secrets

Keep device keys, profiles, activation/invitation tokens, product databases, backups and
release-signing keys out of Git, CI artifacts and reports. Runtime state directories are
ignored, but `.gitignore` is not secret scanning. Check staged changes before publishing.
There is no verified repository-wide secret-scanning configuration claimed by this document.
