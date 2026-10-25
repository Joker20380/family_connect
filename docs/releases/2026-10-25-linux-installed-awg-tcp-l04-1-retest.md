# L04.1-LIVE-1-RETEST — exact corrected Linux candidate,25.10.2026

## Решение и граница

**Review decision,25.10.2026: DONE / review accepted.** Owner принимает matching
request/reply на actual AWG/TCP TUN после cache flush и валидный terminal NODATA.
Fresh-DNS positive/NXDOMAIN/NODATA contract выполнен; positive installed AWG/TCP
acceptance corrected candidate завершена. Повтор gate не требуется. Исходный
PARTIAL ниже и machine evidence сохранены как наблюдения до review, без изменения
измерений. Разрешено отдельно только LIVE-2; parent L04.1 IN_PROGRESS до его review.

**PARTIAL; review pending.** L04.1-LIVE-1-R DONE/review accepted в source/package
scope. Новый installed retest подтвердил исправленный single Disconnect, включая
original AppImage close/reopen, реальные AWG/TCP transfers и полный cleanup.
Однако буквальный fresh-DNS критерий не закрыт: nonce под example.com получает
**NOERROR/NODATA**,0 answer RRs, а `resolvectl` завершает запрос с exit1 «no RR of
the requested type». Это не NXDOMAIN и не успешное разрешение имени. DNS transport
через actual TUN доказан, но его нельзя молча выдать за весь требуемый gate.
Нового product defect не установлен; повторных Connect/Disconnect ради PASS нет.

Parents L04/L04.1 **IN_PROGRESS**; L04.1-LIVE-2/L04.2/L05 и device teardown
**QUEUED / NOT_RUN**. Historical final-2/0.2.12~l03.2.1 не использован как live
candidate и не изменён. Никаких product edits, rebuild, installed patches или
test hooks; только этот documentation/evidence checkpoint.

## Exact inputs / provenance

Input main/remote: `840b67a1a5b4f484c1bc066fd656334368a1317e`.
Product source: `57f8eff8b291062d69248ac46413f8c9fc0f561d`.
Directory: `state-client-build/linux-poll-disconnect-l041r-20261025/build-1/`.
Internal version **0.2.12~l03.2.2**; candidate ID
`d9c0d07f93542a633b5563757f0c5aa0d4f0c37410b3b884ba8b67db01c484ef`.

| Exact artifact | Bytes | SHA256 |
|---|---:|---|
| FamilyConnect-0.2.12~l03.2.2-x86_64.AppImage | 57924088 | `33537e451ab39010b70c989604477fc73c86f6b88f7f5d7d4c5a50dd07887a8a` |
| FamilyConnect_0.2.12~l03.2.2_amd64.deb | 55951452 | `c806ed9fac2466772042cde6c84a59b7bd86172cd3d91dee724449de78f77dda` |

Embedded system build-9:
`8708ba6d5e218f86b42d862dd5a66237e974a03d5434e8f1c30524b16720e2da`;
archive SHA256 `bdd7e04b8ca78a232acccd881004cfb3b6c96b13dc3c608d0b919f53f40f02d9`.
Before launch: sizes/hashes, exact707 user members, candidate manifest, embedded
inventory/identity PASS through the standard verifier. The offline artifact verifier
used a network-disabled build container with no test state; **live acceptance used
only the new KVM guest**, not that container. Installed imports/inventory and both
launchers' candidate checks PASS. Full installed readback:763 files, READY,
installed manifest SHA256 `aabcce5e4baf25db37f05cd43d0ef4ab8a1ae83a622f30f05438c3f0c1c77b31`.

Source VERSION/public Linux remain0.2.11; this exact internal pair is not a public
release. Catalogs, landing, signing, legacy six-file updater and server deployment
were not changed. Previous package/source checks remain attached to their exact
[correction report](2026-10-25-linux-poll-disconnect-l04-1-live-1-r.md).

## Isolation, handoff and setup

- New KVM/qemu10.2.1 guest, Ubuntu24.04.5, kernel6.8.0-147-generic, systemd255.4,
  2CPU/4GiB. Official Ubuntu cloud image verified against published SHA256SUMS.
- LUKS-encrypted qcow2 overlay; private SLIRP network, loopback SSH forwarding,
  guest NetworkManager/systemd-resolved, D-Bus/Secret Service, real polkit agent,
  TUN, nftables/iptables/iproute2. Host routes/DNS/services were not changed.
- Existing read-only preflight PASS. Only protected `home/` streamed into guest
  UID1000; no operator directory, invite, provisioning intent or teardown receipt.
  HOME `/home/tester`, XDG config/data/state under that HOME. Before GUI:0700/0600,
  no symlinks/hardlinks/special files; exact packaged Python3.12/vendor, create=False.
