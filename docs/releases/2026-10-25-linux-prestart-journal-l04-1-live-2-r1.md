# L04.1-LIVE-2-R1 — pre-start refusal terminalization,25.10.2026

**CHECKPOINT: final .4 source/system/package PASS; review pending; live NOT_RUN.** Entry main
`403b22f25722252633c8ca4c5c8cb80f4f0a3395`; affected product source
`57f8eff8b291062d69248ac46413f8c9fc0f561d`.

LIVE-2 PARTIAL/review accepted; Gate A PASS retained for historical exact
0.2.12~l03.2.2/candidate d9c0d07f… only. One helper up request is permitted;
the defect is persistent APPLYING/pending after authoritative pre-start refusal.
RETEST DONE/review accepted; parent L04.1 IN_PROGRESS.

Plan: actual FriendsApplication/control journal/session/fixed-helper red AWG/TCP
in offline disposable systemd; strict pre-start/unknown outcome contract;
same-owner terminalization/recovery and sanitized diagnostics; regression gates;
new system/runtime and user candidate if root protocol/modules change.
No rebuild/patch of historical candidate. FC-3YSQ-BE2D/nl private state and gateways
are not used. Live B1 retest, B2–F, L04.2/L05 and device teardown NOT_RUN.

## Deterministic red — actual installed AWG and TCP

Separate offline Ubuntu24.04/systemd255 root containers, exact historical DEB/setup,
real polkit/session/fixed helper/transport flock. Synthetic local Device Identity
and verified public catalog vector only; no protected state, external network or fetch.
[Sanitized red](2026-10-25-linux-prestart-journal-l04-1-live-2-r1.red.json).

Both: one up request, zero transport starts/owners/TUN, unchanged network. First
authorization failure: BackendError `VPN operation failed`; TCP driver changes this
to `All VPN transports failed`. First rollback exception: ValueError
`invalid application recovery metadata`. Actual normal inventory includes virtual
`fcmesh0`; snapshot persists it, but rollback's normal-profile validator rejects it.
Journal stays APPLYING, generation1/pending true; physical locks free after fixture
release. No IDLE write or finish occurs after the rejection. Initial IDLE recover's
no-op finish is recorded separately. This reproduces the lifecycle defect rather
than inferring it from the GUI's generic waiting label.

The reproduction fixture's first attempt could not export the invalid journal via
its own strict `_read`; read-only raw phase projection repaired that fixture only.
Final AWG and TCP reproductions each use a fresh container and one Connect.

## Source correction checkpoint

Authorization session v2 has strict schema2 replies: OK, PRE_START_REJECTED
(TRANSPORT_BUSY/OWNER_CONFLICT), OUTCOME_UNKNOWN (HELPER_FAILED/HELPER_TIMEOUT).
Only fixed AWG/TCP up plus reserved helper exit78 and a strict schema1 root receipt
can prove pre-start rejection. EOF/malformed/unknown replies remain unknown;
exception text or a free physical lock never proves cleanup.

Normal snapshots exclude inactive virtual MESH/Auto identifiers, including recovery
of the old persisted baseline. Confirmed rejection removes only the operation's
unpaired, UID-owned inactive import using fixed `discard`, writes IDLE, then finishes
the same lease: generation0→1 reserve→2 finish, pending null. No retry/fallback.
Unknown outcome keeps APPLYING/generation1/pending; only same-owner recovery sends
bounded down even when TUN is absent, then checks/discards the inactive profile.
Unconfirmed cleanup retains pending. Primary and cleanup exceptions are kept
separately; expired leases cannot finish later generations. GUI diagnostics retain
bounded category/phase/outcome/cleanup/generation/pending, not profiles or endpoints.

Targeted ownership/Friends/auth pipes/diagnostics/GTK poll suite: **126 PASS**.
Intermediate full desktop runs exposed stale v1 fixtures and a new GTK test which
asserted before the idle render; these test-contract issues are corrected, not xfailed.
Mandatory full/actual-root/system/package gates remain in progress at this source
checkpoint. System build-9 is NOT reused: root helpers, backend and authorization
protocol changed. New internal version reserved: **0.2.12~l03.2.3**; public VERSION,
catalogs and historical .2 artifacts unchanged.

