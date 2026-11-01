# FLEET-BOOTSTRAP-2 — source/package handoff

**READY_FOR_FLEET_BOOTSTRAP_2_HOST**

All selected source/package gates PASS. This is not live-host or production acceptance.
Supported target: **Ubuntu24.04/x86_64**. At source/package qualification, no disposable
host had been supplied, no live permit/material had been generated and no VPS was contacted.
The later read-only host preflight is recorded separately below; it does not change source PASS.
The existing FLEET-BOOTSTRAP-2 remains open for its physical gates, with no new PLAN ID.

## Disposable-host access and preflight continuation

Owner supplied one disposable Netherlands host and explicitly chose the previous interactive
SSH public-key installation procedure after difficulty with the provider console. The owner
entered the password only in a local terminal and successfully installed one public key.
Host-key trust is **OWNER_INTERACTIVE_TOFU_ACCEPTED_PIN_MATCH**, not independent provider
verification. The accepted single-host known_hosts file is mode0600; no existing pin was
replaced, no password was collected, and no private SSH key was copied to the target.

One read-only preflight at2026-11-01T17:46:56Z used the existing `RemoteInstaller` and fixed
probe, strict host-key checking, key-only authentication and a separate private authority's
signed15-minute permit allowing **only `preflight`**. It binds this target, exact accepted
fingerprint, A/B IDs, agent ZIP and bundle signer. No mutation permit was issued. Operator
execution used the existing Ubuntu24.04 qualification image with pinned cryptography46.0.7;
only the selected SSH key, single-host pin, public bundle key, signed A and private output
directory were mounted, not product credentials or the bundle signing private key.

- Authenticated SSH: PASS, exit0, empty stderr; observed target address matches the permit.
- Host: Ubuntu22.04/x86_64, kernel5.15.0-46-generic,2CPU,1927MiB RAM,42892MiB free under `/opt`.
- TUN, synchronized time, resolver/HTTPS, systemd, AppArmor support and role-port availability: PASS.
- Firewall backend: iptables-nft; no pending reboot; no enrollment instance file observed.
- Preflight: **REJECTED / `unsupported_os`**. The supported baseline remains Ubuntu24.04;
  no guard, package, runtime, port or secret contract was changed to admit22.04 or26.04.
- Provider-console recovery: unverified; owner reported a console connection failure.
  IPv6 was not supplied or independently inventoried; this is not a claim that it is absent.
- Operator-installed packages, OS upgrades, service starts, enrollment and transport-material
  delivery: NOT_RUN. The only reported configuration change is the owner's prior SSH-key addition.

[Sanitized preflight receipt](2026-11-01-fleet-bootstrap-2-host-preflight.receipt.json) contains
the target digest, public provenance and safe observations, not the target address, credentials,
SSH-key contents or raw private permit. Full evidence and the separate authority key remain
in ignored private storage. This is not local role health or external data-plane acceptance.
Next within this checkpoint: prepare a supported Ubuntu24.04 host with a usable recovery path,
then issue a fresh bounded permit and rerun preflight. Do not automatically upgrade/reinstall
the OS, restart services or treat accepted TOFU as independently verified provider identity.
Source/package test counts and immutable A/B are unchanged; this continuation is documentation
and read-only observation only, not a new source/runtime test run or a physical acceptance PASS.
Continuation checks PASS: strict JSON and private-receipt binding, private file modes,
staged scope/privacy scan, consistent current blocks,4Markdown files/486local links,
and staged/working-tree `git diff --check`. Unrelated local changes remain unstaged.

## Source and immutable packages

- Continuation entry main: `1c1cd52b48f9aab008eb9cc52d8b634c2c484e4a`.
- Accepted foundation: `a3fc3bf1c11a686ea444ad36d576c05ac5e24810`.
- Superseded incomplete preparation: `39dcadb4d6a85b079c2deebb596453fc632fac9a`.
- Frozen deployable source: `0ecfefeaf907bd87e34e3e5356808c376aab082e` (pushed, remote main verified).
- Source commits and accepted evidence are retained; no history rewriting or release tag.
- Native-only v1 remains intact. [Deployable v2](../../fleet/inventory/deployable-gateway-v2.json)
  preserves exact AWG engine/tools, Xray and canonical gateway artifact/source/license bindings.
- Exact282-file canonical MESH capsule reverified. No FLEET_MESH_PROBE_1 private identity
  was opened, copied or included. Monitoring is new bound standard-library source, not an
  observed unbound binary. Its exact unchanged source was introduced in4f73a5a.

