# NL production gateway replacement — 30 October 2026

## Current result — terminal rollback and renewal complete, client cutover held

Observed 2026-10-30T23:10:37+00:00. Same existing operation; no new product checkpoint.

**NL-REPLACEMENT-20261030 / BLOCKED_NL_REPLACEMENT / RESTRICTED_TEST_IDENTITY_UNAVAILABLE.**
The historical rollback is terminal **ABORTED / ROLLED_BACK_READERS_STOPPED** with
`first_cause=DIRECTORY_INVALID` and separate `terminal_reason=PREVIOUS_LEAF_EXPIRED`.
Two device and two invite additions are preserved; historical expected hashes and restricted
state remain exact under the dedicated overlay contract. Both complete archives/ledgers
PASS, old active owners removed. No old database restoration or expired reader resume.

The bounded publisher recovery created one fresh room (READY PASS), staged and published
one directory through the accepted atomic store. Strict production directory/DirectoryPort
validation PASS. One fresh renewal operation is now **COMMITTED**, CRL/floor **27225/27225**,
current profile/certificate/CRL and synchronized RU/NL directory. Its initial
`NEW_DIRECTORY_NOT_READY` was resolved by the authorized normal gateway start and explicit
committed recovery of the same operation; no additional transaction or manual journal edits.
Actual RU→new-NL forced-command snapshot exits0 with empty stderr; strict schema/signatures
and non-mutating renewal NOOP PASS. Normal publisher produced its own fresh generation.

Remaining real acceptance blocker: no permitted production-bound synthetic MESH identity
was found.98 scoped disposable profiles use independent trust, and four previously recorded
custody locations remain absent. This is not an exhaustive claim about all database users.
No owner/tester identity was substituted, no new client key/identity/grant was generated.
MESH registration/DNS/HTTPS/egress therefore remain NOT_RUN; no catalog publication or
Android106/owner smoke. An existing authorized synthetic identity is required to continue;
creating one would require an explicit exception to the owner's no-new-identities rule.

Safe hold: old NL FENCED; new185.10.158.212 AWG/TCP remain active with accepted synthetic
data-plane evidence. Restricted gateway passed three stable samples/zero restarts, then
was stopped because data-plane acceptance is incomplete. Its integrated publisher is also
stopped; recovery entrypoint disabled and archived. Renewal/read-only sync definitions now
use the accepted package and pinned new-host route; actual read-only sync PASS, timers stay
paused at the acceptance gate. RU ordinary HTTP/public trusted HTTPS healthy, catalog3
unchanged, paid ledger0/0. Current leaf/CRL expire2026-10-31T02:47:21Z: revalidate freshness
before continuation and never start expired readers. **BETA-0-CANARY-1 stays PAUSED;
paid-canary, subscription events and Android stage0 stay off.**

### Source, artifacts and verification

- Registry-overlay source: `e822b391a43dd4cec5949df7a8a33ba6e44872a5`, pushed/remote verified;
  deployed renewal package SHA256 `2624c1ba1f49863f767ca9e9ea165a5c74c0c4f95a5ba84d2cac1d91d81d5dd1`,66287bytes.
 231 focused tests PASS/one optional native interoperability skip; source/member manifests,
  two identical builds,13 imports/four help commands and canonical-route construction PASS.
- Publisher recovery source: `a11eb8f2614ed7dff85522c437c54862daedaf74`, pushed/remote verified;
  package SHA256 `7904fc9e457f74c414e85ac665622a49c9cf5c353affffee1fca301cea59024c`,8700919bytes/4members.
  Helper binary SHA256 `f44ace11d7013cdf2908e888a5ed6175a936970ab9c9195ddf9846d77f587995`,16342590bytes;
  source inventory SHA256 `526a5a9884e115cd78bc7d414cd241f4b876bafdccec933d8c53f628eb47c0e6`.
  The retained282-member source capsule is exact; seven narrowly projected/added members.
  Two byte-identical builds, manifest/member metadata/hashes, help and privacy scan PASS.
  Gateway binary remains exact `f8ff517804c8cc425b172c821630274ce39ccfa9a3e79328db3e8a626f45ebef`.
