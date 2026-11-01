# FLEET-BOOTSTRAP-2 — source/package handoff

## Second trial — READY reached, deadline guard correctly rejected

The900e185 pair passed fresh enrollment, encrypted delivery, verified retired-owner handoff
and stage on instance `fleet-rehearsal-nl-disposable-02`. MESH started without restarts and
created its0600 ready export. Local verification failed and rollback passed: the bounded
read-only observation records directory expiry1793577311 versus material deadline1793577309,
an actual2-second overflow, not an invalid OAuth token. No room URL or credentials are returned.

| Operation | Result | Private receipt SHA256 |
| --- | --- | --- |
| `host472-v2-enroll-a-b6a97c6d49a448aaa6ba42fb93209142` | PASS | `d8b70dfed360e04a5d2efdd62ab21572aacb8bb301de77ae673ab0b781876f3a` |
| `host472-v2-deliver-materials-a-143512e6c32843ee852b2687713e4735` | PASS | `65dff3359663cce4f9ae148e963cfce05b42242b1b9693605456401d35901574` |
| `host472-v2-stage-a-9b1da2f8b0c64d329f4ec4ff39f7625f` | PASS | `dfa098dab30b841e3c7c36d1b971c6a9bb0ba9d5ec30d15aaa6504ead8ea3274` |
| `host472-v2-start-verification-a-cda11e31b3ad4e54a128c9ff0ed95d8f` | FAIL / rollback PASS | `cdf020e8f8a9a95ff8094b20039d1318473459082b45260cf5965699318c5417` |
| `host472-v2-status-a-fbd0f12bf858467988382fe0b0bb03ed` | PASS / bounded expiry observation | `7a2d0601aee243216906258d920aca762bdc8cdedf39fecf8dba4a5cb6d1b780` |
| `host472-v2-drain-a-114ab38940c941a789132df4d32a60a3` | PASS | `e15bdd38ae6dada192c51834efbd50b47a796f62a486604bee1e0311239c6ab5` |
| `host472-v2-retire-a-d7df488f66ae4025949e34f679713602` | PASS / RETIRED | `6c16e172bde5347ff4ab612a682e217007c2658cd19d321ee64564a6e430f86f` |

The native duration began after configuration but previously consumed the entire remaining
permit window. Source now limits each service run to at most900 seconds, reserves240 seconds
when deriving a shorter run, and requires another120 seconds of material headroom on every
unit start. Near-expiry starts fail closed rather than extending the signed four-hour boundary.
No immutable deployed config or old package is edited. Fresh qualification/enrollment is required.

Review also identified missing boot restoration: the old preparation unit only checked a file,
while /run and nft state are volatile. A standard-library boot helper now verifies root-owned
metadata/validation hashes, exact activation pointer, firewall hash and dedicated sysctl file;
it restores only an absent owned table, verifies normalized readback and rejects existing drift.
Preparation creates only its dedicated /run parent and has CAP_NET_ADMIN/AF_NETLINK for this
job. MESH stays unprivileged. The qualification adds real namespace-local nft restore/coexistence
simulation, without claiming an actual host reboot or systemd start.

`reboot-verify --request-reboot` schedules one fixed delayed systemctl reboot only after ACTIVE,
fresh external acceptance and matching local health, with durable request binding before the
command. Same operation replay does not reschedule; a second request is rejected. Stop/drain/
retire cancels a pending same-boot timer. Post-boot verification requires changed boot/identity/
bundle checks and a fresh two-party acceptance cycle. No generic shell or bypass flag is added.
Safe failure receipts retain only a small allowlist of local failure codes, never exception text.
Both failed trial journals, signed packages and receipts are retained; the VPS is not destroyed.
Fresh source checks: fleet316 + console156 =472 PASS, paid170 PASS, Django check PASS and migration drift NONE.
Trial02 disposable operator AWG/TCP/MESH files were removed only after its signed retirement
receipt verified; original FLEET_MESH_PROBE_1 custody was not mounted during cleanup.
Production RU/NL/catalog/user/paid/phone state remains unchanged. Physical acceptance is NOT_RUN.

## Corrected pair requalified — frozen source900e185

Source `900e1859d5b4317e1faab2675425bed78ab85c12` is pushed and remote main verified.
Corrected A/B are built twice each with byte-identical archive, manifest, signature and SHA256
inventory. Their sole within-pair difference remains `metadata/revision.json`; exact natives,
ports, roles, secret slots and material schema are unchanged. Prior immutable A/B remain retained.
Public [requalification evidence](2026-11-01-fleet-bootstrap-2-netlink.receipt.json) contains
only safe hashes/results. Private archives/signatures/signing key remain ignored.

