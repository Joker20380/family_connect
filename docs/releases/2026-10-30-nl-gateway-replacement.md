# NL production gateway replacement — 30 October 2026

## Status and authorization

**NL-REPLACEMENT-20261030 / HOST_BASELINE_VERIFIED_RESTORE_PENDING.** After the initial
blocked audit, the owner authorized installing the required OS/packages over SSH.
Supported LTS upgrades and exact-runtime compatibility checks are complete, not a
provider disk reinstallation or product deployment. Final OS: Ubuntu26.04.1 LTS,
kernel7.0.0-42-generic. Product restore/acceptance remain pending.
No product identity, old-node fencing, catalog publication or client smoke yet.

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
  this documentation change. No branch switch, reset or history rewrite.
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

Final host readback19:11:14UTC: NTP synchronized, cloud-init done, TUN accessible,
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
| Architecture/TUN/NTP | Read-only x86_64/TUN/NTP PASS; no data-plane test |
| Provider constraints/recovery console | Required diagnostic ports reachable from RU/workstation; console NOT_VERIFIED |
| Base preparation, updates/reboot, swap and SSH recovery | Four guarded reboots, final OS/swap/strict SSH PASS; console still unavailable |
| Full private matrix/current identity coverage | INCOMPLETE |
| Old-NL fencing | NOT_RUN; ordinary/support services still active |
| New AWG handshake, DNS, HTTPS and cleanup | NOT_RUN |
| New TCP authentication, tunneled HTTPS and cleanup | NOT_RUN |
| Canonical profile, fresh certificate/CRL/floor/directory | NOT_RUN; expired old material not accepted |
| Actual snapshot SSH, renewal preflight/timer and restricted data plane | NOT_RUN |
| Supporting roles and accepted firewall/NAT/sysctl restoration | NOT_RUN |
| RU-origin packet arrival | Diagnostic ports/SYN PASS; product data plane NOT_RUN |
| Multi-sample stability and monitoring cutover | NOT_RUN |
| Fresh RU backup, ledger and configuration prepublication checks | NOT_RUN |
| New signed catalog sequence and restricted publication | NOT_PUBLISHED; no sequence allocated |
| Android106 endpoint fetch and owner AWG/TCP/Auto-MESH smoke | NOT_RUN |

RU production configuration and the existing catalog were not changed. Paid ledger0/0
is the last accepted incident observation, **not a fresh query in this audit**. Monitoring
inventory remains unchanged; unavailable old registry data must not be reported as zero.
No new NL readiness, rollout or full-success claim is made.

## Resume and rollback

Host preparation is complete. Finish the private restoration matrix and inactive
staging; no normal-client publication is authorized before the remaining acceptance gates.
No disk reinstallation was performed; SSH host keys and root access remain intact.
The preferred24.04 baseline does not meet the full retained extension ABI requirements,
so26.04 is the verified final baseline.
Do not bypass the3.14 guard, replace system libc independently or silently rebuild
accepted runtime bytes. Reverify host identity without replacing the known-host entry.
Continue in the same task with complete private identity/configuration coverage and
fresh restoration guards. Prove old-node fencing before activating copied identities.
Do not regenerate a recoverable identity, trust anchor or client credentials.

Prepare and restore the exact accepted contract, renew expired restricted materials via
the existing authority/renewal/publisher routes, and pass synthetic data-plane, RU-origin
connectivity, actual snapshot/renewal and stability gates before publication. Then take a
fresh RU backup and verify ledger0/0, paused canary and fencing; publish one monotonic
signed NL control-plane update. Verify Android106 without an APK change before asking
for the owner's AWG smoke, then TCP, then Auto/MESH. Canary stays paused throughout.

Rollback now: **NOT_NEEDED_NO_PUBLICATION**. No product endpoint, service or identity
was changed. New-host management changes now include SSH setup and authorized base/OS
preparation; these are not a product rollout. Encrypted pre-upgrade configuration is
retained, but it is not a full disk image or a promise of automatic OS downgrade.
Do not fence the still-serving old ordinary services merely to close this
blocked audit; fencing remains mandatory before replacement identity activation.
Before publication, a failed replacement stays unpublished and RU unchanged. After a
failed publication, use the supported catalog mechanism to stop NL admission/return to
RU; do not reactivate old NL without independent full acceptance. Never serve one copied
identity on both hosts. Preserve all old files as recovery evidence.

## Verification scope

Sanitized documentation checkpoint: strict JSON, targeted privacy/secret scan,10 changed
local Markdown links, exact five-document staged scope and whitespace checks PASS.
Unrelated changes remain outside the index; original document suffixes are preserved.
No platform build or historical full test suite was run; none substitutes for the
unperformed production/data-plane gates. This is a source audit checkpoint, not a release.

[Sanitized JSON receipt](2026-10-30-nl-gateway-replacement.json) ·
[Accepted canonical receipt](2026-10-28-android106-beta-0-canary-canonical-profile.json) ·
[Retained incident](2026-10-27-android106-beta-0-canary-1.md) ·
[Backup contract](../server-secret-backup.ru.md).
