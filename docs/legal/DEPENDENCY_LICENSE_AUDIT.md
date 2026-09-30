# Dependency and repository licensing audit — 2026-09-25

Scope: Home Gateway technology selection and requested proprietary source-available
notice. No executable code or new dependencies introduced in this change.
This is a technical provenance/terms review, not an opinion that all historical
distributions are legally cleared. [Inventory](../../THIRD_PARTY_NOTICES.md).

The scope above is the historical25.09 change. The following27.09 addendum
records the subsequently authorized, recovered5N.1 prototype.

## Recovered Telemost carrier — 2026-09-27

5N.3 addendum: isolated `familysession` uses the already included Go1.27.1
`crypto/tls`/`crypto/x509`/Ed25519 implementation, not a new crypto library,
handshake, RTC stack or module pin. Existing Go BSD-3-Clause notice is retained.
The disposable acceptance issuer uses existing pinned RNS1.5.1 and cryptography
46.0.7 through DeviceIdentity/ProductStore; no code copied from another project.
[Selection/API/trust-boundary review](../testing/webrtc-eu3-session-profile.md)
is not an independent cryptographic audit or production security approval.
The carrier and 23-module dependency graph/notices remain unchanged.

5N.2 Android addendum: Go1.27.1 Android/arm64 CGO `go list -deps` matches the
same23 external modules/versions below. No module fork, new RTC stack or copied
implementation. Android build uses NDK28.2.13676358 and unmodified pinned anet's
documented linker workaround; runtime keeps original notices in APK assets,
including original NDK and LLVM notices conservatively. Those aggregate notices
do not establish that every listed compiler/tool component is linked. Java wrapper
uses Android platform APIs only; JUnit4.13.2 is test-only, not an APK dependency.
APK is isolated/debug/device-test-only, not a published production release.

`carrier/go.mod` was damaged by shutdown (985 NUL bytes); original version pins
cannot be inferred. Original bytes are preserved in recovery commit `ee3a830`.
Reconstructed pins: `pion/webrtc/v4 v4.2.15` (research version, now actually used),
`gorilla/websocket v1.5.3`, `pion/interceptor v0.1.45`, `pion/rtp v1.10.2`,
`pion/logging v0.2.4`. `go.sum` restored through Go proxy/checksum verification;
`go mod verify` PASS. No `replace`, forked RTC or whole reference module.