- Publisher tests:113 current-tree and119 exact-capsule Go tests PASS;181 focused Python
  directory/sync/profile-store tests PASS,29 optional integration prerequisites skipped;
  two bounded source-projection tests PASS. No Android/desktop/full historical suite.
- Fresh authenticated encrypted backups/readback PASS for controller/node journals,
  SQLite/schema/integrity, profile/Locator, publisher metadata/configuration and final routes.
  Protected private records retain full provenance; no material contents enter this report.

### Publisher and fresh renewal result

Recovery directory: old SHA256 `e0c1674381f910b6133d9ce295a01784f47487a437a3ad993e1e3be57a4ba53c`;
fresh SHA256 `101524bb996a39716bde2a9fef2c6c32e94675e7a81c13ec5f3eff560b8f7a90`.
Issued `2026-10-30T22:40:46.140928387Z`, expires `2026-10-31T02:40:46.140928387Z`.
Exactly one recovery room creation and one recovery live promotion; real room READY PASS,
staging left live bytes unchanged, publisher contract/parent/ownership/mode preserved.
Profile/CRL/floor unchanged by this worker. Normal runtime then generated a separate directory:
SHA256 `31ce04ac75168db1119bc299bd8bd4736c79232ae1fa799d448ac18edfa0f77a`, issued `2026-10-30T22:52:38.661449239Z`,
expires `2026-10-31T02:52:36.127149321Z`. This is normal publisher startup, not a second
recovery publication. RU/NL copies are equal through the accepted renewal/read-only sync path.

Historical operation safe label `HISTORICAL_NL_REPLACEMENT_ROLLBACK` remains ABORTED;
original cause and complete archives are retained. Fresh operation safe label
`FRESH_NL_RENEWAL_1` is COMMITTED, with both cleanup ledgers and no active owners.
Its first cause `NEW_DIRECTORY_NOT_READY` is preserved: the original service snapshot was
inactive, so normal resume did not start the publisher. After strict current candidate and
two-node commit reconciliation, one authorized gateway start generated a fresh directory;
explicit committed recovery finished that same transaction. No commit-decision reversal.
The historical terminalization HTTP outage was122.44s. The separate fresh-renewal maintenance
outage was387.23s; RU HTTP is restored with original exact artifact/argv.

Actual forced-account SSH snapshot: exit0, stderr empty, schema/signatures/current certificate
and CRL/floor PASS. Non-mutating renewal evaluation NOOP. The ordinary registry additions and
all pre-renewal device/invite rows remain present. Paid subscriptions/events0/0.
Schedule definitions/source pins/new-NL route aligned, but timers not resumed. A bounded
read-only directory sync service run PASS. Its initial protected-home known-hosts path issue
was corrected by copying the exact already-pinned host entry into the root-controlled runtime
boundary; StrictHostKeyChecking and systemd ProtectHome remain enabled. No trust relaxation.

### Acceptance hold and remaining work

One restricted gateway start, three stable PID/memory samples,0 restarts/OOM/storage errors,
current profile and healthy directory were observed. These are not MESH data-plane acceptance.
No allowed production-bound synthetic credential was located in scoped retained material;
independent-trust fixtures are not a substitute. No owner/tester private identity was used.
Restricted was stopped once for safe pre-publication hold; normal publisher stops with it.
The one-shot recovery permit is archived/disabled. Ordinary AWG/TCP and load monitoring stay
active. Old NL remains persistently fenced; unavailable old-node metrics are not zero users.

Catalog sequence3 and RU configuration remain unchanged; endpoint-routing source is still
NOT_DEPLOYED, normal client publication/Android106/owner smoke NOT_RUN. Full NL acceptance
and READY_FOR_OWNER_NL_SMOKE are not claimed. Continue only after resolving the synthetic
identity prerequisite and revalidating material freshness; then actual MESH data-plane,
normal schedules, monotonic client publication and owner smoke. No new checkpoint is needed.
Rollback status: PRE_PUBLICATION_SAFE_HOLD; no old-NL reactivation, no database restoration,
no identity conflict, no temporary write credential and no pending renewal operation.