Source `ddbf880e4ce5488700aa633c28e2fdffd3a61971` pushed/remote verified.
Full desktop + Friends + Linux chat selections: **1178 PASS/96 SKIP** in the
locked Python3.12 test image with real GTK/Xvfb. Additional fixed-discard security
cases (wrong owner, paired, active/malformed marker, mode/link/hardlink) plus auth
suite: **44 PASS**. The root-gate wrapper explicitly forwards only its public
namespace assertion across its sanitized environment; no credentials are forwarded.
New exact system build `b8140c68…` real offline systemd255 smoke **PASS**:
native/RNS/import readback, actual polkit/root→UID, owner/sticky/start barrier,
real import-readback failure/rollback, unchanged synthetic user state/network.
Desktop pair/actual pre-start gates and CI results follow separately.

Intermediate AWG CI `40216532502/121238763466` exposed the existing isolated
gateway test's raw `ready:1`/`ok` assertions after the protocol change. The fixture
now checks exact v2 OK/unknown envelopes, preserving cross-UID and forbidden-action
denial. No transport implementation, candidate bytes or trust boundary changes in
that test-only correction. Source native/root→UID/Auto/DIRECT isolated job
`40216532591/121238763585` PASS, including both protocol OS jobs.

## Exact internal candidate — not published

Product/root correction source: `ddbf880e4ce5488700aa633c28e2fdffd3a61971`.
Built clean source: `285de3eac39e01185d8a7fafb9c9f2d6d3c80090` (`source_dirty=false`).
Later test/docs-only commits do not change these candidate bytes.
Path: `state-client-build/linux-prestart-journal-l041r1-20261025/build-1/`.
Internal version **0.2.12~l03.2.3**; source/public Linux VERSION remains **0.2.11**.
Candidate ID: `7d00cce0353c04810083f24b0bdf25992f363f0da24353c6efe9a214f1af00bc`.
Runtime contract2 / authorization2 / Python3.12; exact user inventory707 members.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `FamilyConnect-0.2.12~l03.2.3-x86_64.AppImage` |57932280|`8e24354a878e489b4a96b89af5f9cad8ad36bac855acfc7b7c8b3eb196ef2c77`|
| `FamilyConnect_0.2.12~l03.2.3_amd64.deb` |55986174|`b9ea83d6a0d84f104eb06fffc64648a369df7da5dae020022765016b86aa2ccb`|
| Legacy six-file `FamilyConnect-Linux-0.2.12~l03.2.3.tar.gz` |114475|`63c4a8802e15b8b7b4a3200963a14a4a96dc832c535f05f1cbee9fd5675a0a7c`|

New system/runtime `system-build-1`:
- build ID `b8140c68e42f78506cd64c8c254c4db76cef14789bdeda471214e8348bf91c1c`;
- archive49250908 bytes, SHA256 `df5ddf2b7a8c6a10295a7358ba515ee2204b6ed6e32b5e0cc4239fd3faf5b7c7`;
- installer SHA256 `ce9acb1f363b0fafffb11c44097901a7871c28fbf0e6b9c2c5c3eaba9ef7bfb5`;
- 758 payload members,759 archive files including manifest; exact member set unchanged.
Only five system member hashes differ from build-9: `compat/awg-helper.py`,
`compat/tcp-helper.py`, `install.py`, `lib/auto_platform.py`, `lib/backend.py`.
This is **not build-9**. Native remains standard untagged artifact, binary SHA256
`a63cac0491887e6a2393a034442eb093f2e2b16ae140e710794eace3265eced8`,301 source entries,
source digest `cfcb7bae874765cfe6a66742fbeed55cb03399b7e32c13d5a5edcd212299df61`.
Its bytes/notices were recovered and verified from the exact accepted build-9 archive;
no developer/overlay worker. Standard RNS rebuild is byte-identical, archive SHA256
`61e7264459accc6a9a84ac18d11d19b5702cd537c718748d915e202540b0eeb2`.
AWG uses the existing pinned3.1 Docker-builder output; Xray26.3.27/d2758a0/go1.26.1
is the verified retained standard artifact. All other system hashes, Python closure,
public anchor, pins, licenses and protocol schemas are unchanged.

## Actual installed green / package gates

[Sanitized machine-readable evidence](2026-10-25-linux-prestart-journal-l04-1-live-2-r1.green.json).
Fresh Ubuntu24.04/systemd255 offline root containers; private network/cgroup/PID,
D-Bus/resolver, real polkit/pkexec, systemd units and native/RNS readback. No host
bus/resolver mounts, no protected test identity or gateway. Xvfb/cairo flags are
fixture-only. Every container is stopped/removed after its gate.

