# L04.1 — exact installed Linux AWG/TCP acceptance

Date: **2026-10-25**. **BLOCKED — authorized Linux test activation not confirmed**.
Last completed stage: exact final-2 artifact and embedded inventory verification.
Installed baseline and real AWG/TCP sessions: **NOT_RUN**, not acceptance PASS.
Entry main/remote: `2cce01de4e6f7f1b65d0afc1098520dbce61c954`; no checkout/rebuild.

## Review scope and immutable inputs

User review accepts L03.1, L03.2 and parent L03 as DONE in full internal candidate
scope. [L03.2 evidence](2026-10-25-linux-candidate-l03-2.md) remains historical
package/install evidence, not this task's live session result. L04 IN_PROGRESS;
L04.2 QUEUED / NOT_RUN. L01/L01-R, L02/L02.2, D03/D04/D05, D01.3/D01.3-R,
native ownership/refcount/trust, Android106 pins and accepted schemas unchanged.

Only `state-client-build/linux-candidate-l032-20261025/build-final-2/` was used:

| Identity | Exact value |
|---|---|
| Product source | `cf66532c72548767f8ff4aa31faa7588b07eab54` |
| Candidate ID | `9d4b13cc106296264805402b42538b9fa94505433b1bbd239c82145966e22b81` |
| Internal version | `0.2.12~l03.2.1` |
| Source/public Linux version | `0.2.11`, unchanged; no new public distribution |
| Embedded system build | `8708ba6d5e218f86b42d862dd5a66237e974a03d5434e8f1c30524b16720e2da` |
| System archive | 49247776 bytes; SHA256 `bdd7e04b8ca78a232acccd881004cfb3b6c96b13dc3c608d0b919f53f40f02d9` |
| Fixed installer SHA256 | `ed8eac3d1b1c666b1d00433f09ec9a6eec578623249e0895adfa96ae3b53f9d5` |
| Runtime contract | schema2; Python3.12;707 user members /758 system payload files |

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `FamilyConnect-0.2.12~l03.2.1-x86_64.AppImage` | 57924088 | `914f02ff10f31485c5a6b68a8ff41f5b168aaffc8f7f8241723365c40a9109e5` |
| `FamilyConnect_0.2.12~l03.2.1_amd64.deb` | 55951120 | `df13422321f6c5865f1ca1060fe221fbe21954c6981ab05cb2d173e7aa6e04ac` |
| `FamilyConnect-Linux-0.2.12~l03.2.1.tar.gz` | 112233 | `8a3847d88aa0b7098f94518c0e986bbaf3e00bcfcc4bc35f82a6817cae1e15ae` |

Both requested sizes/hashes match before extraction. CI candidate `f7f6e765…` was
not used; no result is transferred between identities. This run installs neither
format, changes no version and publishes nothing.

## Completed offline integrity checks

- Existing `scripts/verify_linux_candidate.py` extracts both exact artifacts,
  invokes their packaged inventory verifier, compares candidate identities and
  exact707-member inventories, audits members, checks DEB maintainer/desktop/user
  systemd/D-Bus integration and AppImage launcher against inventory. **PASS**.
- Legacy archive still has exactly the six expected regular files and matching
  application bytes. **PASS**; updater contract untouched.
- Packaged `candidate_setup.extract_verified` validates embedded archive size,
  SHA256, bounded safe members, fixed installer SHA and invokes the embedded
  installer's `verify`;758 system files and exact build/source digest pass. It
  does **not** invoke install/root_main or apply system changes. **PASS**.
- Expected full candidate/source/system IDs were compared to the user's pins.
  Binding the archive hash in both user inventories ensures both formats embed
  these same verified system bytes. No trust bypass or mock-success was used.

Initial inventory invocation on host Python3.14.4 failed closed with
`Candidate runtime contract/ABI mismatch`. This is a prerequisite mismatch, not
a candidate defect: verification was rerun unchanged under required Python3.12.3.
No ABI check was relaxed and no product correction was needed.

Read-only artifacts mounted in disposable `fc-l032-system:check`, image
`sha256:6705fc0e0b9a4c83fa3710e45f2b54a27c80cd49b27dbfe7db213d946f5b9dce`:
Ubuntu24.04.5, Python3.12.3, systemd255.4-1ubuntu8.18 binary. `--network none`,
all capabilities dropped, no-new-privileges, no host system/network mounts,
containers automatically removed. Only verification code ran; systemd was **not
PID1**, NetworkManager/resolved/polkit/Secret Service were **not started**. This is
an offline artifact check, **not** the requested real systemd+Internet live gate.

Ignored local receipts:
`state-client-build/linux-installed-l041-20261025/exact-candidate-integrity.json`
and `embedded-system-integrity.json`. Sanitized combined receipt:
[L04.1 preflight JSON](2026-10-25-linux-installed-awg-tcp-l04-1.json).

## Blocking prerequisite and credential boundary

