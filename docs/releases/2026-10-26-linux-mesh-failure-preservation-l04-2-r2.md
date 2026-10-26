# L04.2-R2 — process containment versus authenticated drain

## Package-harness continuation — current checkpoint

Input main `4bef7b3083456beeb6debc1dc4a047edfbad3782`,26.10. Same L04.2-R2;
no new task ID, version, candidate, system build or source checkpoint. Review
accepts exact .10 construction/delivery, prior integrity/systemd/pkexec/DEB/
AppImage/shared-state gates, and the durable AWG product assertions/cleanup.
**Result: PARTIAL; Phase B ENVIRONMENT_BLOCKED at rollback fixture entry;
Phase C NOT_RUN. STOP. NEXT — final review L04.2-R2.**

### Immutable entry audit and reviewed AWG evidence

Read-only audit PASS. Current main differs from candidate sourceb8e9196 only in
four documentation files. A clean current-main copy excludes unrelated working
changes; product/package/runtime/test bytes remain unchanged. No build command
or package/native/RNS/system reconstruction is run.

Retained `state-client-build/linux-l042-r2-offline-20261026/candidate/` is the only
delivery input. Exact IDs, sizes and SHA256 match the complete artifact table in
the previous checkpoint below:

- Version `0.2.12~l03.2.10`; candidate
  `4264406722f6dd3efb83e9d9666e67180ce4f950333bb3e711bcbb4f5068b55a`.
- Source `b8e9196d205c6810e02a642678517a4fc44b921b`; `source_dirty=false`.
- System source `169aa687f497f8be690be5331879f994636135e1`; system
  `8ab7f298df10a89bcd116fbddaa8a23e37ff1581de3a456bb1cce69175ad9120`.

`candidate-delivery.json` matches the actual artifacts. Temporary extraction in
an offline disposable container confirms byte-identical DEB/AppImage
`candidate.json`, and both embedded system archives are byte-identical to the
exact complete system artifact. Historical .9 delivery/system and original
protected seven files match their recorded hashes. No earlier incomplete .10
assembly is used. After the audit, the retained candidate directory is made
read-only: regular files0444, executable original AppImage0555, directories0555.
Tests mount artifacts read-only and write only to separate evidence/fixture paths.
Post-stop hashes and modes remain correct.

The preceding durable AWG receipt is read, not regenerated. It contains expected
TRANSPORT_BUSY, IDLE, generation2, pending=false, successful starts0, root owner0,
TUN0, physical user lock free, root fixture released and preserved cache. Its
`network_unchanged=true` is traced to the exact unchanged fixture: before/after
hash equality covers links, IPv4/IPv6 routes and rules, resolver DNS/domains and
the nftables ruleset. The receipt is emitted after releasing the root fixture;
the XIT line follows it. No AWG action or assertion is rerun.

```text
AWG_PACKAGE_REGRESSION=PASS_BY_REVIEWED_ASSERTIONS
HARNESS_FINALIZATION=FAIL_ENVIRONMENT_EXCLUDED
```

The historical wrapper exit1 remains recorded, not rewritten as a successful
wrapper run or general package PASS.

### Immutable scripts and remaining gate results

Before launching remaining gates, all scripts are prepared completely. Each gate
has its own shell script with `set -Eeuo pipefail`; `bash -n` and Python AST
checks pass. SHA256 for every script is recorded, scripts/directories are0555,
and containers receive a read-only scripts bind mount. A separate writable
evidence directory receives logs and one-write PID files. Full current-PID exit
is observed before the next gate starts. All thirteen recorded script hashes
remain unchanged; no running file is edited, renamed, appended or replaced.

| Gate | Result |
| --- | --- |
| Prior integrity/systemd/pkexec/DEB/AppImage/shared-state | PASS retained by review; not replayed as standalone acceptance gates |
| AWG regression | PASS_BY_REVIEWED_ASSERTIONS; no replay |
| TCP package pre-start regression | PASS, wrapper exit0,32.03s; expected TRANSPORT_BUSY, IDLE/generation2/pending=false, owner/TUN/starts0, cache/physical lock/network/root-fixture cleanup PASS |
| Exact .9 rollback fixture | ENVIRONMENT_BLOCKED before first install; exit1,1.42s |
| Actual old/mixed .9/.10 install/rollback assertions | NOT_RUN; first `dpkg -i` is not reached |
| Fresh cleanup32/package46/native15/combined3/MESH/full desktop | NOT_RUN after stop; prepared scripts are not execution evidence |
| Installed P0/P1/Auto/lifecycle | NOT_RUN; Phase C not entered |

TCP and rollback each use a fresh offline Ubuntu26.04/systemd container with
separate namespaces and no host bus/home/resolver mount. TCP exercises the
existing unchanged real-systemd fixture, including normal explicit setup as its
prerequisite, then the actual TCP pre-start refusal/cleanup assertions. Its shell
and container cleanup both exit successfully; no AWG scenario is hidden inside it.

The rollback fixture reaches its first session-environment operation and fails:

```text
stage: ROLLBACK_FIXTURE_SYSTEM_BUS_UNAVAILABLE
command: loginctl enable-linger 1000
exit: 1
stderr: Failed to connect to system scope bus via local transport: No such file or directory
```

The launcher had observed `systemctl is-active dbus systemd-resolved` succeed,
but this did not establish that `loginctl` could use the system bus. The exact
reason for the unavailable bus is not localized; a startup race is not asserted
as proven. This is a harness/environment prerequisite failure, **not** evidence
that the .9 rollback, .10 package, polkit contract or runtime is defective.
The fixture fails before `dpkg -i`, setup, synthetic-state creation or any VPN
action. No retry, sleep workaround, script/source correction or next gate follows.

Both test containers are stopped/removed; readback finds no remaining containers
for this continuation. New receipts/logs are retained separately from the prior
evidence. Candidate/system bytes, historical .9 and protected seven files remain
unchanged; retained encrypted derived bases are not booted or modified. Owner
workstation **NOT_USED**. No private state, keys, materials, messages or artifacts
are staged in Git.

Earlier source-gate native15/cleanup32/combined3/desktop1306 and accepted exact
local36/phase0-Docker54 historical comparisons remain source evidence only. No new
full-suite run, failure-ID comparison or overall CI PASS is claimed. Control/
Client Linux setup incompleteness remains the accepted infrastructure observation.
Live first_reason/cleanup_reason/process_contained/drain_acknowledged/attempt/
generation remain NOT_OBSERVED for .10. L04.1 DONE and parent L04 IN_PROGRESS are
unchanged; L05/messages/voice acceptance/signing/publication/teardown NOT_RUN.

Documentation checks PASS: secret scan, strict JSON/no duplicate keys,417 local
links, four-file staged scope and `git diff --check`. Pre-existing unrelated work
is preserved outside the commit; generated artifacts and private harnesses stay local.

## Verified offline runtime and fresh delivery — previous checkpoint

Input main `b8e9196d205c6810e02a642678517a4fc44b921b`,26.10. Same L04.2-R2;
no new task, version, runtime/source checkpoint or product patch. Review accepts
the three-pin advancement and authorizes one fresh .10 package run after closing
external prerequisites. **Construction/delivery integrity PASS; L04.2-R2 PARTIAL;
Phase B ENVIRONMENT_BLOCKED at package-harness finalization; Phase C NOT_RUN.**
No product defect is established by this run. STOP. NEXT — final review L04.2-R2.