| Item | Corrected A | Corrected B |
| --- | --- | --- |
| ID | `gw-ff5a79a9e88250c16309ad88d9848707` | `gw-a74138aaf796264dcd1f5b4a9c7bb755` |
| Archive SHA256 | `33d86d2b475fe74a588c6f7045ddcd6ab88e49d33270a39ac1db0ea31aac010f` | `00159a4492fc512964dfba72f042117a00e72b822fb4eea80e7c168af3c40181` |
| Manifest SHA256 | `e7b9e8cc282217c7e387781b922ffe0c59a0c9771a0591b530a4c6f17b995aaa` | `aa89b0196e811368e1d61d60c190daeee9b7bb4b1abc3f1823a71d463efb4b91` |
| Signature-file SHA256 | `d01e0cca941c897b73bb4248125c23e6c1087361f48ce82801824834a8e93a33` | `aecb80572521dae145870cdc295fd5179cba9e12f21ac2c197a8b32c0a38f8fa` |

Signer fingerprint remains `d327d9fd0a3088c8b80ee00bc32ce5cd7f8ee61c6dbdd68d2bb292741a54daf6`.
New exact agent digest: `3c1da691e367431ded82d7251dee1bb1b096944f660b18412156913d9a23eee5`.
Permit/remote-agent source hashes remain unchanged; the archive binds the corrected modules.
Fresh full fleet295 + console156 =451PASS, paid/backend/package170PASS, Django check PASS,
migration drift NONE. Ubuntu24.04/x86_64 isolated qualification PASS: exact native paths,
systemd static checks, nft coexistence/rollback, material delivery, A/B pointer installation,
two-phase synthetic external receipts, injected B failure→A, B success, explicit rollback, retire.
This does not assert physical transport or reboot acceptance. Existing34 console static-path
warnings remain non-errors. Original FLEET_MESH_PROBE_1 custody is preserved; the retired
trial's three operator disposable client-material files were overwritten/unlinked after its
verified final retirement receipt. The VPS itself remains reserved, not deleted or reinstalled.

New physical enrollment/permit must bind this pair and a new instance, never rewrite the old
retired identity. Production writes/catalog publications/user invitations/paid events/phone
actions remain0. No second production server or catalog admission is claimed.

## MESH interface-discovery fix and safe trial retirement

The separate token is accepted by the official conference-create API (HTTP201). The exact
accepted native gateway was then exercised operator-side using fresh synthetic short-lived
profiles, not the approved private client probe: denying AF_NETLINK reproduces
`SEED_CONNECT / seed_join_failed`, no ready export, exit1; allowing it produces a valid ready
export and exit0/normal deadline cleanup. These bounded diagnostic sessions are not node
AWG/TCP/MESH acceptance. Their private receipts contain only typed safe outcomes.

The MESH systemd template incorrectly excluded AF_NETLINK, needed by interface discovery.
The source correction adds only that family to MESH; its capability bounding set stays empty.
AWG's existing permission is retained, and TCP/snapshot/monitoring gain no network families.
No native artifact, port, protocol, identity or material schema is changed. Old signed A/B
archives and target units were not overwritten; a newly frozen and qualified A/B pair is required.

The failed physical trial was drained and retired using its original signed runtime/permit:

| Operation | Result | Private receipt SHA256 |
| --- | --- | --- |
| `host472-drain-a-2743c71d5fb34f5aa879d5b53cff19cd` | PASS / DRAINING | `a46bc06cc2ba113fdcc86dbdf82eeb219e76619788f9a56f0f2558f94d0159ee` |
| `host472-retire-a-a67cc08af8bc46a8bf4d09d5221589fd` | PASS / RETIRED | `fd8a1e5ddf96ed4e10a8d7dfd925d585f45959eab6868503edf336cc1af80f14` |

Retirement removes only the failed trial's keys/materials/configuration/units/network state;
it does not delete/reinstall the VPS. Immutable releases and durable receipts remain. To
re-enroll a fresh instance with corrected packages, source now supports ownership handoff
only after verifying the predecessor's same-authority enrollment and same-node signed final
custody, same host/provider/region, unfenced RETIRED state and successful retirement journal,
and absence of keys, slots, active pointer, units, config, run directory, sysctl and owned nft
table. An exclusive root-owned owner lock serializes staging; old evidence is preserved and
its hashes are saved before the atomic owner update. No takeover of a failed/fenced/live owner
or replay of an old enrollment is allowed. Tests cover handoff, idempotency and rejection paths.

