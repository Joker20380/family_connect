# Subscription/access authenticated API — source integration candidate, 6 November 2026

## Scope and isolation

Owner-requested `ANDROID-CONTROLLED-BETA / SUBSCRIPTION-CLIENT-VIEW`, continuing
`47ef0463bd39aa8996ff11b1196c7adbb6bb4c60` on `feature/subscription-status-20261106`
in `/tmp/fc-subscription-status-20261106`. This is an independently reviewable
**source/integration candidate**, not an installed or fully qualified feature.
The commit uses `[skip ci]`; source push is not permission for heavy CI or deployment.
The commit/push receipt and verified remote SHA are reported in the task handoff.

Only synthetic local HTTP/SQLite and small unit tests were run. No real participant,
payment, production request, user notification, server operation, existing DB migration,
AVD, Gradle/native rebuild, Docker action, shared dependency/cache modification, release
artifact, merge or installation. Main checkout and G4 sources/frozen checkout, containers,
network, profiles, artifacts and schedule were not modified or cyclically inspected.

## Existing mechanisms reused

- `control/friends/paid_beta.py` is unchanged: canonical subscriptions, immutable APPLIED
  events, cohort rules, effective state, revision and entitlement boundaries. No new
  paid table, entitlement authority, billing provider or enforcement decision.
- Existing Friends public identity/WG binding, one-use challenge table and
  `verify_transport_key_proof`/`ControlIdentity.proveTransportKey`. No new signer,
  audience, signature format or certificate scheme. Identity/invitation revocation
  still rejects access. Paid expiry/revocation does not revoke the identity.
- Existing bounded `FriendsAccessAndroid` TLS client, `FriendsIdentityVault`,
  `ChatNetworkAndroid` non-VPN HTTPS path, serial `ChatRuntime.WORKER` and chat owner.
- Existing `Session`/`LocalChat`/`Store` encrypted `records` table, one display-only
  `subscription-view` record, event ID/revision fences, durable read/notified flags,
  notification tags/channel and subscription navigation from the preceding checkpoint.

There was no equivalent personal paid read route. `/friends/device/status` is still
exactly `{device, registered, revoked, active}` with its existing meaning and behavior.
Its `active` is **not** mapped to `paid_allow`. Public notices remain non-personal.

## Exact additive wire contract

1. `POST /friends/challenge` with the existing identity/key fields and
   `purpose="subscription"` (`invitation=""`). Only registered identities may acquire
   this purpose. Existing challenge TTL100s, audience and verification policy remain.
2. `POST /friends/device/subscription` with the **existing transport-key proof object
   itself**, not a wrapper or device/support/event selector. Identity is derived only
   from the verified signature, persisted challenge and registered binding.

The proof has the existing exact fields `schema_version, transport, audience, public_identity,
wireguard_public_key, challenge, signature`. Replay, wrong purpose, expired challenge,
tampered proof and extra selector fields are rejected. Valid authentication consumes
the challenge even when paid schema reading fails; retry needs a fresh challenge.

HTTP200 JSON has exactly these top-level fields:

| Field | Meaning |
| --- | --- |
| `schema` | Integer1; unsupported versions are rejected, not partially interpreted. |
| `device` | Exact authenticated identity reference (32 lowercase hex characters). |
| `observed_at` | Integer Unix seconds; one server `now` for this transaction. |
| `cohort` | Boolean; false means no canonical paid row, not unpaid/no access. |
| `subscription` | Null outside cohort; otherwise the exact object below. |
| `event` | Null, or the latest matching APPLIED event object below. |

Member `subscription` has exactly:

- `state`: canonical `trial/active/grace/expired/revoked` state;
- `period_start`, `paid_until`, `grace_until` (nullable), `updated_at`: integer Unix seconds;
- `version`: positive revision; `last_event_id`: existing opaque event ID;
- `effective_state`, `paid_allow`, `entitlement_until` (nullable): existing canonical
  effective calculation at `observed_at`. These are UI evidence, not a new grant.

`event`, when present, has exactly `event_id, event_type, occurred_at, previous_state,
new_state, result`. Types are existing `payment/grace/expire/revoke`, result is `APPLIED`,
previous state may be null. The server checks event device, ID, period bounds, new state,
occurred/applied times against the same revision before projecting this smaller object.
Missing/nonmatching event means snapshot-only display, **never payment confirmation**.
The client verifies event ID/state/time pairing again before saving.

