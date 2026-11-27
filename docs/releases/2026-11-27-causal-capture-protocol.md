# HA-02 common capture preparation — 27 November2026

## OWNER finite maintenance source checkpoint — 19:45UTC

Chosen implementation: close actual admission/launch paths, cleanly finish whole writer domains,
then hold scoped native files and SQLite jointly with PG and the accepted stopped-support procedure.
[Concrete domain/path/late-effect matrix and remaining guarantee](../operators/owner-maintenance-boundary.md).
New source components are not installed. Accepted console/publisher images3af9fbf9/35158514,
7a91d127 twelve-file closures, manual b49c76c0, collector b7f4cbd2 and observer8b remain unchanged.

Native/local qualification:21 root private-namespace tests,3 actual PostgreSQL-image paired tests
(including host store UID10001),10 held-SQLite tests, zero skips. Mount unique IDs plus retained
kernel change notification reject both remount RW→RO and unmount/rebind; cgroup rewrite and unit
condition rewrite are terminal. Old-FD/prefaulted mmap, bind-alias views, detached child, late launch,
temp rename, non-exiting writer timeout, controller death/hang, lost release response and explicit
reconciliation are covered. PG operation UNKNOWN remains UNKNOWN through capture; projection expiry
is not refreshed. SQLite rollback/BEGIN between checks cannot become the old lease. Legacy custody
format is unchanged; the new pair receipt explicitly does not verify a stopped-support hash or
authorize fleet capture. Exact-source CI follows push; no pending run is reported as PASS.

Source6f942ec79d01dce707e91f7130b9b56480577106 pushed/remote-matched. Its first native workflow
46059047882 fails3 Docker-create setup cases; the other31 execute successfully,0 skipped.
Independent failed artifact15228355735 verifies ZIP SHA256
9181303300eafadb6feca94e06b8582eb6320c1c605a4df5865adc996295f214. The original fixture failed to
surface Docker stderr, so no exact daemon cause is claimed. The corrected fixture addresses the
manifest-vs-config image-ID ambiguity using `postgres@sha256:18cfe3ef…`, validates RepoDigests and
resolved container Image, and preserves bounded daemon diagnostics on failure. Product images are
unchanged. Fresh exact-source CI is mandatory; no blind rerun or skipped failing case.

Retained qualification failures: rename across mounts returned EXDEV rather than EROFS; systemctl
serialized Conditions as `[unprintable]`; separate busctl clients let an inactive unit unload.
The final implementation checks actual typed conditions over a single bounded sd-bus connection.
These are explained isolated test/observer failures, not erased production incidents. Ordinary
Gate.drain, historical UNKNOWNs and marker bytes are untouched. No product path was stopped/mounted
by the tests, only new disposable unit/cgroup/container and private namespace resources.

Fresh normal checks: authenticated panel five pages/logout19:33 PASS, monitor/probe natural
invocations a830938ddd704e0dba2ee18072a0a2ae / 962e315975834d6bbf9e8d7a32f550b2 finish0;
observer8b `ACCEPTED_SUPPORT_READ_ONLY_NORMAL`19:35, root bindings e7504de3cc6646e38fbf50a11cb5e5d0
and notifications fc30dddb7d514fc4b230bc6e997512d6 finish0. All four timers enabled/active/waiting.
No completed Resume.run used. NL1 authorized traffic19:39 fails partially after family authentication
and TLS verification (2/4HTTPS,0DNS); this failure is retained, not explained by SIGTERM/provider
blocking. Earlier wrapper attempts failed locally before traffic (nonexistent Python path, then
missing PYTHONPATH), independently of the actual traffic result. Bounded current readback continues.

Common held interval/new stopped-support snapshot/encrypted kit/independent verification/linked
resume remain NOT_PERFORMED. No production capture restriction was acquired; lab cleanup is not
normal resume. Concrete blocker: continuously controlled Docker executor launches and private mount
namespaces for console synthetic writes, plus stopped-support integration and named remote rows.
No broad Docker/OWNER maintenance was substituted. HA-02 independent custody/source-host-free restore,
panel reboot startup and onboarding remain open. Next: enroll that specific executor authority and
qualify old exec/detached/late starts under the same lease, not repeat a general census.

## Continuation from ff20b55c — selective existing-key activation

Follow-up reconciliation on corrected593ae4dd source cannot complete the native encrypted-vault
read: classified `HA_RECONCILE_NATIVE_READ_REFUSED`. No contents/credentials are printed and no
new vault write occurs. Separate immutable refusal evidence is added without changing the original
`HA_OTHER_ENTRIES_CHANGED` record. The actual difference is still unverified; there is no activated-key
PASS. Diagnostic-only follow-up source has26 native/unit checks/0 skips and records safe HA error
codes, preserving first cause. No automatic repeated unlock/read loop is left running.

Sourcefa24461f84d0431605dc696cc79ae4e2629ed704 pushed and remote-matched; vault run46056036135
SUCCESS. The real selective operation `ha-activation-20261127-02` reached entry-created and native
attachment import, then refused `HA_OTHER_ENTRIES_CHANGED`. Its encrypted working-before copy,
intent, entry-created and first failure are retained privately. No repeated add/import, rollback of
current user data or replacement by the old candidate is permitted as a shortcut. A separate
read-only diagnostic failed to unlock/read its encrypted prestate; no password cause is inferred.

The next source correction compares attachment references by exact decompressed content: KDBX XML
export-local numeric IDs can change without changing attachment bytes. Isolated tests include an
existing attachment, working-only later entry, loss-of-response reconciliation, duplicate refusal
and changed attachment rejection:25 PASS/0 skips. Read-only reconciliation validates all old entries
and history plus exactly the new HA entry, runs the real consumer on candidate/working and verifies
no working bytes changed during reading. The actual private difference is not claimed explained
until this readback succeeds. A later success retains the original refusal.

`scripts/ha_wrapping_activate.py` copies only the existing HA custody encryption entry's
`recovery.tar.gz` attachment from the encrypted candidate into the saved/closed working
Family-Connect.kdbx. No key generation and no whole-vault candidate replacement. A local native
dialog precedes access; passwords/payload remain in memory/stdin/memfd, not argv, Git or diagnostics.
The encrypted working prestate and phase records are private; UUID/entry/history preservation and
the real HA consumer must pass before activation is accepted. No password dialog is permitted in
a subsequent held interval. A partial failure is not automatically retried or declared activated.

Native/unit qualification:24 PASS/0 skips, including changes made only in the working vault after
candidate creation, no regeneration, preservation of those entries/history, exact existing-key
readback, duplicate refusal and open-GUI refusal. First local qualification refusals (XML sibling
whitespace comparison and a private-write call arity) are retained with their corrected checks.
The earlier real GUI-copy attempt returned `HA_VAULT_KEY_UNAVAILABLE_PRIVATE_DIAGNOSTICS_SUPPRESSED`
for the working vault; unchanged observed working metadata does not prove a password error.
It is not activation PASS. Exact-source CI/remote SHA are recorded after push, not assumed here.