### Read-only prerequisite receipt

A clean local copy of current main excludes all unrelated working changes. The
complete diff after accepted runtime `169aa687f497f8be690be5331879f994636135e1`
contains only CI/docs/evidence and the already accepted system-reference change.
Runtime/test sources, locks, Go/Xray/RNS pins and Android106 references are
unchanged. The113 source-file keys and exact three accepted hashes are verified
again against accepted Git blobs, current files and actual archive members.

The exact complete system8ab7f298… is reused, not rebuilt: regular archive,
49,251,070 bytes, exact SHA256, expected root,759 unique regular members, uid/gid0,
no group/world-writable members, native/RNS digests and three runtime hashes PASS.
The unchanged fixed installer performs full extraction/verification/readback in
offline Ubuntu26.04/Python3.14. Historical .9 delivery/system hashes and original
protected seven files match their retained baseline before and after the run.
Neither earlier incomplete candidate output nor partial native binary is an input.

Public Type-2 assets are fetched by exact asset IDs in a separate bounded staging
container with network access, no source/private-state mount, dropped capabilities
and a read-only root. Release417724209 resolves to target commit
`fedfad51acc2860b2916a1eef32ba4a500ff31ef`. The continuous tag is mutable; acceptance
uses release/asset IDs and pinned byte hashes, not the tag name.

| External input | Exact identity / size | SHA256 |
| --- | --- | --- |
| Existing appimagetool | revision854e19e951900cf141245b384d45735942521abe;15,092,216 bytes | `95cbe7cce9717fce90c484e34052ee7c7f1d7635b33c12525b4776826a7d29b6` |
| runtime-x86_64 | asset657374641;944,632 bytes | `617aa77314d57c8b8e4fae9c3f0b35af7b30d5529cb69e98f64f92510ed98a46` |
| runtime-x86_64.sig | asset657374763;119 bytes | `4c38bbfd3c8fe7b43cd37483544e5aa682b5932674d89e53fcccd2d3fc3a8f12` |
| signing-pubkey.asc | asset657374839;685 bytes | `db8b615eb5bbf5e8418d52906b4a492960926370e2c5041ad6acaccda56ef0c6` |

Actual tool output: `appimagetool, continuous build (git version 854e19e), build 313
built on 2026-10-04 14:58:08 UTC`; executable ELF64 x86-64. No replacement tool is
downloaded. Detached runtime signature verifies in a new isolated GnuPG home:
VALIDSIG `570C77ACEA40C0F1B758902CBF96CCA56490F695`. Trust comes from the exact
user-pinned public-key bytes, not local Web-of-Trust certification. This is
verification of an upstream artifact, not Family Connect signing/publication.

An initial staging write fails before any asset is written: root with all
capabilities dropped cannot write the UID1000-owned staging directory. Only the
staging container UID is corrected to1000; subsequent exact downloads succeed.
This occurs before the package run and before its prerequisite receipt PASS.
The completed receipt and staged inputs are made read-only before building.

### One fresh package run and complete delivery

Unchanged `scripts.package_linux` runs once in offline Ubuntu26.04/Python3.14,
`--network none`, read-only clean source, fresh writable output,
`GOPROXY=off`, `GOTOOLCHAIN=local`, exact `/workspace` safe.directory. A private
external wrapper passes `--runtime-file` to the same appimagetool; no product,
verifier or package source changes. Embed/seal and AppImage construction complete;
the standard delivery manifest is emitted. Legacy is rebuilt from source: its
deterministic bytes happen to equal the previous legacy output, but are not copied.

- Internal version: `0.2.12~l03.2.10`, unsigned/unpublished.
- Candidate: `4264406722f6dd3efb83e9d9666e67180ce4f950333bb3e711bcbb4f5068b55a`.
- Source: `b8e9196d205c6810e02a642678517a4fc44b921b`; `source_dirty=false`.
- System source: `169aa687f497f8be690be5331879f994636135e1`.
- System build: `8ab7f298df10a89bcd116fbddaa8a23e37ff1581de3a456bb1cce69175ad9120`;
  `system_kind=standard-source-rebuild`.

| Artifact | Bytes | SHA256 |
| --- | --- | --- |
| FamilyConnect_0.2.12~l03.2.10_amd64.deb | 56,146,990 | `e1b9cb323c1bb6bc51ef06c08e0be91639cd25eabca3fe8b6b425657298d717c` |
| FamilyConnect-0.2.12~l03.2.10-x86_64.AppImage | 58,120,696 | `56a4a76db1e3571e90aeba374042f1f02a662fe3ef70333e0c5554fd7cbab6e3` |
| FamilyConnect-Linux-0.2.12~l03.2.10.tar.gz | 114,632 | `7cf31f40806d021b20cd24b12847874feed5b8c982844eb714dfe9d16de8b851` |
| FamilyConnect-MESH-system-amd64.tar.gz | 49,251,070 | `bea874702228b153a4ed6a5c5ecfebc3f47e5c46b64f4e5e8c7b22b91181448f` |

Fresh outputs are retained under ignored
`state-client-build/linux-l042-r2-offline-20261026/candidate/`; prior incomplete
outputs/evidence remain separate and unaccepted. Unchanged artifact verifier PASS:
762 user members, matching DEB/AppImage inventories, integration scripts, embedded
system and candidate IDs, exact artifact hashes, six-member legacy compatibility.
Construction is complete, but the candidate is **not package/live accepted**.

### Disposable package results and stop

All installed checks below use fresh offline Ubuntu26.04.1/systemd259/Python3.14
containers with separate network namespaces, no host bus/resolver/state mounts.
Real systemd/pkexec are exercised; no owner workstation installation occurs.

| Gate | Observed result |
| --- | --- |
| Complete system smoke | PASS: exact inventory/imports, root→UID IPC, real polkit, native AWG/Xray inventory, idle manual/Auto, ownership exclusion, sticky cleanup, failed-import rollback, changed-runtime rejection, state/network preservation |
| Exact DEB | PASS: user imports/GUI, no silent system setup/VPN, explicit pkexec setup/reinstall, READY, tampered embedded payload/missing manifest/mixed capability rejection, prepare-chat without VPN, one background D-Bus service, remove/reinstall preserves encrypted state/root runtime |
| Original AppImage | PASS: extraction/integration/launch, same matching system, READY, tamper/mixed guards, background owner and removal preservation |
| DEB/AppImage sharing | PASS in disposable package fixture: same UID/state/system, original image launch, no second setup |
| AWG pre-start fixture assertions | PASS: expected TRANSPORT_BUSY, terminal IDLE/generation2/pending=false, physical user lock free, cache preserved, successful starts0, root owner0/TUN0, network unchanged, root fixture released |
| AWG wrapper finalization | FAIL: shell reports `line 39: XIT: command not found`; outer gate chain exits1 |
| TCP package regression | NOT_RUN after stop |
| Exact .9 rollback and actual cross-version install gate | NOT_RUN; do not substitute synthetic mixed-capability or failed-import rollback results |
| Fresh cleanup32/native15/combined3/full desktop and remaining regressions | NOT_RUN after stop; earlier accepted results retained, not relabelled as this candidate's package gate |
| Installed live P0/P1/Auto/lifecycle | NOT_RUN; Phase C never entered |

