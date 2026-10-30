# NL production gateway replacement — 30 October 2026

## Status and authorization

**NL-REPLACEMENT-20261030 / BLOCKED_NL_REPLACEMENT.** Localized cause: exact accepted
renewal rejects the expired publisher directory before canonical profile promotion
(`DIRECTORY_INVALID`). RU/NL previous-snapshot rollback readbacks PASS; the transaction
remains `RECOVERY_REQUIRED`, with no commit decision. RU ordinary HTTP is restored;
restricted services remain inactive/quiesced and renewal is paused. Old NL is FENCED.
New ordinary AWG/TCP synthetic data-plane and cleanup PASS, but no client publication,
Android106 endpoint verification or owner smoke. This is not full server acceptance.
Host/staging provenance: after the initial
blocked audit, the owner authorized installing the required OS/packages over SSH.
Supported LTS upgrades and exact-runtime compatibility checks are complete, not a
provider disk reinstallation or product deployment. Final OS: Ubuntu26.04.1 LTS,
kernel7.0.0-42-generic. Inactive file restoration is verified; product activation and
acceptance were then pending. Current fencing/ordinary results are recorded below.

The initial **BLOCKED_NEW_HOST_OS** finding was an incompatible OS/runtime: Ubuntu22.04/glibc2.35
cannot load the exact accepted CPython3.14.4 executable requiring `GLIBC_2.38`.
The snapshot launcher explicitly requires CPython3.14; system Python3.10 is not an
accepted substitute. No runtime downgrade, custom build, libc replacement or OS
upgrade was attempted during that initial read-only audit. This is an ELF ABI
incompatibility, not a missing ordinary tool. Subsequent installation is recorded below.

Initial host-key verification was paused. The owner could not locate the provider
console and then explicitly chose direct public-key installation. In a separate local
terminal the owner accepted the previously observed RSA fingerprint via SSH TOFU and
completed `ssh-copy-id` successfully. Provider-console verification remains **not done**;
TOFU is not independently verified provider identity. The operator subsequently checked
the accepted known-host fingerprint and authenticated with strict host-key checking and
the existing private key, without password prompts. No known-host entry was replaced or
checking bypassed. Password input stayed in the separate terminal, not this transcript,
shell history, command arguments, environment or reports. No private SSH key was copied.

Target: `root@185.10.158.212`, replacement production Netherlands gateway. This is
availability restoration, not a new product checkpoint. **BETA-0-CANARY-1 remains
PAUSED**. Paid-canary, subscription events and Android stage0 were not run.

## Repository and provenance

- Fetched `origin/main`; local and remote entry SHA both
  `17713e70279ed86d13c52ebddf167b6dc3d40a47`.
- Existing unrelated tracked and untracked changes are preserved and excluded from
  this source/documentation checkpoint. No branch switch, reset or history rewrite.
- Accepted coherent canonical source remains
  `c9c0a4de55f455e0788e7b519383c0cb0743fc96`; no rebuild or approximate substitution.
- Read the current incident, canonical acceptance and backup boundaries. The accepted
  old-network findings were not reinvestigated. New NL is the restoration path.
- No client/server version, installer, APK, invitation link or update catalog changed.
  Android106 is the required later client acceptance target, not newly observed here.

## Artifact audit

All five requested anchors have exact retained matches. A private inventory records
size, SHA256, owner, group, mode and source/receipt provenance;889 local files were
inventoried. Matching copies were found twice for each role. Later canonical acceptance
retains these bytes; no artifact supersession is asserted.

| Role | Bytes | SHA256 |
| --- | ---: | --- |
| Snapshot package | 167573 | `6dd51ead36a977abd4e6afee978d81df229ac767a6315bc4b2347328bde60c84` |
| Credential renewal | 60950 | `c2ce2b01ac15cbb553692579e7a03b6bc7ad97f2159906ed884c3fda490a40c0` |
| Restricted maintenance | 201792 | `c134eb6b56f01a4a54829b73c3259ba15886f603726058cc5f29afd3778b2a2d` |
| Canonical gateway | 17925498 | `f8ff517804c8cc425b172c821630274ce39ccfa9a3e79328db3e8a626f45ebef` |
| Exact-payload CRL helper | 138174 | `3c3736917efb1720b7086e57e4e8b2182fcb56734ec85b662b9bed71c15840a6` |

