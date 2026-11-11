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
and2 closed-kit/Compose-merge checks pass.34 panel checks pass against isolated
PostgreSQL and the actual Unix worker.
The Android124 debug app and instrumentation compile; lintDebug passes. Linux
explicit package closure includes the new shared support module; previous targeted
GI-enabled closure check passed. No unrelated VPN/G4 suite was repeated.

The earlier isolated real browser→worker→RNS mailbox→Android exchange reached
recipient_stored and returned a reply, with two separate synthetic app identities,
notification/deep link, offline queue, restart and lost-response dedup checks.
**That earlier fixture is not acceptance:** it injected the role and required a
resumed client exchange to flush its UI reply.

The replacement fixture `https5` now passes the actual round trip. Two separate
Android packages create their own Keystore device/chat identities and activate/register
through the real packaged HTTPS API; the certificate is trusted only in explicit
emulator instrumentation, with hostname verification intact. Guest-only firewall
rules redirect the fixed endpoint into the isolated container and reject other
egress. No production registry/phone is involved. The real forced-SSH importer,
systemd mailbox, acknowledged lease, ordinary Android worker and real browser UI
are used, not transport mocks or direct role injection.

- Browser sends with mailbox offline; exactly one encrypted queued record survives
  duplicate POST and panel/worker restart. Restarted mailbox accepts the same ID.
- Client2 completes its ordinary mailbox cycle without receiving client1's message.
  Client1 posts the private official notification; its PendingIntent opens the exact
  existing ChatActivity dialog. A real composer/button reply reaches the same card.
- Panel observes relayed before recipient_stored, then the incoming reply. Panel,
  worker, mailbox and both client processes restart without losing history/identity.
- A browser response is deliberately dropped **after the real POST completes**.
  The form now retains its signed UUID/text, reports the unknown outcome and enables
  retry without navigation or regenerating the ID. A real second button click creates
  no duplicate; Android stores/ACKs the one message. Two Node built-in regression
  tests cover double click/lost reply and validation correction, in addition to the
  actual browser/runtime qualification. An initial harness mistake used two different form IDs; those two
  independent messages remain in private evidence, not counted as a dedup failure
  or as acceptance evidence. The corrected same-ID run passes.
- Actual browser requests reject GET send, missing CSRF, excessive UTF-8 text,
  recipient/token tampering, unknown cards and a view-only operator's send. Audit
  contains IDs/statuses, not the synthetic message bodies.
- Client2 publishes a real foreign-sender message through the mailbox. Client1's
  ordinary worker reports a rejected payload and does not store it. Renaming a
  normal contact to the support label does not grant the verified official role.

Private receipts: `/mnt/data/fc-support-chat-20261110/https5/result.json`,
`negative-result.json`, `unit-result.json`; raw logs, credentials, screenshots and
databases stay outside Git. API35 and API27 VPN OFF are tested over an available
emulator network. The separate `https27/result.json` and `negative-result.json`
confirm two-client round trip, notification/UI reply, restarts, real same-ID button
retry and foreign-sender rejection on Android8.1, the Friends minimum API. Its first
attempt hit the pre-existing selection of a background cellular Network100 (EACCES);
qualification used Wi-Fi with only the synthetic emulator's cellular data disabled.
No network-selection code was changed, and cellular/multicarrier success is not
claimed. Neither run is an offline-delivery promise nor Russian-whitelist evidence.
The emulator is singular under the shared lock, KVM/host GPU; its actual GLES renderer
is NVIDIA GTX1650Ti, not software rendering. No physical owner device is used.