No accepted component was reinstalled. No production admission, mount, cgroup or support hold was
acquired in this continuation. Native OWNER maintenance components remain in progress and no
common held interval, new stopped-support snapshot, encrypted kit or linked resume exists.

## Historical checkpoint — 18:15UTC

**COMMON_ENCRYPTED_KIT_NOT_CREATED; selected OWNER/all-writer NEXT remains IN_PROGRESS.**
Review items1/2 are fixed and qualified; item3 has a dedicated-process deadline but no complete
production OWNER adapter; receiver/native rows of item4 remain unclosed. Item5 has a qualified
purpose-separated consumer and a real encrypted vault candidate, not a recovery kit. No common
production held interval, new stopped-support snapshot, independent kit verification or capture-linked
resume occurred. There is no kit identifier. Historical e4eace1a is not reused as a current component.

The operational preflight incident is recovered with a new credential-maintenance operation, not by
replaying old capture/support operations. Operation ha02-connect-20261127-1729-e28a771d is COMMITTED;
independent exact terminal archives verify9/8/8 files on RU/NL1/NL2, with old ledgers retained and
no remaining owner.json for that operation. Manifest hashes and original failed invocations are below.
The source-pinned ru-connect-bounded-4da8d7dc wrapper and two unit drop-ins are the only new permanent
operational installation. They retry TCP connection establishment only, never an accepted RPC.
Accepted console/publisher, three manual roots, collector and observer were not reinstalled.

### Fresh normal baseline and physical readback

- Natural RU renewal invocation7fff695bfab742ae89351b6df28098cf starts18:06:11UTC and completes0
  at18:06:20; directory96e2575f741547549faf2607130732b6 completes0 at18:06:10. Both timers are
  enabled/active/waiting. The independent watcher observed the actual exec-ready /proc/PID/root
  namespace of each invocation: exact wrapper6aa6d679 and unchanged original SSHaf809334.
  This is a natural timer cycle, not a manual invocation relabeled automatic. Own two RU timer
  holds were removed after the corrected native fixture and normal unit readback; no own holds
  remain. No production capture fence or support stop was ever acquired in this continuation.
- Real panel login, overview/subscriptions/payments/two existing cards and normal logout PASS
  at18:07:35; five HTTP200 authenticated pages, zero test messages/business mutations requested.
  The shell wrapper subsequently used zsh's read-only `status` variable and exited1; the already
  written browser receipt proves the browser checks completed. It is not a second browser failure.
- Accepted read-only observer8b9355db PASS18:12; support PID240065 and binding, archive, authority,
  cursor, NL1 generation and historical receipts equal the preflight/after-reload values. No completed
  Resume.run health check or resume.prepare tooling update was used. The earlier PAIRED_SETTINGS
  refusal is retained; NeedDaemonReload was observed, while the reason it became set is not proved.
- Automatic notifications593eaf6b3812419f8ffa9a7957dfc12b and support bindings
  59658efa2c2647b480395af42b2fb3e3 finish0; their timers are enabled/active/waiting18:14.
  Monitor e26e847283b24143b09b8fcb18d490ca and probe3867a272eaf34f7996c18bd1e5616dfe finish0,
  both user timers enabled/active/waiting18:13. An intermediate read used the wrong nonexistent
  support-notifications unit name; the actual loaded unit is subscription-notifications and was
  checked explicitly. That mistaken query is retained, not treated as a dependency outage.
- Last bounded authorized MESH traffic: NL1 PASS17:32, NL2 PASS17:37,4HTTPS/3DNS/expected exit.
  NL2's17:33 HTTP failure and later17:34 RELIABLE_FRAME_TIMEOUT remain separate evidence on the
  same invocation. No additional restart, provider-blocking or SIGTERM explanation is claimed.
  Passing confirmation is bounded availability, not sustained-stability acceptance. RU17:52 resource
  sample is79% disk/5.9GiB free with substantial IO pressure, not a proven network root cause.

### Exact code qualification and retained failures

| Source | Scope | Result |
| --- | --- | --- |
| da50370ed19221598935c98c8609c832aec4b6ad | Terminal-state/PG assumptions |118 focused checks; native26 PG plus6 late-import checks/0 skips; production schema read-only39 tables/25 sequences/68 catalogs |
| 4dddd5ec73a76244f8d2447555a3fea19ab4b602 | Separate HA vault consumer |21 native/unit checks/0 skips, signing regression preserved |
| b87397a55637972a2feaa74c149418fb0d880764 | Hard callback deadline/release ambiguity |130 focused checks/0 skips; acquisition/snapshot/cleanup hangs and process death |
| e28a771d79c7d49b2fedfd2e5180b55f97976d59 | One-shot TCP-only recovery |13 focused checks and native SSH effect counts; production fresh operation COMMITTED |
| 4da8d7dcbaf407cc0cefd46d303017039a6000c5 | Scoped RU SSH namespace |Installed wrapper/two drop-ins; original unit/runtime/config/host SSH unchanged |
| 0b8775f3bf3e57301dc113ed9d7a36d37a298e0b | Strengthened actual-wrapper fixture |13 unit checks/0 skips; native bare and actual-namespace tests; all four applicable workflows SUCCESS |

Exact0b workflows: renewal-connect46044969027, Android46044968983, phase046044969070 and Linux
46044969002 SUCCESS. Independent artifact15222445166 exact-set/readback matches0b source,13/0 skips,
native fixture SHA5f31124d340cea8355adcc561a1440bce32510d0821c8e128ecc126d1b91a60f,
three connect attempts/one effect and lost-reply one connection/one effect/no RPC replay. ZIP SHA256
30c05a8d9f603bf0f8f196b9b5c60f0a9e13014b31844464e48ce9d0ff7c9076. The namespace result asserts
actual_wrapper_verified=true after removing the caller's retry option; the bare test is separate.

Independent native support run46034920447 on exactb873 first fails359/360, zero skips, in unchanged
test_old_detached_reader_must_finish_before_application_drain[True], missing drained.json. Its
artifact15217791584 is preserved, ZIP47a4269e2bc39a5512c96f2b460678de4888b9003e552ba99102a490e7d2be77.
One retry of the failed job on the same source succeeds360/360, zero skips; independent artifact
15220773170 ZIPf3e048bfe186956ef18f2174a39e2c081f5d23b89077ac86b12da032369ce04d verifies exact
source and receipts. The successful retry does not establish the first failure's cause.
Earlier pre-fix failures, the dedicated-process deadline race and first RECOVERY_PARENT refusal are
retained. Canceled intervening workflow runs are not PASS. Raw artifacts/evidence remain private.

### Custody, preserved history and exact remaining blocker

The protected local workflow created a separate32-byte OS-CSPRNG HA encryption key and independently
read it back from an encrypted Family-Connect.kdbx candidate. Exact entry `HA custody encryption`,
attachment `recovery.tar.gz`, member `ha-custody/aes256gcm.raw`, purpose
`family-connect/ha-custody-encryption/v1`. The candidate is under the owner's private vault directory
`ha-candidate-20261127-01/Family-Connect.kdbx`; original vault bytes are unchanged. It is NOT merged
into a potentially open live vault or copied externally. No signing key is reused and no key bytes,
password or vault content appear in Git/logs/report. Two earlier generic key-read refusals are kept;
they do not prove a wrong password or absence of a key. Joker/NL2 destination/KeePassXC roles remain
as agreed. Independent external custody and loss-of-laptop access are still unconfirmed.