## Coordinated backup and old-host readback

At17:57:07UTC, read-only SSH using the existing accepted operator route exported the
later accepted coordinated NL backup created28.10 at20:14:20UTC:42 files, manifest
SHA256 `de7f7af32260b310a6b41f6758b95b0175d5f4f2adda42085901fd08bb45c969`.
Every retained payload matched its receipt hash both remotely and locally. The archive
was encrypted in memory with AES-256-GCM before local persistence; encrypted-file
readback and authenticated decryption reproduce the same bytes. Local private material
uses0700 directories/0600 files. No plaintext archive or key was printed or committed.

For the coordinated-backup role, this later42-file receipt supersedes the earlier
34-file staging backup as the selected recovery evidence. Neither is a complete current
machine image. Current gateway identity/TLS/authority, AWG/TCP keys and peers, supporting
identities, forced-command lines, runtime, firewall/NAT/sysctl and monitoring coverage
still require a complete private restoration matrix and fresh coordinated export.
Backup integrity PASS is **not** full identity-recovery or deployment acceptance.

Additional read-only exports are encrypted and verified: current application7 files
and infrastructure14 files, with one SQLite backup checked in each; recovery bundle
3895 files/549 directories and a separate NL renewal-state bundle1394 files/164
directories. Bulk live exports are **not coordinated across all roles**; final
quiescent/fenced export and the full private deployment matrix remain required.
The application snapshot's AWG private identity derives the running server public key;
all46 peer/address mappings match the live interface, with no duplicate addresses.
All46 TCP credential IDs and mappings are unique. No client credential was regenerated.
The canonical private identity matches both retained coordinated profile copies.
Historical canonical profile signatures/bindings PASS, CRL/floor27224 aligned. Its
authority remains valid until16 January2027; gateway certificate and CRL expired
29 October11:42:38UTC. Historical validation is not current-valid production acceptance.

Read-only current inventory at17:57:40UTC retained112 file/directory metadata records,
effective service argv and listeners privately. AWG, TCP, mailbox, Reticulum and load
monitor were active; restricted gateway was inactive/disabled. All six observed
`NRestarts` values were0 in this single sample; this is not a stability or data-plane test.
**Old NL remains unfenced**; nothing has been activated on the replacement. No identity
conflict was introduced. Old service activity is not evidence of healthy production.

## Historical inactive restoration qualification

Private deployment matrix now covers13 roles and10 source units, including ordinary
AWG/TCP, canonical gateway, snapshot/renewal/publisher/maintenance boundaries, mailbox,
Reticulum, monitoring, retained legacy AWG/native WG and the mailbox mount.5285 verified
files and689 directories are restored inactive. Full paths/configurations remain private.
Five locked service accounts preserve names/groups; two numeric UID collisions with
base OS accounts were remapped, without changing those OS accounts or creating admins.
Production service starts are guarded by an absent activation marker. Forced-command
authorized-key routes are not installed; existing new-host SSH identity/admin access is unchanged.

The external interface changes from the observed old `ens3` to new `eth0` in the two
active JSON configurations and two scoped nftables files only. No signed material or
binary was patched. The publisher directory inode/device binding and dependent locator
hashes are rebound to the new filesystem; profile/directory ownership boundaries remain
separate. A missing parent-directory traversal mode was corrected from source metadata.
Exact accepted snapshot launcher bytes match after fresh pinned-runtime qualification.
Mailbox uses a newly allocated bounded ext4 volume with the original marker, identities
and file-level snapshot; no live filesystem image was copied. Mailbox preflight, Xray
configuration, native WG configuration and both scoped firewall syntax checks PASS.
These checks neither start product listeners nor establish current-valid restricted
materials, data-plane acceptance, actual SSH snapshot or successful renewal.

## Fencing and ordinary data plane

Old NL: eight product units stopped/disabled, with persistent missing-marker restart
guards and a separate scoped ingress quarantine. Product interfaces and listeners are
absent; external TCP443/4242/4243 no longer accept connections. RU mutating SSH ingress
to old NL is blocked while direct operator SSH and read-only local monitoring remain.
No old file or identity was deleted. An initial verification fixture treated systemd's
unprintable `Conditions` property as text; corrected readback checks loaded guard files,
unit states, network interfaces and actual firewall rules instead. Fencing is proven.