Focused runtime tests pass; full fleet295 + fresh isolated console156 =451PASS. Django check
PASS, migration drift NONE. This source transition awaits deterministic package rebuild and
Ubuntu qualification before new node writes; the paid170 rerun is pending. Production RU/NL/catalog/user/paid/phone
state is unchanged; the first NL remains untouched and the second VPS remains reserved.

## First physical A start — failure safely rolled back

Following the operator preflight correction, encrypted material delivery and stage A passed.
Fresh disposable AWG/TCP/MESH materials are bound to this instance, enrollment and A/B pair.
The approved FLEET_MESH_PROBE_1 identity was read only in operator custody; none of its private
bytes went to the node or Git. A separate test-account publisher request returned HTTP201;
no participant joined that diagnostic conference and no room URL/token was logged or published.
It proves the token's create permission, not transport acceptance or full provider integration.

| Operation | Result | Private receipt SHA256 |
| --- | --- | --- |
| `host472-deliver-materials-a-fbd8230614084af89f4bb8eb59a9f0ad` | PASS | `8b646d5697fdab7f137588d755977c18d5c919fd181a053d5d4c3c19108d0d4c` |
| `host472-stage-a-36856dcc31804c99938f778c620b38b6` | PASS | `cb3ba995f4f5b94ff5d85b873284acaccddd54f15251601469a9d09ed87cb650` |
| `host472-start-verification-a-1cd47db215f34c8289e1f661a1194506` | FAIL, rollback PASS | `09c72bd245aaba21231ba3320cce222948c89eb13d2d6eb31d6bc92460c9711b` |
| `host472-status-a-cc881105f501460ca53337612e22f214` | PASS, durable FAILED/unfenced | `0c05fa9c711fee5cafcd4d7bb85a2e2161c2e5daa138118b4d202df8866701c1` |

Configuration validation completed (Xray config-test, nft syntax, static systemd verification).
After rollback, MESH reports exit1/restarts3 and no ready export; AWG/TCP/prepare report
successful startup followed by stop. Snapshot was terminated. Current pointer is absent,
actual bundle null, A remains staged, accepted list empty, verification nonce absent.
These are local startup observations, not AWG/TCP/MESH external acceptance. No blind retry.

Operator status diagnostics now report bounded service/file metadata, including canonical
profile ownership/permissions and extended-metadata counts, without raw logs or secret reads.
The target profile is root:service0640 beneath root:service0750, with no extra inode flags or
extended attributes; ancestor ownership/modes match the canonical contract. Exact native
offline synthetic0600/0640 loading reaches SEED_RUN, then deliberately fails network access.
Physical MESH startup remains under investigation; no inferred success or invented root cause.
Focused35PASS and full fleet272PASS. Console156/paid170 remain the accepted prior results.
Frozen runtime/A/B/agent/signing authority unchanged. No production RU/NL writes, catalog
publications, user invitations, paid events or phone actions. Upgrade/reboot/retire pending.

## Operator preflight repair after private input

Owner supplied the separate publisher token through the hidden local helper. Custody mode0600
and the exact rehearsal input schema pass; provider validity is not yet claimed. A fresh
four-hour signed permit retains the frozen A/B, agent and signing-key binding, the accepted
single-host SSH pin and every production/user/catalog/paid exclusion.

Fresh host preflight passed. The following material-delivery attempt failed at its own
read-only preflight, before material generation or target mutation: the CLI intentionally
passes an empty port-absence list after enrollment, but the standalone probe rejected it.
The failed operation `host472-deliver-materials-a-6ea66c2b802c4a44bbe934f2f759a5b2` and its
private intent/receipt are retained. It is not an unknown remote mutation or a failed tunnel.

The operator probe now accepts that empty set while retaining strict port type/range/count
validation and every other host gate. The operator also obtains its target agent and receiver
from the signature-verified selected bundle, not the mutable operator checkout; missing,
changed or misbound sources/metadata fail closed. This preserves the original exact target
agent and enrolled A/B bindings while permitting an operator-only repair. No target runtime,
native artifact, material schema or signing key changes. There is no skip/force option.
Focused probe/remote29PASS; complete fleet266PASS. The accepted console156/paid170 results
are retained. Material generation/delivery and physical acceptance remain pending this
repair's source checkpoint; no production host, catalog, user or payment operation occurred.