At the17:57 historical readback, root119 plus41 earlier additions (160 byte/stat records) and
inventory3+12+6 plus8 earlier additions (29 records) remain unchanged. Non-atomic current names
sample246 root/101 inventory; new86/72 are separate, not merged into the original UNKNOWN groups.
Probe14 is unchanged. Original support33 full bytes match the beginning of this continuation;
current221 names include188 additional retained entries. Normal automatic cycles can add more;
these samples are not a claim of a frozen final count. No marker was deleted, whitelisted or settled.
Gate.drain remains strict.

The first unclosed production channel is OWNER native writes to
`/var/lib/docker/volumes/fc-control-plane-0_synthetic_state/_data/synthetic/registry.sqlite3`,
`/etc/family-connect-support/panel-pseudonym-aliases.json` and native collector projections.
A qualified PG boundary does not fence these files. There is no integrated, continuously held
physical boundary covering already accepted file descriptors/mappings/child work with bounded
acquire/snapshot/cleanup and safe late-effect reconciliation. A synthetic prefaulted-mapping
experiment later observes EPERM for old-FD pwrite and SIGBUS for a mapped write under an inode flag,
with original synthetic bytes/flags restored; this is one feasibility case, NOT a qualified adapter
or proof of crash cleanup/tree coverage/lease continuity.

RU `/friends/notices/publish` still also needs its notice DB and both export file paths (including
temporary-file/os.replace effects) held together; peer/operator/profile and remaining receiver-file
rows below remain open. Receiver subprocess lifetime must be covered independently of a dead parent
or completed SSH/HTTP client. New RU wrapper/drop-in source closure must join the exact kit binding.
No source-only maintenance hold, empty ExecIDs or stored intent substitutes for these guarantees.

**Next concrete step:** implement/qualify the exact OWNER native-file boundary, then compose it with
the qualified PG transaction, installed mandatory gates and accepted stopped-support procedure in
one bounded participant lease. Do not start common capture with partial coverage. This is unfinished
engineering, not a request for another key path or new inventory. HA-02 independent custody,
source-host-free current/post-ACK recovery, console reboot startup and
FLEET-PRODUCTION-ONBOARDING-1 remain separate/open. Current HTTP PASS is not reboot acceptance.

Code-only operational rollback removes only the two owned
`95-ha02-connect-bounded-4da8d7dc.conf` drop-ins after holding own timers and waiting for selected
invocations, then daemon-reloads; it does not restore databases, profiles, authority or history.
Rollback was not needed. No public release/catalog/version change occurred. All logical source
commits were pushed normally and remote-matched; main stays da94566a. This checkpoint is not a release.

## Historical renewal/directory reconciliation — 17:43–17:49UTC

At17:46 the two scoped4da8d7dc drop-ins are installed after CI46044326107/native namespace PASS.
Wrapper SHA6aa6d6797cc7aa94a0376d67e22cfdd6a60e33dac5649df7d0ecdcbd37cf5d2b;
drop-in SHA377d4dbfa7bb90ca5057ddc68792a905c65302957efd7e0e15a446355aec6835;
unchanged host SSH SHAaf809334cc71603f0e27a53e2234e15bd3c36503b3af7d367d103d2db2ffc15f.
Original unit files/ExecStart/runtime/config bytes compare unchanged. Normal directory invocation
5c66ea4fd6dd4a24a12bc1af571bde46 completes0. Initial /proc/MainPID mount assertion was attempted
without first proving exec-ready identity; it is retained and NOT a successful loaded-code proof.
The native namespace fixture is strengthened to assert actual wrapper bytes/original ELF and to
remove the caller's own ConnectionAttempts option. Without the wrapper it must fail. No timers
are released on the basis of the earlier insufficient namespace fixture alone.

Corrected e28a771d79c7d49b2fedfd2e5180b55f97976d59 launcher SHA
af6fdf10c4fb6d3cef7db6bcbe75b6ff224d9010f6fd70e5a0e17596242f38af runs once in transient
invocation82fcf10e75a54aa4bffc066336956f5d. Operation ha02-connect-20261127-1729-e28a771d
commits with first_cause=null. Existing runtime source e9fd31754bdf50c95842a1644f86ddb328b839ec1e0c9454daf08d3e9d17f0cc
and controller config a3fae10e013b770bf4edf1e18ceec3046c4670feee784f3f567ea0a256c30801
remain unchanged. Independently read completed ledgers and exact9/8/8-file archives, no owner.json;
manifest hashes RU1c1b2225013c4a13bd5f7ceb3ecff5a037f8b2232434c23714dab2a246c14251,
NL1 449aea284f9f51ffe704471fc0a824ff593c0f75fb0e7fd3bcdd42bf5376647b,
NL2 d7e7682dcdf760c09ecbb75b311e0c2edd1de59a69f04a106793e4f2e78b37cf.
Previous completed operation remains in every ledger. Normal original renewal invocation
d0c392134c9a4c07b4ea50acb0ac86b0 returns NOOP/0. This is credential maintenance recovery,
not a capture-linked resume or evidence of unrelated historical request completion.

Directory invocations8dbcc2b1263445278169b4054f2c390b and f97bbd1a229249e983006bd0e1ec4a0e
return GATEWAY_CHECK_REQUIRED/NL2 GATEWAY_READ_UNAVAILABLE with zero changed files. A fresh
separate read-only inspection of both gateways returns NOOP with over3h credential headroom.
At the17:43 pre-install checkpoint both own RU timers remained held; no repeated automatic failing
cycle was resumed. A two-line
SSH connection wrapper is qualified in a private service mount namespace to retain original
ExecStart, runtime/config, strict SSH pins, key paths and all receiver/RPC rules. The original
SSH binary is bound read-only at /run/family-connect-ssh-original; only /usr/bin/ssh inside the
two selected units is wrapped with ConnectionAttempts=3. Host SSH and unrelated services are
unchanged. This was not installed at17:43; the17:46 installation and18:06 acceptance are recorded above.
Code-only rollback removes only the two owned drop-ins;
it never restores product databases, old authority, credential profiles or transaction history.
Any installed wrapper/unit source closure must be included and qualified before the common kit.

Post-renewal NL1 traffic passes17:32; NL2 fails all4 HTTP reads17:33 after verified end-site TLS,
then one17:37 confirmation passes4 HTTPS/3 DNS/expected egress. Same NL2 invocation
9f62619fc83f45ddb21134293540fb95 stays active/NRestarts0. Its17:34 RELIABLE_FRAME_TIMEOUT is
later than client17:33 failure and not proof of the initiating cause. No MESH restart or provider
blocking/SIGTERM explanation is asserted. Panel login/five existing pages/logout PASS17:31.