The finalization error is caused by agent orchestration: while the AWG wrapper
was still executing, the agent edited that same private shell file to prepare a
later exact-.9 rollback mode. The active shell subsequently read a displaced
fragment of `EXIT` as `XIT`. This is a **test-harness/environment error**, not a
failure of the AWG protection assertions, runtime cleanup or sealed package bytes.
The later rollback helper was only prepared, never executed. No source/test patch,
package rebuild, gate replay or next profile follows this failure.

The existing cleanup trap removes the test container; subsequent Docker readback
finds no remaining containers with this run's namespace. The durable AWG receipt
already confirms zero owner/TUN, IDLE, no pending journal operation, unchanged
network and released root fixture. No cleanup is performed on host/client/server
resources. Logs, prerequisite receipt and complete delivery are retained locally.

Accepted source gate results remain cleanup32/native15/combined3/desktop1306 with
82 skips. Local36 and phase0/Docker54 exact historical ID comparisons remain the
accepted evidence below; there is no new full-suite run or new comparison claim.
Control/Client Linux dependency setup incompleteness is still infrastructure-only.
No overall CI PASS, suppression, xfail, test deletion or deselection is claimed.

Retained encrypted derived bases are not booted or modified. Original protected
seven files and historical .9/system remain byte-identical. Live first_reason,
cleanup_reason, process_contained, drain_acknowledged, attempt and generation are
**NOT_OBSERVED** in this continuation, not fabricated from the package pre-start
fixture. Chat delivery_unavailable stays untouched in L05 backlog. Owner workstation
**NOT_USED**; L05/messages/voice acceptance/signing/publication/teardown NOT_RUN.
Parent L04 remains IN_PROGRESS; Phase B requires review of this bounded stop.

Final documentation validation: secret scan, JSON parse,417 tracked local links,
four-file staged scope and `git diff --check` PASS. Pre-existing unrelated edits
are preserved and excluded. No generated artifact, private state or helper script
is staged; only STATUS/PLAN, documentation index and this report are committed.

## Reference advancement and package continuation — previous checkpoint

Input main `3ae2e3c0acf8f5cb1c3deaff9f1123ce435801e3`,26.10. Same L04.2-R2.
Review authorizes only three source-file pins and their provenance string in
`packaging/linux/system-reference.json`; accepted runtime169aa68 remains unchanged.
No new runtime/source checkpoint or PLAN ID is created. **Reference gate PASS;
L04.2-R2 PARTIAL; Phase B ENVIRONMENT_BLOCKED at AppImage runtime acquisition;
Phase C NOT_RUN. STOP. NEXT — final review L04.2-R2.**

Before editing, SHA256 is independently computed from `git show` of accepted
`169aa687f497f8be690be5331879f994636135e1` and actual members of the exact complete
system archive, then compared with its manifest. Both sources match the requested
new hashes for backend.py, mesh_chat_service.py and mesh_service.py, listed in the
previous package-failure table below. No hash is copied without this verification.

The only product-tree diff is four literal replacements: exactly those three
source_files SHA256 values and source_checkpoint, now exactly:

```text
L04.2-R2 source 169aa687f497f8be690be5331879f994636135e1 primary-cleanup-containment-drain
```

Strict old/new parsing confirms no duplicate keys, unchanged113-member source_files
key set/count, exactly three changed hashes, exactly one provenance change, and all
other reference bytes unchanged. Native digestcfcb7bae… and RNS digest66128235…
remain unchanged. No verifier, SYSTEM constant, runtime, dependency or toolchain
pin is changed; the whole reference is not regenerated.

Exact reusable archive: build8ab7f298df10a89bcd116fbddaa8a23e37ff1581de3a456bb1cce69175ad9120,
49,251,070 bytes, SHA256
`bea874702228b153a4ed6a5c5ecfebc3f47e5c46b64f4e5e8c7b22b91181448f`.
Regular-file/hash/root/native/RNS checks,759 unique regular members, uid/gid0,
no group/world-writable members and actual fixed-installer extraction/verification/
readback PASS. No system rebuild is required or performed.

Using the unchanged real `embed()` and fixed installer in disposable offline
Ubuntu26.04/Python3.14, the bounded reference harness records:

| Reference case | Result |
| --- | --- |
| Old reference + exact new archive | Exact source-contract rejection |
| New reference + exact new archive | PASS, matching build/ABI3.14 |
| New reference + separately mutated backend / mesh_chat_service / mesh_service | All three rejected |
| New reference + mutated unchanged mesh_network member | Rejected |
| New reference + exact historical .9 system | Rejected as source-contract mismatch |

Synthetic mutation archives are temporary copies with recomputed member/manifest
hashes, so these negatives exercise source pins rather than only an outer digest.
The real complete archive and historical .9 are never modified. Existing targeted
`test_linux_candidate.py` and `test_system_runtime.py`: **46 PASS**, no skips or
suppression. No additional source test is needed for this literal pin advancement;
the exact-archive positive/negative receipts remain local sanitized evidence.

Reference advancement commit
`70f33f66a3e52269f4f197c777565ae9ff6b15da` contains only the reference plus
STATUS/PLAN/this report, and is pushed separately before candidate build. Remote
main SHA is verified equal. Secret/JSON/link/scope/whitespace checks PASS; the
working product tree is clean. Continuation begins immediately without another
review pause, from a clean copy of this exact commit.

### Candidate embed/seal PASS; first packaging environment failure

The fresh Ubuntu26.04/Python3.14 candidate build reuses only the exact complete
system8ab7f298… archive. No system/native rebuild, incomplete prior candidate
assembly, old partial binary or .9 system member is used. Unchanged `embed()` now
passes; sealing records source_dirty=false, source_commit equal to the reference
commit and system_source_commit equal to accepted runtime169aa68. Verifier and
SYSTEM constant remain unchanged. Unrelated work is excluded from the clean copy.

| Identity/artifact | Exact value / status |
| --- | --- |
| Internal version | `0.2.12~l03.2.10`, incomplete delivery, not installed |
| Sealed user-bundle candidate ID | `5286116a5e75b913028bb0c7040fd0be6641a535283e1c09b2a3ed24166b120b` |
| source_commit | `70f33f66a3e52269f4f197c777565ae9ff6b15da` |
| system_source_commit | `169aa687f497f8be690be5331879f994636135e1` |
| source_dirty / system_kind | `false` / `standard-source-rebuild` |
| System build ID | `8ab7f298df10a89bcd116fbddaa8a23e37ff1581de3a456bb1cce69175ad9120` |
| System archive | 49,251,070 bytes; SHA256 `bea874702228b153a4ed6a5c5ecfebc3f47e5c46b64f4e5e8c7b22b91181448f` |
| DEB, built but NOT_ACCEPTED | 56,146,922 bytes; SHA256 `e2342b9fb5a53aa3a82ea6bcf1aaeb14a6e1e7c153abeab37476356e8ca74ad1` |
| Six-file legacy archive, shape compatibility only | 114,632 bytes; SHA256 `7cf31f40806d021b20cd24b12847874feed5b8c982844eb714dfe9d16de8b851` |
| AppImage | NOT_BUILT; size/SHA256 N/A |
| candidate-delivery.json | NOT_CREATED; no complete delivery inventory/acceptance |

After DEB and legacy creation, AppImage packaging stops with exit1. The existing
appimagetool (continuous854e19e/build313) attempts to download its separate type2
runtime; the offline builder has no supplied runtime file and no external network:

```text
package.appimage.runtime-fetch
Failed to download runtime: server returned status code 0
Failed to download runtime file ... pass it to appimagetool with --runtime-file
```