## Earlier observations — superseded by the current result

## Confirmed terminal rollback and publisher continuation

The existing rollback is now terminal **ABORTED / ROLLED_BACK_READERS_STOPPED**.
Source `e822b391a43dd4cec5949df7a8a33ba6e44872a5` and its deterministic renewal package
were deployed through the recovery-only bridge. Fresh quiesced proof preserved two device
and two invite additions, all historical rows and exact restricted tables. Historical
expected hashes and `first_cause=DIRECTORY_INVALID` are unchanged; terminal reason is
`PREVIOUS_LEAF_EXPIRED`, with no commit decision or expired reader resume. Both node owners
were released only after complete archive and `CLEANED_FENCED_ROLLBACK` ledger verification.
The single RU HTTP stop/start lasted122.44s; ordinary HTTP/public trusted HTTPS are restored
with the original artifact/argv and all registrations retained. Paid ledger remains0/0.

Next within **NL-REPLACEMENT-20261030**: bounded publisher recovery, one fresh renewal,
actual restricted/snapshot/MESH acceptance, schedules and monotonic client publication.
The integrated publisher has no one-shot command and rejects the expired predecessor before
room creation. A narrowly scoped fixed-configuration recovery worker is therefore qualified
from the exact retained publisher source; no gateway binary rebuild or validator weakening.
It checks historical signatures/binding and the exact publisher contract, journals one room
attempt, verifies READY, stages privately and uses the existing locked atomic store.
It never writes profile/CRL/floor and never starts expired readers. Recovery is unavailable
once its fixed permit expires or normal current material is restored.

New NL185.10.158.212 ordinary AWG/TCP server data-plane remains accepted; old NL is FENCED.
Restricted gateway inactive, renewal paused, stale directory retained. No room generation,
directory publication, fresh renewal, client catalog change or owner smoke yet. Catalog3.
**BETA-0-CANARY-1 remains PAUSED; paid events and Android stage0 remain off.**

Renewal package SHA256 `2624c1ba1f49863f767ca9e9ea165a5c74c0c4f95a5ba84d2cac1d91d81d5dd1`,
66287bytes/17members; two byte-identical builds, exact source/member inventory,13 imports,
four help commands and canonical-route construction PASS.231 focused Python tests PASS,
one optional native interoperability skip. Fresh authenticated encrypted backups/readback
PASS before deployment, during writer quiescence and after terminalization.
Historical rollback is labeled `HISTORICAL_NL_REPLACEMENT_ROLLBACK`; its private ID and
complete controller/node journals are retained privately, not published. The controller
transaction remains available as ABORTED; no database/profile/directory writes occurred.

Publisher recovery source qualification is separate from production execution. The exact
282-member retained capsule is verified; only the atomic-store extraction and six bounded
recovery source/test members are projected. Normal publisher logic is unchanged.
Focused publisher checks:113 current-tree and119 exact-capsule Go tests PASS;
181 directory/sync/profile-store Python tests PASS,29 optional integration prerequisites
skipped; two bounded source-projection tests PASS. No Android/client/full-history suites.
Production helper deployment, fresh room/publication and fresh renewal are pending.

## Historical source qualification and blocker evidence — superseded

The following entries describe earlier states, not the current operation gate.

## Append-only registry correction — same operation

The owner authorized retaining strictly proven device/invite additions without rewriting
the historical database snapshot or any expected-state hash. The new narrow RU
`rollback-registry-overlay` RPC validates schema, integrity, foreign keys, unique identities,
application bindings, unchanged historical rows and exact restricted security tables.
Only safe hashes/counts enter its immutable private receipt. Later drift is rejected.
Normal previous-readback, rollback and grant application retain exact-state comparisons.

Explicit fenced recovery binds the historical and live database hashes and overlay receipt,
archives the complete evidence and returns `ROLLED_BACK_READERS_STOPPED` with controller
state `ABORTED`. It preserves `first_cause=DIRECTORY_INVALID`, never writes the database,
never publishes a directory and never resumes expired readers. A recovery-only source
bridge verifies both retained and replacement source inventories without changing the fixed
node configuration included in historical state. Ordinary/scheduled entrypoints cannot use
the overlay. Production deployment and recovery execution are not yet performed.

