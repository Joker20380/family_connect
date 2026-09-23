# Current state / Текущее состояние

Updated 2026-09-23. Distributed clients and test candidates are listed separately.

| Platform | Public download | Candidate under test |
| --- | --- | --- |
| Android 8+, ARM64 | 0.1.18-beta35/code35; 36,407,372 bytes | beta38/code38 installed on a test phone; 147 unit, 5 UI and 1 reconnect test passed |
| Linux | 0.2.9 paired bundle146d221d0ad23c07 | 0.2.10; 24 layout checks passed |
| Windows x64 | 0.2.9 previewa6c68fe | 0.2.10 source54506d8; build, native UI and ordinary-user broker CI passed |
| macOS / iOS | No app release | Longer-term roadmap |

[Downloads, checksums and test evidence](releases/2026-09-23-public-client-status.ru.md) · [Installation](getting-started.en.md).

The README image shows the beta38 test candidate. Public beta35 still uses manual
invitation-code activation. The next update preserves invite-only access and device
keys while removing manual key entry, and places country/protocol selection beside
the battery. New installers, invitation page and catalogs have not been published.
Android CI setup failed; remaining release gates must pass before distribution.

The current pilot supports VPN and Android text messaging. Incoming chat refresh
requires the messenger to remain open; background push and broader offline/restart
acceptance remain incomplete. Desktop messenger parity is not claimed.

Invitations: up to 20 new referral claims per sponsor per rolling 24 hours, within a
shared pool of 500. Retrying the same request does not consume an additional slot.
These are configured limits, not a live remaining count. Direct invitations use a
separate budget. Device keys remain individual and revocable. Billing is not implemented.

Public main does not yet reproduce the distributed Android APK. Matching source
publication remains open. This documentation update does not publish that source,
change servers, revoke keys or change signed update catalogs.

Repository-wide licensing, private security reporting, Windows publisher signing,
broader platform acceptance and the commercial access model remain open.
[Next actions](PLAN.md) · [Documentation](README.md).
