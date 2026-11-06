# Subscription/access client — isolated source checkpoint, 6 November 2026

## Scope and result

Owner-requested parallel subtask `ANDROID-CONTROLLED-BETA / SUBSCRIPTION-CLIENT-VIEW`.
Worktree `/tmp/fc-subscription-status-20261106`, branch
`feature/subscription-status-20261106`, base `6a462f5`.
This is source and focused unit evidence, **not an installed, integrated or fully
qualified feature**. The production data binding is absent, not simulated as successful.
Commit uses `[skip ci]`: this source push must not start the heavy client CI matrix.

No primary-worktree files, shared dependencies/caches, services, network configuration,
profiles or running/frozen G4 artifacts were changed. No G4 polling, emulator, native
rebuild, Docker action, existing-database migration, paid operator action, participant
lookup, real payment/event, outgoing user notification or product publication was run.
Existing main-worktree uncommitted work was not copied into this branch.

## What already existed and is reused

- `control/friends/paid_beta.py`: canonical subscription rows, effective status,
  immutable `payment/grace/expire/revoke` event records, `version`, `last_event_id`,
  exact epoch-second period bounds and idempotent application. This remains the only
  paid authority; no changes to admission, cap10, certificates, renewal or VPN routing.
- `FriendsAccessAndroid.deviceStatus()` / `control/friends/access.py::status()`:
  authenticated device-registration recovery, not a payment or subscription API.
  The existing diagnostic `normal_entitlement` check is preserved as registration
  evidence, with an additional link to the subscription/access view.
- `messenger/service_events.py`, `messenger/notices.py`: HTTPS public service notices
  and pinned-publisher signed LXMF notices. Both have bounded schemas and accept only
  `update/maintenance/server_change/information`. Their expiry is notice lifetime, not
  paid access expiry. We do not parse their human text as a payment confirmation.
- `messenger/store.py` / Android Keystore-backed `ChatStoreCipher`: existing encrypted
  `records` table and serialized owner. The new single `subscription-view` record is
  a disposable UI projection, not a second subscription database or entitlement source.
- `ChatRuntime.WORKER`, `ChatNotifications`, `mark_events`: existing delivery owner,
  service-events notification channel, permission flow and durable read/notified flags.
  No separate polling job, retry loop, signature scheme or delivery supervisor was added.

## Exact missing contract

`POST /friends/device/status` currently returns exactly `device`, `registered`,
`revoked`, `active`; Android validates this exact field set. `active` means matching,
non-revoked registration, **not paid access**. The response has no subscription state,
period end, paid revision, last paid event or authoritative observation time.

`paid_beta.status(database, support, now)` is a private operator/database function.
For a cohort member it contains `subscription` (including `device`, `state`,
`period_start`, `paid_until`, `grace_until`, `updated_at`, `version`, `last_event_id`),
`effective_state`, `paid_allow` and `entitlement_until`. Its response does not carry
the `now` used to evaluate expiry. `apply_event()` returns the canonical applied event
but is not a client delivery operation. Its event record does not carry the resulting
subscription version; an event must be paired with the matching snapshot/last_event_id.

Neither the public HTTPS feed nor the existing signed notice schema transports these
recipient-bound paid fields. No verified mapping from a private paid event to the
recipient's chat delivery has been found. Therefore they cannot safely be wired by
reinterpreting a general notice or adding a guessed production route.

`Store.accept_confirmed_subscription(...)` is an **unbound, internal adapter seam**,
tested with actual canonical backend records generated in an in-memory synthetic DB.
There is deliberately no production caller and no writable Android JSON-RPC import.
Its `confirmed_at` must eventually come from a reviewed authenticated observation,
not an arrival timestamp or device button. Its `device` must be the authenticated
recipient. Until that binding exists, a real installed client would display no confirmed
paid data; registration, payment-page return and network success do not fill the gap.
No claim of live activation/renewal/expiry delivery is made.

## Implemented client behavior

- Settings → **Subscription and access / Подписка и доступ**, also reachable from the
  existing access diagnostic dialog. Android reads its own Friends identity and the
  encrypted local projection, without creating a replacement identity/store on failure.
- Last confirmed active/trial/grace/expired/revoked state and exact period end, confirmation
  timestamp, locale, seconds, year, timezone ID and UTC offset. Current truth is never
  inferred from a cached active flag. Offline status preserves the last confirmation;
  an online network still explicitly reports that paid refresh is not yet supported.
- Device-clock expiry is a warning about the **last confirmed period**, not a locally
  generated backend expiry or denial. Clock rollback is explicit. Grace/expiry explain
  that renewal was required by the last confirmation. No timer or UI result grants access.
- Notifications require a matching `APPLIED` backend event and canonical snapshot.
  A snapshot alone does not announce payment. A renewal is called an extension only
  when a newer confirmation demonstrably extends the previously confirmed boundary;
  otherwise text says access confirmed, without claiming money was collected.
- Revision floor, matching event ID/device, immutable same-version fields and monotonic
  confirmation observation fence reject conflicts and ignore older snapshots/events.
  Natural expiry can update effective status at the same version without resurrecting
  an older active observation. Current notice flags survive duplicate delivery/reopen.
- One latest subscription event is projected into the existing Family Connect events
  view; this is not a full client ledger/history. Older revisions cannot displace it.
  Already-ended confirmations and notices arriving over24h late are not fresh alerts.
- Existing `service-events-v1` notification channel, private lock-screen content and
  cold/warm intent targeting the existing Friends settings/access UI. A stable per-event
  Android notification tag plus `onlyAlertOnce` avoids duplicate visible alerts on repost;
  a distinct newer event can alert. Superseded subscription notifications are removed.
  Durable flags are written only after the existing notification method reports success.

