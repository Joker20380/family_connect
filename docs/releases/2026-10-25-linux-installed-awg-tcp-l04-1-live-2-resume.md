# L04.1-LIVE-2-RESUME — installed negative acceptance,25.10.2026

**PARTIAL — B1 terminalization PASS; full entry gate blocked by changed server
baseline. B2–F NOT_RUN.** No new product defect established. Entry main
`88c98f7c03f52b5f845a29819b0ccccb5484fd7d`; R1 DONE/review accepted only in
source/system/package scope. .2 B1 failure remains historical. Gate A for exact .4
is inherited from [R1](2026-10-25-linux-prestart-journal-l04-1-live-2-r1.md), not repeated.
B1 was first and the only user Connect. Its local installed lifecycle satisfies the
corrected contract, but the required unchanged-server invariant is not established;
this is not a complete B1/LIVE-2 PASS. No second Connect or later scenario was attempted.

## Immutable input / read-only preflight

Source `053c4e5f9532ca927f49a78f9c0ed17903375baf`, internal `0.2.12~l03.2.4`,
candidate `42ea0699263f2527057a36082b2b95235c4ac452cc5e86eed6ec15ebd50898cf`.
Only `state-client-build/linux-prestart-journal-l041r1-20261025/build-2/`.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `FamilyConnect-0.2.12~l03.2.4-x86_64.AppImage` | 57928184 | `c78c68ec99b187269b87d40d457c8db09d3593b45f199a8705d0a83222cc3273` |
| `FamilyConnect_0.2.12~l03.2.4_amd64.deb` | 55986866 | `8b23ac6d93c747955017a3b0d5c33745e7272f2c24fc950f4e8f0d0b367af4da` |
| Embedded system archive | 49250848 | `ddd74c2132a76ac833b587d9df6409d779ce6afcdaa45fafd23faa86d7817726` |
| Legacy six-file tar.gz | 114462 | `106f09e2ff7bc31b2a2eff64a5b4c157ded7a76ea6e4d037ad5cdb513803ffaa` |

System build `8d7d78ec06fc897fa7e94d21f208b08b31d6c6c3e33eaad19a262705117c8f9d`.
Fresh standard extracted verifier PASS: exact artifacts/candidate,707 user members,
embedded system identity and unchanged six-file legacy shape. The network-disabled
container is only an artifact verifier, not a substitute for installed KVM gates.

Existing protected-state preflight PASS: UID1000,0700/0600, `create=False`,
Support ID **FC-3YSQ-BE2D**, public fingerprint
`d07d33a81728ff70aec350ae59785990c194d90ecd44574b0da28439189532de`, only verified nl
AWG/TCP cache and signed floor. Source state remains outside Git and unmodified;
only `home/` entered the guest, never operator/teardown material.
Read-only server baseline: AWG DB/live1/1, Xray persisted/runtime1/1, RU0/0.
No manual configuration fetch, issuance, activation, provisioning or operator server
mutation. One product Connect was allowed its ordinary idempotent nl fetch.

## Environment / installed baseline

New real KVM: Ubuntu24.04.5, kernel6.8.0-147-generic,
systemd255.4-1ubuntu8.18, QEMU7.2.22,2CPU/4GiB, encrypted qcow2. The container
only launches QEMU with `/dev/kvm`; VPN services run inside the independent guest
kernel. Real NetworkManager, resolved, TUN, nftables/iptables/iproute2, D-Bus,
Secret Service and polkit; SLIRP/loopback SSH. No host network/service modification.

Exact DEB installed; original AppImage copied but not launched (F2 NOT_RUN).
UID1000 GUI before setup reports absent system runtime. Settings → Install system
component → Install → real polkit password approval produces exact matching READY.
No allow-all polkit rule or root GUI. Root inspection via guest sudo is fixture work,
not substituted authorization. Setup creates no VPN intent, transport or TUN.
Installed Python3.12 `-I -S`, exact packaged modules and `create=False` verify the
same Support ID/fingerprint, only nl cache, signed catalog/floor and state hashes
before/after setup, reboot and B1. HOME `/home/tester` and consistent XDG roots;
copied identity directories0700/files0600, no links/special files.

Before any Connect, the first clone failed networking because the fixture netplan
named the wrong interface. Fixed only cloud-init/netplan fixture, verified real
NetworkManager connectivity and powered off a clean encrypted base. A new B1 clone
boots that base. Product/candidate/installed files were not patched. Guest SSH host
key regeneration was pinned against its private QEMU serial console, not accepted
blindly. No test action occurred in the failed networking fixture.

## B1 — corrected local terminalization PASS

Clean initial journal absent/IDLE, generation0, pending null. Separate root fixture
holds the real root-owned0600 `/run/family-connect-transport.lock` with `flock`.
At **18:34:12UTC**, one AT-SPI GUI **Connect** on Netherlands/AWG; one real polkit
approval. No helper CLI connect, installed hook, retry or second click.