No existing Linux test identity together with current AWG/TCP activation was
confirmed as authorized for use in a disposable live environment. This means
**no eligible input established**, not a claim that no private credentials exist.
Discovery was limited to repository documentation and local filenames/directories;
private keys, activation bodies, profiles, invitation codes and personal identity
stores were not read, copied or output. No gateway/API probe was attempted.

- Existing desktop parity evidence identifies the workstation's personal Linux
  owner; it is not a confirmed isolated test credential. It was not borrowed.
- The [September control pilot](2026-09-13-linux-control-resume.ru.md) has a
  historical registered test identity, but its [recorded configuration/lease](2026-09-13-linux-control-pilot-pass.ru.md)
  expired13 September and required a new revision/lease for continuation. That is
  not evidence of current AWG/TCP activation; no renewal, signing or conversion
  was attempted. Current registration validity was not queried or inferred.
- The only `.fcactivation` files found under the inspected repository state
  roots are Windows-labeled; their contents/validity were not inspected. They
  were not repurposed as a Linux identity. Legacy raw WG profiles are not a
  matching activated AWG/TCP test pair.
- The [confirmed three-device cohort](2026-10-23-tester-p1-cohort.md) is Android
  field scope, not permission to clone its credentials into this Linux fixture.
  Existing offline synthetic L03.2 identities cannot satisfy this live gate.

Per the explicit stop rule, no further installation/live actions were taken.
To resume, identify a protected local location of the **already authorized**
Linux test state/activation with current AWG and TCP materials, and confirm its
use in the disposable environment. Do not paste keys/tokens into chat or Git.
No new registration, grants, floors, policies or signing are requested. A fully
isolated outbound Ubuntu24.04/systemd255 environment must then be established;
this run did not validate such an environment or select public transfer targets.

## Acceptance ledger — no session evidence fabricated

| Required stage | L04.1 result |
|---|---|
| Exact AppImage/DEB/embedded hashes, members, candidate binding | PASS, offline only |
| Clean DEB install, ordinary-UID GUI, root runtime absent before setup | NOT_RUN |
| Real pkexec setup, installed readback/capabilities, no VPN intent | NOT_RUN |
| Existing activation resume/restart; network/process baseline | BLOCKED / NOT_RUN |
| Real installed GUI AWG, DNS/HTTPS/download/upload through TUN | NOT_RUN |
| Real installed GUI TCP/Xray, DNS/HTTPS/download/upload through TUN | NOT_RUN |
| AWG↔TCP handoffs, reconnect generations, exact cleanup/baseline restore | NOT_RUN |
| Wrong build/capability, busy owner, pending journal on installed candidate | NOT_RUN |
| Cancel, gateway refusal, pipe loss, late result, disconnect during transfer | NOT_RUN |
| Same-UID original AppImage +DEB state/runtime/owner/GUI-close coherence | NOT_RUN |
| Live state/identity/floors preservation | NOT_RUN; existing state not modified |

Sessions attempted: **0**. Transport/generation/session ID, selected-next/active,
interface, routes/rules/nft/DNS, public IP before/during/after, transfer counters,
cleanup inventory and sanitized session diagnostics: **not collected**. No
CONNECTED/READY/live cleanup conclusion is inferred from package inventory or
historical tests. No external production VPN/Telemost traffic or P1 operation.

## CI, rollback and handoff

No implementation/tests/workflows were changed. No new installed-live CI gate was
run or represented as passing without credentials/isolation. Existing public CI
packaging integrity, Client Linux, isolated native/root→UID/Auto/DIRECT and full
suites remain mandatory and unchanged. This documentation/inventory checkpoint
does not need a repeat of the entire historical suite; any push-triggered CI is
source regression only, not exact final-2 installed AWG/TCP evidence.

Prior package CI40184803906/job121143223621, Client Linux40184498169/job121142388736
and isolated native40183917928/job121140566226 PASS remain **L03 evidence**.
Latest recorded full results: control40184803896/job1211432346393102/54/140;
phase040184803868/job1211432234763102/54/140; Docker same run/job121143223341
3100/54/142 (passed/failed/skipped), errors0. D01 stays open with54 residual
failures; D02.1-R PARTIAL/NOT_RUN. Windows TLS/voice observations are not fixed,
hidden or relabeled. No overall CI PASS claim.

Nothing installed by L04.1, so no rollback/uninstall/network cleanup was required.
The L03.2 root backup and explicit idle reinstall/removal story is unchanged, not
retested live here. Host routes/DNS/services/connections and existing user data
were not modified; no VPS, catalogs, landing, public releases or signing changes.
Parallel ops STATUS/PLAN hunks and untracked VPN health report stay outside the
commit. Only safe docs/sanitized inventory evidence enter Git.

**STOP. NEXT — review L04.1.** L04 remains IN_PROGRESS, L04.2 QUEUED/NOT_RUN;
no L05/L06/L08, MESH/Auto live or cross-format upgrade acceptance.