- AWG and TCP separately: actual FriendsApplication, durable control owner, real
  authorization session/fixed helper and root flock; import1/up1/discard1,
  successful starts0/owner0/TUN0. First error remains typed TRANSPORT_BUSY;
  cleanup failure **none**. Rollback→IDLE write→same lease finish execute.
  generation0→1→2/pending null, later poll PASS, idempotent recover unchanged2.
  One local verified-fixture fetch, no HTTP/configuration replay; cache preserved.
- Exact system gate PASS: imports under `-I`, real root→UID acceptance/wrong-UID
  refusal, idle units/no VPN, live owner/sticky refusal, exclusion throughout install,
  actual failed-import readback→rollback, tamper refusal, synthetic state preservation.
- Exact DEB and original AppImage PASS: inventory/ABI/import/GUI, explicit real
  pkexec setup/reinstall, exact READY, no silent VPN, user D-Bus/background owner,
  removal/integration, synthetic encrypted history/settings retained. AppImage owner
  reopens original image. Both formats also checked with the **same UID/HOME and
  already-installed system**: matching candidate-check/READY, no second root setup.
- Actual retained exact build-9 installed separately: new client reports
  **RUNTIME_INCOMPLETE**, not READY; explicit matching setup restores READY.
  This is distinct from manifest/schema/member tamper tests, which also PASS.

Unknown pipe/timeout and partial-start cleanup failure are separate targeted tests,
not claimed as installed live B2–F. They retain APPLYING/pending until proven
same-owner rollback; foreign/expired leases cannot finish. No unconditional finish.
Artifact/setup readback never uses mock-success. The first old-build fixture attempt
created Python bytecode while importing its verifier; inventory correctly rejected
that extra file. The fixture now disables bytecode, and a fresh container passes;
no installed product file was patched to obtain PASS.

Build tooling attempts missing git/file or offline AppImage runtime download were
not accepted artifacts. A stale native input and already-adapted AWG quick input
were rejected by existing integrity checks; checks were not relaxed. Final build
uses the verified standard inputs above. Appimagetool SHA256
`95cbe7cce9717fce90c484e34052ee7c7f1d7635b33c12525b4776826a7d29b6`;
only its public GitHub runtime download used builder networking. All installed gates
were offline; original .1/.2 artifacts remain immutable.

Rollback/removal remains explicit matching root reinstall only while idle/cleanup
confirmed; root-owned backups retained. User uninstall preserves identity/history/
settings and independent root runtime; units are not silently enabled. No L08 claim.

## Intermediate .3 CI / limits

Client Linux `40216881690/121239898896` PASS; TCP `40216881704/121239821034` PASS;
fixed AWG `40217060322/121240380205` PASS. Native/root→UID/Auto/DIRECT receipt above.
Phase0 `40216881715/121239821629`: **3163 PASS/55 FAIL/156 SKIP**, errors0;
Docker full-suite build `40216881715/121239821424`: **3162 PASS/54 FAIL/158 SKIP**.
The additional observed readiness-adapter local-port `Address already in use`
failure is reported, not fixed or hidden. Existing residual54/voice/Windows
observations remain separate; current voice run passed, not a historical resolution.
CI standard-source package `40216881734/121239821448` **PASS**, including new actual
AWG/TCP root-lock terminalization gates. Final local full selection after the added
discard security cases: **1194 PASS/96 SKIP**. Control CI is still in its apt/local
HTTP prerequisite step; no control-suite result is inferred from phase0.
No combined CI PASS. Local exact package acceptance is not transferred to CI's
different standard-rebuild IDs or to historical artifacts.

Test-only follow-up `762ffae1728342f35a46f724cb7ad229670b189a` pushed/remote verified.
Completed logical source and evidence changes use ordinary main pushes; staged
allowlist excludes parallel VPN ops hunks/reports and all ignored state/artifacts.

L04/L04.1 IN_PROGRESS. Live B1 retest, B2–F, LIVE-2 completion, L04.2, L05,
physical-network recovery, cross-format upgrade and device teardown/revoke **NOT_RUN**.
Original protected identity/assignment, server policy/registry/catalog/signing,
public release and workstation network/services were not used or changed.

