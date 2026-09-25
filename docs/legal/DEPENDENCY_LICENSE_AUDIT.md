# Dependency and repository licensing audit — 2026-09-25

Scope: Home Gateway technology selection and requested proprietary source-available
notice. No executable code or new dependencies introduced in this change.
This is a technical provenance/terms review, not an opinion that all historical
distributions are legally cleared. [Inventory](../../THIRD_PARTY_NOTICES.md).

## Repository history and ownership

Audited the available non-shallow local history (`HEAD` at inspection: `3f6f662`),
all local refs, tracked license filenames, commit author identities and co-author
trailers. `git shortlog -sne --all` reports 348 commits, one identity:
`Vladimir <80757922+Joker20380@users.noreply.github.com>`. No additional co-author
trailer was found. No root LICENSE/COPYING history was found; license-path history
contains the third-party Xray license (`fa3c71e`, `c51f8c5`). This is evidence from
available refs, not proof of ownership of every line or of absent deleted/unfetched
history. Existing uncommitted changes were present before this task and preserved.

Existing third-party files/assets and packaged components are expressly excluded
from the root rights claim. The known ICQ smiley provenance gap was recorded on
2026-09-19 and is still unresolved; do not silently claim those images. Dependency
notices do not themselves establish rights in contributions. If prior licensing or
another rights holder is discovered, preserve those permissions/rights and resolve
that material separately; the new notice is not retroactive revocation.

Use the user-specified project identification, not an invented legal company:
`Copyright © 2026 Joker20380 / Family Connect. All rights reserved.`

Reproduction commands (from repository root):

```sh
git rev-parse --is-shallow-repository
git shortlog -sne --all
git log --all --format='%an <%ae>'
git log --all --format='%B' --regexp-ignore-case --grep='Co-authored-by:'
git log --all --format='%h %s' -- '*LICENSE*' '*COPYING*'
git ls-files '*LICENSE*' '*COPYING*' '*NOTICE*'
```

## Home Gateway dependency decision

| Dependency | Version/commit | License | Purpose | Redistributed? | Source modified? | Notice required? | Risk/comments |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Official Python `rns` | 1.5.1, existing lock and Android Gradle pin | Reticulum License | Existing identity/control; selected Home Gateway wire implementation | Yes, existing Android; no new artifact here; Windows worker proposed | No modification introduced here | Yes, complete copyright/permission text | Custom use restrictions; not MIT/public-domain implementation. Verify actual wheel and bundled notices before Windows packaging. |
| pyserial | 3.5, existing pin | BSD-3-Clause, retained Android notice | Existing RNS runtime dependency | Yes, existing Android | No change here | Yes | No new dependency decision; retain notice. |
| Chaquopy | Existing Gradle plugin/runtime configuration; no version change | MIT for plugin, separate runtime dependency notices | Existing Android Python embedding | Yes, existing Android | No change here | Yes | Audit full runtime package when adding Home Gateway packaging. |
| rns-vpn-rs | Upstream manifest 0.1.0, master inspected; not pinned for inclusion | MIT | PoC reference only | No | No | Not applicable to this codebase: no copied portions | Mutable reference URL is not an approved build input. Record immutable SHA before any adoption. |
| Reticulum-rs / riptun / Rust dependency tree | Not selected or added | Not audited for inclusion | Evaluated only as dependencies of the reference project | No | No | N/A | STOP for inclusion until version-specific licensing and reference-stack wire compatibility are verified. |

No GPL/AGPL/strong-copyleft dependency is added by this task. This does not classify
all pre-existing dependencies as permissive: e.g. Xray has MPL-2.0 obligations,
and WireGuard/Wintun source and binary distributions need separate inspection.
Unknown terms block the specific dependency or new packaging decision, not
unrelated documentation work. A comprehensive pre-existing transitive audit remains
open and must not be represented as complete.

## Reticulum terms and platform feasibility