The agent omitted this offline packaging prerequisite. This is a **build-environment
packaging blocker**, not a recurrence of the reference mismatch or evidence of a
runtime/cleanup/VPN defect. Optional AppStream/GPG warnings are not the failure;
signing is not attempted or required here. No runtime download retry, online
fallback, package replay, source/verifier/pin fix or further gate is performed.
The incomplete outputs are retained as evidence, not an accepted candidate to
install or reuse automatically. The container is removed; no installed resources
need cleanup.

R1/R2 cleanup tests already running alongside the build complete **32 PASS**;
targeted reference/candidate/runtime46 PASS remains recorded above. Native15,
combined3, full desktop, MESH/admission/AWG/TCP package regressions, real systemd/
pkexec setup, imports/root→UID, candidate-check/READY, DEB/AppImage inventory/
coherence, reinstall/remove/.9 rollback and tampered/old/mixed/wrong-build gates
are **NOT_RUN in this continuation**. Prior accepted source/CI evidence is not
relabelled as package acceptance; no new full-suite comparison or overall CI PASS.

Phase C entry/P0/P1/Auto/lifecycle/AppImage sharing are **NOT_RUN**. No user Connect
or Disconnect, certificate renewal, chat registration or live diagnostic values
are produced. first_reason, cleanup_reason, process_contained, drain_acknowledged,
attempt, generation and owner/TUN counts remain unobserved for .10 live sessions.
The original seven protected files and .9 artifacts/system remain byte-identical;
retained encrypted snapshots are not booted or modified. No new identity/store,
invite, activation, grant, policy change, message, teardown or owner-workstation
operation occurs. Owner workstation **NOT_USED**; L05, signing/publication NOT_RUN.

Local receipts/source copy: `/var/tmp/fc-l042-r2-pins-20261026`. Incomplete .10
outputs: ignored `state-client-build/linux-l042-r2-pins-20261026/candidate`.
Earlier evidence and complete system archive are preserved. Final STATUS/PLAN/
report/index changes contain no generated artifacts or private state; secret scan,
JSON, links, staged scope and whitespace checks PASS. Existing public version,
download links and owner-use .9 status are unchanged. Unrelated work is preserved.

## Prior Phase B package source-contract stop — review accepted

Input main `9bfee698f1793e8fc7700a7438b6e7c244b31fb5`,26.10. Same L04.2-R2,
no new task ID, R3 or source checkpoint. Review accepts the previous namespace/
native-test PASS and Git VCS128 as an environment error; it authorizes one new
complete Phase B attempt, without reusing its partial binary or manifests.

**Result: L04.2-R2 PARTIAL; Phase B FAIL at candidate package source-contract
verification; Phase C NOT_RUN. STOP. NEXT — final review L04.2-R2.**

### Clean inputs and corrected builder

Product/runtime/test sources, locks, Go/Xray pins and accepted Android106
references remain byte-identical to accepted source
`169aa687f497f8be690be5331879f994636135e1`. Later commits change only CI evidence
workflows and documentation. The main worktree stays on current main; its unrelated
changes are preserved and excluded from the build through a clean, exact-current-
main local source copy. Its Git status is empty before and after the build.
An initial local hardlink clone cannot cross filesystems and exits before creating
the copy; copying objects with `--no-hardlinks` succeeds before any builder/test.

A new empty output directory is used. No previous partial binary, incomplete
manifest, .9 archive or .9 system member is an input. AWG/TCP inputs are freshly
extracted from the previously completed pinned Docker input images, not from
failed build directories or installed packages. Native module/compiler caches
are reused offline; the native delivery itself is rebuilt.

The builder retains `--network none --cap-add NET_ADMIN`, read-only `/workspace`,
fresh writable output, `GOPROXY=off` and `GOTOOLCHAIN=local`. Only the exact
`safe.directory` values `/workspace` and `/xray.git` are configured in disposable
container HOME; no wildcard or host Git configuration change. Dummy `fcbuild0`
is created with loopback up and brought up without an address, route or uplink;
dummy automatic IPv6 address generation remains disabled as in the accepted run.
Preflight confirms a distinct network namespace, interface count2, non-loopback
`fcbuild0` flags `up|broadcast|running`, zero dummy addresses and zero IPv4/IPv6
default routes. The bounded numeric-address external probe returns ENETUNREACH;
no resolver access is used. No host network metadata is printed or changed.

Ubuntu26.04.1/system Python3.14.4, all four exact locks,630 RECORD files across17
runtime distributions, pip check and Android106/native reference verification
PASS. Go1.26.0, Xray`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0` and patch SHA256
`eaeb30fd1e2aa52272d7f3a2a06bcad7b983ca9866a87fbd0a614eede6048872` are unchanged.

### Full native/RNS and new system build PASS

The unchanged standard native builder completes once, including its own
`go test -race -count=1 -mod=readonly ... ./...`, binary build, `go list -deps`,
licenses, dependency inventory and source/build manifests. Seven packages PASS:
automatic, chatipc, direct, materials, normal, platform and worker; the command
package has no tests. No separate duplicate test invocation, suppression,
deselection, xfail or source modification occurs.

`TestProtectionFailureNeverConnectsAndProtocolIsBounded` PASS includes the
unchanged assertions: protector invoked exactly once, protection denial returns
UNAVAILABLE, four malformed commands return DENIED without another protector
invocation. Binary build occurs after test PASS. Standard RNS delivery completes.
The native and RNS source digests match their unchanged reference pins.

The standard system packager completes with the newly built native/RNS delivery,
locked Python runtime and pinned normal-transport inputs. Its own native metadata,
source inventory, dependency notices, installer verification and archive extraction/
readback checks PASS. Additional read-only archive accounting confirms759 regular
members, uid/gid0 and no group/other-writable members. This is package construction
and integrity evidence, **not installed runtime or real pkexec acceptance**.

| Identity/artifact | Exact value |
| --- | --- |
| Accepted runtime source | `169aa687f497f8be690be5331879f994636135e1` |
| Build input main | `9bfee698f1793e8fc7700a7438b6e7c244b31fb5` |
| Native source digest | `cfcb7bae874765cfe6a66742fbeed55cb03399b7e32c13d5a5edcd212299df61` |
| RNS source digest | `66128235484f01b82bfd2e4ad604a486428706fc48020abbf84211554edef26e` |
| Fresh native binary | 29,017,971 bytes; SHA256 `5de514390105b5fab5fbf52238cdb5055d17c8fe37db7736d4cf263f5ade8dab` |
| New system build ID | `8ab7f298df10a89bcd116fbddaa8a23e37ff1581de3a456bb1cce69175ad9120` |
| New system archive | 49,251,070 bytes; SHA256 `bea874702228b153a4ed6a5c5ecfebc3f47e5c46b64f4e5e8c7b22b91181448f` |
| Requested candidate | `0.2.12~l03.2.10` NOT_BUILT; candidate ID N/A |
| DEB / AppImage / legacy | NOT_BUILT; sizes/SHA256 N/A |

The fresh binary has the same size but a different hash from the previous partial
binary. It was produced by this run, not copied or relabelled. New system ID differs
from historical .9 system43266d97…; neither archive is substituted for the other.

### First package failure: pinned system-source contract

One standard candidate build with `--standard-system-rebuild`, Ubuntu26.04 and
internal version0.2.12~l03.2.10 reaches `scripts/linux_candidate.py:embed` and exits1:

