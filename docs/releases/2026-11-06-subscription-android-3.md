# SUBSCRIPTION-ANDROID-3 — narrow physical ARM and normal ingress

## Live checkpoint17:47UTC

Prepared overlay source/tool checkpoint `4053da47bb9d484bd87bb60884cf74ded17b6634`
was pushed and remote-verified before deployment. At17:43:50UTC only
`family-connect-friends-http-candidate.service` restarted with the new last override
`zzzzzzzzzz-subscription.conf`; actual PID3482330 owns127.0.0.1:18086, NRestarts0.
Loaded argv points to `/opt/apps/family_connect/friends-access/subscription-0fa13b0a9240/friends-http.pyz`;
SHA256 `0fa13b0a92406c9d58043287e880b6533768d031f31e1de10059b9072eb6473e` verified remotely.
No dependency, app environment, DB schema or old drop-in changed. Guarded rollback
was prepared but not used. The existing nginx master794445 received graceful HUP only;
no container/service restart. Before/after nginx syntax checks PASS; config SHA256
`6eb5d694dfe5f6b8b604484c790dc6457bdcd866f566e6a90ab51d1ac098602f`, only one exact
location added, targeting the existing18086 (not the generic snippet's18084).
Normal TLS POST without proof now returns403 JSON access-rejected, upstream403,
Cache-Control:no-store. Preflight had404. This negative is not authenticated acceptance.

**Installed:** `adb install -r` returned Success18:44:17 local/17:44:17UTC.
Pulled installed base.apk has the fixed119 SHA256, UID10283 and original firstInstallTime
`2026-09-19 17:30:26` retained. No downgrade/uninstall/clear/private-key extraction.
Ordinary release startup and Python subscription projection work; no app native/Chaquopy
exception in the bounded post-install log. Existing ChatDeliveryService starts naturally,
confirming the retained activation path. No Family Connect/third-party VPN network exists.

**First fresh physical response PASS:** ordinary subscription navigation via its existing
activity intent,17:45:23UTC, displays “По последнему подтверждению устройство вне платного
пилота. Это не означает отсутствие оплаты или доступа.” and confirmed18:45:23+01:00
Europe/Brussels. Initial UI showed pending/no confirmed data, then a fresh server label.
Read-only server correlation maps the pre-update public Support ID to the same existing
registered/non-revoked identity: zero subscription challenges before, one fresh consumed
`subscription` challenge afterward; canonical paid row absent. No supplied dictionary,
alternate endpoint/CA, operator-generated proof or synthetic production event was used.
This proves own authorized **non-cohort** response, not a paid subscription/event test.

Physical Refresh/restart retention remain pending at this checkpoint. MIUI refuses ADB
input injection and UIAutomator click; do not bypass that permission. Ordinary screenshot
is unavailable under FLAG_SECURE; standard dump waits never idle with the animated UI.
The read-only existing UIAutomator pattern with idle timeout0 reads actual visible labels;
its initial dump-file method emitted no file, so the helper now reads bounded text nodes.
An explicit user Refresh tap is requested. These harness limitations are not app defects.

## Prepared checkpoint (6 November)

This section records preparation, not deployed or installed acceptance. Worktree
`/tmp/fc-subscription-status-20261106`, branch `feature/subscription-status-20261106`.
Initial remote/HEAD `ef2daa59b6233d2ce3c5cf800d34ee8f24a1a029`; only six documentation
files differ from APK source `b2a37fe989294018ab08060bdebfa46d741d11d5`.

Fixed APK `/mnt/data/fc-subscription-android-2-build/release/FamilyConnect-Test-0.1.18-beta119.apk`:
SHA256 `52a9847b74181c48808c86a0c5bf5925b53ef498eec628aef2d78d26f1c92d2d`,
Friends `com.familyconnect.app.friends`,119/`0.1.18-beta119`,ARM64,min27,target35.
Existing release certificate SHA256
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` reverified.
No rebuild, test CA/endpoint, signer replacement, publication or version change.

Initially no ADB device. After the user connected Redmi Note9 Pro, inventory showed
Android12/API31/ARM64, installed Friends118, UID10283, first install19 September.
Documentation identifies this as the owner phone, not a dedicated device. We explicitly
asked and received permission for this exact118→119 retained-data check before install.
Installed118 APK SHA256 `b7b0be92456f522f81d87c71c401c2622d2f823178510b28510a6fb8d5c69fca`
and signer match accepted118. Public Support ID is available through the existing
consent-gated diagnostics; no private identity key extracted. VPN OFF, ordinary LTE.

## Serving backend and minimal candidate

Release origin is `https://185.251.89.19:8443`, unchanged native TLS trust/hostname checks.
Preflight normal HTTPS POST `/friends/device/subscription` returns404 (not local-stand evidence).
Actual service `family-connect-friends-http-candidate.service`, loopback18086,
serves `/opt/apps/family_connect/friends-access/mesh2-e2ed4ca6b41e/friends-http.pyz`:
SHA256 `e2ed4ca6b41e134516a7fa33210cc71e80bc62c09efc370d56ecd4c6d4e6bfd9`.
Provenance: [accepted MESH2 overlay](2026-11-04-mesh2-android112.md#backend-installed),
projected source `e7d2739f2f1c15632532e0c6e47c4184beb8dd51` onto the then serving package.
Current process3295297, startup16:37:37UTC, NRestarts0. This unit has no PartOf/BindsTo
dependency on renewal/G4; no timer, certificate or common-writer operation is needed.

`scripts/package_subscription_overlay.py` pins the downloaded live archive and applies
only reviewed single-occurrence replacements; it rejects an unexpected/repeated input.
It does **not** replace live access.py wholesale (the feature file has an unrelated
revoke helper), paid_beta.py, restricted.py, readiness or any other serving member.
Candidate SHA256 `0fa13b0a92406c9d58043287e880b6533768d031f31e1de10059b9072eb6473e`.
Changes: `friends_http.py`, one purpose allowlist in `control/friends/access.py`, new
`control/friends/subscription.py`;33 other ZIP members are byte-identical.

Contract remains [schema1](2026-11-06-subscription-authenticated-api.md): one-use
identity-bound `subscription` proof, single transactional canonical paid_beta read,
minimal snapshot/latest corresponding APPLIED event, no-store; no migration on read.
`/friends/device/status` body/semantics and all enforcement remain unchanged. No event
means no invented payment confirmation; event kind, not APPLIED alone, selects notice.

Targeted checks:3 overlay guards PASS;43 subscription tests PASS against extracted
**actual candidate archive** modules/handler and synthetic isolated SQLite, real loopback
HTTP→decoder→encrypted store. Includes replay/purpose/expiry/other-device rejection,
paid states/non-cohort/schema errors/concurrent snapshot/event and exact status response.
First capsule run had42 PASS and one missing Java source-guard fixture; copied those
unchanged guard inputs and reran43 PASS. No production fixture/payment/identity writes.

## Deployment/rollback plan

Retain the exact old archive, all existing unit drop-ins, and a private copy of current
ingress config (SHA256 `42b95d71f7a33e1cce87304ae1fad93a079f5b61e268c678a435abb057e7bf26`).
Stage the new archive separately; verify isolated import and current runtime/config pins.
Add one last ExecStart override for the same service/18086; restart **only** that unit.
Add exact `/friends/device/subscription` location using18086, bounded body/timeouts and
disabled cache. Validate nginx in its existing mount namespace, then graceful HUP of
the existing ingress master; no container restart. Check actual argv/hash/listener and
normal TLS route. No data restoration/migration or other service restart.

Rollback: remove only the new override, daemon-reload and restart that same HTTP unit
against retained `mesh2-e2ed4ca6b41e`; restore only the pinned nginx preimage (after
checking no intervening change), validate and graceful HUP. Preserve all DB state and
other drop-ins/config. Unknown/moved pins require reconciliation, not overwrite.

## Remaining gates / behavior

Pending physical installation, fresh authenticated response, process restart/cache,
one repeat Refresh, and optional event only if legitimate unread event exists.
The connected owner phone is authorized specifically for this task, not redesignated
as a disposable fixture; no uninstall, downgrade, data clear or identity recreation.
FLAG_SECURE is respected. Existing shell UIAutomator pattern only reads/clicks ordinary
UI with idle wait disabled; no instrumentation inside the app or notification forcing.

New personal events are discovered only on subscription screen open/Refresh. Delivery
after durable save is automatic; ordinary launch may drain previously saved events.
Closed-app payment is not background acquisition. No full payment-history guarantee.
Whitelist/COLD_BOOTSTRAP_GAP, natural time expiry, real identity switch through UI and
the previous mixed-network failure remain open. No G4/main/MESH bootstrap/renewal change.