## Final audit — same-generation diagnostic recovery

Before stopping, a separate audit found that a recovery error after restart could
overwrite the persisted first failure category within the same generation. The
collector now keeps the first bounded operation diagnostic immutable for that
generation; a later generation can replace it. New restart/cleanup regression plus
diagnostics/Friends selection: **41 PASS**. This does not clear pending or authorize
cleanup. Because backend is also installed system code, a **new system-build-2**
and internal **0.2.12~l03.2.4** are required; .3 and its green evidence above remain
immutable intermediate artifacts, not the final retest candidate. Exact gates will
be repeated, not transferred. Control285de3e job ended cancelled in apt prerequisites;
its full suite is NOT_RUN, not PASS.

## Final exact .4 checkpoint

Final product/system source and build input:
`053c4e5f9532ca927f49a78f9c0ed17903375baf` (clean main, ordinary push/remote verified).
The diagnostic regression was also run against the actual prior backend from
`285de3e`: **1 deterministic failure** (CHANNEL_LOST replaced by HELPER_FAILED),
then **41 PASS** on corrected source. No installed files were patched.

| Identity/artifact | Exact value |
| --- | --- |
| Internal version | `0.2.12~l03.2.4` |
| Candidate ID | `42ea0699263f2527057a36082b2b95235c4ac452cc5e86eed6ec15ebd50898cf` |
| AppImage | `FamilyConnect-0.2.12~l03.2.4-x86_64.AppImage`,57928184 bytes |
| AppImage SHA256 | `c78c68ec99b187269b87d40d457c8db09d3593b45f199a8705d0a83222cc3273` |
| DEB | `FamilyConnect_0.2.12~l03.2.4_amd64.deb`,55986866 bytes |
| DEB SHA256 | `8b23ac6d93c747955017a3b0d5c33745e7272f2c24fc950f4e8f0d0b367af4da` |
| Legacy six-file archive | `FamilyConnect-Linux-0.2.12~l03.2.4.tar.gz`,114462 bytes |
| Legacy SHA256 | `106f09e2ff7bc31b2a2eff64a5b4c157ded7a76ea6e4d037ad5cdb513803ffaa` |
| New system-build-2 | `8d7d78ec06fc897fa7e94d21f208b08b31d6c6c3e33eaad19a262705117c8f9d` |
| System archive | 49250848 bytes, SHA256 `ddd74c2132a76ac833b587d9df6409d779ce6afcdaa45fafd23faa86d7817726` |
| System installer SHA256 | `ce9acb1f363b0fafffb11c44097901a7871c28fbf0e6b9c2c5c3eaba9ef7bfb5` |
| Contract | runtime2, capabilities schema2, authorization2, Python3.12, user707/system759 archive members |

Final files are under ignored
`state-client-build/linux-prestart-journal-l041r1-20261025/build-2/`, with system
archive in sibling `system-build-2/`. Source VERSION/public remains0.2.11;
.4 is built and installed only in disposable acceptance containers, unsigned and
unpublished. .3/build-1 and historical .2 remain unchanged, not final candidates.

[Exact .4 sanitized evidence](2026-10-25-linux-prestart-journal-l04-1-live-2-r1.final.json)
is freshly collected, not copied from .3:

- Inventory/hash/member/isolated import verification PASS: both exact formats,
  707 user members, 759 system archive members, legacy exactly6. No checkout/dev
  dependencies or private state in the payload.
- Separate AWG/TCP real root-lock sessions each PASS: actual FriendsApplication,
  control journal, polkit/session/fixed helper; import1/up1/discard1, start0,
  owner0/TUN0, TRANSPORT_BUSY preserved, cleanup exception none. IDLE generation2,
  pending null; read-only poll and same-owner repeated recover PASS without replay.
- New exact system smoke PASS: isolated/installed imports, native/RNS readback,
  actual root↔UID/wrong-UID rejection, idle units, install exclusion/live-owner/sticky
  preservation, actual import-readback failure rollback and tamper rejection.
- Exact DEB install/reinstall/remove and original AppImage integration/GUI/setup/
  removal PASS with real pkexec/systemd255. Same UID/HOME and matching installed
  system in both formats PASS; background user owner survives GUI exit; no silent
  VPN, second setup or dangling FUSE dependency. Synthetic state retained.