```text
candidate.embed/system-source-contract
ValueError: System sources differ from the pinned candidate contract
```

Read-only comparison localizes exactly three mismatches in the unchanged
`packaging/linux/system-reference.json`. Each actual system payload hash matches
both the clean source copy and accepted runtime commit169aa68:

| System member | Pinned SHA256 | Actual accepted-source SHA256 |
| --- | --- | --- |
| lib/backend.py | `7a39e76b5e725f232dfa3c28a586a2795f7fee87317b787087b97ec01a95233e` | `3805bdb290c39af3738fbe803bf5bc415e31c251196e5673cbcaea41c33e6157` |
| lib/mesh_chat_service.py | `d906207df0d9a1aade141890e2266adad8b09e717f9b777af782957d29d68637` | `8570fd3a26932b77ad1446073947747800e28d23811ae7eed42a669e4ddac00d` |
| lib/mesh_service.py | `540db319e9a2cff21fc6f13278bdb302df2154de764934d4ef85d8f06377faa6` | `277d6fe544b86a34da85bf1f37f2dc739faf8c4d5035a2efe14409ff3e6bf244` |

The candidate's pinned source contract has not been advanced to the already
accepted R1/R2 runtime bytes. The strict verifier rejects the mismatch as designed;
this is a **package integration gate failure**, not recurrence of the prior build
environment error or evidence of a live VPN/cleanup defect. No pin refresh, bypass,
source fix, package retry or next gate follows. R1 primary/cleanup preservation
and R2 containment/drain separation are unchanged. The partially assembled user
bundle is not sealed into a candidate and is not an installer or build input.

### Unreached gates, preservation and handoff

Real systemd/pkexec installation, installed imports/root→UID checks, candidate-check/
READY, DEB/AppImage coherence, reinstall/remove/.9 rollback, tampered/old/mixed-build
rejection, chat preparation and affected source/package regression reruns are
**NOT_RUN** after this first package STOP. Prior native15/cleanup32/combined3/
desktop1306 and exact local36/phase0-Docker54 baseline comparisons remain accepted
historical evidence, not rerun results. CI infrastructure observations remain
unchanged; no fresh full-suite failure-ID comparison or overall CI PASS is claimed.

Installed entry, P0, P1, Auto, lifecycle and AppImage shared-state gates are
**NOT_RUN**. No live first_reason, cleanup_reason, process_contained,
drain_acknowledged, attempt, generation or owner/TUN result is fabricated.
No old .9 P0 replay, chat delivery diagnosis, message or voice acceptance occurs.

Historical .9 artifacts/system and the original protected seven files are
byte-identical at entry and final audit. Retained encrypted derived snapshots are
not booted or modified; identity/store/cache/floors/settings are preserved. No
provisioning, certificate renewal, registration, policy change or teardown occurs.
Disposable builder/extraction containers are removed, no installed system or VPN
resources require cleanup. Owner workstation **NOT_USED**. L05, signing and
publication remain NOT_RUN; public VERSION/download links are unchanged.

Private receipts/logs/source copy are retained under
`/var/tmp/fc-l042-r2-safedir-20261026`; new system/native outputs and incomplete
candidate assembly remain ignored under
`state-client-build/linux-l042-r2-safedir-20261026`. Previous evidence is preserved.
Only the report, STATUS/PLAN and documentation index are staged. Secret scan,
JSON, links, staged scope and whitespace checks PASS; unrelated work is preserved.

## Prior Phase B isolated-namespace checkpoint — review accepted

Input main `601f6a7afb72f30711fe150f9e16a5422a302942`,26.10. Same L04.2-R2,
no new task ID or source checkpoint. Review accepts the previous missing-interface
observation as an environment precondition failure, not a protection assertion
failure. The one newly authorized standard native build is attempted below.

**Result: L04.2-R2 PARTIAL; Phase B ENVIRONMENT_BLOCKED at post-build dependency
inventory; Phase C NOT_RUN. STOP. NEXT — final review L04.2-R2.**

### Unchanged inputs and isolated preflight

Runtime source `169aa687f497f8be690be5331879f994636135e1` remains DONE / review
accepted. Read-only comparison through601f6a7 and the working tree confirms
byte-identical product/runtime/test sources, locks and pins. Subsequent commits
change only two CI receipt workflows and four documentation files. No checkout
back, cleanup repair, protocol/schema change or pin update occurs.

The fresh output directory is empty before this run; neither the previous failed
output nor .9 package/system members are build inputs. Existing pinned Go module
and compiler caches are reused offline. Ubuntu26.04.1/system Python3.14.4, all four
exact requirements locks,630 runtime RECORD files/17 distributions, pip check and
accepted Android106/native references PASS. Go remains1.26.0 and Xray remains
`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`; accepted patch SHA256 remains
`eaeb30fd1e2aa52272d7f3a2a06bcad7b983ca9866a87fbd0a614eede6048872`.
Native source digest remains
`cfcb7bae874765cfe6a66742fbeed55cb03399b7e32c13d5a5edcd212299df61`.

The disposable container uses `--network none --cap-add NET_ADMIN`, read-only
root/source and a temporary writable build output. No host networking, bridge,
privileged mode, physical interface or namespace peer is used. Before the standard
builder it brings loopback up, creates dummy `fcbuild0`, disables automatic IPv6
address generation on that dummy, and brings it up. No address, gateway, DNS or
default route is assigned. The separate read-only Go interface preflight reports:

```json
{"interface_count":2,"found":true,"synthetic_interface":"fcbuild0","flags":"up|broadcast|running"}
```

Namespace inode comparison confirms a different namespace from the host without
printing host metadata. Dummy address count0; IPv4/IPv6 default route count0.
A one-second numeric-address TCP probe fails with `ENETUNREACH`; no DNS lookup or
`/etc/resolv.conf` access is used for the probe. `GOPROXY=off` and
`GOTOOLCHAIN=local` enforce offline cached build inputs. External connectivity is
not available or required; the successful tests use their local fixtures.

### One standard native build: tests PASS, metadata environment failure

The unchanged `scripts.build_desktop_mesh` runs its own
`go test -race -count=1 -mod=readonly ... ./...` exactly once. No separate product
test invocation precedes or follows it. All seven tested packages PASS:
automatic, chatipc, direct, materials, normal, platform and worker; the command
package has no tests. No suppression, deselection, xfail or assertion change.

`TestProtectionFailureNeverConnectsAndProtocolIsBounded` now PASSes beyond its
interface precondition. Its unchanged assertions verify protector call count1,
UNAVAILABLE on protection denial and DENIED for four malformed commands; the
final count remains1, so malformed commands never reach the protector. This is
evidence from the full native test run, not a second test or an inferred bypass.
Counting correction to the previous receipt: that failed run had six passing
packages plus one failing direct package, not seven other passing packages.

Only after test PASS does `go build -buildvcs=false` produce `fc-mesh`.
The following `go list -deps` dependency/license inventory step exits1:
`error obtaining VCS status: exit status 128`. A bounded read-only diagnosis
confirms Git rejects the mounted `/workspace` repository as dubious ownership:
container root differs from its filesystem owner, and the agent configured
`safe.directory` for the Xray checkout but omitted `/workspace`.