No support IDs, reference/payload hashes, operator references, payment details,
other-device data or whole operator status/`SELECT *` rows are returned.

### Consistency and failure behavior

`subscription.request()` uses the existing `Access.db()` `BEGIN IMMEDIATE` transaction:
after the lock is acquired, it captures one `now`, validates/consumes the challenge,
reads the explicit subscription/event columns and computes effective state. Concurrent
renewal/revocation cannot mix revisions, bounds or event timestamps in one response.
There is no migration-on-read. Except normal challenge bookkeeping, reads leave paid
records/events, cohort, support records, identities/invites, grants and certificates unchanged.

| HTTP/result | Client behavior |
| --- | --- |
| 200 valid cohort | Validate completely, then accept confirmed local projection. |
| 200 valid non-cohort | Confirm outside-pilot status; no unpaid/payment notice. |
| 403 authentication rejected | Separate identity failure; never convert to unpaid. |
| 404/405/501 on the new route | API unsupported; retain old confirmed cache. |
| 501 missing paid tables | Unsupported, not authoritative non-cohort. |
| 503 partial/corrupt paid schema or read failure | Unavailable, never false non-cohort. |
| 429/temporary HTTP failure/timeout/offline | Preserve cache; no fresh confirmation. |
| Invalid JSON/schema/recipient/pairing | Reject without changing confirmed cache. |

Existing malformed-request400 and handler slot limits remain. All handler replies,
including errors, carry `Cache-Control: no-store`; personal requests use POST.
The exact new Nginx location disables proxy caching and buffering, caps body at8KiB,
and uses the existing loopback handler. Ordinary installer allowlist, HTTP runtime source
manifest and packaging inputs include the additive route/module/snippet. These are source
changes only; no ingress or runtime was installed. Readiness/renewal routes are unchanged.

## Client integration and backward compatibility

The dialog loads the identity-bound saved projection, then requests refresh once; an
explicit RU/EN Refresh button repeats this operation on demand. One process-wide gate
prevents concurrent duplicate operations. No timer, polling, retry loop or new supervisor.
Normal refresh is two HTTP requests (challenge + proof/read) with a shared20s deadline,
existing TLS trust/no redirect behavior, bounded response read and strict16KiB decoder.

Old servers can reject the new challenge purpose before reaching the route. Only for
that rejection, the operation performs one bounded registration check using a fresh
`status` purpose. Exact verified own registered/non-revoked/active registration classifies
this as **unsupported**, never paid. Registration rejection remains an identity error;
temporary failure does not retry/fallback. This compatibility branch is at most three
HTTP requests total, within the same deadline. Old clients never use the additive API.

The subscription operation uses `FriendsAccessAndroid(context, deadline)` (direct mode),
therefore the existing non-VPN HTTPS control path even when a VPN is attached or paid
access has expired. It does not call enrollment/configuration/renewal/readiness to obtain
a VPN first. Underlay route selection and allowlists are checked in source; actual
Android connectivity and deployed ingress reachability are **not runtime-qualified here**.

The path is `FriendsIdentityVault → FriendsAccessAndroid → SubscriptionRequest →
ChatLocalAndroid.acceptSubscription → Session.accept_subscription →
LocalChat.accept_subscription_response → decode_response →
Store.accept_confirmed_subscription → subscription_status`.
The writable method is intentionally absent from generic UI JSON RPC. Decoding rejects
duplicate keys, wrong recipient/version/types, excess fields, excessive size, invalid
time/effective state and event pairing before accepting anything.

The refresh binds the exact open owner and identity, reloads the vault before commit,
and checks the owner/session and cancellation gate again. Closing/dismissing or switching
identity cannot commit an old response into another state. Cancellation is distinct from
backend identity refusal. Last-confirmed cache and transient refresh outcome remain
separate; restart does not persist a misleading "fresh" flag. Same-revision conflicts,
older revisions/observations and natural expiry rules from the checkpoint are retained.

Notifications use the existing event IDs/tags/flags/channel. RU/EN text says access
confirmed/extended, not money received. Snapshot alone, registration, HTTP200 alone,
payment-page return and Refresh button are not payment evidence. Only the latest matching
event is obtained on refresh: **not instant push or guaranteed delivery of every event**.
Time rendering includes year, seconds, time zone and offset; expired grace displays the
last granted grace boundary instead of an earlier paid-period end.

## Focused evidence

84 Python tests PASS:43 new HTTP/adapter cases,29 projection tests from the checkpoint,
9 existing Friends auth regressions and3 existing encrypted notice-flag regressions.

