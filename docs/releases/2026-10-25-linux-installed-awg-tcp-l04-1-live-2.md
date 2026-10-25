# L04.1-LIVE-2 — bounded negative installed AWG/TCP,25.10.2026

## Result / review boundary

**PARTIAL — first product failure at B1; STOP.** Gate A PASS (actual installed
manifest tamper/reinstall). B1 prevents transport creation, but does not return the
user operation journal to baseline. B2–F NOT_RUN, not waived and not inherited PASS.

One GUI AWG Connect with the real root transport lock held leaves
`friends.application.json` in **APPLYING**, operation generation **0 → 1** and a
durable pending reservation. After releasing the fixture lock both physical locks
are FREE, but read-only poll raises **ConnectionBusy: Connection recovery is pending;
resume the control client**. No owner/TUN is created; network baseline is unchanged.
The pending journal persists through the final observation,183.492s after the click.
No retry, second Connect, Disconnect, manual journal deletion or source correction.

Input main `472b37483ff918f2e4870003b7901beb249e14ba`.
RETEST DONE/review accepted: valid terminal positive/NXDOMAIN/NODATA fresh-DNS
contract. Positive gate не повторяется. Parent L04.1 IN_PROGRESS до LIVE-2 review.

## Immutable input

Exact internal0.2.12~l03.2.2, product source
`57f8eff8b291062d69248ac46413f8c9fc0f561d`, candidate
`d9c0d07f93542a633b5563757f0c5aa0d4f0c37410b3b884ba8b67db01c484ef`,
system build `8708ba6d5e218f86b42d862dd5a66237e974a03d5434e8f1c30524b16720e2da`.
Pair только `state-client-build/linux-poll-disconnect-l041r-20261025/build-1/`.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `FamilyConnect-0.2.12~l03.2.2-x86_64.AppImage` | 57924088 | `33537e451ab39010b70c989604477fc73c86f6b88f7f5d7d4c5a50dd07887a8a` |
| `FamilyConnect_0.2.12~l03.2.2_amd64.deb` | 55951452 | `c806ed9fac2466772042cde6c84a59b7bd86172cd3d91dee724449de78f77dda` |
| Embedded system archive/build-9 | 49247776 | `bdd7e04b8ca78a232acccd881004cfb3b6c96b13dc3c608d0b919f53f40f02d9` |
| Legacy six-file tar.gz | 112344 | `79a2c8d7961d49e3b3c0240c259352c7bd426cdf98f260037cc6eaa98d13f4f2` |

Standard extracted verification PASS: candidate identity,707 user members, exact
embedded archive/installer/system identity. A network-disabled container was used
only for artifact verification; installed negative tests used **real KVM**, not
container/mock/helper-CLI evidence. No rebuild, repack, public version/catalog change.
Candidate imports/inventory rechecked after B1: PASS; installed product not patched.

## Environment and state handoff

Ubuntu24.04.5, kernel6.8.0-147-generic, systemd255.4-1ubuntu8.18, qemu10.2.1/KVM,
2CPU/4GiB. Real NetworkManager, resolved, TUN, nftables/iptables/iproute2, D-Bus,
Secret Service and polkit. SLIRP/loopback SSH, encrypted qcow2, ordinary UID1000.
Guest-only GTK/AT-SPI/Xvfb/openbox and auditd fixtures; no installed product hooks,
no allow-all polkit rule, no host network/service changes. Actual password approval
through the polkit agent; guest sudo inspection is not counted as product authorization.

Clean exact DEB + GUI explicit setup created build-9 READY without VPN. An offline,
encrypted clean snapshot was made; A and B1 use independent copies. Gate A has no
protected test state: stock unactivated GUI creates local bootstrap keys, but no
invite, activation or new registered test device. Before preparing the separate
live base, only these guest-local bootstrap files were removed.

Existing read-only source preflight PASS. Only
`/var/tmp/fc-l04-test-20261025-6uva6jb3/home/` streamed into guest, not operator/receipt.
HOME `/home/tester`, consistent XDG config/data/state roots, UID1000,0700 directories,
0600 files, no symlinks/hardlinks/special files. Installed Python3.12 `-I -S` with
exact packaged vendor: `create=False`, **FC-3YSQ-BE2D**, public identity SHA256
`d07d33a81728ff70aec350ae59785990c194d90ecd44574b0da28439189532de`.
Verified cache only nl, AWG/TCP present, signed floor sequence3/catalog hash
`f4d812db722705d8fc853a1a1afd454922cd2bca71175db025f40b9a58c3628d`.
No manual configuration fetch; only the one product Connect may perform its existing
idempotent nl fetch. Original protected state was read, never mounted writable or edited.

## Gate A — PASS, limited to installed manifest tamper

READY → append one newline to root-owned0644
`/usr/local/lib/family-connect-mesh/installed.json` in the disposable snapshot.
SHA256 before `aabcce5e4baf25db37f05cd43d0ef4ab8a1ae83a622f30f05438c3f0c1c77b31`;
after `b5d4cf0faef53757f81d40b769b93d2197e6397356b9d291583133637494a049`.
Exact candidate readback returns **INSTALLED_MANIFEST_MISMATCH**, not READY.
GUI Connect disabled; AT-SPI action cannot dispatch. This GUI is also unactivated:
disabled Connect alone is not evidence of the tamper cause; the typed inventory
readback independently demonstrates it. No helper up/down, owner, TUN or network change.