There is no transactional exactly-once guarantee across Android's notification manager
and SQLite: a process death between posting and flag persistence remains a platform
integration boundary. Stable tags make a surviving notification a replacement, not a
second card; post/crash/dismiss/reopen behavior requires the deferred Android checks.

## Focused validation

**32 Python PASS**:29 new tests plus3 existing store regressions,0.22s in the final run.
Separate `/tmp/fc-subscription-venv-20261106`; installed control, identity and provisioning
lockfiles plus hash-pinned messenger LXMF, with no shared dependency/cache writes.
Python3.14.4, pytest9.1.1, cryptography46.0.7, RNS1.5.1, LXMF1.1.1.
Only synthetic in-memory backend and temporary encrypted client stores were used;
the RNS network runtime was not started.

```sh
/tmp/fc-subscription-venv-20261106/bin/python -m pytest -q \
  tests/test_subscription_view.py \
  messenger/tests/test_inbox_events.py::test_unread_notification_flags_persist_and_migrate_old_history \
  messenger/tests/test_inbox_events.py::test_event_dedupe_read_persistence_and_changed_id_rejected \
  messenger/tests/test_inbox_events.py::test_revision_migration_update_replay_and_notification
```

Coverage: canonical active/expired/grace/revoked and trial snapshot; confirmed extension;
same-boundary payment not mislabeled as extension; duplicates, stale expiry/activation,
conflicts, cross-recipient and malformed input, atomic rejection, natural same-version
expiry, offline cache/elapsed period, reopen with durable flags, encrypted storage and
no new table, no payment claim from registration/page return, no snapshot-only banner,
public notice rejection, actual Android Python RPC read and import rejection, packaging
allowlist, RU/EN resources, static notification/channel/navigation guards.

**10 JVM PASS** (`SubscriptionPresentationTest`,0.196s): actual RU/EN resource strings,
unknown/offline/unsupported refresh, active/ended/grace and renewal text, exact expiry
boundary without backend mutation, clock rollback, epoch-seconds validation, DST-fold
offsets in Europe/Brussels, half-hour Asia/Kolkata, Unix epoch and post2038 timestamps.
Only two Java sources compiled
with cached read-only JDK/Gson2.13.2/JUnit4.13.2/Hamcrest1.3; classes went to a separate
`/tmp/fc-subscription-jvm-20261106`. No Gradle, SDK/native build or emulator invocation.

The JVM test uses `-Dfc.resources=<worktree>/clients/android/app/src/main/res` when run
outside the Android app directory. XML/content links and `git diff --check` are also
checked. Source guards and pure JVM tests are not Android UI/runtime qualification.

## Deferred completion gates

1. Agree the recipient-authenticated paid snapshot/event binding, including canonical
   version/event pairing and trustworthy observation time; do not expose operator
   references, hashes or payment details in a public feed. Bind through the existing
   trusted delivery/recipient mechanism in a separately reviewed task.
2. Review and merge separately; do not change the accepted G4 combination for this task.
3. When resources are free, compile the actual Android application and check its
   Keystore-backed store, process restart, permission denied/disabled channel,
   post-before-flag crash, cold/warm notification intents, visible events screen,
   language changes, timezone/DST/clock changes and offline/reconnect on Android.
   Any later emulators must follow the repository's one-AVD NVIDIA/KVM gate.
4. End-to-end synthetic authenticated delivery/refresh qualification is still required;
   no real payments, production events or user sends are authorized by this report.

## Versions, delivery and rollback

Source version stays `0.1.18-beta118` / code118. No new build, installation, installer,
release tag, catalog sequence, invitation page, server or enforcement change. Retained
documentation distinguishes opt-in field118 from default invitation/updater113/catalog7;
this task neither re-verifies nor changes those distributions. No rollout took place.
Rollback for this source checkpoint is to leave the branch unmerged, or separately
revert its source commit if later integrated; no database restore, identity deletion,
paid-table migration, client downgrade or server rollback is needed/authorized here.

## Changed files

- [Projection and canonical evidence validation](../../messenger/subscription_view.py)
- [Encrypted store and durable notice flags](../../messenger/store.py)
- [Read-only local API](../../messenger/local.py)
- [Android Python RPC allowlist](../../clients/android/app/src/main/python/fc_chat_store.py)
- [Android Python packaging allowlist](../../clients/android/chat-python.gradle)
- [Pure RU/EN/time presentation](../../clients/android/app/src/main/java/com/familyconnect/app/SubscriptionPresentation.java)
- [Access dialog and local intent](../../clients/android/app/src/main/java/com/familyconnect/app/SubscriptionUi.java)
- [Existing worker/notification projection](../../clients/android/app/src/main/java/com/familyconnect/app/ChatRuntime.java)
- [Existing notification channel and target](../../clients/android/app/src/main/java/com/familyconnect/app/ChatNotifications.java)
- [Service event display](../../clients/android/app/src/main/java/com/familyconnect/app/ChatActivity.java)
- [Settings and access navigation](../../clients/android/app/src/main/java/com/familyconnect/app/FriendsActivity.java)
- [EN strings](../../clients/android/app/src/main/res/values/strings.xml)
- [RU strings](../../clients/android/app/src/main/res/values-ru/strings.xml)
- [Python tests](../../tests/test_subscription_view.py)
- [JVM presentation tests](../../clients/android/app/src/test/java/com/familyconnect/app/SubscriptionPresentationTest.java)
- [Status](../STATUS.md), [plan](../PLAN.md), this report.