Final coordinated export19:59:43UTC runs with product services inactive, mutating ingress
isolated and profile/registration/membership locks held:5289 files,709 directories,
75623230bytes, SHA256 `a7e8b7ed5eec29ec0ccec166d295c02995dc2608bce179d2a2165d46daae9b8f`.
Authenticated encrypted readback PASS; two changed files reconciled before activation.
The new host retains its own verified SSH host identity and owner administrative key.
Four accepted forced-command public-key lines and one bounded sudoers route are restored;
no private SSH key was transferred. Actual RU→new-NL canonical RPC inspection PASS.
Snapshot rejects the expired profile; this is not current-valid snapshot acceptance.
A canonical JSON newline fixture error was corrected without rebuilding any artifact.

New scoped ingress is default-deny with loopback, established/related, ICMP/IPv6 ICMP,
SSH and only required product ports allowed. SSH/fail2ban remain usable; no global flush.
Accepted IPv4 forwarding/rp-filter and IPv6 policy verified; scoped AWG NAT uses `eth0`.
AWG/TCP plus retained legacy interfaces, mailbox, Reticulum and monitoring started.
Restricted gateway remains inactive pending current-valid materials.

- AWG20:03UTC: synthetic handshake, DNS, HTTPS, new-IP egress, IPv6 fail-closed and cleanup PASS.
- TCP20:04UTC: synthetic REALITY authentication, remote DNS, HTTPS, new-IP egress and cleanup PASS.
- No owner/paid-canary identity or persistent peer/credential was used. A non-root Docker
  fixture write-permission error was corrected inside the bounded synthetic container.
- Three samples over30seconds: stable ordinary/supporting PIDs,0 restarts,46 authoritative
  AWG peers/46 TCP credentials, no duplicate allowed addresses, no OOM/kernel storage error.
- New monitoring samples are fresh. Old provider capacity200Mbps is not asserted for the
  replacement: capacity remains unknown until independently established.
- Fresh RU application backup:54 files/six SQLite databases; infrastructure backup:40 files;
  encrypted/hash-verified. Paid subscriptions/events0/0; signed catalog sequence3 unchanged.

These are server-side ordinary results, not full supporting-role/MESH or owner acceptance.
No normal-client endpoint or RU production route has been switched.

## Restricted renewal blocker and safe rollback

At20:14UTC, non-mutating evaluation of the retained exact renewal package reported
`RENEWAL_REQUIRED`: no file changes, remote writes or restarts. Actual forced-command
RPC inspection already passed through the new host's pinned SSH route. The owner-paid
identity was not used. The renewal timer was paused to exclude overlapping runs.

One manual accepted renewal transaction started20:21UTC, using a private controller
configuration pointing to new NL, without changing the production controller route.
Fresh candidate profile validation reached the canonical promotion boundary, where
`DirectoryPort.read(candidate, now)` rejected the still-expired publisher directory.
The exact maintenance gate reports `DIRECTORY_INVALID`; no binary, validator or
accepted package was patched. Independent20:29UTC readback confirms directory expiry
at29.10 13:04:25UTC; its historical signature/binding validates, its current validity does
not. Original certificate/CRL are also expired; CRL/floor remain aligned at27224.

The accepted recovery logic rolled profile state back on both nodes. Actual RU and NL
readbacks return `PREVIOUS_SNAPSHOT_RESTORED`. Reader resumption is blocked by the expired
previous materials, so the coordinator retains `RECOVERY_REQUIRED`, first cause
`DIRECTORY_INVALID`, `commit_decided=false`. Preserve this journal and staged evidence;
do not rerun renewal, erase the transaction, relax validation or create a new trust anchor.
The legacy credential-only publication helper is not an accepted canonical-directory
recovery path; the expired-apply route reaches the same promotion gate.

After both rollback readbacks, only the pre-existing RU ordinary HTTP service was
restarted with its unchanged accepted artifact.20:26UTC loopback dispatch and20:34UTC
external trusted HTTPS return the expected JSON400 for malformed requests. This verifies
API availability, not an authenticated client/VPN smoke. Automatic renewal remains paused;
restricted sync timers remain quiesced. New restricted gateway was never started and
has0 restarts. The manual controller is no longer running. Renewal failure records and
state from both nodes were encrypted, hash-verified and read back privately.

