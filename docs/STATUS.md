# Current state / Текущее состояние

Updated 2026-09-19. This page distinguishes distributed applications, public source,
and work in progress. Historical reports are evidence for their dated stage.

## Available applications

| Platform | Distribution | Verified scope / limits |
| --- | --- | --- |
| Android 8+, ARM64 | 0.1.18-beta19, versionCode 19; 36,390,988 bytes | Pilot VPN and two-phone messaging confirmed. Foreground incoming refresh; background push and broader offline/restart acceptance incomplete. |
| Linux | v0.2.9 desktop prerelease, GTK 4/libadwaita | Operator-assisted setup; current Android friends invitations and messenger are not included. |
| Windows x64 | v0.2.9 desktop prerelease | Native installer/broker; operator activation; no trusted publisher signature. |
| macOS / iOS | No application release | Longer-term roadmap only. |

[Android download and verification](releases/2026-09-19-beta19-download.ru.md) ·
[Installation](getting-started.en.md) · [Desktop guide](clients.en.md).

Android SHA256: `5ebe38168f084d3e19bb740722ec7c3a7ceb5e9ed63508efc3e3ff3f5e0bf3a4`.
The user chose to keep the current animated smileys despite rough edges.
Android APK, installed application, servers and release catalogs are unchanged by this documentation publication.

## Invitations

The pilot has separate budgets: 50 direct invitations and a shared pool of 500
referral invitations. A referral slot is consumed when a new code is issued, not
when it is activated. A direct code does not reduce the referral pool.
The latest read-only check returned 0 referral codes issued, 0 activated, 500 remaining.
The user confirmed using a direct code. The Android pool-limit label is fixed;
the remaining count is loaded once when opening the invitation screen.

## Source and desktop work

Public main currently predates Android beta19; do not claim it reproduces the published APK.
The corresponding local Android/messenger changes still need a reviewed source checkpoint.
Desktop integration is developed separately on `desktop/friends-access-20260919`,
commit `429eb77`; it has not been merged into main or released.

[Identity storage report](releases/2026-09-19-desktop-identity-storage.ru.md):
53 scoped / 549 full Python checks passed locally (2 upstream warnings).
Windows control CI 35469710256 passed. Client builds 35469710250 Windows and Linux
jobs passed, including Windows broker restart, UI and layout checks.
Android failed during SDK setup; overall CI was not successful and release was skipped.
No new desktop installer is offered as a user release.

## GitHub presentation

Product README EN/RU, installation guides, security/privacy, documentation map and
contribution templates are prepared as a documentation-only main update. Markdown
links, 17 external URLs and four Mermaid diagrams passed validation. See the
[presentation report](releases/2026-09-19-github-presentation.ru.md).

## Public launch gaps

Repository-wide license and commercial model are not chosen. Billing is not implemented.
Third-party artwork rights, private vulnerability reporting/contact, Windows publisher
signing, matching Android source publication and broader messenger acceptance remain open.
GitHub About requires owner authentication; the exact command is in the
[presentation report](releases/2026-09-19-github-presentation.ru.md).

[Next actions](PLAN.md) · [Documentation](README.md) ·
[Previous public status, historical](STATUS.before-2026-09-19.md).
