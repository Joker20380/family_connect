# Limited cold field handoff / ограниченная полевая поставка

**PREPARED ONLY. No production operation or user handoff is authorized by this file.**
Accepted F remains its exact emulator result, not physical API28 acceptance. The
candidate is beta120;119 is reserved by the independent paid branch. No paid changes
are imported. Public113/catalog7 and the existing public118 download are unchanged.

## Package and custody / пакет и custody

Build once, before issuing short-lived material:

```sh
python3 scripts/package_cold_provision.py --go /trusted/go/bin/go --output /private/new-package
```

`manifest.json` records source, clean/dirty state, runtime source hashes and artifact
digests. Only a clean-source package is eligible. `deployment.json` is the exact
unapplied deployment plan. The Linux entry is for the existing NL1 node
`185.10.158.212`, not the user's phone. `186.246.45.246` is the retired gateway,
not an alternative management address or relay for NL1. The canonical collector,
offline reverified signed catalog4/6 and retained replacement/live-traffic receipts
agree on NL1. AMS2 is185.10.158.196, not this entry. See the
[binding receipt](../../../docs/releases/2026-11-07-cold-field-node-binding.json).
Management, ordinary relay and observed egress happen to share the NL1 address;
none proves cryptographic gateway identity. Telemost is the provisioning carrier,
not a raw TCP relay at that address. These are historical observations, not fresh
server checks. Authorized preflight must reconfirm the registered user's selected
route, canonical profile/leaf and current signed routing policy before staging.

The gateway private key stays on NL in the existing canonical profile
`/etc/fc-canonical-pinned-venv/profile.json`, resolved by the retained NL1 locator
readback (not the old `friends-restricted/gateway.json`). The existing issuer,
registry, admission and signed CRL stay on RU `185.251.89.19`. The entry does not load
the issuer key. RU's one-shot `cold-provision-locator.pyz` reuses the existing issuer;
it performs no migration, enrollment, grant or policy write. No new signer, database
or renewal controller exists. Only the public gateway certificate and seed cross
between hosts during issuance.

The entry joins one fresh Telemost room and serves the existing coldprovision protocol.
Two bound RPCs reach the **existing** RU authority HTTPS endpoint8443 from NL with
normal system-root/IP-SAN verification, no HTTP proxy or redirects. The user's blocked
direct path is not reused on the phone: phone→Telemost→NL entry→RU handlers. Before
approval there is no assertion that this server-side HTTPS link or credentials are
currently usable. Do not bypass trust if its preflight fails. Disposable tests can use
literal loopback; no arbitrary remote URL or TCP/DNS/HTTP forwarding is accepted.

The server maximum is420s; systemd watchdog440s, bounded stop20s, Restart=no. These
are entry lifetimes, not changes to candidate200s/readiness30s/TLS/network timeouts.
No listener, ingress route, firewall or working gateway service changes are required.

## Authorized execution / после отдельного разрешения

1. Complete applicable release acceptance before real vault signing. Preserve all
   accepted local build reports and downloaded CI receipts; a local unsigned build
   is not a release-CI PASS. Do not use a previous version's signature/CI as proof of
   the new artifact. No fresh locator is needed for heavy builds or immutable checks.
2. Confirm the registered user's selected NL1, current admission and trust/floors
   using existing read-only operations. Do not activate a new identity or alter policy.
   Confirm the current authority handlers support the two targeted RPCs and NL can
   verify RU's existing HTTPS certificate without insecure flags. Compare APK
   `control-anchor.pub` with RU's public anchor. Keep gateway profile owner/mode intact.
   Resolve the running NL1 canonical profile locator. The unit's configured
   `/etc/fc-canonical-pinned-venv/profile.json` must still be that current profile, not a stale
   pre-renewal copy. Stop on any mismatch; do not move/copy a gateway key or certificate
   to another host, change canonical locators or substitute the retired gateway.
   `ProtectSystem=strict` already protects `/etc`; do not add a bind/read-only mount
   at the canonical profile directory. The unchanged native custody reader rejects
   mounts at/below that boundary, including a `ReadOnlyPaths` bind of the directory.