Focused qualification:231 tests PASS, one optional native interoperability probe skipped.
This includes overlay rejection/replay, cleanup fault injection, explicit CLI gates,
unchanged ordinary recovery, package inventory and canonical-route construction with
both retained/current source tamper rejection. No unrelated client/build suite was run.

The retained authenticated encrypted SQLite backup and live accepted schema match for all
five projected tables. Read-only entry audit reconfirms two device and two invite additions,
no removals, exact restricted tables, unchanged coordinator journal, NL exact rollback and
RU ordinary HTTP active. Counts are observations, not hard-coded acceptance requirements.
Next: qualify the deterministic renewal-only package, fresh backup/quiescence, terminalize
the existing operation, restore ordinary HTTP, then continue publisher/fresh renewal and
cutover. The earlier blocker evidence below remains historical, not a new operation.

## Status and authorization

**NL-REPLACEMENT-20261030 / BLOCKED_NL_REPLACEMENT / BLOCKED_RENEWAL_JOURNAL_UNRESOLVED.**
The owner-authorized fenced-rollback source correction is qualified but **NOT_DEPLOYED**.
Fresh read-only verification supersedes the earlier two-node rollback PASS: RU now returns
`ROLLBACK_READBACK_MISMATCH`; NL still returns `PREVIOUS_SNAPSHOT_RESTORED`.
Only RU `database_sha256` differs from its recorded expected state. Relative to the
rollback snapshot, the current registry contains two additional device rows and two
additional invite rows, with no removed rows. Restricted grants, certificates and CRL
sequence rows are unchanged. The recorded previous database hash is internally consistent.
The RU ordinary HTTP reader is active and belongs to the renewal barrier; therefore the
claim that both barriers are stopped is also no longer true. No records were deleted,
expected hashes rewritten or services stopped to manufacture an exact rollback proof.
The existing journal remains `RECOVERY_REQUIRED`, `first_cause=DIRECTORY_INVALID`,
`commit_decided=false`. Recovery execution and package deployment are **NOT_RUN**.
This is a genuine live-state conflict, not another leaf-validation exception.
Restricted services remain inactive/quiesced and renewal is paused. Old NL is FENCED.
New ordinary AWG/TCP synthetic data-plane and cleanup PASS, but no client publication,
Android106 endpoint verification or owner smoke. This is not full server acceptance.

## Fenced rollback correction — source only

Entry local/remote main: `c6e1f725a638c0a3f416712ffeed3b381d0067cd`.
This continues the same operation; no new PLAN ID or product checkpoint.

- The controller distinguishes verified rollback, current-valid predecessor and resumed
  readers. Only the exact `LEAF_EXPIRED_OR_FUTURE` exception, with a historically valid
  and demonstrably expired leaf, permits fenced finalization. Future material and other
  validation failures remain fail-closed. Normal valid rollback, committed recovery and
  expired-authority rollforward retain their existing paths.
- The new `finalize-fenced-rollback` RPC binds the existing operation, expected state and
  controller recovery evidence. It requires stopped barriers, exact readbacks and no start
  intent, reconciliation or directory publication. It writes only a private terminal receipt
  and node owner state `ABORTED_FENCED`; it never restores material or resumes readers.
- Cleanup archives the complete node journal, terminal receipt and owner/first-cause
  evidence, then durably records `CLEANED_FENCED_ROLLBACK` before releasing ownership.
  Replay verifies the archive and stopped barrier. Partial finalization/cleanup is resumable
  without a second rollback or reader start.
- The controller remains available as `ABORTED`, with external result
  `ROLLED_BACK_READERS_STOPPED`, `rollback_verified=true`,
  `previous_material_current=false`, `readers_resumed=false`, `readers_state=STOPPED`,
  `terminal_reason=PREVIOUS_LEAF_EXPIRED`, and no commit decision. Original `first_cause`
  is retained; the terminal receipt also exposes the same value as `first_reason`.
  Only explicit recover CLI actions accept this result as successful command completion.