Final20:34UTC safety checks: eight old product units remain inactive with persistent
guards; old interfaces/listeners absent and external TCP checks negative. New ordinary
AWG/TCP remain active, no catalog cutover; paid subscriptions/events freshly0/0 and catalog
sequence3 unchanged. No paid-canary, subscription event or Android stage0 activity.

## Source-only cutover preparation

Endpoint routing preparation is committed as a **NOT_DEPLOYED source checkpoint**:
ordinary NL registration uses the same operator-owned catalog envelope returned to the
client, chat synchronization uses its configured node, mailbox acknowledgement uses the
identity-bound bootstrap, and monitoring accepts a configured remote host. Strict SSH
pinning is preserved; RU registration remains local. No endpoint/private configuration,
monitoring inventory, signing key, APK or production HTTP artifact was switched.

Focused routing, monitoring, HTTP-runtime and chat tests:43 PASS,14 optional skips.
Skipped tests require the configured native Nginx matrix or pinned synchronization
artifact; this is not a complete HTTP deployment gate. Two local HTTP builds are
byte-identical:47368bytes, SHA256
`44a6b50f1a1ce00fd74f53e0d35c5937c6b5f5c2a561fc94b7a0150f39149204`.
This candidate does not supersede any retained accepted artifact. The unchanged active
RU HTTP package is47091bytes, SHA256
`dcd769986a1da7cb1662c0f73d18a88e9f73485a977db937ca5b1428c1fd1029`.

## Acceptance and publication gates

### Authorized host preparation continuation

- Owner authorized required installation; continuation entry main
  `6ed27282b582d0600208cdb31d32e245e0ee99f8` was fetched and remote-verified.
- New-host SSH/access, package-source, network and boot configuration were backed up
  encrypted before management writes; authenticated decryption readback PASS.
- Official Jammy security updates and base diagnostic/upgrade packages installed.
  Root/password access was not disabled. No public product listener was introduced.
- Hostname identifies replacement NL. Bounded SSH fail2ban configured; journald limits
  200MiB persistent/32MiB runtime/14days. Existing approximately1GiB swap partition is
  retained; an additional1GiB mode0600 file is enabled persistently, total about2GiB.
  Swappiness10; no gateway service memory cap was guessed before exact restoration.
- Package `needrestart` restarted the preparation runner once during its first pass.
  Readback reconciled the running job rather than starting a duplicate. Base installation
  subsequently completed; upgrade runners are now excluded from automatic needrestart.
- A local boot-test fixture initially expected ext4 as a module; the installed kernel
  builds ext4 in. The corrected gate accepts the exact kernel configuration or initrd
  module, not an absent filesystem driver. GRUB, initrd/virtio/root-filesystem, dpkg and
  SSH checks passed before reboot. No product service was involved in either recovery.
- One controlled security-update reboot returned successfully with unchanged trusted
  SSH host key and key login: Ubuntu22.04.5 LTS, kernel5.15.0-202-generic.
- The supported22.04→24.04.5 operation completed, followed by a guarded reboot to
  kernel6.8.0-147-generic. The upgrade left the resolver disabled; enabling the already
  installed system resolver restored DNS and the official26.04.1 upgrade offer. This
  ordinary configuration error was corrected without changing provider networking.
- Read-only inspection of53 retained runtime ELF files also identifiesGLIBC2.42 and
  OpenSSL3.3/3.4 version requirements in the accepted extension set. Ubuntu24.04 alone
  is therefore not the final runtime baseline. The official24.04→26.04.1 upgrade also
  completed successfully, then rebooted to7.0.0-42-generic. No CPython rebuild or libc
  transplant. Temporary SSH restart windows recovered; no host-key bypass or reset.
- Ubuntu26.04 automatically reserved320MiB for crash capture despite the existing
  disabled crash-dump policy. A guarded boot-configuration override removed that
  reservation; the fourth reboot restored1960380KiB usable RAM. Kernel reservation
  readback is0; persistent swap remains about2GiB, unused in the sample.
