# L04.2 — installed Linux MESH/Auto acceptance

26.10.2026. **BLOCKED on test-state prerequisites / installed live NOT_RUN.**
This is not CHECKPOINT PASS, an observed product failure, or an entitlement denial.
**L04.1 DONE; parent L04 IN_PROGRESS. STOP. NEXT — review L04.2.**

## Scope and review decisions

Entry: current `main`, local/upstream SHA verified as
`1877821b8848a46cb1585b3a0e1bfe6074503a87`. No checkout/reset/rebuild.
Pre-existing VPN-health reports and their STATUS/PLAN preambles remain local,
unstaged and outside this checkpoint. Only L04.2 was authorized.

Owner review, accepted as input rather than re-tested in this task:

- Exact **0.2.12~l03.2.9** is installed on the owner workstation;
  candidate/package/system checks PASS; one main window with embedded chat,
  one ChatClient and one D-Bus owner are confirmed.
- **OWNER-CHAT-UX-2-INSTALL: PARTIAL / owner-use accepted.** The two observed
  queue operations have unknown origin and are excluded from acceptance evidence.
  No product defect is established. No further owner installation/UX acceptance.
- The owner workstation was **not used for L04.2 live acceptance**. No owner
  application action, message, smiley, composer or visual check was performed.
  Its personal identity/state was not read or copied for this task.
- CHAT-UX-2 source/package is DONE; historical full-suite failures and FD teardown
  observation remain unsuppressed. Neither owner-use nor source/package acceptance
  closes full L05 or authorizes publication.

Read inputs: [desktop architecture](../desktop-architecture.md),
[L02.2 combined local gate](2026-10-24-linux-chat-mesh-l02-2.md),
[L03.2 candidate/package](2026-10-25-linux-candidate-l03-2.md),
[L04.1 entry](2026-10-25-linux-installed-awg-tcp-l04-1.md),
[installed retest](2026-10-25-linux-installed-awg-tcp-l04-1-retest.md),
[final accepted AWG/TCP receipt](2026-10-25-linux-installed-awg-tcp-l04-1-final.md),
[test activation/handoff](2026-10-25-linux-test-activation-l04-1-auth.md),
[test provisioning](2026-10-25-linux-test-provisioning-l04-1-auth.md),
[CHAT-UX-2](2026-10-26-chat-ux-2.md) and its
[immutable delivery manifest](2026-10-26-chat-ux-2/candidate-delivery.json).
Historical local/synthetic gates do not substitute for installed live evidence.

## Exact immutable inputs

Internal **0.2.12~l03.2.9**, Ubuntu26.04 / system Python3.14.
Source `cb81cd50e0afaee0b25d78bb3bd7176c9999d250`;
candidate `6f312d1e7c783ea42a39ca164d93d74b0ec4faf5bac53e24c12551cedd052a5b`;
matching system `43266d97c6a9f8d4e7026727cbb4b5cb6aeea49db799f93bd798b67a8135198c`.
Existing artifacts: `state-client-build/linux-chat-ux-2-20261026/build-final/`;
matching retained archive from `state-client-build/linux-ubuntu2604-python314-20261026/system/`.

| Artifact | Bytes | SHA256, rechecked |
|---|---:|---|
| `FamilyConnect_0.2.12~l03.2.9_amd64.deb` | 56149054 | `e79bca1bb70a1b8d6db1ba44436cb9216c8fa7bf769fb3d919a1f2c8c96eaf62` |
| `FamilyConnect-0.2.12~l03.2.9-x86_64.AppImage` | 58112504 | `dc790701321da9e63325bc097bf6eab81032ed7f46236e0ed2de39cc673d45d4` |
| `FamilyConnect-Linux-0.2.12~l03.2.9.tar.gz` | 114597 | `348f5e9609987a9c1751e3cca47e321b2622cb142ecbebedbe70f874fc17b215` |
| Matching system archive | 49252181 | `402affe5628da4ecd1df3e274f3c67848d5e59023a63374765c91419490b9a55` |

