# L03.1 — Linux system/runtime component

Date: **2026-10-25**. Internal system/runtime checkpoint, **review pending**.
Only L03.1 is authorized; **STOP. NEXT — review L03.1**.

Entry branch: current `main`, `d7b4122`. Parallel uncommitted ops hunks in
STATUS/PLAN and `2026-10-24-vpn-health.md` are preserved, not part of this work.
D01.3/D01.3-R review accepted in the public completion/admission scope.
L01/L01-R, local L02/L02.2, D03/D04/D05 and native ownership/refcount/trust
boundaries remain accepted. D01 open; D02.1-R PARTIAL/NOT_RUN. The 54 full-suite
failures, former voice failures and Windows protocol failure on `b910edb` are
outside scope, not silently waived or repaired.

Parent L03 is not complete until L03.2 assembles and verifies the matching full
desktop artifacts after review of L03.1. No version/catalog/landing/signing or
server changes; no release or publication. Installed/live traffic, real grants,
activation and messaging remain L04/L05; migration L08 and visual L07 not started.

## Exact internal artifact

`FamilyConnect-MESH-system-amd64.tar.gz`, internal build **L03.1/build-7**;
not signed, not a desktop installer, not publicly distributed.

- Build/source ID: `1cadeee74b8877ded664b1b84e7f39539faaccdae3ba47d42b8ea9c8de496433`.
- Archive SHA256: `c21265ff36ed0b2f07e2e8762889bf0826e782250a75f032b9a14c93d994a858`.
- Size: **49,247,762 bytes**,759 regular archive members including the manifest.
- Manifest schema2 binds758 payload members, exact sizes/SHA256, architecture,
  signing status and native source digest; build ID covers all those fields.
  `installed.json` binds the actual fixed destinations/modes/bytes, including
  compatibility helper copies. Capabilities bind that installed manifest and ID.
- Local artifact/evidence: `state-client-build/linux-system-runtime-l031-20261025/`;
  working logs `/tmp/fc-l031/`. No raw evidence, state or binaries are in Git.
- Public versions remain Linux0.2.11 / Windows0.2.15 / Android106 reference;
  catalogs, signing workflow, landing, servers and installed workstation unchanged.

The packager's `delivery.json` deliberately retains `installed:false` and
`runtime_acceptance:NOT_RUN` from **build time**. The separate system-smoke receipt
records the subsequent disposable installation; this is not workstation rollout.

## Composition and provenance

The existing mesh packager/installer now deliver manual MESH + Auto; DIRECT and
service-only chat hosts/units; shared helpers/backend/ownership modules; the
unchanged desktop `update.pub`; standard native/RNS artifacts and notices.
System Python ABI for this artifact: **3.12, amd64**, verified on Ubuntu24.04,
systemd255. No source checkout, PYTHONPATH, user site or build venv supplies imports.
Production entrypoints reset interpreter paths before dependencies; service units
use `-I -S`; root helper `-I` also selects only packaged runtime/stdlib paths.

17 distributions /630 vendored members are verified against wheel RECORDs and
existing locks: RNS1.5.1, pyserial3.5, LXMF1.1.1, cryptography46.0.7, cffi2.1.1,
pycparser3.0, pydantic2.13.5, pydantic_core2.46.5, annotated-types0.8.0,
typing-inspection0.4.4, typing_extensions4.16.0, httpx0.28.1, httpcore1.0.9,
h11 0.16.0, anyio4.15.1, idna3.19, certifi2026.7.22. Their metadata/notices are
included, as are native Go/dependency licenses and Xray modification notice.

| Component | SHA256 |
|---|---|
| Standard `fc-mesh`,29,027,173 bytes | `a63cac0491887e6a2393a034442eb093f2e2b16ae140e710794eace3265eced8` |
| Isolated `fc-rns.pyz`,720,383 bytes | `61e7264459accc6a9a84ac18d11d19b5702cd537c718748d915e202540b0eeb2` |
| Packaged `update.pub`,45 bytes | `d0ae60e61af6ac5018428aaad89e362ec0f75d7468633a26c22906356228d281` |
| AWG3.1 engine | `e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f` |
| AWG tools | `906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278` |
| Adapted `awg-quick` | `9dcbd799b7906d5105a16a8363879df9e5099273ce7ff50aaec10f7c97c2001b` |
| Xray26.3.27,46,755,260 bytes | `4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940` |

Native is the existing **standard** `scripts/build_desktop_mesh.py --test` output,
whose complete source inventory still exactly matches current source:
`cfcb7bae874765cfe6a66742fbeed55cb03399b7e32c13d5a5edcd212299df61`.
Go1.26.1, empty build tags, local packet/IPC tests PASS; not a test-overlay worker.
Native ownership/refcounts, Android106 pins, schema and IPC limits are unchanged.
RNS rebuilt through the standard builder; source digest
`66128235484f01b82bfd2e4ad604a486428706fc48020abbf84211554edef26e`.

AWG uses existing `pilot/awg31/Dockerfile`, engine
`b5928efb6ca19f0153958460c3d141f04abc5c2e`, tools
`ee0f0a9aa34ff0a0da4b3433b9512781cfe02843`, with accepted patches.
The two existing install-time awg-quick adaptations are now one shared function,
not a second implementation; source and installed hashes are separately retained.
Xray comes from `pilot/tcp/Dockerfile`, revision
`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`, Go1.26.1, runtime26.3.27.
Both inputs were extracted from their existing standard build images, **not**
from workstation binaries. Pins/manifests/version readback are not an artifact
signature or a claim of independently reproducible base-image/APT bytes.