- These are **tested source semantics, not production terminalization results**. The
  historical rollback operation is referenced only by the safe label
  `replacement-initial-renewal`; its private operation ID and journals are not published.

Focused qualification: **168 passed,1 skipped** across fenced rollback, activated
maintenance, renewal transport, deterministic renewal packaging and canonical profile
store tests. The skip is the optional accepted-native-source/toolchain interoperability
probe; no gateway or client build was requested or performed. Fault coverage includes
terminal-receipt/owner interruption, partial archive moves, archive fsync and completed
ledger interruption, idempotent replay and fresh-operation exclusion until both cleanups.
Ordinary test-harness issues (missing Git, explicit synthetic unit argument and CLI umask
isolation) were corrected before the successful run. No production workaround was used.

Source checkpoint `dfbfbc34cc3345e281294ff429555d9b95a35f91` was pushed and remote SHA
verified before packaging. Only the credential-renewal/controller-node package was rebuilt:
two byte-identical builds,62716 bytes,17 members. Package SHA256:
`349018be0015b03743cd9164f287589b79e46f60d405da26712a7d9b71e61e0d`.
Exact13-module inventory SHA256:
`7d5012cb0ff7b811f4d33ad42cb4da5e74ae6ce1d1be00a9a38a0c34a9025cf1`.
Manifest SHA256:
`edc26e30c88edaf8fabf2d7c69d9e869374b1f0e7238374d4f8394005c9436c4`.
Six changed modules match the source commit; archive/API member hashes and privacy scan
PASS. The actual package passes13 module imports, four CLI help commands and one isolated
canonical-route construction test using its pinned API. Import/help runtime: Python3.13.15;
this is local qualification, not a production CPython3.14.4 deployment claim.
The prior accepted renewal artifact remains deployed and is **not superseded** operationally.
AWG, TCP, gateway binary, Android, snapshot and maintenance artifacts were not rebuilt.

Fresh21:18–21:21UTC read-only evidence confirms the database-only conflict and retains
authenticated encrypted evidence. At21:22UTC the old node remains fenced with eight
product units stopped/disabled and no product interfaces/listeners. New AWG/TCP remain
active; restricted remains inactive, with expired directory still correctly rejected.
Paid ledger0/0 and catalog sequence3 remain unchanged. No publisher room, directory
publication, new renewal operation, service start, client cutover or owner smoke occurred.
Final21:29UTC readback confirms the same conflict, byte-identical controller journal,
paid0/0, catalog3, paused renewal, fenced old NL and available RU public HTTPS. No new
production recovery command was sent; both node owners and all history remain retained.

**Next gate:** reconcile the live RU registry additions with the retained operation
without discarding records or weakening exact-state checks. Do not deploy or execute
recovery until both exact rollback readbacks and stopped-reader prerequisites are proven.
Only then may the authorized publisher/fresh-renewal/cutover sequence continue.

## Earlier host preparation provenance

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

### Read-only continuation: publisher and journal recovery gate

Fetched local/remote main both match `edadd7fe050147d05dc976af9530234a2b6896ff`.
Fresh actual RU/NL rollback readbacks confirm the accepted previous snapshots; coordinator
is still normal-mode `RECOVERY_REQUIRED`, `commit_decided=false`, first cause unchanged.
Journal files are hash-identical before/after the audit. The candidate is current-valid;
the predecessor passes historical validation only, not current validation.

Exact publisher audit PASS: effective executable is the retained canonical gateway
`f8ff517804c8cc425b172c821630274ce39ccfa9a3e79328db3e8a626f45ebef`, covered by Locator's
unchanged publisher contract. All282 retained source-member hashes validate against
manifest `27b54a9dd167c3b6af639bb03864f4d7d121c0e8b96c90eccb45a198c936f117`.
Provider configuration matches the exact fenced backup; no credential/API call was made.
The sole declared publisher is integrated into the stopped restricted gateway: duration4h,
seed rotation3h, systemd restart delay30s, not a separate publisher timer. No accepted
publisher process is running. The exact executable has no one-shot recovery command.
Publication uses the retained `Cache.Store` lock, exclusive sibling temporary file,
file fsync, rename and parent fsync. The source validates the current profile before
starting the seed publisher. Normal startup is not an expired-predecessor recovery path.