- Same **FC-3YSQ-BE2D**, public identity SHA256
  `d07d33a81728ff70aec350ae59785990c194d90ecd44574b0da28439189532de`;
  verified cache only nl, signed floor sequence3/catalog hash
  `f4d812db722705d8fc853a1a1afd454922cd2bca71175db025f40b9a58c3628d`.
- Exact DEB installed. GUI ordinary UID1000; no root component/TUN before setup.
  Settings → Install system component (no VPN) → Install → actual polkit
  authentication. READY/build-9/full inventory PASS, no VPN intent or root VPN/chat
  start. GUI and user chat service restarted; same identity readback PASS.
- Fixture-only preparation: missing host GTK dependencies installed inside guest;
  networkd→NetworkManager DNS handoff completed before baseline. Interrupted setup
  authorization resumed in the **same pending dialog**, not a second Install.
  AT-SPI auth selector corrected to select the button, not the same-named dialog.
  No product files or authorization rules were patched; no allow-all polkit rule.

Baseline: lo/enp0s1,0 TUN/root FC units/transport processes/active journals;
routes4/6 counts7/4, rules4/6 counts3/2,0 owned nft tables. Separate readback of
routes/rules/firewall, resolved DNS/domains/default-route and public IP is in the
[sanitized machine evidence](2026-10-25-linux-installed-awg-tcp-l04-1-retest.evidence.json).
Evidence JSON SHA256: `b1432800c0d69a6f46a3669d8ff03c70cfa50b5cbe9cdce6bcf217bf7482837d`.
Host raw routes4/rules4/resolved DNS/domain hashes match before/after.

## Installed sessions — no helper CLI substitute

Each Connect/Disconnect was one real GUI action with actual polkit/helper path.
No standalone FriendsOwner.configuration call, driver bypass, direct helper up/down,
SOCKS-only proof or Auto fallback. Country nl only. Each session had exactly one
root transport owner and actual TUN; AWG/TCP ownership did not overlap.

| Session | Connection ID | Root generation / invocation | Interface | Operation generation at ready → after one Disconnect |
|---|---|---|---|---|
| DEB AWG | `0b65e5f4-707c-41ec-a2c1-b26aa76e39ae` | `f887a02040e6cc3ceed1e073cbccad3f` | `fcawgb0dc9fcb` | 2→3 |
| DEB TCP | `66a77c98-8251-4f5f-829c-57e0dcb9a3ba` | `7a6c8975fe3149d88c77d26b4193072a` | `fctcp52569225` | 5→6 |
| AppImage AWG | `8b53cce7-f423-4553-9f78-417658d5d30b` | `fc40cdbf551902b91155f98fd201e12c` | `fcawga98f09b3` | 8→9 |

Selected-next/actual were awg/awg or tcp/tcp, distinct fields in diagnostics;
after Disconnect actual none, DISCONNECTED. AWG handshake present in both AWG
sessions. TCP ran the real Xray service with full TUN routing. `ip route get` selected
the actual TUN. HTTPS, **65536-byte download +65536-byte upload** passed for each
of the three sessions; observed TUN RX/TX deltas respectively83360/71702,
84768/73886 and82938/71494 bytes. These are bounded functional checks, not throughput
benchmarks. Public IP SHA256 baseline/restored:
`3f53078c747ff27aa70f8906808e6030259e94412c4b964d6b12f1ac45d8444b`;
connected expected nl gateway hash:
`9e873c4c9e4f0a2356811cce0215504451108ce64fae1d466c1b41e13622b086`.

Kernel audit records confirm **helper down ×1 per Disconnect**. Each mutation changed
operation generation exactly once, no pending owner after completion. Initially
`ausearch` selection returned no events; fixture read the actual guest audit file
and counted matching EXECVE events instead. Raw audit logs were not exported and
were destroyed with the guest. This was instrumentation repair, not a repeated down.

## Fresh DNS — precise remaining gate

Inside guest caches were flushed. Bounded capture on the **actual session TUN**,
unique nonce under example.com, systemd-resolved query; no raw pcap saved/exported.
Wire-header decoding matched response transaction IDs and the nonce in memory.

| Transport | Final measured UTC interval | DNS requests/replies | RCODE / answer / authority | resolvectl |
|---|---|---:|---|---:|
| DEB AWG | 15:11:10.590–15:11:10.843 | 2/2 | NOERROR×2 /0 /2 | exit1, NODATA |
| DEB TCP | 15:15:16.598–15:15:17.036 | 2/2 | NOERROR×2 /0 /2 | exit1, NODATA |

Each final sample had4 DNS packets; resolver-address-set SHA256
`fed6626955584d44ee31af537ee46e318e52711245ebb82759294cae44f329d7`.
No nonce names, DNS packet payloads or raw captures remain in evidence. TCP capture
was a bounded AF_PACKET read on that TUN, decoding only matching UDP53 DNS packets;
it does not claim a separate TCP53 fallback test.

