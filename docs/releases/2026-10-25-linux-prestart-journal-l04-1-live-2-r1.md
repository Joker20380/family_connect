# L04.1-LIVE-2-R1 — pre-start refusal terminalization,25.10.2026

**Final audit follow-up ACTIVE: immutable first failure across recovery; .4 rebuild.** Entry main
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

## CI / limits

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

STOP after final exact gates. NEXT — review L04.1-LIVE-2-R1.
