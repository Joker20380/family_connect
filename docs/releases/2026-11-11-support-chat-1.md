# SUPPORT-CHAT-1 —11 November2026

**IN_PROGRESS / SOURCE_CHECKPOINT / NOT_INSTALLED / NOT_ACCEPTED.**
Existing worktree branches from remote main87fbe744. The intervening RU incident
was handled separately; it is not a prerequisite or part of this change.

## Implemented boundaries

- The production device card gains Messages, history, explicit recipient/address,
  text/send/status/error and an inbox navigation entry. Existing panel style/auth
  remain. Permissions `view_support_messages` and `send_support_message` are
  separate. Sending is CSRF-protected POST, never GET; actor/recipient/request UUID
  are signed together, double clicks are disabled and the worker deduplicates retries.
- A root-owned projection maps full inventory HMAC to canonical device identity
  and its registered chat public key. No address guessing, Support-ID conversion
  or user identity creation. Explicit authenticated support-protocol enrollment
  pins the official sender in the existing chat binding; an additive SQLite column
  leaves old bindings unconfirmed. Old beta123 clients cannot satisfy this contract.
- Existing authenticated dual-proof chat registration returns a bounded support
  role only to an opted-in client. Android validates device/chat/sender/revision/
  expiry and stores the role encrypted. A display name or manually trusted contact
  cannot grant official status. Revocation/identity replacement blocks old queues;
  neither a later valid snapshot nor a contact rename silently reassigns them.
- A separate support identity owner uses existing Store, LXMF/RNS, durable outbox,
  DeliveryController/backoff and mailbox storage ACK. The Django image gets only
  a bounded Unix-socket interface, not SSH, the registry, HMAC, signing keys or a
  command-execution interface. A separate pinned forced-command collector has only
  binding-export access. No private message body enters PostgreSQL/audit/outbox
  plaintext; encrypted history/request dedup survive worker restart.
- This is private support, not service_events or announcements. The operator sees
  only conversations with the dedicated support identity, not other user contacts.
  Messages do not alter admission/subscriptions, execute commands, install APKs or
  acknowledge payments.

## Status meanings

| Status | Evidence |
| --- | --- |
| queued | encrypted local message/outbox/request transaction committed |
| sending | a transport attempt, not delivery |
| relayed | existing mailbox accepted the message; recipient storage not yet proved |
| recipient_stored | existing signed ACK emitted after client storage |
| received | incoming reply saved by the support identity |
| expired | existing delivery lifetime exhausted |

There is no read-receipt claim; opening the panel is not client reading. HTTP200,
queue success and a running worker are not substituted for a storage ACK. Offline
delivery waits for an available carrier and retains the same message identity.

## Evidence at this checkpoint

38 focused chat-identity/enrollment/migration/worker/security/packaged-HTTP checks
pass.34 panel checks pass against isolated PostgreSQL and the actual Unix worker.
The Android124 debug app and instrumentation compile; lintDebug passes. Linux
explicit package closure includes the new shared support module; previous targeted
GI-enabled closure check passed. No unrelated VPN/G4 suite was repeated.

The earlier isolated real browser→worker→RNS mailbox→Android exchange reached
recipient_stored and returned a reply, with two separate synthetic app identities,
notification/deep link, offline queue, restart and lost-response dedup checks.
**It is not acceptance:** that fixture injected the role and required a resumed
client exchange to flush its UI reply. New instrumentation instead uses the actual
HTTPS registration and ordinary ChatRuntime worker; that qualification is unfinished.
The emulator is singular under the shared lock, KVM/host GPU; its actual GLES renderer
is NVIDIA GTX1650Ti, not software rendering. No physical owner device is used.

Candidate version is `0.1.18-beta124`, versionCode124. Existing123 artifacts and
catalogs are untouched. Only isolated debug artifacts exist; release qualification,
signed ARM64 artifact/checksum, minimum-supported-API verification and hosted
review/ordinary merge remain open. Public guides retain their existing downloads.
This incomplete checkpoint skips automatic broad CI; no hosted gate is claimed
passed or waived. Applicable final-head CI remains required before acceptance.

## Commissioning and local installation gates

Source components: `control/friends/support.py`, existing chat-sync publisher,
`deploy/friends/support-bindings-read.py`, `provisioning/support_bindings.py`,
`provisioning/support_worker.py`, and `deploy/support-chat/` systemd units.
They are **not installed service instances**. The final tested commissioning kit
must still document exact immutable archives, identities, paths and rollback.

Required before real sending: an explicitly designated/registered official support
identity and its existing encrypted store/key; verified sender policy and fresh
node membership ACK; additive registry migration; independently scoped read-only
projection credential; separated worker/socket permissions; compatible enrolled
client; an operator explicitly granted send permission. Missing production
credentials are not permission to search other services' secrets.

The local panel still runs imagec179d1ae/database0011. Support migration0012 and
the app changes are not installed. Before updating it, verify actual runtime and
take a fresh consistent backup, restore it into an isolated database and compare
users/history/secrets/source pins. Preserve all volumes; no down-v/prune/reset.
No automatic mass send, RU/NL/paid-policy change or phone installation is part of
this checkpoint. Real sends must remain explicit authorized operator actions.