Root execve audit (`lost=0`) observes **AWG import1/up1/discard1/down0**, TCP requests0,
transport starts0. The imported inactive profile is removed by product discard.
No AWG/Xray owner/process, TUN, route/rule/firewall/DNS mutation or active/cleanup
marker. GUI returns **VPN is off**, selected-next AWG, actual none.

Installed sanitized diagnostics:

```json
{"category":"TRANSPORT_BUSY","phase":"IDLE","outcome":"PRE_START_REJECTED","cleanup_confirmed":true,"generation":2,"pending":false}
```

`first_failure=TRANSPORT_BUSY`, not NONE. Observed generation **0 → 2**; intermediate1
is the accepted reserve/finish contract, not a separately sampled live observation.
No manual generation/journal write. After fixture release both physical locks FREE;
actual read-only backend poll returns active=false/generation2/active_count0.
Exact candidate imports/inventory and installed READY rechecked after the action.
No TCP/Auto/MESH fallback observed. Identity/settings/cache/floors remain byte-equal.

One GUI request and one up are proven; independent server HTTP fetch-count evidence
is **NOT_VERIFIED**: a bounded20s read-only journal query timed out. It is not reported
as proof of zero replay. No manual fetch was used to fill this gap.

## Server invariant — blocker, not a product failure

Initial server baseline at **18:17:53UTC** and post-B1 readback agree on:

- Existing target AWG DB/live1/1 and Xray persisted/runtime1/1; same address/bindings.
- Foreign DB/live peer and persisted/runtime client hashes unchanged; RU0/0.
- NL gateway AWG/TCP service PID/invocation hash unchanged.
- Registry active, signed source archive/catalog and foreign registry hashes unchanged.
- NL server.json/global configuration, address/route/rule and immutable file hashes unchanged.

However, registry `family-connect-friends-http-candidate.service` properties hash
changes from `ab3f3f68b1c45f71ea61228045041f4ec41131f51ff7c081435903382cd9ebaf`
to `9d17484adaff8dffee88c276c1849c3ebb5b95f581e376b8b375d5d9a843141c`.
Read-only `systemctl show` reports current start **18:28:22UTC**, before the B1 click;
three subsequent property reads agree. Reordering the current four properties cannot
reproduce the old hash. Thus this is not a property-order artifact. No restart/deploy
was issued by this checkpoint; the cause/actor of that intervening transition is not
established. Do not attribute it to the later product Connect or silently rebaseline it.

The NL iptables hash also differs. The initial read-only projection normalized save
timestamps but retained live counters, so it cannot independently prove structural
firewall equality. A later canonical hash is **not** substituted for the missing
pre-action canonical receipt. This measurement limitation is separate from the
confirmed registry service transition. Post-cleanup target/foreign/service readback
matches post-B1; only the counter-inclusive iptables hash continues changing.

Required full B1 server stability therefore remains **BLOCKED**, despite local
terminalization PASS. B2/C1/C2/D/E/F1/F2 **NOT_RUN**, no inferred PASS. Further gates
need a review-authorized continuation with a stable server observation window and
counter-free structural firewall baseline; no server restart/change is requested.

## Cleanup / evidence / checkpoint

Product discard already left IDLE/pending null, no profiles/owners/markers. GUI received
its normal Close action. The idle catalog host was stopped explicitly as **fixture cleanup only**,
not as product disconnect behavior. No manual helper down, journal deletion,
test-device gateway cleanup or revoke. Same-boot links/routes4/6/rules4/6/nft/iptables/
DNS/domains/default-route hashes match baseline. Original host routes/rules/DNS/domains
read-only hashes also match; no host service changes were performed.

Guest powered off and launcher removed. All task-owned encrypted base/clone disks,
encryption key, guest credentials/SSH keys, seeds and raw logs deleted; only sanitized
evidence remains. Original protected state retained, final read-only preflight PASS.
The existing nl assignment remains for future review-authorized gates.

[Sanitized JSON receipt](evidence/l04-1-live-2-resume-20261025.json) records exact
inventory, helper/generation/typed-error evidence, network baseline, server comparison
hashes and cleanup; SHA256
`2035814a617363aa54c1391b61b75faf95b90ff16ab6c785ceebceeea2fdd5e7`.
Entry docs commit `4fb62b937f76f4c393bb7dd1efef072818ff28e3` pushed
and remote SHA verified. Final result commit/remote readback is reported at handoff
(no self-referential commit SHA). Parallel ops hunks/files remain outside task commits.

Only docs/evidence change. No new source/package CI claim; accepted R1 evidence is
historical, not rerun. Full suites54/54/53 residual failures and voice/Windows
observations remain visible. JSON/content/links, staged allowlist, secret scan and
`git diff --check` are the checks for this docs-only result.

L04.1 **IN_PROGRESS**; LIVE-2-RESUME **PARTIAL**, not CHECKPOINT PASS.
L04.2/L05/device teardown/revoke **NOT_RUN**. No publication/catalog/source changes.

STOP after this bounded checkpoint. NEXT — review L04.1-LIVE-2-RESUME.