Support observer first refuses PAIRED_SETTINGS: actual protected settings match, but systemd
reports NeedDaemonReload=yes for support/dependencies. Saved unit bytes are unchanged; one
manager daemon-reload (no service restart) restores observer PASS. Original PID240065, archive,
authority, cursor, NL1 generation and five historical receipt hashes compare equal. Original33
support marker names remain; current215 names include182 additional records saved separately.
An initial exact-count33 assertion is retained as a failed assumption, not a deletion or settlement.

## Historical bounded operational continuation — 17:20UTC

First recovery-wrapper invocation b11394dbba1c42a38988993659b92744 refuses RECOVERY_PARENT
before its intent journal/runtime import/any RPC. The actual transaction is root-owned0600 under
root-owned0700 renewal directories, but `/opt/apps/family_connect` is historically ubuntu-owned0775.
Do not change those permissions or bypass the code check. Corrected helper keeps exact data hash,
canonical path, regular-file/root-owner/mode/size checks; root-owned ancestor restrictions remain
mandatory for all executable sources/config. The first unit and unchanged predecessor are retained;
only a new invocation/operation can follow. d583 TCP-only CI46041238861 SUCCESS; native isolated
SSH and116 focused renewal/serialization tests PASS. Initial missing-RNS test collection is retained,
then the existing pinned support dependency environment supplies the module (no runtime pip install).

Review source commits da50370ed19221598935c98c8609c832aec4b6ad,
4dddd5ec73a76244f8d2447555a3fea19ab4b602 and b87397a55637972a2feaa74c149418fb0d880764
are pushed and remote SHA verified. No accepted console/publisher/collector/manual component
was reinstalled. Independent CI artifact byte verification: causal130/0 skips
artifact15216401637/910040d9040288ea3e193a9d14f0f5bccdfb2e70d514aa4ac6769a7427900dc5;
vault21/0 skips15215866749/2bfe80ef69e967b8673cdfad811a8eddb8d3f0c186a3d5f8db7f6c880e0394b1;
PG32/0 skips15215067000/b7a75332f73fadd199ad2d7330db36e0bf3e91fb0d8f9ece18d72afe14d93fd5.
b873 causal/Android/Linux/phase0 CI SUCCESS; native support46034920447 FAILED:
`test_old_detached_reader_must_finish_before_application_drain[True]` did not produce
drained.json (359 pass,1 fail,0 skips). Artifact15217791584, exact SHA
47a4269e2bc39a5512c96f2b460678de4888b9003e552ba99102a490e7d2be77 is retained. This is
unchanged legacy support code, not an explained-away timing failure or full native PASS.
Earlier Linux runs cancelled by subsequent pushes remain CANCELLED, not acceptance.

Fresh observer8b at16:51 returns ACCEPTED_SUPPORT_READ_ONLY_NORMAL with unchanged PID240065,
archive621009b8, authorityb0c470dc, NL1 generationb75ef2a2 and cursor52bd903e. Panel actual
login/five existing pages/logout PASS16:19. NL1 real traffic PASS16:34. NL2 first16:35 response
failure is retained; one16:42 confirmation passes4 HTTPS/3 DNS/expected egress without restart.
Later RELIABLE_FRAME_TIMEOUT/session-close diagnostics do not prove the initiating cause.
Reviewed PG source read-only production scope PASS:39 tables/25 sequences,68 catalog tables,
69 information_schema objects; no triggers. No production ALTER/lock was taken.

RU renewal invocation56c13e5a88f74d18ae49ae52b25b431f failed16:41 with
REMOTE_OUTCOME_UNKNOWN_READBACK_REQUIRED. One controlled normal invocation
5d03860eb7164711968a3d846149ef5e also fails before ACQUIRING. Previous operation
scheduled-1795788667-d73ff598aee18ca8 remains COMMITTED, transaction SHA
025cc60dae673e075f7386f5ae87afa4fd8fa0bef4a7f1e3fec335aeb63c5069; all three terminal
ledgers read independently, no owner record. Own renewal/directory-sync timers are held
inactive but remain enabled under `/root/fc-ha02-review-reconcile-20261127-1650` on RU.
No capture/support barrier exists. Fresh read-only RPC diagnostics preserve the original
67-byte SSH TCP-connect timeout. At17:10 dual-host header-only captures see repeated NL1
SYN-ACK output for RU port43958 but no corresponding RU input; neighboring flows succeed.
Kernel capture reports zero dropped packets. This localizes the observation, not a provider,
SIGTERM, SSH policy or ultimate network-root-cause verdict. No firewall/policy was changed.

`scripts/renewal_connect_recovery.py` prepares one fresh scheduled operation using the unchanged
installed runtime/config and exact source/config/committed-transaction pins. Both own timer
holds and inactive services are mandatory. A new immutable journal directory refuses repeats.
Only OpenSSH ConnectionAttempts=3 is added; original8s connect timeout/120s RPC timeout, strict
pins, authentication and downstream policy remain unchanged. RPC results/lost replies never
trigger a second RPC. This is an explicit bounded recovery path, not automatic retry of an
uncertain operation or a permanently installed wrapper. Native isolated NL2 OpenSSH qualifies
two refused TCP connects then one command/effect, and lost reply with one connection/effect
and no retry. Synthetic daemon stops afterward; no production paths are used. Recovery has
not yet run; both RU holds must be explicitly reconciled before ending this operation.

Dedicated HA AES key preparation succeeds in an encrypted Family-Connect.kdbx candidate;
attachment export/readback succeeds and original vault bytes remain unchanged. Candidate
activation/live-vault merge and independent custody are not claimed. No real encrypted recovery
kit exists. Root119/earlier41 and inventory29/probe14 exact retained records remain unchanged;
new marker names are saved separately, not settled. Native-file experiment2 confirms EPERM for
an old FD and SIGBUS for a prefaulted mapping on one synthetic NL2 inode; original experiment
without terminal receipt remains a failure, and neither is complete tree/continuous-lease coverage.
Private evidence: `/mnt/data/fc-ha02-review-20261127`; secrets/raw state never enter Git.

## Historical pre-review result and exact boundary

The requested **production encrypted RU/NL1/NL2/OWNER kit does not exist yet**.
No production stop/capture/resume operation was started. Existing accepted components
were not reinstalled. This change qualifies a missing causal four-host protocol and
checks delayed read-model imports on the exact installed console image. Neither result
is an all-writer permit. HA-02, independent custody, source-host-free current/post-ACK
restore and FLEET-PRODUCTION-ONBOARDING-1 remain open.

Work continues on feature/device-technical-metadata-20261115 from de41922a; main remains
da94566a. Fetch found no subsequent feature commits. Independent GitHub readback now
confirms all five d7d8b9a9 workflows SUCCESS, including runs45941591986/91987/92002/92021/91970.
The accepted native360/0-skips scope and OWNER custody format are retained, not rebuilt.

## Fresh bounded operational preflight