3. Stage only the new paths listed in `cold-provision-deployment.json`, with exact
   accepted package hashes. Install the new template unit, **do not enable** it.
   Parent `cold-provision/run` is owned by existing `family-restricted`, mode0700.
   Place the matching public anchor under `cold-provision/anchor.pub`.
4. Agree the private APK delivery channel with the user **before starting the entry**:
   an already reachable messenger as a document attachment, or an agreed local
   transfer. Do not assume the blocked8443 download page is reachable. No third-party
   VPN is a cold-test prerequisite. The user must already be available for handoff.
5. Select a fresh, never-used invocation name. Start only
   `cold-provision-entry@<invocation>.service` on NL. No reboot of normal gateways.
   Wait for `SEED_CONNECTED_AWAITING_EXISTING_ISSUER` and private `run/<invocation>/seed.json`.
   This is not TLS/bundle readiness. Stop if no fresh seed appears within the bounded
   lifetime; do not supply a previous room or locator.
6. Export only the existing gateway **public certificate** through the current
   `public-gateway` maintenance operation. Copy it and this seed to a fresh private
   RU invocation directory. Run under the existing authority custody:

```sh
/opt/apps/family_connect/friends-access/venv/bin/python -I \
  /opt/apps/family_connect/cold-provision/cold-provision-locator.pyz \
  --database /opt/apps/family_connect/friends-access/access.db \
  --material /opt/apps/family_connect/friends-restricted \
  --certificate /private/invocation/gateway.pem \
  --state /private/invocation --node nl-amsterdam-1 --sequence POSITIVE_SEQUENCE
```

`POSITIVE_SEQUENCE` must be a fresh increasing operator-recorded locator sequence;
retain the previous receipt, do not invent a reset or alter trust floors. Issuance
refuses an existing output, expired trust/CRL/certificate, wrong binding or malformed
seed. It caps expiry by existing certificate/CRL/issuer/seed, never extends any TTL.
Copy only the resulting public locator atomically into the matching NL invocation
directory as `locator.json`, not into ordinary `friends-restricted/directory.json`.
Normal MESH directory/renewal services stay unchanged.

7. Confirm `LOCATOR_VERIFIED_SEED_CONNECTED`/`ready.json`, no `stopped.json`, exact
   locator hash/expiry and matching live unit MainPID. The marker means seed connected
   and locator verified, not proof that a client has completed TLS or fetched a bundle.
   Capture unit liveness with server time adjacent to handoff/Connect. Copy public
   locator, ready receipt and anchor over the existing protected operator channel.
8. On the operator machine, with heavy builds already finished:

```sh
python3 scripts/prepare_cold_field_apk.py prepare \
  --unsigned /private/accepted/FamilyConnect-Test-0.1.18-beta120-unsigned.apk \
  --verification /private/accepted/verification.json \
  --locator /private/invocation/locator.json --ready /private/invocation/ready.json \
  --anchor /private/invocation/anchor.pub --node nl-amsterdam-1 \
  --verifier /private/package/cold-provision-entry \
  --zipalign /trusted/android/build-tools/35.0.0/zipalign \
  --output /private/new-finalization
```

The helper accepts only the checked120 prebuild and ARM64 native digest, verifies
the locator using existing Go verification and matching APK anchor, requires a recent
entry receipt and ≥200+60s remaining, changes only the one locator asset, aligns16K
and checks every other ZIP payload byte. It does not assert remote liveness. It emits
`connect_not_after` as an absolute Unix timestamp (expiry minus200s); communicate it
as explicit UTC/local time, not an inferred promise of connection duration.