No build, repack, candidate-manifest edit or byte replacement. The manifest's
`installed:false` / `acceptance:NOT_RUN` remains immutable build metadata;
the owner review and this task's separate results are recorded here instead.

## Read-only prerequisites and blocker

Only the previously authorized **FC-3YSQ-BE2D** test home was inspected.
Public identity fingerprint:
`d07d33a81728ff70aec350ae59785990c194d90ecd44574b0da28439189532de`.
The existing protected AUTH handoff was mounted read-only into a new disposable
container; only `home/` was copied into private temporary storage. No operator
directory/invitation, owner identity, product DB or signing material was imported.

The exact .9 packaged identity/store modules, not checkout modules, ran offline
with `create=False`. All seven original files are owner1000, directories0700,
files0600, without symlinks/hardlinks/special files. Exact identity and signed
**nl AWG/TCP** cache verification PASS. Floor sequence3 and catalog hash
`f4d812db722705d8fc853a1a1afd454922cd2bca71175db025f40b9a58c3628d`
are preserved. There is **no chat identity/store**, no settings directory and no
application journal in this handoff; absence is not a tested SERVICE_ONLY/IDLE
state. No root-owned verified MESH material/context accompanies that user home.

At **13:14:27 UTC**, one bounded read-only SSH check on authorized
`185.251.89.19`, scoped to the existing Family Connect service, verified the exact
test public-identity hash and active/non-revoked registration/invitation.
SQLite was opened `mode=ro` with `PRAGMA query_only=ON`. Only sanitized booleans,
counts and public-code/policy hashes were returned; no raw bindings or DB rows.

| Read-only fact | Result / meaning |
|---|---|
| Registry service / exact running archive | active; `21d64558e542ff6ad80fb9b13799fbcb333167ffb5a79ec841e7c94dc65d71fa` |
| Admission policy | `all_activated`; this active test identity is eligible |
| Policy SHA256 | `b65c0f53845be1ab4c413c5f18e186309dde25d3a4be16282330adb781e4f629` |
| Explicit restricted grant rows / active rows | 0 / 0; **not a denial under all_activated** |
| Unexpired restricted certificates for this device | 0 |
| Deployed restricted source | `3f8613a92d1b26e6dc4d7d9e2f05ff6e87d4a8e3482580db0a7745058b48ae09`, matches local source |

Eligibility is not a verified, issued/applied native profile context. No claim
that all_activated requires an explicit grant row is made. The deployed
[readiness fetch](../../control/friends/restricted.py) issues/persists a certificate
when no reusable current certificate exists. No challenge/fetch/ACK was called:
obtaining that new material was not treated as permission for new provisioning.
No server-side DENIED or gateway outage was observed or inferred.

Independently, the missing existing chat identity/store blocks the required
authenticated chat registration/health and chat/VPN ownership baseline. The
[chat owner](../../provisioning/chat_owner.py) cannot resume an absent store;
creating it would generate new chat identity/keyring state. This was not done
under the prohibition on new identity/provisioning. No synthetic chat account or
credentials from another user/device were substituted. No Connect was attempted.

**BLOCKED is an input/handoff boundary, not a newly reproduced product defect.**
Review must resolve the missing authorized chat state and the scope of obtaining
current MESH material before any installed scenario; this report grants no such
permission and starts no provisioning/activation follow-up.

## Offline verification actually run

New disposable **Ubuntu26.04.1 LTS / Python3.14.4**, UID1000, image
`sha256:f3f6eb49125eac073f8cb99c7c4c00538dafe4df61fd6cfa5782986bebea3d1d`.
`--network none`, distinct netns, read-only filesystem/input mounts and private
executable tmpfs; no host D-Bus/resolver/network namespace mounts. No systemd/GUI
or product service was started. This container is an offline preflight, not the
installed live environment or a package-entry PASS.