This is an **agent build-environment configuration error**, not a native test,
product, cleanup, gateway or dependency-pin defect. It does not erase the native
test PASS, but the standard builder as a whole did not complete. No configuration
repair, builder replay, manual metadata completion or source change follows.
The diagnostic reads Git status and binary version only, not another build/test.
The disposable containers are removed; no installed service, VPN owner or TUN
is created. No host network setting is changed.

### IDs, incomplete artifact and unreached gates

| Output | Result |
| --- | --- |
| Accepted runtime source | `169aa687f497f8be690be5331879f994636135e1` |
| New standard native delivery | INCOMPLETE: dependency/license/build manifests not produced |
| Partial native binary, evidence only | 29,017,971 bytes; SHA256 `3f2909d63eeb329b86db861e1dea75b26570d9ca2aa7d6edc1b1272137bfc3e0` |
| New matching system build ID/archive/inventory | NOT_BUILT; ID/size/SHA256 N/A |
| Requested internal candidate `0.2.12~l03.2.10` | NOT_BUILT; candidate ID N/A |
| New DEB / AppImage / legacy archive | NOT_BUILT; sizes/SHA256 N/A |
| System/package imports, modes, polkit, root→UID, real systemd/pkexec setup | NOT_RUN |
| Reinstall/remove/.9 rollback, tampered/old/mixed rejection, candidate-check/status | NOT_RUN |
| Package MESH/admission/cleanup/AWG/TCP regressions and chat preparation | NOT_RUN |
| Installed entry / P0 / P1 / Auto / lifecycle / AppImage sharing | NOT_RUN |

The partial binary's read-only version metadata matches Go1.26.0,
android106-native105 and the source digest above. It is retained only as incomplete
build evidence, not accepted delivery or a subsequent build input. Native/RNS/system
and package completion must not be inferred from this binary.

Accepted source results remain native15, cleanup32, combined3, desktop1306/82skip,
and exact local36/phase0-Docker54 historical failure IDs. Those selections and
full suites are not rerun after the environment STOP; no new full-suite comparison
or overall CI PASS is claimed. Control timeout before pytest and Client Linux
dependency setup hang remain accepted infrastructure-incomplete observations,
not package evidence. No workflow timeout change or waiting for a hung CI job.

### State preservation and scope

Historical .9 candidate/system and all three artifact sizes/hashes are rechecked
against the unchanged [candidate manifest](2026-10-26-chat-ux-2/candidate-delivery.json).
Original protected seven files remain byte-identical. Retained encrypted derived
snapshots are not booted or modified. No identity/store/cache/floor/settings change,
certificate renewal, registration, provisioning or teardown occurs. No new live
first_reason, cleanup_reason, process_contained, drain_acknowledged, attempt,
generation or owner/TUN measurement exists: Phase C is NOT_RUN, not a zero-attempt
accepted session. Old .9 P0 is not repeated.

Private sanitized receipts/logs are retained under
`/var/tmp/fc-l042-r2-namespace-20261026`; incomplete generated output is ignored
under `state-client-build/linux-l042-r2-namespace-20261026`. Previous BLOCKED
evidence is preserved. Nothing from these directories is staged.

Owner workstation **NOT_USED**. L05/messages/voice acceptance, signing/publication,
Android106 changes and server policy changes **NOT_RUN**. Chat delivery_unavailable
remains uninvestigated L05 backlog, not a VPN gate. Parent L04 remains IN_PROGRESS;
L04.1 remains DONE. STATUS/PLAN retain the same L04.2 ID. Secret/JSON/link/staged-scope
and whitespace checks PASS; unrelated pre-existing work is preserved unstaged.

## Prior Phase B checkpoint — environment observation review accepted

Input main `0aec7a1324a5457a0936ff5219f988491367e4fd`,26.10.
The source correction at `169aa687f497f8be690be5331879f994636135e1` is **DONE /
review accepted in source scope**. Exact affected native15, cleanup32, combined3,
desktop1306 and unchanged local36/phase0-Docker54 residual IDs remain accepted.
The previous control setup timeout and Client Linux setup hang are infrastructure
incomplete observations, no longer progression blockers. No overall CI PASS,
workflow timeout change or new top-level PLAN ID is claimed.

**Result: L04.2-R2 PARTIAL; Phase B BLOCKED at native build-test environment;
Phase C NOT_RUN. STOP. NEXT — final review L04.2-R2.**

### Entry and exact inputs

Read-only Git comparison confirms that169aa68→0aec7a1 changes only the two CI
receipt workflows and documentation. Product/runtime, locks, native sources,
Android106 references and package source bytes are unchanged, including the
working tree. No checkout back to the runtime commit occurred.

The fresh disposable builder reports Ubuntu26.04.1 and system Python3.14.4.
All four exact requirements locks match installed distributions; runtime wheel
RECORD verification covers630 files/17 distributions; pip check and accepted
Android106/native-reference verification PASS. Go is pinned1.26.0; Xray remains
`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`, with unchanged accepted patch/reference
pins. Native source digest remains
`cfcb7bae874765cfe6a66742fbeed55cb03399b7e32c13d5a5edcd212299df61`.
No locked dependency was unavailable or updated.

Generated output starts in a new empty ignored directory. No .9 system archive
or package member is used as build input. AWG/TCP inputs were independently
obtained from the current committed pinned Docker recipes (Go1.26.1, including
normal build-cache reuse), not extracted from .9. Both input-image builds finish;
they are not a matching MESH system, candidate or package acceptance result.

### First affected test failure and stop

The agent launched the native builder with `--network none` without first
providing the non-loopback test interface. The unchanged standard build command
uses `go test -race -count=1 -mod=readonly ... ./...` before producing its binary.
It exits1 with exactly this test failure:

```text
github.com/Joker20380/family_connect/desktopbridge/direct
TestProtectionFailureNeverConnectsAndProtocolIsBounded
direct_test.go:182: test requires one up non-loopback interface
```

The test enumerates interfaces and exits at that explicit fixture precondition,
before invoking the protection assertion or attempting its synthetic destination.
The supplied network-none namespace does not satisfy the recipe. This is an
agent build-environment configuration error, **not evidence of a product,
gateway, certificate, cleanup or protocol defect**. Six other native test
packages pass; the command package has no tests. The failing test is not waived,
deleted, suppressed or counted as PASS, and is not added to the accepted
historical full-repository residual baseline.

The requested rule to stop if an affected/package test fails is applied here.
No native test replay, new candidate build, source patch, pin update or live
attempt follows. The parallel AWG/TCP input build had already completed; its
temporary extraction containers were removed. The native builder was `--rm`;
no installed system, service, VPN owner or TUN was created by this run.

Two earlier harness-only invocation errors are disclosed: the initial lock
auditor incorrectly matched across lines, then passed with line-wise parsing;
the local Docker legacy builder rejected an unsupported progress flag before
any build, then accepted the otherwise unchanged recipe without that flag.
Neither changes dependency pins, runtime code or test assertions. Unlike those
pre-test invocation corrections, the native test failure terminates Phase B.

### Unreached package/live gates and preserved state

Requested version **0.2.12~l03.2.10 NOT_BUILT**. The native output contains only
the failed test log; there is no new native binary, RNS delivery, matching system
manifest/build ID, candidate ID, DEB, AppImage or legacy archive. New artifact
sizes/hashes are therefore **N/A**, not inherited from .9. System source-reference
updates, inventory/imports/modes/polkit/root→UID checks, real systemd/pkexec setup,
tampered/old/mixed-build rejection, rollback to exact .9, candidate-check/status
and package regressions are **NOT_RUN**. Accepted source results are not relabelled
as new package results; the requested post-build full-suite comparison is NOT_RUN.