9. Use [the existing vault signer](../../../docs/android-vault-signing.ru.md), same
   beta113 certificate `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
   Use the existing approved vault entry/member names; master password only in its
   protected local dialog. No manual key extraction, command-line password, debug
   key or lineage reset. Supply the exact fresh unsigned digest and a new output path.
10. Run `prepare_cold_field_apk.py verify-signed` with the same CI `--unsigned` and
    `--verification` inputs, `--prepared` fresh unsigned,
    `--apk` new signed, `--apksigner`, `--aapt`, `--zipalign`, and the same verifier/anchor/node.
    It checks signer, unchanged payload, native/trust, package/minSdk/ABI and current
    locator validity. Save its receipt and perform the normal `zipalign -c -P 16 4`.
    Only then hand off those exact bytes privately with digest and Connect cutoff.
    Do not publish a tag, catalog entry, general download or updater change.

The bundled `cold-field-qualified.json` pins the accepted CI head/run/job/artifact,
unsigned APK, verification receipt, native library and trust anchor. Final verification
rechecks that CI input, not just a supplied prepared APK. Only the one node locator asset
may differ before signing; all other APK payload members must remain byte-identical.

## Actual handoff window

Accepted prebuild: Client builds42385799106, Android job128442818128,
source55525859465ff4713196db7206129ad840f67cb3, ARM64 artifact13580421361.
The unsigned APK SHA256 is
`9eae8668544c9b0d968befb82dc655a2594535fe59c4b5af5d55a804fd67348c`.
Use the downloaded `verification.json` and accompanying audio source from that artifact.
The old local269a9219 prebuild is preserved but is not this CI-qualified input. The new
JNI includes isolated native callback threads after an API35 multi-Go-runtime failure;
API27/API35 release gates confirm that fix, not a new Telemost/F or physical-phone run.
The final locator-bearing signed APK necessarily gets a new digest. Never label it
with the unsigned prebuild hash. Retain the corresponding source/notices beside handoff.

Let entry start be T0. Its context ends atT0+420s. `SeedManager` takes the minimum
of its own lifetime and that parent deadline, so seed expiry never extends the entry.
The issuer uses `E=min(seed expiry, trust expiry, gateway leaf notAfter, CRL nextUpdate)`.
The default60s handoff reserve and200s candidate reserve require `E-now >=260s` at
both preparation checks; `connect_not_after=E-200s`, rechecked after signing.
At best, preparation must finish byT0+160s and Connect start byT0+220s. Room creation,
seed Connect, issuance, transfer, alignment, signature and verification consume that
window; earlier certificate/CRL expiry shortens it. This is not420s available for
handoff and not a promised connection duration. Readiness30s is unchanged. The20s
stop allowance/systemd440s ceiling is cleanup, not additional locator validity.
Do all CI, source/archive preparation, SDK/vault-path checks and recipient/channel
coordination beforeT0. Recipient availability and a reachable document/local transfer
channel are still required before the authorized operation starts.

If the window is missed: do not Connect with expired material, extend TTL, change
clock or substitute a cached bundle. Stop only the new entry, retain evidence and
schedule a fresh synchronized issuance. If120 has already been handed off, reserve a
new free versionCode for any replacement bytes; no immutable version reuse. An
unsigned draft with no live locator is **NOT ready for field installation**.

## One field check / одна проверка на исходном телефоне

- Install the correctly signed ARM64 APK **over beta113**, without uninstall, clear
  storage, identity regeneration or activation. Preserve user settings/access/data.
  If Android refuses the update, stop and retain the reason; never fix it by wiping.
- Record versionCode, API28/arm64 ABI, selected node, readiness-cache classification,
  and other-VPN state. Do not erase user data to manufacture a cold state. If a valid
  cache exists, label the attempt warm; it cannot accept cold behavior.
- User Wi-Fi OFF, other VPN OFF; capture entry live state/time; one ordinary MESH
  Connect before the communicated cutoff. Preserve native stages/reason/network/bind,
  elapsed/remaining and request-ID correlation before cleanup.
- At READY: verified hostname HTTPS and expected selected-node egress; retain DNS
  result and minimal diagnostics. Do not infer physical mobile behavior/timing from F
  or map emulator EACCES onto the historical phone export. E's2/2 counters stay unknown.
- Export minimal diagnostics via the app's existing path, no keys/tokens/bundle or
  full profile. Only after the owner/user opts into handoff is any phone operation done.

## Stop / rollback

Stop only `cold-provision-entry@<same-invocation>.service`; verify inactive/MainPID gone,
owned connections ended and stopped marker where graceful shutdown was possible.
Retain the private invocation directory, immutable artifacts and safe hash receipts.
Disconnect is not confirmation of provider room-object deletion. Do not stop normal
MESH/bootstrap/authority/renewal services or restore old credentials/floors. Removing
new unit/package files is optional after evidence retention; no existing file needs
rollback. Android downgrade may be rejected: do not uninstall/wipe; use a separately
approved forward-version corrective build if ever needed.