| Artifact | A | B |
| --- | --- | --- |
| Bundle ID | `gw-f93d6eb5613b913cb29f2ba168765e77` | `gw-215af561736b8c73b072085c31ffba70` |
| Archive SHA256 | `ecf24da19723822edff315f03e65f8665b3a2b85809b1b914fca8a23ceacacd3` | `46a0c4891fece4b00e604e893ad7a45a68f33b35e3602cd8dc619392a4c5d1ca` |
| Manifest SHA256 | `68d8b5a3f2032dbc13487d86009b99bd3f9f5d40ec49919230535207a03e7d63` | `39e197c0a37cb54658790a9a53c0a5bce61a046b345b5094cc6b6ca7e351c77f` |
| Signature-file SHA256 | `8693042420d380d06226d007a48d6ede12a5b4ef3ca44f74158dca397886c14f` | `9418c7ee807994bc1c1a461b15d6f41d4ba9f65e7b8f21f3fc4a871f69b3fc58` |
| SHA256-inventory SHA256 | `f5b9969f408e652fb9ace607458074252185eda34fba5236d537502a603791f1` | `41f0fb8301cff99d85be1ad9e2698145f8501470c63af0a32f867addbd11259e` |

Each bundle was built twice and verified independently: archive, manifest, signature and
SHA256 inventory are byte-identical per bundle. A/B differ **only** in
`metadata/revision.json` (explicit revision/monitoring marker). Native binaries, transport
contracts, role identities, ports and material/slot schema are identical.

Bundle signer public-key SHA256: `d327d9fd0a3088c8b80ee00bc32ce5cd7f8ee61c6dbdd68d2bb292741a54daf6`.
This is a fresh private rehearsal signer outside Git, not the public synthetic seed or
product release key. Archives, signatures, source capsules and private key remain in
ignored private artifact storage. Earlier be31646/102d2aa/a6ba912 private builds are
superseded preparation attempts and must not be selected for the host handoff.

Permit source SHA256: `47b1dfe7ee90221a452a762595ce9017e5d4c51e8ddd1195238cc567ff9eaacc`.
Agent source SHA256: `04e43c21631434ff32286345bb94b7c038e2d27e45058d08ee945b9246f071dd`.
Exact deployed agent ZIP SHA256: `0d5db7baae392254678af14c055f9a99cec837efc052dc219b13e7bfde773bc1`.
The permit must bind the latter ZIP digest and this exact bundle signer fingerprint.

## Implemented boundaries

- Admitted: awg, tcp, mesh, profile-reader, publisher, snapshot, monitoring, load-monitor.
- Explicitly disabled: mailbox/chat-services; production renewal/restricted-sync;
  production registry/control-plane database. Disabled roles are explicit health-contract
  exclusions, not unimplemented admitted roles.
- Root operation boundary; immutable versioned releases and fsynced atomic current pointer;
  separate configuration/state/secrets; retained predecessor; exact service users/modes,
  argv/capabilities/limits and absolute permit-expiry service/timer. Strict umask077 covered.
- Owned nftables table only, syntax checked, no global flush; exact predecessor rollback;
  dedicated sysctl file and previous forwarding restoration. Foreign tables/files/interfaces
  are not adopted or deleted. Unknown outcomes are reconciled by durable operation binding.
- Separate node-generated X25519 material key, signed enrollment binding, X25519/HKDF/AEAD
  envelope, signed authority, instance/host/A+B/key/expiry binding and one-time nonce.
  Secrets never enter bundle, argv, safe receipts, journal or Django. Pinned offline wheels:
  cryptography46.0.7/cffi2.1.1/pycparser3.0 for target CPython3.12.
- Local health checks exact native process/argv, listeners, AWG server/peer/address/MTU,
  profile signatures/floor/CRL/expiry/directory, restart counts, firewall/sysctl and resources.
  It explicitly cannot assert external data-plane PASS.
- Durable start-verification → AWAITING_EXTERNAL_ACCEPTANCE → complete-verification → VERIFIED.
  Operator receipt binds unpredictable post-start nonce and current local-health digest;
  signed <=300-second lifetime, replay/forgery/drift rejection; activate-local requires VERIFIED.
- Operator AWG/TCP and newly source-bound MESH probe, no user/payment API. The MESH probe
  rebuild is byte-identical and binds egress to the later permit target, not production IP.
- Append-only sanitized evidence imports, idempotency/conflict checks and DB UPDATE/DELETE
  triggers; Russian dashboard covers bundles/state/operations/health/duration/rollback/reboot/retire.
  Web requests have no SSH, signing or material-decryption authority.

## Qualification results