All normal binaries/helpers/notices, authorization markers, TCP unit and empty
root-owned configuration directories are installed by the same transaction,
including on a clean system. L03.2 receives a closed path, not instructions to
find developer binaries. Required OS packages: Python3.12, systemd254+,
systemd-resolved with resolvconf, iproute2, nftables, curl, procps, bash, polkit,
and `/dev/net/tun`. No host resolver reconfiguration is performed by the installer.

## Installation, activation and rollback boundaries

Installation holds the shared lifetime/startup exclusion exclusively, all existing
transport/runtime/command locks, MESH reservation/transport locks and extant
per-UID chat lifecycle locks. Sticky transport bytes are read, never truncated.
Live units/owners and pending journals fail closed. Persistent temporary masks of
only fixed templates also exclude **older** units lacking the new startup lock;
the second real unit-state check closes the pre-mask start window. Per-instance
units/drop-ins require separate review. There is no `stop` in the installer.

Regular/no-follow/bounded member checks, exact inventory, atomic writes, explicit
public directory modes independent of caller umask, file/directory fsync, and
root-owned own-file backups precede native/RNS/Python readback. Capabilities are
published last. Schema1 hosts, unchanged-native/mixed Python hosts, modified or
missing files and extra vendor members cannot advertise READY to the new client.

Explicit Chat settings → **Prepare protected chat access (no VPN)** reuses the
existing pipe-only polkit authorization. Only `chat/up/fcchat0` is accepted; UID
comes from pkexec, not GUI data. Only the fixed DIRECT/service-only units start.
No unit enablement, VPN intent/session, arbitrary command/endpoint/trust input or
background-setting change. Hosts are idle until bounded demand. Repeat setup
after reboot; ordinary user GUI/daemon behavior and delivery settings are retained.

Normal rollback: reinstall the previous reviewed complete component while idle,
under the same locks/barrier. `/var/backups/family-connect/mesh-bundle-*` has
`restore.json`, original bytes, modes and SHA256; `service-barrier-*` separately
records original templates (or absence), mode/hash and temporary-mask recovery.
After an interrupted process keep masks/journals and use that root-owned record
for operator recovery; do not delete ownership markers or force a connection down.
No public catalog rollback or server rollback is involved.

## Verification

[Reproducible fixture and commands](../../tests/fixtures/linux_system_runtime/README.md).
Actual package/system smoke uses an independently booted Ubuntu24.04/systemd255
container, private cgroup/PID/mount/net namespaces, D-Bus and resolver, loopback
only and no host service mounts. The system image has **no checkout or dev venv**.
Its temporary fixture polkit rule admits only UID1000's fixed installed helper;
this fixture rule is not in the shipped archive. No test trust switch is shipped.

- Extracted manifest/hash/member verification; `python -I -S` extracted and
  installed imports, crypto and packaged-anchor readback; actual native/RNS PASS.
- Actual `pkexec` from ordinary UID1000 through the existing session starts both
  installed chat units. Root/service-only hosts retain hardening/UMask0077;
  UID sockets are0600. UID1000 DIRECT probe succeeds; wrong root peer UID is
  rejected; service-only without materials is **unavailable**, not a fake success.
- Live owner refuses installation without changing either service PID. Held MESH
  ownership and sticky cleanup refuse installation; marker bytes are preserved.
- Real systemd start **and** direct executable start cannot enter a held install
  transaction; installation completes after release. No mock systemctl/readback.
- Separate negative bundle with invalid Python syntax fails real installed import
  readback; previous source, manifest and capabilities are restored. Synthetic
  identity/history/settings and unrelated safe files survive. Production payload
  is unchanged; the negative fixture is not a released/test-overlay worker.
- Capabilities reject changed size, changed hash, missing module, old schema with
  the same native, and extra vendor symlink; restoring exact bytes returns READY.
- AWG/Xray installed version readback PASS; TCP unit loads. Manual/Auto idle-start
  checks do not request VPN materials or a VPN session. Actual AWG/TCP/MESH traffic,
  registration, Telemost, P1 grants and installed message delivery remain L04/L05.

Local targeted packaging/installer/authorization/backend checks: **94 PASS**.
Desktop full suite with the standard native artifact: **1117 PASS /24 SKIP**
(before final directory/capability hardening, followed by the94 targeted checks).
Final exact archive **build-7 system smoke PASS**, including caller umask077 and
manual/Auto idle units: `system-smoke-7.log`, all listed checks and archive/normal-binary
metadata. Root backup in that disposable system was `mesh-bundle-udlkqwzz`.
`build-and-targeted-7.log` records94 PASS; `desktop-full-2.log` records1117/24.
Source CI is pending the source checkpoint push; no combined CI PASS claimed.

Initial failed attempts retained: first full desktop invocation lacked GI and
failed collection (fixed only by test-image dependencies); first smoke imported
the installer with bytecode generation and correctly failed the exact-member
check. Earlier package Xray exceeded the old40MiB limit; only its allowed path
now has a64MiB bound, total128MiB remains. These are not counted as successful gates.

Mandatory source desktop/native/root→UID/Auto/DIRECT and control/phase0/Docker CI
remain enabled. The prior54 full-suite failures and Windows/voice observations
are not hidden, repaired or reclassified as PASS. Parent L03 and full Linux
candidate remain incomplete; **STOP. NEXT — review L03.1**.