- Exact accepted interpreter SHA256
  `52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41`
  matches the installed CPython3.14.4. Isolated retained-runtime qualification1795
  files PASS: cryptography46.0.7, rns1.5.1, pyserial3.5, snapshot package import,
  exact gateway help and Xray version execution. No identity/configuration was installed
  with this runtime probe; it is not actual snapshot-account or data-plane acceptance.
- Old NL deployment contract was additionally collected read-only:88 metadata records,
  six units and11 network/runtime sections; source/configuration bodies encrypted and
  verified locally. This remains a partial private matrix, not a consistent full backup.

Historical pre-activation host readback19:11:14UTC: NTP synchronized, cloud-init done, TUN accessible,
no failed units, no pending reboot or reported package upgrades, strict pinned root SSH
PASS. Fail2ban/resolver/time synchronization active with0 restarts in this sample.
Only public SSH22 and loopback DNS listeners remain. Root/password login was not disabled;
provider-console recovery remains unverified. No broad firewall flush was performed.

Diagnostic ingress19:06:45UTC PASS from both workstation and RU: TCP443/4242/4243 and
UDP443/51820/51823. Paired bounded capture confirms a RU-origin SYN at the new interface.
All12 nonce echo checks passed; temporary diagnostic listeners closed. No product
identity was used. Provider-path reachability is demonstrated, not VPN/TLS/mesh operation.

### Historical new-host entry preflight

Observed18:08:03UTC, successful root public-key login. Ubuntu22.04.1 LTS, kernel
`5.15.0-46-generic`, x86_64, KVM,2 CPUs;1973984KiB total RAM (about1.88GiB).
50GiB virtual disk; root ext4 about9% used. Existing swap partition1048551424bytes,
unused in the sample; no additional swap was created or persistent policy changed.
TUN character device exists and is readable/writable. NTP synchronized, cloud-init done,
no failed units, no reboot-required marker. Only TCP22 is listening on IPv4/IPv6.
iptables uses the nftables backend. Numerous package updates are pending; no package
installation, security update, reboot or firewall change was made before the OS gate.
Provider firewall/console recovery is not independently confirmed.

Compatibility readback18:09:50UTC: old NL uses Ubuntu26.04, CPython3.14.4 and glibc2.43.
Its accepted interpreter ELF version-needs entries explicitly require `GLIBC_2.38`.
New NL has Python3.10.4 and glibc2.35; no CPython3.14 package candidate was identified
in its configured Jammy package metadata. `postgresql-plpython3-14` is a PostgreSQL
extension, **not** CPython3.14. The source guards in
[`build_profile_snapshot_launcher.py`](../../scripts/build_profile_snapshot_launcher.py)
require CPython3.14 for both executable qualification and the isolated pinned venv.
The retained gateway itself requires at most GLIBC2.34, so this finding must not be
misreported as gateway-binary corruption or a failure of all five accepted packages.

| Gate | Current result |
| --- | --- |
| New-host SSH identity/login | Owner-interactive TOFU, pin matched, key login PASS; no provider verification |
| New-host OS/runtime | Ubuntu26.04.1/kernel7.0.0-42; exact interpreter and retained runtime import/execution PASS |
| Architecture/TUN/NTP | x86_64/TUN/NTP PASS; ordinary data-plane acceptance separately recorded |
| Provider constraints/recovery console | Required diagnostic ports reachable from RU/workstation; console NOT_VERIFIED |
| Base preparation, updates/reboot, swap and SSH recovery | Four guarded reboots, final OS/swap/strict SSH PASS; console still unavailable |
| Private deployment matrix/identity staging |13 roles derived; inactive staging and final coordinated mutable export complete |
| Old-NL fencing | FENCED; eight product units disabled, interfaces/listeners absent, persistent guards |
| New AWG handshake, DNS, HTTPS and cleanup | PASS synthetic; egress185.10.158.212, IPv6 fail-closed |
| New TCP authentication, tunneled HTTPS and cleanup | PASS synthetic; egress185.10.158.212 |
| Canonical profile, fresh certificate/CRL/floor/directory | BLOCKED_DIRECTORY_INVALID; previous snapshot restored, expired material not accepted |
| Actual snapshot SSH, renewal preflight/timer and restricted data plane | RPC inspect PASS; snapshot rejects expiry; renewal RECOVERY_REQUIRED/timer paused; restricted inactive |
| Supporting roles and accepted firewall/NAT/sysctl restoration | Services started; scoped networking verified; supporting data plane pending |
| RU-origin packet arrival | Diagnostic ports/SYN PASS; product data plane NOT_RUN |
| Multi-sample stability and monitoring cutover | Three ordinary/supporting samples PASS; inventory cutover pending |
| Fresh RU backup, ledger and configuration prepublication checks | Backups PASS, ledger0/0; recheck before publication |
| New signed catalog sequence and restricted publication | NOT_PUBLISHED; no sequence allocated |
| Android106 endpoint fetch and owner AWG/TCP/Auto-MESH smoke | NOT_RUN |