Installed entry, P0, P1, Auto, DNS/HTTPS, selected-next/active separation, refresh,
stale callback, lifecycle and AppImage sharing are **NOT_RUN**. No new first_reason,
cleanup_reason, process_contained, drain_acknowledged, attempt count or generation
was observed for a live session. Old .9 P0 was not repeated.

Historical .9 candidate/system/artifact hashes are rechecked against the unchanged
manifest. Original protected seven files remain byte-identical. Retained encrypted
derived snapshots are not booted or modified; no identity/store/cache/floor/settings
change, certificate renewal, registration, provisioning or teardown occurs.
Private continuation evidence is retained under
`/var/tmp/fc-l042-r2-package-20261026`; partial generated input output remains
ignored under `state-client-build/linux-l042-r2-20261026`.

Owner workstation **NOT_USED**. L05/messages/voice acceptance, Android106 changes,
wire/schema/policy changes, signing and publication **NOT_RUN**.
STATUS/PLAN retain the same L04.2 ID; parent L04 remains IN_PROGRESS.
Secret/JSON/link/staged-scope/whitespace checks PASS; unrelated pre-existing
working-tree changes remain unstaged and preserved. No installed rollback or
remote deployment is needed or performed.

## Prior source checkpoint — preserved evidence, now review accepted

Date: 2026-10-26. Same PLAN **L04.2**, no new top-level ID.
Input main `e3cc0348ad8ee87631b83f78b8f9618876f57138`;
R1 source `9c6f867ea3e866df6a0ce65dbd311e1882336bb0`.
**PARTIAL / STOP before package build: mandatory source verification BLOCKED.**
The two isolated product regressions are fixed and their exact selection passes.
Control CI exceeded its15-minute setup budget before pytest; its complete
failure-ID comparison is unavailable. This is not a new product failure finding
or a claim that the historical54-ID residual set grew. Client Linux CI was still
in dependency preparation at the stop readback. **NEXT — review L04.2-R2.**

The [R1 primary/cleanup correction](2026-10-26-linux-mesh-failure-preservation-l04-2-r1.md)
is retained. The accepted historical .9 live P0 failure is not repeated.
Owner workstation **NOT_USED**; no private state or live gateway in source tests.
Chat delivery_unavailable remains uninvestigated L05 backlog, not a VPN gate.

## Localization: both causes, separately evidenced

The exact CI selection (lifetime, terminal, status native), root/private network
namespace, FC_L021_WORKER and the same test-only native overlay recipe reproduce
**2 FAIL / 13 PASS** on R1. The original two tests and their8s joins/assertions
are unchanged. A read-only pytest observer records only lifecycle booleans,
relative monotonic timestamps, signal counts and return codes, never materials.

Times relative to cleanup_entered; each case has one stop RPC attempt:

| Observation | R1 cancel | R1 peer | Corrected cancel | Corrected peer |
| --- | --- | --- | --- | --- |
| cleanup_entered since test origin | 2345ms | 2352ms | 2318ms | 2331ms |
| stop timeout | 4004ms | 4003ms | 4004ms | 4004ms |
| terminate calls | 2 | 2 | 1 | 1 |
| kill calls by existing join boundary | 0 | 0 | 1 | 1 |
| watcher at8s join | alive | alive | finished at6020ms | finished at6020ms |
| failed / gate.active | false / true | false / true | true / true | true / true |
| process poll/returncode | running/null | running/null | -9 | -9 |
| reap / reader stopped / descriptors closed | no / yes / no | no / yes / no | yes / yes / yes | yes / yes / yes |
| stop acknowledged / cleaned observed | no / no | no / no | no / no | no / no |

**A:** the original assertions fail because the watcher has not finished within
the existing8s boundary: stop4s, terminate2s, duplicate terminate2s, then kill.
No timing assertion or join timeout is increased.

**B:** a separate controlled source red using real NativeWorker subprocess/IPC
and real ServiceOwner with an admission spy proves that R1 releases admission
after force containment without an acknowledged drain. Invalid/negative/EOF stop
replies do not raise CLEANUP_UNCONFIRMED on that old source. This is independent
of the8s observation; a later test-fixture teardown is not presented as native
proof at the original boundary. Corrected9-case old-red selection: **9 FAIL**.
Together these establish **C: both defects**, without attributing either to the
unlocalized historical live .9 Connect failure.

## Contract and scope

- Frozen, memoized internal NativeCleanup exposes process_contained,
  drain_acknowledged, cleanup_reason and admission_release_safe. No wire change.
- Containment requires reaped process, closed stdin/stdout/chat descriptor and
  stopped reader. Nonzero exit alone is not incomplete packet cleanup.
- A drain ACK requires the existing validated stop reply, ok=true and
  state=DISCONNECTED, plus no forced termination. Schema/ID reject booleans.
  EOF, malformed reply, ok=false, STOPPING, exit0 without ACK and forced exit
  cannot release authenticated admission.
- Existing Go ServeWithOwner sends the stop reply only after Server.Close waits
  for the packet lifecycle and chatOwner.Close drains ownership. That existing
  proof is sufficient; no Go, public IPC schema or network protocol modification.
- Stop RPC retains its4s deadline and graceful process exit retains its2s wait.
  There is at most one terminate and one kill, no duplicate initial wait. A7s
  shared cleanup budget bounds containment/reap/reader checks; no synchronization
  sleeps are introduced.
- PacketSession/Supervisor retain R1 first_reason, separate cleanup stage,
  all-stage binding/worker/detach cleanup, retry fencing and generation safety.
  Force-contained worker without drain ACK can still permit packet retry after
  confirmed network detach; no general stop-RPC-failed⇒CLEANUP_PENDING rollback.
- ServiceOwner invalidates current/binding, attempts worker containment even if
  binding close fails, and releases admission only for a strict safe result.
  Otherwise failed is sticky, gate/transport.lock remain chat-owned, new admission
  is OWNER_BUSY, no bootstrap/new worker occurs and close is CLEANUP_UNCONFIRMED.
  Retained admission does not keep a child, reader or descriptor alive.

## Source evidence and stop gate

Initial corrected focused selection: **237 PASS / 2 SKIP** (explicit native
artifact skips). Final added case also refuses forced exit after a valid reply.
Final R1/R2 cleanup selection: **32 PASS / 0 FAIL**, including that case.
Exact authenticated lifetime/terminal/status: **15 PASS / 0 FAIL**. Full desktop
with privileged disposable kernel and real GTK/Xvfb: **1306 PASS / 82 SKIP**.
Final combined/manual/Auto root→UID: **3 PASS / 78.90s**.
Runtime source commit `169aa687f497f8be690be5331879f994636135e1` is pushed and
remote main verified. Full local repository: **36 FAIL / 3387 PASS / 99 SKIP**,
7 passing subtests; all36 failure IDs exactly match CHAT-UX-2 and R1, zero new
failure/error IDs. No suppression, deselection or new xfail is used.

Automatic source CI: native bridge (including exact15/combined), AWG, TCP and
voice source jobs PASS. The evidence-only commit
`ca8c7108f2cc891379533355985554259c297ac4` is pushed/remote verified and does not
change runtime sources or test selections from169aa68. It adds narrow workflow
receipts retaining the full pytest command and nonzero pipeline exit, uploading
only source SHA, outcome, completion, summary and sorted failure/error IDs as
JSON. Both generators validate against the local36-ID log and an incomplete-log
case; pipefail preserves a synthetic nonzero exit17. Raw logs are not uploaded by
the new receipt step. No blanket CI or complete source-gate PASS is claimed.