```sh
/tmp/fc-subscription-venv-20261106/bin/python -m pytest -q \
  tests/test_subscription_http.py tests/test_subscription_view.py tests/test_friends_access.py \
  messenger/tests/test_inbox_events.py::test_unread_notification_flags_persist_and_migrate_old_history \
  messenger/tests/test_inbox_events.py::test_event_dedupe_read_persistence_and_changed_id_rejected \
  messenger/tests/test_inbox_events.py::test_revision_migration_update_replay_and_notification
```

Real `deploy/friends/access-api.py::Handler` listens only on ephemeral localhost against
a separate synthetic DB. Tests exercise real challenges/signatures/HTTP responses, the
real Python Android bridge/decoder, AES-GCM encrypted Store and displayed event projection.
LocalChat's network runtime is replaced by an open-owner marker in this harness; Android
transport/Chaquopy/Keystore are **not** simulated as a passed runtime gate.

Covered through HTTP: own active/grace/expired/paid-revoked and non-cohort reads; foreign
selectors/identity, replay, expiry/wrong-purpose/signature/identity revocation; missing and
corrupt schema; no matching event; concurrent renewal/revoke serialization; natural active
and grace expiry without new event/version; duplicate/delayed/conflicting responses;
malformed schemas and wrong recipient; temporary503/cache preservation; encrypted reopen,
durable flags; closed-owner refusal; unchanged exact registration response and unchanged
paid/admission rows (including pre-existing synthetic grants/certificates).

26 pure JVM tests PASS (direct `javac`/JUnit, no Gradle):13 presentation/resource/time tests,
7 request compatibility tests and6 single-flight/lifetime tests. Old-server challenge
fallback, exact status parsing, route404/405/501 classification and local identity/owner
fences are unit-tested, **not executed on Android**. Offline/time/DST/2038, RU/EN and
no-payment-claim rendering use real resource XML. JDK/Gson/JUnit/Hamcrest were reused
read-only from existing local tooling; class output is task-local `/tmp/fc-subscription-jvm-20261106`.

## Remaining gates and rollout boundary

1. Separate review/merge; no automatic continuation into unrelated PLAN work.
2. When resources are free, Android Java/Chaquopy build and API27/API35 qualification
   of the existing HTTP/vault/bridge call sites, using this contract (not another API design).
3. Android Keystore encrypt/decrypt, process restart, corrupted-store/no silent reset,
   identity switch/owner close while an actual request is pending and repeated tapping.
4. Existing HTTPS/TLS trust and deadlines on Wi-Fi/cellular, offline/timeout/old backend,
   expired paid access without VPN, clock skew/time-zone changes, fresh vs cached rendering.
5. Notification permission denied/granted, duplicate/restarted durable flags, superseded
   cancellation, foreground behavior and cold/warm notification→subscription navigation.
6. Separately authorized backend/ingress qualification before any production rollout.
   No installed/public endpoint readiness or delivery guarantee is claimed by these tests.

Versions unchanged: Android source118 (`0.1.18-beta118`), previous opt-in field118;
invitation/updater113 and signed catalog7. No distribution was rechecked, APK was built
or updater published. Paid baseline108 (`0.1.18-beta108`)/cohort/cap10,
admission/certificates, renewal, VPN routing and G4 combination
are unchanged. There was no rollout to roll back; discard/revert this isolated source
change if needed, not any running service, data or G4 artifacts. Preserve checkpoint47ef0463.

## Changed code/test areas

- Backend: `control/friends/subscription.py`, purpose allowlist in `access.py`,
  `deploy/friends/access-api.py`, installer allowlist, exact Nginx snippet, HTTP runtime
  source manifest and `scripts/package_friends_http.py`.
- Client: `messenger/subscription_view.py`, `store.py`, `local.py`, Android `fc_chat_store.py`,
  `FriendsAccessAndroid`, `ChatLocalAndroid`, `ChatRuntime`, `SubscriptionRequest`,
  `SubscriptionRefreshGate`, `SubscriptionUi`, `SubscriptionPresentation`, RU/EN strings.
- Tests: `tests/test_subscription_http.py`, resource assertion in `test_subscription_view.py`,
  JVM `SubscriptionRequestTest`, `SubscriptionRefreshGateTest`, `SubscriptionPresentationTest`.
- Tracking: STATUS, PLAN, this report and the historical checkpoint report cross-link.