At12:28UTC normal real panel login, overview, subscriptions, payments, two existing
cards and logout pass. No test message or manual business-data mutation is performed.
Console3af9fbf9/publisher35158514/PostgreSQL18cfe3ef remain running, restart counts0.
Read-only observer8b9355db returns ACCEPTED_SUPPORT_READ_ONLY_NORMAL. SupportPID240065,
archive621009b8, authorityb0c470dc, NL1 generationb75ef2a2, cursor and accepted history
are byte/binding-identical to the05:05 checkpoint. No completed Resume.run is executed.
The actual runtime directory is0750 fc-support:fc-support-ipc and contains worker.sock0660;
an initial check of a nonexistent `ipc` child is retained, not treated as IPC failure.

NL1 PID2822717/invocation09bbec58 and NL2 PID3203344/invocationf37b8845 are active/running,
NRestarts2 each. Existing authorized FLEET_MESH_PROBE_1 passes4HTTPS/3DNS/expected egress
for each node at12:31/12:32UTC, without an SSH tunnel or normal-broker fallback. Its existing
identity is unchanged. Process status alone is not this traffic result. Two initial local
probe launches fail before dispatch on missing Python imports; those logs remain separate.
The correct existing support venv plus repository source resolves those prerequisites.

RU has about6GiB free/79% used; IO PSI avg10 some3.34/full2.27, memory pressure0 at this
sample. This is not the earlier severe-pressure observation or a root-cause diagnosis.
Normal renewal/directory-sync invocations exit0, both timers enabled/active/waiting.
Current renewal scheduled-1795778757-6f85e99b1d8ed952 is COMMITTED, first_cause null.
The bounded searched renewal state has no owner.json; this readback is not a held
maintenance lock and must be refreshed when the actual operation starts.

No production hold is acquired by this iteration. Root authentication uses the ordinary
local sudo dialog; sudoers/polkit are unchanged, and Docker is not used to obtain host root.

## Review follow-up

27 November16:18UTC, continued from exact ab902e274d9a208fbde16481c794c80fc58c80ef;
remote feature matched and main remained da94566acb770dc758a1e057f02bfef784585a75.
This is source-only review correction, not a production capture or installation.

- Reproduced five failures: changed HELD replay, request shape, operation, command, and cleanup
  preservation. All active request validation is now inside terminal handling; FAILED retains the
  first sanitized cause, a separate cleanup record distinguishes RELEASED/UNKNOWN, and later CAPTURED
  refuses. A correct completed replay remains idempotent even after an invalid completed replay.
  118 focused causal/local-gate tests PASS. Cleanup failure is not evidence of physical release.
- Production PostgreSQL17.11 was inspected with read-only transactions before code changes:
  zero event triggers; information_schema contains65 stock views and four stock persistent tables
  (sql_features, sql_implementation_info, sql_parts, sql_sizing), no sequences. No production boundary
  acquired. The narrow PG17 contract checks this explicit composition and column types/owner and
  includes the four tables in held locks; unknown/changed persistent objects refuse.
- pg_event_trigger is locked before scope validation and any ALTER SEQUENCE; any event handler
  (including disabled handlers) is unsupported. The isolated ddl_command_start/setval regression
  proves refusal with unchanged sequence/history; a subsequent control ALTER proves the handler
  really would change the sequence. Concurrent trigger installation is physically blocked.
- Retained pre-fix PostgreSQL5 failures/21 passes; exact console3af9fbf9 and PG18cfe3ef now pass26
  native cases. Operation f22454fc7d9436d7df77048ac1dbbc25 also fences an already-created Docker exec,
  dumps/restores independently, and reconciles its late effect exactly once. Boundary SHA256
  e6179b25be861c6d266eba0b712c3a71fd99ed94ba36f47355c23ddf319c45d5;
  test SHA256 cfe272d99af26955cffe897632850aa68419adbc49e6663ae897abc5dfe8bea2.
  These are synthetic, unencrypted objects; no product mounts. Private evidence is retained under
  `/mnt/data/fc-ha02-review-20261127/`; no private data is committed.

No accepted installed component, original marker, authority or support operation was changed.
No production common interval, stopped-support snapshot, encrypted kit or linked resume is claimed.
Outstanding OWNER native-file and remote receiver rows below still prohibit acceptance. Acquisition/
callback death and physical continuity integration must qualify before production; in-memory protocol
replay is not fresh-process recovery. HA-02/custody/source-host-free restore/reboot/onboarding stay open.
Applicable exact-source CI is pending the review-fix push; no pending run is counted as PASS.

Review fix committed/pushed as da50370ed19221598935c98c8609c832aec4b6ad, independently matched
remote feature. At16:27 causal46032656216, Control panel46032656358 and Android46032656463
are SUCCESS; native support46032656146, Linux46032656237 and phase046032656208 are still running.
Predecessor ab902e27 phase046011184148 is SUCCESS. No in-progress run is a PASS.

### Dedicated HA vault consumer

The separate AES consumer and encrypted-candidate preparation use the existing verified
`vault_archive` memfd reader, not the signing loader. Fixed database/entry/attachment/member and
purpose, exact32 raw bytes, strict exact-set archive and suppressed CLI diagnostics are tested.
OS CSPRNG is used only for the new HA entry. Native KeePassXC import/export/readback plus AES-GCM
roundtrip and existing signing regression:21 PASS, no skips. One initial test assertion incorrectly
rejected the dialog's explanatory words “No signing key is used”; retained, then corrected to
check actual CLI entry selection (no product change). Current vault remains unopened/unmodified.
Preparation intentionally leaves a separately encrypted candidate, not automatic replacement of
a potentially open vault. [Protected local activation workflow](../operators/ha-wrapping-key.md).

Fresh panel read-only login/overview/subscriptions/payments/two existing cards/logout passes16:19.
RU's initial16:27 SSH connect timeout is retained; one16:29 confirmation succeeds, IO pressure
some5.00/full3.41 avg10. No recovery action or root-cause claim. NL1/NL2 preflight shows active MESH
processes; this is not fresh traffic PASS. Local normal monitor/probe latest invocations exit0.
Local sudo dialog is pending, not substituted by Docker; no support observer result yet this turn.

### Dedicated process deadline and release ambiguity

Dedicated `capture_fleet.serve` now arms a CLOCK_MONOTONIC POSIX timer delivering SIGKILL;
Python exception interception cannot prolong a hanging acquisition, snapshot or cleanup.250ms
is reserved only for cleanup after the protocol deadline; it does not extend the signed lease.
This API must run in a dedicated process, not a shared service/interpreter. It does not kill or
prove completion of downstream descendants; their independent physical fences remain mandatory.
Remote PostgreSQL server-side transaction deadlines are still required independently of controller
liveness. Adapter source closure must include `control/capture_process.py` as well as the protocol.