GUI Settings → Install system component → Install → real polkit approval restores
READY and imports/inventory PASS from the same embedded bytes. Same-boot network
hashes unchanged. Cross-boot IPv6 route hashes varied during fixture boot; they were
not used as an equality oracle, nor hidden as a product cleanup result.
No retained nonmatching exact artifact was installed. **Mixed-build NOT_RUN here**;
only [accepted package evidence](2026-10-25-linux-poll-disconnect-l04-1-live-1-r.md)
is inherited, explicitly distinct from actual installed manifest tamper.

## Gate B1 — FAIL / first-failure boundary

Independent clean snapshot, transferred accepted state, GUI selected Netherlands/AWG.
Separate root fixture opens `/run/family-connect-transport.lock` with O_NOFOLLOW,
checks regular file/root owner/0600/nlink1 and holds actual nonblocking exclusive flock.
One Connect, one polkit submission; no subsequent user mutation.

Actual audit EXECVE counts: **AWG import1/up1/down0**, TCP import/up/down0. Thus the
requested helper-up count0 gate is not met. A helper process invocation is not a
successful transport start: held lock prevents any AWG interface/owner/network apply.
Root helper exits; no helper/transport process remains. Actual remains none,
diagnostic state DISCONNECTED, selected AWG; no CONNECTED or fallback observed.

At32.610s: generation1/pending=true, journal APPLYING. Fixture released; root and
user operation flocks independently FREE. At153.882s and183.492s pending/APPLYING
still present, UI **Status unavailable / Connection settings are being updated.
Waiting for completion.** Real installed read-only poll raises ConnectionBusy with
the exact pending-recovery message above. Baseline active count0; no second mutation
or automatic recovery was attempted. This proves retained durable ownership, not
an indefinitely held physical lock. The underlying rollback exception is not
established by this black-box run; a later source checkpoint must reproduce it.

Diagnostics still report `first_failure=NONE`; that is an observed diagnostic
limitation, not evidence that the negative gate passed. Network/identity preservation
PASS does not make the operation/journal baseline PASS.

An idle `family-connect-auto@1000.service` was started by the existing normal-catalog
path. Read-only IPC: DISCONNECTED, desired=false, controller=null, selected empty.
It is not Auto VPN/MESH fallback. Its later explicit stop is **fixture cleanup only**.

## Cleanup, server readback, remaining gates

Before/after B1: lo/enp0s1 only,0 owned TUN/routes/rules/nft/DNS, no transport process,
no root active/sticky marker. Same-boot routes4/6, rules4/6, firewall structure,
resolved DNS/domains/default-route hashes match. GUI closed normally; idle catalog
host stopped only after disconnected readback. Pending user journal **not** manually
removed or declared recovered; it remained until encrypted guest destruction.

Read-only server baseline/B1/final compare PASS: target AWG DB/live **1/1**, Xray
persisted/runtime **1/1**, same assigned address/bindings, foreign bindings/global
settings/network/catalog and service PID/invocation hashes unchanged; ru counts0.
No new device/invite/provisioning, operator fetch, server restart/deployment or revoke.
Identity/cache/floors byte/readback preservation PASS; source preflight unchanged.
Guest, all encrypted clones/keys, seed/SSH/password, transferred state and private
logs removed. Original protected state and teardown receipt retained for later gates.
Host routes4/rules4/resolved DNS/domain hashes match before/after.

| Gate | Result |
|---|---|
| A actual installed tamper + explicit reinstall | PASS; mixed-build inherited only |
| B1 shared root transport lock | FAIL: helper-up1 and persistent pending journal; no transport/network apply |
| B2 durable foreign user reservation | NOT_RUN after first failure |
| C1/C2 AWG/TCP endpoint unavailable | NOT_RUN after first failure |
| D authorization channel loss | NOT_RUN after first failure |
| E queued Connect/GUI close | NOT_RUN after first failure |
| F AWG/TCP Disconnect during transfer | NOT_RUN after first failure |

L04.1-LIVE-2 **PARTIAL / review pending**, not CHECKPOINT PASS. L04/L04.1 IN_PROGRESS;
L04.2/L05/device-scoped cleanup → readback → registry revoke remain QUEUED / NOT_RUN.
No repeat positive traffic/DNS gate, no new live TCP claim. Historical RETEST remains
accepted for these exact bytes; this negative defect is recorded separately.

## Evidence, checks and checkpoint provenance

[Sanitized machine evidence](2026-10-25-linux-installed-awg-tcp-l04-1-live-2.evidence.json),
SHA256 `e0ac07123be13e8b5f7f6d8cccd37a2ef2373d1808b2577921991663cd51ddfa`:
exact artifact inventory, scenario/generation/count/error/cleanup snapshots, public
identity fingerprint and server binding hashes only; no raw state/profiles/keys/UUIDs.

Entry documentation commit `01715f5` accidentally included the parallel ops prose;
ordinary follow-up `4e9f1f6805740f14a8febe37ae604a942ace2e3f` removed those hunks from
the branch without rewriting history and retained the original uncommitted ops work.
That corrected execution checkpoint was pushed and remote SHA verified before B1.
Final docs/evidence commit and remote readback are reported at handoff (no self-referential SHA).

Only sanitized docs/evidence change. Final gate: links/content, JSON parse, exact
artifact hashes, staged allowlist/secret scan and `git diff --check`; no product tests
disabled or xfailed. No new full-suite CI result claimed: accepted source/package
Linux/AWG/TCP/native checks remain historical; full suites54/54/53 residual failures,
voice and Windows observations remain open. Source correction is a separate task.

**STOP. NEXT — review L04.1-LIVE-2.**