AWG instrumentation first stopped before issuing the query due to buffered tcpdump
stderr readiness. After correcting this fixture, text classification of two bounded
nonce probes failed to classify NODATA. Final in-memory wire parsing established
RCODE0 with no answer, not NXDOMAIN. **No reconnect/retry Disconnect was used**.
DNS request/reply routing PASS; the literal successful-resolution/NXDOMAIN acceptance
remains **NOT_CONFIRMED**, so overall RETEST is PARTIAL. No alternative domain, trust
bypass or relaxed product readback was substituted. Remaining decision belongs to
review; no further live gate starts automatically.

## Targeted AppImage close/reopen

Original exact executable launched from `/home/tester/`, via FUSE. Process environment
confirmed original APPIMAGE and shared HOME; same candidate/build-9 READY, no second
root setup. Second launch exited0 into the existing GUI instance; owner/interface/
process/generation unchanged. Actual GUI PID18552 exited after the standard warning
and **Close window** confirmation, while root owner/TUN/generation and HTTPS remained.

Reopen PID19851 displayed **Tunnel is on / Disconnect**, actual AWG. One Disconnect
after normal refresh triggered real polkit authentication and one helper down, no
«Connection settings are being updated», retry or second click. Reopened diagnostic
connection ID `f9b99380-99e2-47c4-aa24-9fc5d1e8921f`. Owner/TUN removed, generation8→9,
exact network/IP baseline restored.25 one-second post-disconnect samples over25s
remain DISCONNECTED/actual none/generation9/pending null; late polling did not restore
CONNECTED. This is actual installed behavior, not a forced race/test-hook proof.

## Server readback and final cleanup

Read-only registry/nl/ru baseline, after each product session and final readback:
target DB/live AWG peer **1/1**, persisted/runtime Xray user **1/1**; ru target counts0.
Total peers/clients46/46. Same row/address/bindings; foreign DB/live bindings, immutable
settings/server keys/endpoints, catalog/archive and service PID/invocation hashes
unchanged. Only normal product-internal idempotent nl configuration fetches allowed;
no manual fetch, provisioning, server restart/deployment/policy/signing mutation.

Instrumentation qualification: the old readback script hashed raw `iptables-save`,
including wall-clock comments/live counters. That raw hash differed; equality is
**not claimed**, nor used as an immutable server-config gate. Other server network
address/route/rule hashes and all required target/foreign/global/config/service
checks matched. Guest firewall structural hashes, which are the acceptance cleanup
criterion, returned exactly to their own baseline after every Disconnect.

All sessions removed owned TUN/routes/rules/nft/DNS and restored public IP; no active,
pending or sticky markers. User operation/shared transport/mesh reservation/install
locks tested FREE. Normal configuration leaves one **idle catalog host**:
family-connect-auto@1000, DISCONNECTED/desired=false/generation empty/controller=null.
No Auto VPN, MESH or service-only fallback. After final product Disconnect, fixture
explicitly stopped only that idle host; then root units/processes also matched baseline.
Do not attribute this fixture stop to product Disconnect.

Final create=False readback: original7 identity/cache/marker files byte-identical,
same Support ID/fingerprint and verified nl assignment/floors. Newly created normal
Friends application journal is IDLE/baseline null; not pending cleanup. UID1000,
directory0700/file0600. Selected settings persisted across formats/close/reopen.
Original protected state and private teardown receipt hash unchanged; neither deleted.

Guest shut down; QEMU process and SSH listener absent. Encrypted overlay, LUKS key,
guest SSH/password/seed, transferred state and raw logs deleted. Only sanitized
evidence remains; original FC_L04_TEST_STATE and nl assignment retained for later
authorized gates. Device-scoped gateway cleanup → readback → registry revoke NOT_RUN.

## Validation and checkpoint

This turn ran artifact integrity, installed readback, real KVM GUI/setup/traffic/
cleanup and documentation checks; product suites/CI rebuilds were not manually rerun
as acceptance of this documentation/live checkpoint.
Existing Client Linux/AWG/TCP/native/root→UID/Auto/DIRECT/package CI acceptance remains
in the correction report, not new evidence from this turn. Full suites remain red:
control/phase0/Docker54/54/53 failures; D01's54 residual debt, D02.1-R PARTIAL/NOT_RUN
and voice/Windows observations are not fixed or hidden.

Documentation-only commit: STATUS/PLAN, routing guides, this report and sanitized JSON.
Staged allowlist, secret-pattern scan, local links and whitespace checked; parallel
ops hunks and their untracked report remain outside the commit. Input remote SHA
verified unchanged before staging. This report's commit is the documentation
checkpoint; exact commit/ordinary push/remote equality are verified in the final
handoff, without a self-referential SHA or rewriting historical product provenance.

**STOP. NEXT — review L04.1-LIVE-1-RETEST.**