RU renewal attempted canonical mutation and rolled back; ordinary HTTP availability was
restored afterwards. The signed catalog and production endpoint configuration were not
switched. Paid ledger0/0 is freshly queried at final readback. Monitoring inventory remains
unchanged; unavailable old registry data must not be reported as zero.
No new NL readiness, rollout or full-success claim is made.

## Resume and rollback

Host preparation, private matrix, final coordinated export, fencing and ordinary synthetic
acceptance are complete. STOP on the signed-material validation blocker, not an ordinary
installation error. The exact remaining action is to qualify an accepted recovery path
that refreshes the expired publisher directory before canonical profile promotion,
while preserving authority, the shared transaction lock and the pending recovery journal.
Only then complete restricted renewal/supporting gates before publication.
No disk reinstallation was performed; SSH host keys and root access remain intact.
The preferred24.04 baseline does not meet the full retained extension ABI requirements,
so26.04 is the verified final baseline.
Do not bypass the3.14 guard, replace system libc independently or silently rebuild
accepted runtime bytes. Reverify host identity without replacing the known-host entry.
Continue only after that localized blocker is resolved, with fresh restoration guards.
Reverify old-node fencing before any further identity activation.
Do not regenerate a recoverable identity, trust anchor or client credentials.

Prepare and restore the exact accepted contract, renew expired restricted materials via
the existing authority/renewal/publisher routes, and pass synthetic data-plane, RU-origin
connectivity, actual snapshot/renewal and stability gates before publication. Then take a
fresh RU backup and verify ledger0/0, paused canary and fencing; publish one monotonic
signed NL control-plane update. Verify Android106 without an APK change before asking
for the owner's AWG smoke, then TCP, then Auto/MESH. Canary stays paused throughout.

Rollback now: **PREVIOUS_SNAPSHOTS_RESTORED_RU_ORDINARY_AVAILABLE_RECOVERY_REQUIRED**.
No catalog rollback is required; new NL remains unpublished and old NL remains fenced.
Do not mistake profile rollback for successful restricted-service recovery. Ordinary/supporting services
and forced SSH routes are active on new NL; old NL must remain inactive. Stop the affected
new service if an identity conflict appears. Do not return traffic to old NL. Encrypted pre-upgrade configuration is
retained, but it is not a full disk image or a promise of automatic OS downgrade.
Old NL must remain fenced. New ordinary/supporting identities are active only on the new host.
Before publication, a failed replacement stays unpublished and RU ordinary service is preserved. After a
failed publication, use the supported catalog mechanism to stop NL admission/return to
RU; do not reactivate old NL without independent full acceptance. Never serve one copied
identity on both hosts. Preserve all old files as recovery evidence.

## Verification scope

Sanitized source/documentation checkpoint: strict JSON, targeted privacy/secret scan,
changed local Markdown links, exact11-file staged scope and whitespace checks PASS.
Unrelated changes remain outside the index; original document suffixes are preserved.
Focused tests and two deterministic HTTP package builds are recorded above. No platform
build or historical full test suite was run; none substitutes for unperformed production
and client gates. This is an incomplete restoration checkpoint, not a release.

[Sanitized JSON receipt](2026-10-30-nl-gateway-replacement.json) ·
[Accepted canonical receipt](2026-10-28-android106-beta-0-canary-canonical-profile.json) ·
[Retained incident](2026-10-27-android106-beta-0-canary-1.md) ·
[Backup contract](../server-secret-backup.ru.md).