The [upstream license](https://github.com/markqvist/Reticulum/blob/master/LICENSE)
permits commercial use, redistribution and modification subject to its retained
notice and restrictions concerning purposeful harm to humans and AI/ML training
datasets. Do not describe it as standard MIT or waive those restrictions through
Family Connect's root LICENSE. The existing bundled 1.5.1 notice identifies
Copyright (c) 2016-2025 Mark Qvist; current upstream master identifies 2016-2026.
Do not silently replace a pinned component's notice with a mutable master copy.
The protocol's public-domain designation is a separate statement, not the
implementation license. The dependency does not require relicensing original
Family Connect source under its terms, but its own obligations survive bundling.

Reference Python is selected because existing identity and Android embedding
already use it; no alternative wire implementation is needed. Windows packaging,
secure worker IPC and lifecycle remain implementation work. Recheck installed
distribution metadata, hashes and transitive notices before a new release.

[rns-vpn-rs license](https://github.com/BeechatNetworkSystemsLtd/rns-vpn-rs/blob/master/LICENSE):
MIT, Copyright (c) 2025 Beechat Network Systems Ltd. No files/portions imported,
translated, modified or bundled. A research mention is not a claim to have used
their code. Any future source inclusion requires exact provenance and full MIT
notice, not merely an entry in this table.

## Separate root LICENSE review deliverable

Reviewed before the legal documentation commit:

- Scope is original material owned by the identified project owner; third-party
  components and other rights holders are excluded.
- Public visibility grants no general reuse, derivative distribution, sale,
  substantial republication or branding permission. No open-source claim remains
  in the current READMEs.
- Existing permissions, applicable law and platform viewing/forking terms are
  preserved. [GitHub's explanation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
  distinguishes public repository access from licensing rights.
- No invented company, trademark registration assertion or third-party ownership
  claim; no Reticulum license pasted into the Family Connect root license.
- Source availability is distinct from binary/service use terms. This source
  notice does not purport to be a complete consumer EULA or commercial service contract.
- RU/EN README statements and retained notices agree; ICQ rights gap and incomplete
  historical artifact audit remain explicit. This review is not legal counsel approval.

## WebRTC carrier reference audit — preparation only, 2026-09-25

The owner limited this iteration to documentation/preparation. No code copied,
modified, linked or redistributed from either inspected repository; no Go/Pion
module or fork added. Existing proprietary Family Connect LICENSE is unchanged.

| Repository / immutable revision | License verified in checkout | Files/logic inspected | copied / modified / linked / redistributed | Use |
| --- | --- | --- | --- | --- |
| [kulikov0/whitelist-bypass](https://github.com/kulikov0/whitelist-bypass/tree/7c19a7ec40900940fe0c43ea1db7768ee632393d) | MIT; copyright line is exactly `Copyright (c) 2026`, no named holder on that line | `relay/wbstream/{api,session}.go`, `relay/livekit/*.go`, `relay/telemost/api.go`, headless creator entrypoints, Android joiner structure, `relay/tunnel/rtc/vp8tunnel.go`; guest/signaling/ICE/DC/VP8/lifecycle | no / no / no / no | Reference-only |
| [openlibrecommunity/olcrtc](https://github.com/openlibrecommunity/olcrtc/tree/92b2332769c3dd5000584366201572efc448065f) | WTFPL v2; Copyright (C) 2026 zarazaex | `internal/auth/wbstream`, `internal/auth/telemost`, engine/transport boundaries, reconnect contracts and example configs | no / no / no / no | Reference-only |

Upstream license files at inspected revisions:
[whitelist MIT](https://github.com/kulikov0/whitelist-bypass/blob/7c19a7ec40900940fe0c43ea1db7768ee632393d/LICENSE),
[olcrtc WTFPL](https://github.com/openlibrecommunity/olcrtc/blob/92b2332769c3dd5000584366201572efc448065f/LICENSE).
Do not label olcrtc MIT or attribute all transitive files to its root license.
If any source is adopted, record exact source/destination files and modifications,
retain the complete applicable notice and inspect all included transitive licenses.
No full VPN/SOCKS/tun2socks architecture is selected for reuse.

| Candidate dependency | Inspected version | License status for inclusion | Purpose | Redistributed / modified now | Notice requirement / risk |
| --- | --- | --- | --- | --- | --- |
| `github.com/kulikov0/headless-client` | v0.1.0 in whitelist go.mod | Not audited; STOP inclusion until its own license and forks are checked | Pion-derived headless RTC/HTTP runtime reference | no / no | No adoption from parent project's MIT alone |
| `github.com/pion/webrtc/v4` | v4.2.15 in olcrtc go.mod; not a Family Connect pin | Exact version/graph license review pending | Candidate carrier engine | no / no | Select minimal dependency set and retain upstream notices before coding/bundling |
| LiveKit/forked RTC engines | olcrtc manifest, not selected | Not audited for inclusion | WB signaling/media reference | no / no | Avoid importing whole graph; unknown licenses block that dependency |
| Go toolchain | Installation deferred; no project version selected | Packaging/license review with chosen toolchain | Candidate isolated process build | no / no | Current shell has no Go executable; no build performed |

Root-source license permission and service API access are different questions.
WB guest joining is visible in code but live room creation/media permissions and
provider usage terms/quotas must be checked before deployment. No provider login,
room creation or traffic exchange was performed by this audit. These sources do
not prove current availability on restricted mobile networks. No GPL/AGPL or other
new dependency has been silently introduced.