## Owner-authorized node registration — 1 November18:47UTC

The owner requests completing this checkpoint and ultimately retaining two Amsterdam
servers. The working first NL server remains untouched; only the supplied new VPS is
authorized for rehearsal. No new PLAN ID, production identity or catalog admission was
created. Permanent second-server provisioning is not equivalent to a disposable rehearsal
and must not reuse its temporary keys. The reserved VPS will not be destroyed automatically.

A new one-hour, signed permit admitted only `preflight`, `enroll`, `status`, bound to the
exact target, owner-accepted SSH pin, frozen agent, bundle signer and A/B IDs. All production,
catalog, user and paid capability flags remain false. Provider/region are owner-supplied
`trainhosting`/`amsterdam`; independent provider identity and console verification are not
claimed. The existing known_hosts, target exclusions and second bundle verification were
used unchanged. The bootstrap installed only its guarded prerequisites/agent; no role started.

- Fresh host preflight PASS at18:43:03UTC.
- Enrollment PASS at18:44:59UTC, operation
  `host472-register-enroll-04b564f90f1248df8a1e870cb0a25e08`, elapsed101.415seconds.
- Separate node-local Ed25519 ownership and X25519 encryption-key proofs verified. Private
  node keys never left the target. Signed enrollment/material bindings remain in private
  custody; no real `FLEET_MESH_PROBE_1` private identity was opened or copied.
- Durable remote readback PASS at18:46:13UTC: both proof and commit completed successfully,
  no RUNNING/unknown operations, no fence, state `PREFLIGHTED`, staged releases empty,
  actual bundle null. Enrollment is recorded separately from the runtime's stage state.
- [Sanitized signed enrollment evidence](2026-11-01-fleet-bootstrap-2-host-enrollment.receipt.json)
  is ready for the append-only import path; no production Django database was touched.

The localized next-input gate is **DISPOSABLE_TELEMOST_PUBLISHER_INPUT_NOT_SUPPLIED**.
No separately supplied publisher material exists in this checkpoint's private input custody.
Reusing production OAuth or inventing a provider credential is not permitted. Material
delivery precedes staging in the accepted state machine; staging early would prevent normal
delivery, so no stage/start action was attempted. This is a live credential-input gate,
**not** a failed or missing source/package artifact. A/B and the exact agent remain unchanged.