| Gate | Final result |
| --- | --- |
| Full fleet suite, pinned Ubuntu24.04 container |237 PASS |
| Full console suite, isolated PostgreSQL/control lockfile image |156 PASS |
| Combined console/fleet |393 PASS,0 failures/errors |
| Existing paid/backend/package regression, control + identity locks |170 PASS |
| Django system check / migration drift | PASS / NONE |
| A and B each built twice, all four files compared | PASS |
| Target receiver and agent bundle reverification, both bundles | PASS |
| Native four help/version paths and exact Xray config-test | PASS |
| Systemd static verification, dedicated account and0600/0640 ownership | PASS |
| nft syntax, neighbor coexistence, predecessor restore and owned cleanup | PASS |
| Synthetic envelope delivery and real versioned fake-root layout | PASS |
| Two-phase synthetic receipts; B failure→A; B success; explicit rollback; retirement | PASS |
| Strict JSON, privacy/secret scan, staged scope, whitespace | PASS |
| Markdown links | PASS in committed task scope |

There are34 existing console warnings for the absent test static directory; no test errors.
Console and fleet are full runs in their respective pinned isolated environments, not a
claim that unrelated platform/release/physical suites ran. Unrelated pre-existing working
changes remain unstaged, including a historical STATUS link with a missing anchor in an
untracked report; that unrelated feed is not part of the committed handoff link gate.

Isolated qualification image:
`sha256:3fe0baf04e0df8629100edabfd9e532a780867e7df7333f54cba81f63f1f7b74`.
The [Dockerfile](../../scripts/fleet-rehearsal.Dockerfile) pins Ubuntu's base digest. Runs used
network-none, namespace-local NET_ADMIN, read-only source/package mounts, no private signer
or identity custody mount. [Qualification harness](../../scripts/qualify-fleet-rehearsal.py)
source SHA256: `bdf6ac4f13edaf80029cdc2e53ed9d21c03cdc13d47bce74ce6666ed0ccda208`.
The full safe result is embedded in the [receipt](2026-11-01-fleet-bootstrap-2.receipt.json).

The first container attempt exposed an ordinary nft fixture formatting error and strict
umask directory mismatch; both were localized, fixed and requalified. They are not retained
as blockers or hidden physical failures. Cache reuse requires the exact public source,
patch, compiler and two previously reproduced operator binary hashes; it is not reuse of
an unbound observed monitoring/runtime binary.

## Operator commands and remaining physical gates

Ready: `prepare`, `plan`, `preflight`, `enroll`, `deliver-materials`, `stage`,
`start-verification`, `run-acceptance`, `complete-verification`, `activate-local`, `status`,
`upgrade`, `rollback`, `reboot-verify`, `drain`, `retire` through
[`scripts/fleet-rehearsal`](../../scripts/fleet-rehearsal). See the [runbook](../fleet-bootstrap.md)
for required permit/pins, custody paths, envelope creation, evidence export/import and recovery.

**NOT_RUN:** real systemd service start, AWG handshake/DNS/HTTPS/egress, TCP tunnel/auth/egress,
MESH Telemost room/join/READY/registration/Family TLS/DNS/four HTTPS streams/egress/cleanup,
live upgrade/rollback, reboot persistence and live retirement. Their timings are NOT_MEASURED.
Source/container qualification does not substitute for those signed two-party host receipts.
A source push is not installation, public distribution, catalog publication or production rollout.

Live rollback path: stop the attempted B, atomically restore accepted A and its config/owned
firewall, run local health; final external acceptance remains a distinct receipt. A failed
rollback/retirement fences mutations; provider-console recovery/disposal must not bypass it.
Drain/retire delete only owned disposable material after a final custody receipt; retained
read-only releases are nonsecret. SSD/COW/snapshot forensic erasure requires provider disposal.

## Unchanged production and private host inputs

Production RU/NL writes0; catalog publications0; user invitations0; paid events0; phone actions0.
Public Android109, Android sequence4, gateway catalog4, paid baseline108, owner entitlement,
ledger1/4, cohort1/10 and revenue0 are unchanged by this work. No product version or installer
was rebuilt/released. No FLEET-ACTIVATION-1 or other queued task starts automatically.

The original host-input checklist was: disposable VPS IPv4; SSH user; provider; region; independently verified
`SHA256:` host-key fingerprint; accepted single-host known_hosts path; SSH key path or
confirmed SSH-agent context; provider console availability; VPS resources; optional IPv6.
No password in chat. The continuation above records supplied inputs and their trust limitations;
it does not authorize deployment or waive unsupported-OS and recovery gates.