Existing `scripts.verify_linux_candidate.verify()` rechecked both extracted
inventories, integration payloads, candidate/system pairing and legacy archive.
**762 members / six legacy files / exact manifest and separate system archive PASS**.
The first harness attempt lacked the public source mount required by its inventory
validator and stopped with FileNotFoundError before private-state validation.
The corrected mount-only invocation PASS is retained separately. No installed
user action was retried and no candidate/product source was changed.

Private local receipts/scripts are retained under `/var/tmp/fc-l042-20261026/`,
outside Git/CI; directory0700 and files0600. Sanitized receipt hashes:

| Receipt | SHA256 |
|---|---|
| `assignment-readonly.json` | `97514757b650dd4faa134c624aa425a03f71e2b9f839f33ed9c0f15c242dcfcc` |
| `offline-preflight-final.json` | `ee59aafe67744874372386126d9f5b4391474cf75b05a8916f3a7bb07bdb5813` |

## Acceptance ledger

| Required gate | This task's result |
|---|---|
| Exact DEB hash/candidate inventory/matching system bytes | PASS offline only |
| Installed .9 / explicit matching setup / candidate-system READY / prepare-chat / no auto-Connect | **NOT_RUN**, stopped at prerequisites |
| SERVICE_ONLY, authenticated chat registration/health, clean journal/pending before VPN | **BLOCKED / NOT_RUN**; absent state is not a successful baseline |
| Manual MESH P0, actual profile/generation, DNS/readback/bounded HTTPS, refresh/selection | NOT_RUN |
| Manual MESH P1 in independent clean snapshot, no false P0 fallback | NOT_RUN |
| Auto in independent clean snapshot, preference/assignment/applied separation, stale callback fencing | NOT_RUN |
| One VPN owner/TUN and verified-context chat borrowing, not country matching | NOT_RUN |
| Disconnect/IDLE/pending null/network-DNS restore/renewed SERVICE_ONLY | NOT_RUN |
| GUI close/reopen during active system session, one Disconnect/no late CONNECTED | NOT_RUN |
| AppImage/DEB sharing installed system/state | NOT_RUN; equal offline inventories alone are insufficient |
| Original test-state/cache/floor preservation | PASS for offline copy/readback of seven files only; no post-session claim |

No real messages, history/voice/notification/delivery acceptance, performance
benchmark, soak, sleep/resume, network migration or updater migration. L05 NOT_RUN;
L06/L07/L08 retain their previous QUEUED status without new acceptance.

## Cleanup, rollout and closure

The disposable containers were removed, including temporary private copies.
The original protected test home and existing teardown receipt are retained;
all seven original bytes match before/after. No live resources were acquired:
no VPN/session/GUI action, new identity/invite, peer/user provisioning, gateway
addition, policy change, server restart, Android106/Windows/iOS change, signing
or publication. No test-device revoke/teardown was performed.

No user/system installation occurred in this task, so no package/network rollback
was required or claimed. Owner-installed .9 remains untouched. Any future live
attempt requires the permitted existing state and a fresh disposable installed
baseline with explicit matching setup; no owner credentials, manual journal
deletion, floor reset or substitution of older artifacts. Last documented public
Linux remains0.2.11, not reverified over the network here. No public rollout claim.

Closure checks **PASS**: three JSON documents/manifest-receipt consistency,
18 introduced relative links, public-source guard2981 index entries/0 blocked,
added-content secret scan0 findings, staged four-document scope and working/staged
`git diff --check`. The pre-existing ops diff is preserved byte-for-byte apart
from Git's index-blob header, and its two untracked reports remain untracked.
No unrelated full product suite is rerun for this documentation/preflight result.
The ordinary documentation commit/push and remote SHA verification are recorded
in the final handoff; a source push is not a deployment or release.

**L04.2 BLOCKED / live NOT_RUN; L04 remains IN_PROGRESS. STOP. NEXT — review L04.2.**
