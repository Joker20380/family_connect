# Restricted product readiness receipt v1

Local implementation/acceptance only. No production deployment, authority refresh,
device installation or FIELD-1 is authorized by this document. This supersedes UI
collection as the owner-product gate in OWNER_PROOF_HANDOFF.md, not its server,
admission, lifetime, transaction or rollback contracts.

## Authoritative point

`FriendsReadinessProtocol.fetch` still performs the real application's purpose-bound
Device Identity proof. HTTP200 alone means no import acceptance. `ReadinessProduct`
calls `RestrictedCache.importProduct`: native `ValidateDelivery` (delegation,
certificate, CRL, device binding and BootstrapDirectory), existing monotonic checks,
then `RestrictedVault` Keystore-encrypted AtomicFile replacement and plaintext
readback comparison. Request correlation is saved inside that same encrypted atomic
state, not later inferred from a previous receipt.

Only afterwards `RestrictedCache.evaluate` re-reads and validates persisted state,
checks current expiry, and invokes **the same `usable()` predicate consumed by
`RestrictedTunnelEngine` through the Orchestrator**. READY is constructed after
those checks, with a post-import clock reading. It means credentials/bootstrap are
usable for restricted recovery, not that a provider session/VPN is already connected.
No traffic, browser or FIELD acceptance is implied.

## Transport-neutral schema

Payload `type=READINESS_IMPORT_RESULT`, integer `version=1`, maximum2048 UTF-8 bytes,
exact fields (unknown fields, duplicate JSON keys and wrong types are rejected):

- `correlation_id`, `challenge_id`, `fetch_id`: random32 lowercase hex; correlation
  equals challenge ID, fetch ID differs. No device-derived identifier.
- `result`, `failure_reason`: stable enums, never exception messages. READY uses
  failure_reason NONE. Other reasons equal their result code.
- `provisioning`, `bootstrap`: PRESENT_VALID only for READY, otherwise NOT_READY.
- `orchestrator_usable`: boolean, true only for READY.
- `revision`, `minimum_crl`, `expires_at`: validated safe metadata for READY;
  zero allowed for failures. Expiry is the effective bounded delivery expiry.
- `observed_at`: epoch seconds; `phase`: import or restart.
- `app_version` (bounded64 ASCII version characters), positive `version_code`.

Codes: READY, NATIVE_VALIDATION_FAILED, BOOTSTRAP_VALIDATION_FAILED,
ATOMIC_IMPORT_FAILED, PERSISTENCE_FAILED, EXPIRED_ON_IMPORT,
ORCHESTRATOR_NOT_USABLE, INTERNAL_ERROR, STALE_STATE, AUTHORIZATION_REJECTED,
FETCH_FAILED, MISSING. All numeric fields are bounded by2^53−1.

No identity, proof, public/private crypto bytes, certificate bundle, OAuth, seed or
room URL, exception string, traffic or user data is copied into this payload.
Native code returns bounded category codes; it does not stringify errors.

## Local durability and restart

`ReadinessReceiptStore` stores `{payload,ack_state}` in private no-backup app storage
`restricted-readiness-result-v1.json`, maximum4096 bytes. AtomicFile finish/rollback,
explicit fsync and readback are used. It is not exported, backed up, logged or
accessible through a shell/provider/debug endpoint. Metadata is safe; credential
material remains only in the existing encrypted vault.

Every attempted prewarm records its outcome before ACK transport. ACK_PENDING,
ACK_RECEIVED and UNKNOWN are delivery status, never local credential state.
ACK or receipt-storage failure cannot undo a successful credential import. If
receipt storage itself fails, durability is not claimed; ACK can still report the
actual imported result. If both channels fail, acceptance remains UNKNOWN.

Once per application process, first foreground prewarm re-reads the encrypted
bundle, revalidates native credentials/directory/current expiry and recomputes
`usable()`. It never trusts the previous receipt. It then writes a fresh restart
event and, when encrypted correlation exists, attempts one ACK. The usual
foreground prewarm/cooldown remains unchanged; no new polling worker/alarm or
independent retry transport. A canary54 legacy cache without correlation does not
invent a historical owner ACK; the next normal refresh supplies correlation.
Expired, denied, stale incoming or cryptographically invalid state cannot emit
READY. Offline revocation visibility remains bounded by the existing signed CRL
policy; this gate does not promise knowledge of unpublished revocation.

## Authenticated ACK on existing control HTTPS

The existing trusted Friends HTTPS transport and normal in-app proof primitive
carry READINESS_ACK as `{proof,receipt}`. Notices are a public/admin publishing
feed and are intentionally not reused for private device acknowledgements.
No new transport stack, exported signing method or unauthenticated status endpoint.

1. Existing challenge/fetch requests carry random `X-FC-Probe-ID` values. Private
   DB correlation records bind them to the admitted device and successful issued
   revision/CRL/expiry. Old clients without IDs retain their existing fetch protocol.
2. POST `/friends/restricted-readiness/ack-challenge` carries public binding and safe
   receipt. The server rechecks current grant/issuer/CRL/admission, bounds the payload
   and binds a one-use100s nonce (existing Access CHALLENGE_TTL) to its canonical SHA256 digest.
3. POST `/friends/restricted-readiness/ack` carries the real app's normal signed
   transport-key proof and identical payload. Purpose/device/key/digest/expiry/replay
   checks precede durable ACK storage. Changing the result after nonce issuance is
   rejected. READY metadata must match the recorded successful fetch; revoked or
   superseded grant/certificate cannot acquire an accepted READY ACK.
4. Readback again checks authorization and expiry. Missing, unavailable or stale
   ACK is ACK_PENDING/UNKNOWN, **not device readiness failure**.

Only additive `restricted_readiness_results` is introduced by the existing explicit
restricted migration. Correlations are bounded to16 recent attempts per device,
24h retention pruned on new attempts. Private DB device references never enter
safe support-facing receipts. No current DB is migrated by this local task.

## Future physical acceptance without gestures

The HTTP archive contains a read-only operator path (no listener or mutation):

```sh
python -I /accepted-new-bundle/friends-http.pyz --root /private/friends-access \
  --readiness-ack RANDOM_CORRELATION_ID --material /private/friends-restricted
```

Get the random correlation from scoped server challenge/fetch traces, not an app
private-state dump. The command binds readback to the sole admitted owner and
returns only the allowlisted ACK. Its SQLite connection is read-only. Pass this
fresh result plus the two generation-bound ingress receipts to `OwnerProduct.observe`.
The method rejects legacy UI-only receipts, mismatches, stale observations, missing
fetch proof, failures and ACK_PENDING. A valid authenticated READY ACK plus matching
challenge/fetch proves OWNER_PRODUCT_READY even if ADB gestures/UI are unavailable.
UI is supplemental only. ACKs are authenticated product statements, not hardware
remote attestation or proof that a compromised application runs unmodified code.

Existing pinned attempt14 HTTP/sync/readiness archives remain immutable and do not
gain this API retroactively. A separately authorized future deployment must build,
review and pin compatible new bundles/migration/nginx configuration. Do not deploy
canary55 against old APIs and claim receipt acceptance; a404 ACK leaves local
readiness intact but server evidence pending. Retire old HTTP only after real owner
ACK acceptance under the existing transaction. No automatic PROV-1 retry here.

DIAG-1 may later consume this event for incident/support metadata. OPS-1 may later
deliver the exact same versioned payload using a different authenticated envelope,
including Reticulum. Neither subsystem, routing nor Reticulum transport is built
by this gate.