The [23-module linked inventory](../../carrier/DEPENDENCIES.md) records exact
versions/root LICENSE SHA256 values from `go list -deps ./cmd/telemost-binary`
on Linux/amd64. Pion roots MIT; UUID/Gorilla/anet/Go x/* BSD-3-Clause. Additional
Pion BSD-3-Clause and CC0 texts are retained, not overwritten with MIT. Google
UUID is an actual Pion transitive despite the local auth helper avoiding it.
[Complete original notices](../../carrier/licenses/dependencies.txt) include
module LICENSE/NOTICE/LICENSES texts and Go1.27.1's license. No modifications to
dependency implementations. No GPL/AGPL module is linked by this executable.
Upstream test/tool-only nodes of the full module graph are explicitly separated;
their presence in go.sum does not mean they ship in this harness. Re-audit before
adding them or changing platform/build tags. This is not historical app clearance.

Recovery provenance cannot justify the old Go comment “not copied”: protocol
maps, layout and byte constants overlap the references. Treat those narrow
portions as reference-derived and retain both complete notices conservatively:

| Pinned source | Recovered destination / adaptations | Terms / disposition |
| --- | --- | --- |
| olcrtc `92b2332769c3dd5000584366201572efc448065f`: `internal/auth/telemost/{api,telemost}.go`, `internal/engine/goolom/{signaling,media,capabilities}.go` | `carrier/telemost/{auth,signaling,session}.go`: HTTP fields, hello/capability maps, pub/sub SDP/ICE; bounded lifecycle, sanitized failures and queues adapted locally | WTFPL v2, Copyright (C)2026 zarazaex; [full notice](../../carrier/licenses/olcrtc.txt) |
| olcrtc same SHA `internal/transport/vp8channel/wire.go`; whitelist-bypass `7c19a7ec40900940fe0c43ea1db7768ee632393d`: `relay/telemost/api.go`, previously inspected `relay/tunnel/rtc/vp8tunnel.go` | `carrier/telemost/{vp8,signaling}.go`: recovered VP8 prefixes/protocol constants; bounded FC framing is separate, no KCP/session epoch protocol imported | WTFPL v2 + conservative whitelist MIT attribution; [full MIT notice](../../carrier/licenses/whitelist-bypass.txt), original copyright line retained exactly |

No cookies, bearer tokens or room secrets are included. Only a local temporary
test executable was built; nothing publicly distributed or integrated into
Android/Linux product/Windows releases. Copy `carrier/licenses/` with any later
private PoC binary transfer. Live continuation27.09 used the same pins/notices:
binary + complete `carrier/licenses/` were privately transferred to Amsterdam,
run as an unprivileged temporary process and removed after acceptance. The small
application ping/pong heartbeat follows the already-attributed goolom signaling
contract; no additional dependency or reference implementation was imported.
Proprietary root LICENSE unchanged; reference-code
terms do not grant Telemost service access or prove provider usage permissions.

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

Minimal Telemost carrier dependency set verified from `olcrtc/internal/engine/goolom`
and `olcrtc/internal/auth/telemost`: the Telemost join path uses only
`github.com/pion/webrtc/v4` (MIT, plus its MIT Pion transitives),
`github.com/gorilla/websocket` (BSD-3-Clause) and `github.com/google/uuid`
(BSD-3-Clause, avoidable). It does not import `kulikov0/headless-client` or any
LiveKit/forked engine module. Exact versions remain Family Connect pins TBD and
must be re-audited in the FC `go.mod`/`go.sum` before coding/bundling.

Root-source license permission and service API access are different questions.
WB guest joining is visible in code but live room creation/media permissions and
provider usage terms/quotas must be checked before deployment. No provider login,
room creation or traffic exchange was performed by this audit. These sources do
not prove current availability on restricted mobile networks. No GPL/AGPL or other
new dependency has been silently introduced.

## Direct EU priority correction — 2026-09-25

The new5N plan uses the same inspected whitelist-bypass and olcrtc references,
reference-only: no copied/modified/linked portions or new dependencies. No additional
crypto/mux/tun2socks library is selected or licensed by this decision. Inspect the
existing Xray TUN conversion boundary first; its MPL-2.0 obligations still apply
if modified. Audit exact versions and transitive licenses before implementing the
new Family encrypted session/reliability/mux. Root proprietary LICENSE is unchanged.

## EU-6 diagnostic packet reuse — 2026-09-30

The isolated Android adapter reuses the existing product packet dependencies:
Xray `v1.260327.0`, commit `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0` (MPL-2.0),
gVisor `v0.0.0-20260122175437-89a5d21be8f0` (Apache-2.0), and the existing Family
carrier dependency graph. It is not a new TCP/IP stack or copied bypass project.
Exact module closure is recorded in `pilot/android-restricted/go.mod` and `go.sum`.
The existing Xray ConnectionHandler boundary is opened by
`pilot/android-restricted/xray-packet-boundary.patch`; modifications to MPL files
remain subject to MPL, not relicensed by the proprietary repository root.
`build.py` requires the exact upstream pin, archives it, applies the patch and
packages the patch, Xray/gVisor license texts and existing carrier notices in
diagnostic APK assets, with patch/binary hashes. No public distribution is made;
any future distribution must supply corresponding modified MPL source and retain
all applicable transitive notices, rather than treating this note as a waiver.
Provider API permission/quotas and license permission remain separate matters.