130 focused cases PASS, including real subprocesses hung in each callback, forced process death,
independent kernel-lock readback and refusal to reconstruct a participant on its existing journal.
A killed process can leave only partial journal evidence; it is not a completed operation or
fresh-process recovery. Preserve it and use safe reconciliation/new operation after proving old
physical restrictions absent/retained. For a hung cleanup after changed replay, failed.json retains
FLEET_REPLAY_CHANGED before process death. An ambiguous release callback is attempted once only;
no automatic second effect is hidden inside abort. UNKNOWN cleanup is explicitly not normal resume.
Two initial channel-timeout tests exposed a deadline/cleanup race and are retained; the bounded
cleanup allowance fixes this without extending valid capture time. Exact-source CI follows push.

An isolated NL2 inode-flag feasibility experiment (only a new synthetic file under
`/root/fc-ha02-inode-fence-lab-04jentm_`) lost its terminal response. Readback found its immutable
flag still set; byte/UID/path checks preceded clearing exactly that owned flag. Independent receipt
records before/after flags and unchanged synthetic SHA256
8649d1a112971044db74efd7a67be996e8f110ef74cda0417906384deebe7e6d.
No product file was opened and no production fence was set. The experiment is NOT qualification:
its missing terminal reason and outstanding old-mapping guarantees prohibit adopting it as the
native-file fence. Receipt is retained privately as `inode-probe-cleanup.json`; nothing is settled
by absent processes or a successful later command.

## Finite writer/endpoint matrix

“Required” below is an outstanding production adapter obligation, not a claim of a held fence.
Each adapter must check installed sources/UIDs/paths, take the actual local constraints,
keep them continuously until sealing, and issue receipts for the same operation. An old
UNKNOWN need not become settled; its possible future effects must be covered by these rows.

| Writer / endpoint | Captured state and already dispatched work | New admission | Old work and continuous proof required | Queued/late behavior after resume |
| --- | --- | --- | --- | --- |
| OWNER root support/subscription collectors | Local projections/cursor; cursor IPC and SSH exports may have been sent | Accepted mandatory b7f4cbd2 gate | Hold admission/operations; include downstream rows, not deletion of root119/additional markers | Fresh source-bound collection; support cursor/queue continuity remains the accepted linked-resume contract |
| OWNER inventory/probe/manual collectors on three installed roots | Read-model projections, Docker import calls, SSH exports | Accepted b49c76c0 per-role mandatory bindings, including no-env entrypoints | Hold role/cycle locks; already accepted Docker/receiver work requires its own downstream boundary | Inventory/subscription/probe digest/identity dedup; metadata consent/sequence floors; new native checks below |
| OWNER Docker `exec` imports into console | Accepted `import_inventory`, `import_subscriptions`, `import_network_probe`, `import_technical_metadata`; PostgreSQL effects may outlive the invoking client | Installed console gate on actual database operations | **Missing integrated production adapter:** held PostgreSQL/native-write boundary or exact operation terminal proof, including already-created/started execs and their accepted DB work; empty ExecIDs is insufficient | Qualified read-model replay does not regress latest observations, duplicate effects/audits, or resurrect revoked metadata; it is not physical fencing |
| OWNER HTTP, scheduler, management, direct ORM and known native SQL | Business/fleet/auth/audit/read-model PostgreSQL data; synthetic registry and aliases | Accepted image/binding checks and console gate cover admitted application paths | Need exact full database/file coverage, accepted transaction/sequence/native access constraints; the existing two-table PublicationFence is not a whole-database boundary | Application idempotency and retained journals only; arbitrary queued native SQL is not certified by the six import checks |
| Publisher and RU `/friends/notices/publish` | Queued/unknown message IDs, signed payloads, notice store/feed; an HTTP request may already be accepted | Installed publisher gate plus receiver HTTP admission | Need both database publication boundary and continuously held RU notice receiver/store boundary; client HTTP completion is insufficient | Existing stable message ID/immutable payload and explicit unknown retry; canonical receiver/readback must be included, not only sender state |
| RU Friends HTTP and application stores | Registry, diagnostics, notices, metadata, proofs, grants, paid/referral/support/chat/routing state | Installed receiver overlay0d181404 and its actual gate | Existing local SQLite writer locks plus receiver operation coverage must be one continuously held participant; retain sidecar/schema checks | Existing nonce/version/CAS rules must be bound to installed code and captured floors; no guessed historical outcomes |
| RU peer worker, native operator CLIs and deployment paths | Peer allocation, profiles, membership, aliases, support policy and local/file effects; Docker/SSH children possible | Existing optional CLI guards alone are not mandatory native coverage | **Outstanding:** actual storage/operation/receiver boundaries for each path; do not infer closure from stopped sender/absent process | Preserve intent/expected-version journals and use qualified reconciliation; offline signer/deployment changes cannot run concurrently |
| RU renewal/directory-sync and NL receivers | Coordinator, owner/ledger/archive, profile/CRL/lease floors and gateway directories | Existing coordinator/node operation locks and receiver admission | Acquire actual locks and verify all three node ownership/reconciliation states throughout capture; preflight COMMITTED is not a hold | Existing current-generation/native operation identity; do not replay old start intents or downgrade authority |
| NL1/NL2 registration, profile snapshot, fleet/transport receivers | Per-node allocation and installed receiver files; already accepted forced-command work | Existing pinned receiver wrappers/gates where installed | Held receiver operations and native allocation/profile/file boundaries; include possible children rather than sender SSH status | Existing allocation identity, generation/sequence/CAS rules; actual adapter coverage remains required |
| OWNER support lifetime writer ↔ NL1 mailbox | Spool/RNS persistence, cursor, mailbox queues/dedup/floors; old links/envelopes | Accepted managed stop plus closed mailbox generation | New stopped-support snapshot inside the common interval, closed receiver/readback, final persistence and independent exit proof | Accepted fresh linked forward resume and old-generation/link rejection; preserve support33 and all queue/history bytes |
| Paid-watch/deny and transport runtime | Enforcement and runtime-derived leases, not permission to activate stale authority | Do not disable enforcement or change its timing/policy | Explicitly distinguish captured durable authority from ephemeral runtime state; bounded barriers must preserve ordinary watchdog behavior | Restore/reconcile from current authority; no stale lease or stopped enforcement shortcut |

The immediate concrete blocker is production integration of the OWNER Docker-import/accepted
PostgreSQL/native-write row. The isolated logical boundary qualified below now supplies an actual
database lock mechanism, but installed admission gates/replay alone and native file paths are not
its equivalent. The causal protocol still has no integrated production adapter for that row and
always reports capture_permitted=false. No manifest-only or source-only
maintenance hold can satisfy it. Remote/file rows must also be covered before final acceptance.

## Causal protocol and independent reader

New `control.capture_fleet` uses signed per-participant receipts with exact source,
coverage and late-policy pins, operation/challenge, boot and immutable journal-path binding.
Every CAPTURED receipt depends on the complete four-host HELD set. Every SEALED receipt
depends on the complete captured set and independently checked exact file manifest while
that participant still owns its original barrier. Release requires the complete seal set.
This causal ordering, not UTC overlap or cross-kernel monotonic comparisons, demonstrates
the interval for the qualified adapter. Local capture_group and strict Gate.drain are unchanged.