The new operator-only [hidden input helper](../../scripts/fleet-rehearsal-publisher-input)
stores a separately acquired test token locally without argv/stdout/network exposure, rejects
unsafe custody/overwrite/echo fallback and never claims provider validity. The
[runbook](../fleet-bootstrap.md#private-publisher-input-and-retained-host-capacity) documents
separate OAuth consent and terminal input. No actual token was supplied during this run.
Focused helper15PASS; complete fleet252PASS (237existing+15new). Accepted console156 and
paid/backend/package170 results are retained, not rerun or represented as fresh runs for
this operator-only change. Source/runtime/bundle hashes remain the accepted frozen values.
Strict JSON, safe evidence signature/custody binding, exact agent hash and retained signed
A/B double-build equality PASS. Staged scope8files; public-source guard3340entries/0blocks;
5Markdown files/507links and `git diff --check` PASS. Unrelated local changes are excluded.

Next: owner supplies the separate OAuth input privately; then issue a fresh bounded mutation
permit, deliver materials and execute the existing two-phase physical gates. Services,
external AWG/TCP/MESH acceptance, upgrade/rollback, rehearsal reboot and retirement remain
NOT_RUN. Production RU/NL writes0, catalog publications0, user invitations0, paid events0,
phone actions0; Android109/sequence4/catalog4/paid108/entitlement/ledger1/4/cohort1/10/revenue0
are unchanged. Earlier OS-preparation text below records its own narrower authorization and
is historical, not a claim that registration remains unstarted.

**READY_FOR_FLEET_BOOTSTRAP_2_HOST**

All selected source/package gates PASS. This is not live-host or production acceptance.
Supported target: **Ubuntu24.04/x86_64**. At source/package qualification, no disposable
host had been supplied, no live permit/material had been generated and no VPS was contacted.
The later read-only host preflight is recorded separately below; it does not change source PASS.
The existing FLEET-BOOTSTRAP-2 remains open for its physical gates, with no new PLAN ID.

## Authorized disposable-host OS preparation — 1 November18:30UTC

**HOST_OS_PREPARATION_PASS.** After the initial unsupported-OS rejection, the owner explicitly
authorized preparing only the new disposable host and confirmed that the provider panel has
a Reinstall OS option. No provider reinstallation was performed. The approved work was the
official Ubuntu22.04→24.04 transition, not an upgrade to26.04 or a role deployment.

The separate, fixed-target private maintenance helper signs each bounded OS action under
`OWNER_AUTHORIZED_DISPOSABLE_OS_PREPARATION`; the existing fleet deployment permit, remote
agent, state machine, supported OS check and immutable A/B were not modified or bypassed to
install roles. Each action checks root, the accepted SSH fingerprint, actual target addresses,
production exclusions and absence of an installed Family Connect instance. Fixed stages have
root-owned journals/immutable scripts and exclusive per-operation logs; an uncertain launch
is reconciled, not blindly repeated. No generic live CLI or arbitrary inventory command exists.

- Before changes,49management-backup members were streamed into authenticated encrypted
  private custody and decrypted for readback. Private SSH keys were not included. Configs,
  backups, raw requests/logs, credentials and private signing keys remain outside Git.
- Jammy base packages and the official Noble transition completed; the upgrader offered24.04
  and the final observed OS is Ubuntu24.04/x86_64, kernel6.8.0-147-generic.
- Two actual OS reboots have distinct observed boot IDs and strict pinned key-only SSH after
  each. GRUB/initrd/virtio/ext4 prerequisites passed. These are OS boot checks, **not** proof of
  rehearsal service persistence: no role was installed or started.
- The first launcher response was uncertain after its systemd start wait timed out; the
  journal proved the unit was running, so it was not relaunched. Later, needrestart attempted
  to restart that unit; the existing-log guard rejected a replay. A clean dpkg audit and a
  separate base-reconciliation operation completed with list-only needrestart behavior.
- A pre-reboot check found no `/vmlinuz` alias and fenced that attempt before reboot. The
  actual `/boot/vmlinuz`, matching initrd/GRUB and driver configuration were verified before
  a separately identified successful reboot. Both failed/uncertain observations are retained.
- SSH temporarily refused connections while Noble packages were being configured. Bounded
  read-only observations recovered access with the same pin; no upgrade command was replayed.
- After the Noble reboot, the first new preflight correctly rejected missing DNS/HTTPS/time
  capabilities. The installed but inactive systemd-resolved service was enabled, time sync
  restarted, and final package checks completed. No replacement external DNS was invented.
- Final observed resources:2CPU,1919MiB RAM,42408MiB free under `/opt`; dpkg audit clean,
  no failed units and no pending reboot. SSH configuration and authorized_keys hashes match
  the encrypted pre-change backup exactly. Ordinary host DNS/HTTPS, NTP, TUN, AppArmor,
  systemd, nft-compatible backend and rehearsal port availability all PASS.
- At18:30:22UTC a **fresh signed preflight-only permit** passed the unchanged `RemoteInstaller`
  with the exact frozen agent and A/B binding. This is host qualification, not local role
  health, external VPN acceptance, `VERIFIED`, enrollment or activation.

[Sanitized OS-preparation receipt](2026-11-01-fleet-bootstrap-2-host-os-preparation.receipt.json)
binds the final private preflight, successful OS-operation observations and signed custody
receipt by hashes.44signed maintenance requests and the authenticated encrypted backup were
verified locally. Source/runtime tests were not rerun for this host-only/docs continuation;
the previously accepted393fleet/console and170paid/backend/package results remain unchanged.
Continuation validation PASS: strict JSON, custody/preflight hash binding, private file modes,
staged scope/privacy scan, unchanged frozen runtime, consistent current blocks,
4Markdown files/487local links, and staged/working-tree `git diff --check`.

Recovery remains provider-assisted repair or the owner-confirmed reinstall option if the
disposable OS becomes unusable; that would require renewed host-key acceptance and fresh
qualification, not a silent pin replacement. Reinstall availability is owner-reported, not a
tested provider-console session. SSH trust remains explicit owner-accepted TOFU, not an
independently verified provider identity. No role mutation permit, enrollment, transport
material delivery, probe identity access, catalog publication or automatic next task occurred.
Production RU/NL writes/user invitations/paid events/phone actions remain0. Next is a separately
authorized permit-bound role rehearsal within this same checkpoint, not automatic activation.

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
At this earlier preflight, the next gate was supported Ubuntu24.04 preparation and recovery
availability, followed by a fresh signed preflight. The later explicitly authorized OS work
above resolves the OS gate; it does not turn TOFU into independently verified provider identity.
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