Candidate version is `0.1.18-beta124`, versionCode124. Existing123 artifacts and
catalogs are untouched. Only isolated debug artifacts exist; release qualification,
signed ARM64 artifact/checksum and hosted
review/ordinary merge remain open. Public guides retain their existing downloads.
This checkpoint skips automatic broad CI; no hosted gate is claimed passed or waived.
The existing Control panel workflow now has an explicit `support_candidate` dispatch:
panel regression/image, messenger/support contracts and a source-bound unsigned ARM64
candidate with JVM/lint checks. It rebuilds pinned native dependencies but does not
repeat unchanged VPN/G4/transport runtime suites. Applicable final-head CI and
independent review remain required; final identities/results belong in [draft PR18](https://github.com/Joker20380/family_connect/pull/18).
No hosted run or review is currently recorded. This session's GitHub connection
can create/read the PR but exposes no initial workflow-dispatch action; there is no
authenticated local `gh` command. No credentials were searched in unrelated services.
The exact remaining dispatch from an authorized GitHub session is:

```sh
gh workflow run control-panel.yml -R Joker20380/family_connect \
  --ref feature/support-chat-1-20261110 -f support_candidate=true
```

Wait for the three jobs and inspect their artifacts/review before an ordinary merge.
This is a pending gate, not a green CI result or permission to publish/install124.

## Commissioning and local installation gates

Source components: `control/friends/support.py`, existing chat-sync publisher,
`deploy/friends/support-bindings-read.py`, `provisioning/support_bindings.py`,
`provisioning/support_worker.py`, and `deploy/support-chat/` systemd units.
They are **not installed production service instances**. The closed candidate kit
is built with `python -m scripts.package_support_chat --output <private-output>`.
Local archive: `/mnt/data/fc-support-chat-20261110/support-kit-candidate124.tar.gz`,
SHA256 `09295fed04b444558bedc1021a05938b111865ee415047dd22acadb34975afb3`.
It contains65 allowlisted source/configuration files plus a hash manifest, the
packaged HTTP API, separate registry helpers, worker/collector, pinned dependency
locks, systemd units and a socket-only Compose overlay. No identities, credentials,
database, backup or release-signing material is included.

The unchanged packaged units run in an isolated systemd container: nonroot
`fc-support`, strict filesystem protection, private devices, no-new-privileges and
group-only Unix socket. A separate root collector uses a different SSH key restricted
to `support-bindings`; the worker cannot read that key. Actual SSH collection and
worker restart preserve the five-record synthetic encrypted history. The web overlay
merges with, rather than replaces, existing PostgreSQL/synthetic volumes; it mounts
only the socket directory read-only and grants its numeric IPC group, not keys/state.

### One commissioning sequence, not an automatic rollout

1. Complete hosted candidate qualification and review/merge; retain exact accepted
   source/artifact hashes. Verify the kit manifest in an empty staging directory.
   Never install a test certificate or emulator endpoint redirection in production.
2. An authorized operator must designate a dedicated, registered support device/chat
   identity and provide its **existing** encrypted store and external storage key.
   No user identity is reused/created on their behalf. These inputs are currently
   missing; stop here rather than searching other services' secrets or auto-generating
   a replacement. The stored chat public key must equal the approved sender public key.
3. On the authorized registry, back up access.db consistently before the additive
   `ChatAccess.initialize()` migration. Deploy the verified HTTP artifact and helpers
   through its existing maintenance procedure. Root-owned `chat-support.json` has
   exactly schema1, sender_device32hex, sender_public128hex, positive revision and
   enabled boolean. `support-inventory-hmac.key` must be the existing full inventory
   HMAC key, not a new key. Keep it root-owned0600; do not copy it to panel/worker.
   Existing chat-sync membership publication must ACK before publishing the projection.
4. Provision one separately scoped key with authorized_keys restriction
   `restrict,command="<existing-python> -I /opt/apps/family_connect/friends-access/support-bindings-read.py"`.
   Pin the host key out of band. Do not reuse an unrestricted operations credential.
   Set collector-only `/etc/family-connect-support-bindings/source.env`
   (`SUPPORT_REGISTRY_HOST`), `readonly.key` and `known_hosts`, root-owned0600.
5. Install kit `app/` and an independent venv under `/opt/family-connect-support/`;
   install provisioning.lock, then messenger.lock with `--no-deps --require-hashes`.
   Never upgrade a VPN environment. Create `fc-support`, groups `fc-support-ipc` and
   `fc-support-read`. History lives at `/var/lib/family-connect-support/history`
   (fc-support0700); external key at `/etc/family-connect-support/store.key`
   (fc-support0600); sender.env contains only `SUPPORT_SENDER_PUBLIC`.
   `/var/lib/fc-support-bindings` is root:fc-support-read0750. Install the three units,
   run the collector, verify the exact binding/sender/lease, then start worker/timer.
   Missing store/key must fail startup, never create an identity automatically.
6. After the panel backup/restore gate, merge `panel.override.yaml` with the installed
   Compose files; set `FC_SUPPORT_IPC_GID` to the actual group number. Preserve existing
   project name, volumes, env secrets and collector/source pins. The web image gets
   no SSH/registry/key mount. Apply migration0012; grant separate view/send permissions
   only to approved operators. Inspect the complete canonical device and chat address.
7. Install the separately qualified124 artifact only by an explicit deployment decision;
   enroll through the authenticated API.123 remains blocked for verified support.
   Send one explicitly authorized message and verify signed storage ACK plus a client
   reply before declaring production ready. No batch-send operation is part of the kit.

Rollback: stop the support worker and binding timer, remove only the socket overlay,
return the panel to its prior verified image, and retain all history/keys/volumes.
Migration0012 is additive permissions, not a data reset. Disable the support policy
with an increasing revision and publish it before stopping its publisher if clients
must receive a durable revocation. Do not roll the registry back to a pre-migration
binary with positional two-column inserts against the new schema; use the compatible
artifact with support disabled, or a separately reviewed frozen-registry restore.
Never automatically restore an old registry snapshot over newer enrollments.

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