| CI gate / exact run | Result at stop readback,18:40UTC |
| --- | --- |
| [Native bridge](https://github.com/Joker20380/family_connect/actions/runs/40374958486) | PASS, including exact authenticated15 and combined root→UID |
| [AWG](https://github.com/Joker20380/family_connect/actions/runs/40374958436) | PASS |
| [TCP](https://github.com/Joker20380/family_connect/actions/runs/40374958412) | PASS; publication jobs skipped |
| [Voice/encrypted source](https://github.com/Joker20380/family_connect/actions/runs/40374958304) | PASS, not L05/live voice acceptance |
| [Client Linux](https://github.com/Joker20380/family_connect/actions/runs/40374958403/job/121755378905) | IN_PROGRESS in Python3.12/dependency preparation; source/package steps not yet reached, not PASS |
| [phase0 full pytest](https://github.com/Joker20380/family_connect/actions/runs/40377384729/job/121764050147) | 54 FAIL / 3242 PASS / 226 SKIP,7 subtests; exact54 IDs match R1 retained CI baseline; no new IDs/errors |
| [phase0 Docker](https://github.com/Joker20380/family_connect/actions/runs/40377384729/job/121764049239) | 54 FAIL / 3240 PASS / 228 SKIP,7 subtests; exact54 IDs match R1 Docker; downstream failover not reached |
| [Control exact receipt](https://github.com/Joker20380/family_connect/actions/runs/40377384751/job/121764050127) | CANCELLED at Local HTTP contract proxy dependency setup; annotation: maximum execution time15m0s exceeded; pytest SKIPPED |

Control setup ran18:24:10–18:39:20UTC; the job finished18:39:24UTC. The retained
receipt has outcome=skipped, completed=false, summary=null. Empty failure/error
lists in that incomplete receipt are **not** zero-failure acceptance. The earlier
[169aa68 control run](https://github.com/Joker20380/family_connect/actions/runs/40374958594)
failed its full suite, but available truncated logs are not an exact54-ID proof.
No manual CI retry, timeout increase, apt workaround or source repair follows
this stop. Later asynchronous CI completion cannot retroactively authorize .10
build/live progression in this checkpoint.

### Exact residual-ID accounting

Local36 IDs match both the recorded CHAT-UX-2 and R1 lists. phase0 and Docker54
IDs match the full retained R1 Docker build log (artifact12670228037), not merely
its count. Each completed comparison has new_failure_ids=[], missing_failure_ids=[]
and error_ids=[]. Control comparison remains **NOT_PROVEN**, rather than borrowing
phase0's result. Affected cleanup/lifetime tests are absent from all completed
failure sets and separately pass the exact native selection.

Canonical sorted ID-list SHA256 (UTF-8 JSON with compact separators):

- Local36: `e8e3d06b12a79058aefbcd7c653627e7b71eeee5a20d9a8ed7751f316713f549`.
- R1/R2 CI54: `066830f3630ee7caa5ccd8d956c8861f13b459a7eca3ffd4b48bc03382bd5a60`.

Download/readback-verified sanitized evidence artifacts:

| Evidence | Artifact ID | ZIP SHA256 |
| --- | --- | --- |
| R1 Docker baseline | 12670228037 | `6b93e382aff386bfdfeaa99b71411633f902a542fb26b681b29c1073cc45a28c` |
| phase0 receipt | 12676791295 | `281afb35d88db5aeb5479287c870f307df0c4a0349634e87d28671e5d6b6edc5` |
| phase0 Docker | 12676921545 | `dd9631cffd5d1adcaaaac75505f2fa93cd6b64272aab4ac04e868518f1e4ef98` |
| Control incomplete receipt | 12677746129 | `8a5d7dd2fbaf2fd885dbf59b546771b284c00ab464c70c74ca982554a71bbcfb` |

The automatic internal-candidate preview rejects changed system source hashes
against the historical pinned candidate contract before sealing. Readback of
both R1 job121726914811 and R2 job121755378779 confirms the same rejection at
linux_candidate.embed, not a new pytest failure ID. Push CI built a temporary
preview system and passed its smoke, but no preview output is promoted or reused.
It is not the requested .10 build or acceptance; reference/inventory updates belong
to the gated new system/package phase, not a bypass of historical .9 integrity.

Fixture-only corrections are retained, not hidden: initial test import order and
unsafe temporary root-ownership fixture were corrected before the retained red
comparison; standalone tests use an admission spy while exact isolated tests keep
real root ownership/OWNER_BUSY. Two typed fake workers explicitly return the new
cleanup result. The combined observer initially discarded super().close's result;
it now returns it unchanged, without changing assertions, timing or product proof.
Initial non-privileged desktop skipped two TUN preflight tests; the final proper
kernel run exercises them. Fixture compilation first needed container Git
safe.directory and missing pinned Go dependencies; those were corrected without
changing source pins. The resulting fixture is never a release/system artifact.

Review policy: exact historical failure IDs may remain only with no additional
failure/error IDs and no suppression/xfail/deselection. This is not an overall
green-CI claim. The local reference is the36 IDs in
[CHAT-UX-2 validation](2026-10-26-chat-ux-2/validation.json) and R1; control/phase0/
Docker are compared to their corresponding recorded baseline, not local counts.

## Candidate, state and boundaries

Requested exact .10 candidate and matching system **NOT_BUILT**, IDs/hashes not
assigned. Package inventory/imports/setup/rollback/tampered/mixed/old-build/
coherence/AWG/TCP gates and new live P0/P1/Auto/lifecycle are **NOT_RUN**. The stop
is before Phase B, not a failed installed .10 scenario. No .10 DEB/AppImage or
system archive hash is fabricated; rollout/installed rollback are NOT_RUN.
The historical [exact .9 manifest](2026-10-26-chat-ux-2/candidate-delivery.json),
system and retained encrypted test bases are not modified or booted in this phase.
Old candidate `6f312d1e7c783ea42a39ca164d93d74b0ec4faf5bac53e24c12551cedd052a5b`
and system `43266d97c6a9f8d4e7026727cbb4b5cb6aeea49db799f93bd798b67a8135198c`
remain historical inputs, not R2 outputs. All three .9 artifact hashes/sizes and
the system archive hash match that manifest. Original protected seven files are
byte-identical; derived encrypted snapshots remain unbooted. No live Connect,
renewal, chat registration, identity creation or teardown receipt change occurred.
No identity/store/cache/floors/settings, provisioning, policy or underlay IPv6 edits.
No deployment, installed rollback, owner-workstation operation, Android106,
Windows/iOS acceptance, L05/messages/voice, signing, publication or teardown.
Private source evidence is retained under `/var/tmp/fc-l042-r2-20261026`.
It includes old/new timelines, full local log/ID comparisons, exact CI receipts
and archive digests; no materials or private fixture values enter the report.
Secret scan, JSON validation, local links, staged scope and git diff --check PASS.
Unrelated existing working-tree changes are preserved and excluded from commits.
L04.2 remains PARTIAL; parent L04 IN_PROGRESS, L04.1 DONE, L05 NOT_RUN and
L06/L07/L08 unchanged. **STOP. NEXT — review L04.2-R2.**