Protocol errors, incomplete sets, lost leases, changed bytes/signatures/operations, wrong
boot/journal and controller EOF/deadline yield failure, retaining partial files. A failed
operation is not retried. An exact completed request returns its retained receipt without
re-entering the barrier or rerunning snapshot effects. Journals cannot be reused/rebound.
The reader validates exact bytes and composition; source authenticity/coverage remains
the responsibility of trusted, pinned physical adapters, not self-declared inventory hashes.
No production signer keys or HA activation authority are introduced by lab receipt keys.

Final isolated four-host operation: `715d0af8b59b9ca47ffa9e5c31e71443`.
Protocol SHA256 `e794f6025df08897a6be6b13f8a3af1107bc76a9522a553d28f7c325ccd959da`;
adapter SHA256 `f134c07aa601930eb9e26f3aa48adb656dad9b7575f9c408660e7db91dbeef40`.
Independent exact-set manifest SHA256 `791a4631ca8eb60de023d0db73c849f06f39b1de42def79f7d84558920e10c6c`.
All four distinct real kernels use disposable SQLite data, not product paths. A writer
accepted before capture is blocked by its actual SQLite writer lock, its queued intent
is captured, and after release its journal reconciles exactly one effect; a duplicate
adds none. Four independent post-release readbacks confirm completion, not merely SSH exit.
Lab private keys/state remain in new private operation directories, never Git/CI artifacts.

## Qualification and retained refusals

-112 focused tests/0 skips pass: causal protocol, existing local group and strict gate.
  Real process/channel tests cover controller EOF, incomplete frames/deadline, lock release;
  other tests cover response loss, incomplete participants/files, barrier loss during capture,
  changed snapshots, replay and boot/journal binding. CI at the source commit is required.
- The first protocol draft allowed reuse of an operation at a different journal path.
  A failing counterexample is retained. Boot/path/identity binding fixes it; the final
  four-host qualification is a new operation, not a reinterpretation of the earlier run.
- Exact console3af9fbf9 and PostgreSQL18cfe3ef pass6 new isolated late-import/replay checks,
  operation39a42a1fe54c6ca6d840ec927e77afe0. Actual loaded inventory/probe/subscription/metadata/
  model hashes match source. No product mounts, external network, live database or messages.
  The disposable native containers are removed; existing PostgreSQL is never recreated.
- Retained native prerequisites: first PG fixture used wrong UID999 and timed out. That
  attempt lacks server logs, so its detailed initiating cause is not claimed; image identity
  subsequently verifies UID70. The next attempt names a test absent in the old installed
  image. A self-contained six-case fixture then passes; both refusals remain recorded.

Private evidence: `/mnt/data/fc-ha02-common-20261127`. Source-only changes can be reverted
normally without changing installed images, bindings, support or any product data.

## Preserved history, custody and next step

Fresh readback verifies the prior160 root marker bytes/inodes/modes/UID/mtime,29 inventory
and14 probe markers unchanged. A non-atomic name census observes175/37/14; additional names
are retained separately, not declared settled or assigned a historical outcome. Original
root119, inventory3+12+6, later additions, probe14 and support33 remain separate. Accepted
support history is identical. No marker is deleted, whitelisted or used to weaken drain.

The mandatory encryption input still has no supplied approved HA wrapping-key reference;
a protected path was requested, never the secret in chat. Joker, NL2 destination
`/opt/apps/family_connect/ha-recovery/`, KeePassXC and Family-Connect.kdbx remain fixed.
Actual off-laptop custody/access remains unconfirmed. This input is not the only blocker:
the production downstream adapters above are still required independently.

**One next step within the same NEXT:** connect the qualified OWNER logical PostgreSQL boundary
to the causal participant with exact installed database/schema/readback binding and native-file coverage,
then complete the remaining matrix coverage before any production common stop/capture.
There is no production kit ID, new stopped-support snapshot, independent encrypted-kit
PASS or linked normal-resume receipt from this iteration. e4eace1a remains history.
Normal services continue; no production holds were left by these qualifications.
Console automatic reboot startup remains unqualified: order runtime directory creation,
accepted support/IPC recovery and effective-config console startup in an isolated fixture
before any installed startup change. Current HTTP success is not reboot acceptance.
Onboarding remains the separate required result: prepared VPS → IP/access/roles →
normal enrollment → verified active node, not a consequence of an encrypted recovery kit.

## Logical PostgreSQL boundary follow-up

13:25UTC source-only `fc_control_plane.capture_pg_boundary.PostgresBoundary` closes a concrete
mechanism gap rather than treating an empty ExecIDs census as proof. It holds SHARE locks on the
exact persistent public tables and PostgreSQL catalogs and ShareRowExclusive locks on all sequences.
Sequence locks are obtained by same-value ALTER CACHE inside the never-committed transaction;
release rolls it back. It refuses unsupported/uncovered relations, changed schema, an already
accepted conflicting transaction, reacquired/different XID, missing locks and expired deadline.
PostgreSQL17 transaction/idle timeouts bound an abandoned controller independently of its client.
The first failure survives a cleanup failure. Logical read/dump remains possible while writes wait.

This is a dedicated database/cluster operation, not a general-purpose host fence. It does not
cover native filesystem/configuration writes, external SQL-function effects, another database,
arbitrary unknown SQL replay or remote receivers. No integration or installation into working
console/publisher images is claimed. Existing helpers and their accepted meanings are unchanged.

Exact final native operation2cbcb034addbfbb90ac7851eb19bcd04, boundary source SHA256
96ce0c6354ba69fb1c8279abe39de42823d2594c518a1cea121a226d3f0b0b28:

- 20 checks PASS on console3af9fbf9/PostgreSQL18cfe3ef, private network/tmpfs, no product mounts.
- INSERT/UPDATE/DELETE/TRUNCATE, nextval/setval, table/schema DDL and large-object writes block;
  reads remain usable. Incomplete coverage, an active earlier transaction, lost/reacquired barrier,
  server timeout and killed controller are explicitly exercised. A pre-existing CACHE32 sequence
  allocation cannot bypass the lock; last_value/is_called/cache survive the barrier unchanged.
  Original history/schema survives.
- An actual Docker exec and its DB connection exist **before** the boundary. Its late INSERT
  independently appears as a server lock wait. The barrier holder reads no late effect; pg_dump
  succeeds. After release, the original request and identical retry leave one unique effect.
- A separate pg_restore/psql reader restores that held dump into another disposable database and
  finds only the original history/unchanged sequence. Dump SHA256
  1b6fc5561008bd37dc88cefd34c0b1a8e4e721ca2ddf0cf8fa6d562cd9c81949,2241 bytes.
  Reader projection SHA2567f224f12486feedd0a36c93a3ae9c8ba3432a3620307a3d7383a28bf610b2b89.
- Native01 retains the fixture's malformed Docker mount argument refusal before console execution.
  Native02 retains17 PASS/one failed test expectation: PostgreSQL reports TransactionTimeout during
  rollback after its timeout already releases locks. Explicit failure/cleanup behavior is now tested;
  it is not hidden as a normal release. Native03–06 remain earlier qualification receipts.