Current directory remains unchanged:
SHA256 `e0c1674381f910b6133d9ce295a01784f47487a437a3ad993e1e3be57a4ba53c`,
issued29.10 09:04:28.459218429UTC, expires29.10 13:04:25.250203756UTC.
Historical family/gateway binding PASS; current-time validation rejects expiry.
No new directory hash/generation exists. Room creation, room validation, directory
publication and restricted start are **NOT_RUN**, not failed attempts or acceptance PASS.

The deployed renewal controller source matches the repository exactly, SHA256
`d0ab545cc71d54d95600b10a03d3e501226c018a01d60a5ea4039f9003627bce`.
Its normal `recover()` path verifies rollback, then requires current-valid predecessor
credentials before restoring readers and reaching cleanup. Exact production validation
returns `LEAF_EXPIRED_OR_FUTURE`. An in-memory replay of the deployed method with all
writes and node RPCs replaced by simulation reaches `ROLLED_BACK` then `RECOVERY_REQUIRED`;
it never reaches directory reconciliation or terminal cleanup. These are simulated
states only: no production journal write, service fence/restart or recovery RPC occurred.
Normal `run()` always dispatches this unfinished operation back to recovery; it does not
resume the fresh candidate. The exact expired-recovery checkpoint check independently
rejects `OTHER_OPERATION_RECOVERY_REQUIRED`, because it requires a committed checkpoint.

This is **BLOCKED_RENEWAL_JOURNAL_UNRESOLVED**, not a publisher permission/package fixture
error. The allowed publisher-only source correction cannot change that controller gate.
Stop before creating a room or publishing a directory that cannot unblock promotion.
Required next authorization within the same operation: a bounded controller recovery
transition that makes verified rollback terminal while expired readers stay fenced,
preserving first cause, prior receipts and authority; no manual journal edit or validator
relaxation. No source was changed or production artifact rebuilt in this continuation.

Focused directory/profile-store/snapshot/restricted-sync checks:127 PASS,72 deselected
in an isolated root container with network disabled and read-only source/artifacts.
Two initial missing retained-fixture inputs were supplied and hash-verified, then the
entire same selection passed; no test was skipped to hide those fixture errors.
Final21:00UTC readback confirms old NL FENCED, RU ordinary HTTP available with trusted
public HTTPS dispatch, renewal paused, ledger0/0 and catalog sequence3. New ordinary
services remain active with0 restarts; restricted inactive, CRL/floor27224 unchanged.
No owner/canary identity, subscription/event, APK or client endpoint change.

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
acceptance are complete. STOP on the proven journal recovery gate, not an ordinary
installation error. First qualify an explicitly authorized bounded controller path to
terminal verified rollback without resuming expired readers or losing journal history.
Publisher recovery is already authorized, but is insufficient without that transition.
Then refresh the expired publisher directory before canonical profile promotion,
preserving authority and the shared lock; complete restricted/supporting gates before publication.
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

Current read-only continuation updates five existing documents only: strict JSON,
targeted privacy/secret scan, changed local Markdown links, staged scope and whitespace
checks PASS. No extra report or sanitized receipt file is created.
Unrelated changes remain outside the index; original document suffixes are preserved.
Current127 focused tests and the earlier two deterministic HTTP package builds are recorded above. No platform
build or historical full test suite was run; none substitutes for unperformed production
and client gates. This is an incomplete restoration checkpoint, not a release.

[Sanitized JSON receipt](2026-10-30-nl-gateway-replacement.json) ·
[Accepted canonical receipt](2026-10-28-android106-beta-0-canary-canonical-profile.json) ·
[Retained incident](2026-10-27-android106-beta-0-canary-1.md) ·
[Backup contract](../server-secret-backup.ru.md).