- Retained exact old build-9 actually installed: new client is RUNTIME_INCOMPLETE,
  not READY; explicit exact .4 embedded setup restores READY. Separate embedded/
  installed tamper checks PASS. No old-build evidence relabelled as .4.
- Final full desktop plus Friends/Linux chat: **1195 PASS/96 SKIP**. All local
  installed gates used fresh Ubuntu24.04/systemd255 containers with private D-Bus,
  resolver/network/cgroup, `--network none`; no host service/network mutation.

All task gate containers are stopped/removed after each run. Synthetic fixtures
only; protected identity/assignment and gateways never accessed. Same explicit
rollback/removal boundaries above apply to .4. This is source/package acceptance,
not installed live B1 retest, B2–F or L04.1 completion.

## Final source CI

All following jobs target exact source `053c4e5`; CI standard rebuild has its own
artifact identities, not the local .4 hashes above.

| Gate | Run/job | Result |
| --- | --- | --- |
| Client Linux | [40218252850/121243988256](https://github.com/Joker20380/family_connect/actions/runs/40218252850/job/121243988256) | PASS |
| AWG | [40218252802/121243987783](https://github.com/Joker20380/family_connect/actions/runs/40218252802/job/121243987783) | PASS |
| TCP | [40218252840/121243987868](https://github.com/Joker20380/family_connect/actions/runs/40218252840/job/121243987868) | PASS; release jobs skipped |
| Standard system/package + actual pre-start AWG/TCP | [40218252828/121243987827](https://github.com/Joker20380/family_connect/actions/runs/40218252828/job/121243987827) | PASS |
| Native protocol Linux/Windows | [40218252889](https://github.com/Joker20380/family_connect/actions/runs/40218252889),121243988079/121243988114 | PASS |
| Isolated root→UID/Auto/DIRECT | [40218252889/121243987856](https://github.com/Joker20380/family_connect/actions/runs/40218252889/job/121243987856); [rerun121246025793](https://github.com/Joker20380/family_connect/actions/runs/40218252889/job/121246025793) | First attempt FAIL at DIRECT underlay `AssertionError: fallback used`; one unchanged diagnostic rerun PASS |
| Control full suite | [40218252902/121244048760](https://github.com/Joker20380/family_connect/actions/runs/40218252902/job/121244048760) | 3165 PASS/54 FAIL/156 SKIP |
| Phase0 full suite | [40218252842/121243987751](https://github.com/Joker20380/family_connect/actions/runs/40218252842/job/121243987751) | 3165 PASS/54 FAIL/156 SKIP |
| Docker full suite | [40218252842/121243987858](https://github.com/Joker20380/family_connect/actions/runs/40218252842/job/121243987858) | 3164 PASS/53 FAIL/158 SKIP |

All three full suites actually ran, with errors0 and7 subtests passed; no disabled
assertions or xfails. D01 residual failures remain open, including observed local
readiness adapter port collision in control/phase0; no unrelated repair. Voice job
121243988131 passed, but historical voice/Windows observations are not declared fixed.

The first isolated-native artifact12608780747 records Auto kernel **18 checks PASS**
and combined manual/Auto/terminal **3 PASS**, but the DIRECT JSON is empty because
the final DIRECT request used its forbidden fallback. Cause is not established;
do not label the whole job PASS or transfer ddbf880's earlier PASS. Exactly one
unchanged rerun of that failed job completed **PASS**, including the final fixed
protected DIRECT isolated-kernel step, at exact same source053c4e5. First failure
remains evidence; a single successful rerun does not establish or repair its cause.
No further retry, product/candidate change or trust relaxation accompanied it.

Final evidence checkpoint `21e46df1d3db271f73b33b22f3fe3cf2670f1af7` was pushed
normally and remote main matched; this documentation continuation records only
the completed CI receipt, not new product bytes. Staged allowlist/local links/JSON,
whitespace and secret-pattern scan of staged files and this task's Git history PASS;
public-source guard2920 index entries/0 blocked. Parallel ops changes remain outside
the commits. Final artifact hashes and historical .2 hashes rechecked unchanged;
all task systemd containers removed. No protected state/operator receipt in Git.

Overall CI is not green. Source/system/package checkpoint is ready for review;
live B1 retest, B2–F and the parent L04.1 completion remain NOT_RUN/open.
STOP.
NEXT — review L04.1-LIVE-2-R1.