This dump is **synthetic and unencrypted**, not a component of the requested production kit.
The actual delayed business-import replay checks remain the separate6-case qualified scope.
No history marker is settled by the new boundary; ordinary Gate.drain is unchanged.

Causal checkpoint010d8c6c3dbe77734f6a44ed210e32ea8ecdf72f is committed/pushed and independently
matches the feature remote. Causal CI46005005447, Control panel46005005254 and Android46005005298
are SUCCESS; phase0/Linux/native support are still running at13:25. The new database-boundary
source's applicable CI must be checked separately after its own push. No source push is deployment.

## Installed schema, final service readback and CI

Read-only execution of the exact new scope inspector inside the unchanged installed console
uses its effective database configuration and mandatory application admission, plus PostgreSQL
default_transaction_read_only=on, statement timeout3s/lock timeout100ms. It finds PostgreSQL17.11,
39 public tables,25 sequences and64 catalog tables; scope SHA256
69c88ee0af68132a0a0731af76b6cc32fdc9dbf3622a9955e83465049fcd2fe1. No boundary is acquired,
no service code is replaced, no customer row is read into the report, and no production permit
is issued. This is compatibility evidence for later integration, not a snapshot/hold.

At13:27–13:28UTC the accepted read-only observer again preserves supportPID240065, archive,
authority, mailbox generation, cursor and history exactly. Automatic notifications invocation
23672a4e93684c6dbe42a00e165b4934, bindings1658976d26c646d494aa4fb74093b0d8,
monitorfceef9895d4e4ec58ac1fd3e13ae1163 and probe0c56710c829948f583cd7e6521b8981c
complete0; their four timers are enabled/active/waiting. The first final unit query used a nonexistent
short notifications name; its not-found result is retained separately, not called a dependency outage.
Actual loaded units are family-connect-subscription-notifications.service/timer.
Real login, overview, subscriptions, payments, two existing cards and logout pass again13:28:29UTC.
The three installed containers remain running at their accepted image IDs, restart counts0.

At13:32UTC RU renewal invocationcc8d656c401a45249e1f13d948957b77 and directory-sync
10ef88db002d4cd4bf1dde6aa2a3b69d have completed0; timers enabled/active/waiting.
RU IO PSI some9.73/full6.84, disk79%/6GiB available are retained as a later bounded resource sample.
NL1 PID2854412/invocationefa61ffa253843eb9860d03b47261008 and NL2 PID3225337/invocation
6cec44a177224139a7343fdc21d70718 are active/running. Restart counts3/6 differ from preflight:
automatic restart history is not erased or misattributed to a successful probe.

NL1 traffic again passes4HTTPS/3DNS/expected egress at13:30:15UTC. NL2's13:31:18 verification
**fails**: Family authentication and end-site TLS succeed, but one speed.cloudflare.com stream
reports HTTPS response invalid, while the other three HTTPS streams pass. DNS/egress were not
completed. The matching client error site is http.ReadResponse, not an observed SIGTERM or provider
block. Its underlying parse/read error is not exposed by this binary. Server invocation6cec44a1
later records RELIABLE_IDLE_TIMEOUT/FAMILY_TLS_ERROR/session close at13:31:38–39; this timing alone
does not prove they caused the earlier HTTPS failure. Raw private client/journal evidence is kept.
A single bounded independent recheck at13:34:27 passes4HTTPS/3DNS/expected egress on the unchanged
NL2 service, with no restart, credential regeneration or policy change. That PASS does not explain
the earlier refusal or establish sustained MESH stability. Current bounded availability is confirmed;
no operator recovery or capture-linked normal resume was performed in this iteration.
At13:51:05/06 both nodes retain those same active PIDs/invocations and restart counts3/6.

Final historical readback still preserves160 prior root markers,29 inventory and14 probe byte/stat
records. Non-atomic current names remain175/37/14; additions stay separate. Support33 history is
unchanged. No marker is deleted/whitelisted/settled. No production holds were acquired or remain
from this iteration; all owned disposable lab containers were removed and the sudo execution
session was closed. The raw evidence stays private under /mnt/data/fc-ha02-common-20261127.

Exact source and installed bindings:

| Component | Binding |
| --- | --- |
| New causal protocol, source-only | 010d8c6c3dbe77734f6a44ed210e32ea8ecdf72f |
| New logical PG boundary, source-only | 948978bb9a90891f83220d6357537aaad0afa3f2 |
| Installed console/publisher source | 7a91d1278eda8594e448e5794e183e313aed8440 |
| Console image, unchanged | sha256:3af9fbf95b36b33f1c0414ac41b84687f502391e311ff0bc35658cbf50da5cb1 |
| Publisher image, unchanged | sha256:35158514371e2a321643dbfe4b64b9a87a9b85b32228a5184d2c95e3b8ac19e8 |
| PostgreSQL image, unchanged | sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73 |
| Installed three-root manual bindings | b49c76c02394feaa57a74747dbb75689b087691b |
| Installed root collector | owner-collectors-b7f4cbd2 / b7f4cbd2b96750cb9c97eee61f27a9881d5b4bdb |
| Accepted observer/stopped/recovery | 8b9355db6a114e13f53d3d7298060057acb06da8 |
| Prepared OWNER custody policy | d7d8b9a939a9b7d4aed548bf6f1d09b196fee437 |

Both new source commits are pushed with matching independently read remote feature SHA;
main remains da94566a. On010d8c6c, causal46005005447, Control panel46005005254,
Android46005005298, native support46005005552 and phase046005005470 are SUCCESS.
Linux46005005386 is CANCELLED, not PASS; the workflow has branch-scoped cancel-in-progress,
and the newer source has its own run. No failed invocation is silently overwritten.

Independent download/read of artifact15201425262 checks exact010d8c6c source,112 tests/0 skips,
exact native module/adapter hashes and four queued/replayed synthetic journals. ZIP SHA256
cb52aec261f0e75ec7a0f00731dc67c1994e9f9cbdaa128f69bef1228a8d04fd.
For948978bb, all four applicable workflows finish SUCCESS by13:53:40UTC: Control panel46007308956,
Android46007309280, phase046007309101 and Linux46007309159. Independent artifact15202367773 binds exact
948978bb and26 checks/0 skips (20 boundary+6 late imports); ZIP SHA256
19f398ba2b07cdd853fbeb1e8f5c44039970a5c61a5f95cd5d7a89c7380ca005.

**Iteration completion remains NOT_PASS.** There is no real encrypted kit/common production
interval/new stopped-support snapshot/independent encrypted-kit verification/linked resume.
The immediate next implementation is the OWNER causal adapter combining this exact logical DB
boundary with mandatory local gates and native-file boundaries, followed by the remaining matrix's
receiver/profile-file coverage. RU /friends/notices/publish and peer/operator profile/file paths
still need continuously held receiver-side proofs in the same operation. Arbitrary old SQL/native
work cannot be declared replay-safe solely from the qualified import cases. The separately supplied
32-byte HA wrapping-key reference is still unspecified; no release/signing key is substituted.
