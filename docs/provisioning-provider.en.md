# Authenticated provisioning delivery and cache

Update: migration v3 now requires [staging and confirmed gateway reconciliation](gateway-reconciliation.en.md). The manual --peers-ready workflow below describes the historical v2 stage; that flag has been removed. Use commands in the new document.

2026-09-10. Local product implementation; not deployed, no VPN peer changes.

## Protocol and persistence

`POST /v2/provisioning/challenge` accepts exactly `public_identity` and
`wireguard_public_key` (canonical base64). The registered identity, key and
entitlement must be active. Response: `challenge`, `expires_at`, and
`audience=family-connect/provisioning-fetch/v1`. Challenges expire within 120 seconds
and entitlement validity, are stored as SHA-256 hashes, and bind both keys.
At most 16 unconsumed live challenges are allowed per device.

`provisioning.auth.prove(device, challenge)` signs schema 1, the fixed audience,
both keys and nonce under a separate fetch domain. POST the complete proof as JSON
to `/v2/provisioning/fetch`. Enrollment proofs are not accepted. One transaction
rechecks device/key/entitlement authorization and the latest publication and consumes
the challenge. Concurrent replay has one winner. Successful delivery returns the
stored ciphertext/signature envelope, without client private credentials.

After a lost response, use a fresh challenge to retrieve exactly the same bytes.
Fetch does not create revisions. No ACK or tunnel application is implied. The server
never falls back to an older version. Errors: 400 `INVALID_REQUEST`,
403 `PROVISIONING_REJECTED`, 503 `PROVISIONING_UNAVAILABLE`; bounded bodies, fixed
errors and `no-store`. TLS, ingress timeouts/rate limits and redacted body logging
remain deployment requirements, as for registration.

SQLite migration v2 transactionally preserves v1 enrollment data and adds fetch
challenges and immutable per-device versions. History contains encrypted envelopes
and public lease/key/entitlement metadata, not traffic. No history pruning is
implemented. Never remove the maximum revision or restore an old database to reset
versions. Follow the [registration backup/storage requirements](registration.en.md).
After restoring an old database, clients may reject revisions until their persisted
floor is exceeded; there is no automatic floor reset.

## Operator workflow

```sh
python -m control.product.admin --database state-product/product.db migrate
python -m control.product.admin --database state-product/product.db init-provisioning-signer --key-directory state-product/signing
```

Initialization creates a dedicated RNS signing identity, a 0600 `signer.key` in a
0700 directory; reruns cannot overwrite it. Only the public anchor is printed.
Distribute that anchor through an already trusted channel. No TOFU or anchor
rotation is implemented. The HTTP process serves stored envelopes without loading
the signing private key.

The network JSON accepts exactly `addresses`, `dns`, and `gateways`. Each gateway
requires `gateway_id`, `provider_id`, two-letter `region`, `transport=wireguard`,
IP `endpoint`, `port`, and canonical base64 WG `public_key`; optional `asn` is
supported. See the [complete example](provisioning-provider.ru.md).

Install peers and verify unique device addresses and every gateway candidate before:

```sh
python -m control.product.admin --database state-product/product.db publish-provisioning DEVICE_IDENTITY --network network.json --key-directory state-product/signing --lease-seconds 3600 --peers-ready
python -m control.product.admin --database state-product/product.db provisioning-versions DEVICE_IDENTITY
python -m control.product.admin --database state-product/product.db prune-challenges
```

`--peers-ready` is an explicit operator assertion, not a gateway probe. The database
supplies recipient, revision, registered key and entitlement. Leases last at most
24 hours and cannot exceed entitlement expiry. Renew by publishing a new version.
Signing/storage failures roll back the revision. Address allocation, peer
reconciliation/outbox and peer removal on revocation remain separate work.

## Linux reference client

`ProvisioningClient(http_client, device, cache)` takes a configured `httpx.Client`
with an HTTPS base URL and bounded timeout. `refresh(now=...)` authenticates a fetch
and passes the bounded response to the cache. Redirects and automatic retries are
disabled. Retry a timeout with a fresh challenge. Authorization failures propagate;
`cached(now=...)` is explicit offline access, not automatic error fallback.

Initialize `ProvisioningCache(path, verifier)` once with `initialize()` under trusted
local application storage. Supply the verifier with the pinned public anchor, local
identity and WG public key. `accept`/`load` return `VerifiedProvisioningState`, never
apply a tunnel. The cache stores ciphertext, revision/entitlement floors and time
using 0700/0600 permissions, flock, atomic replace and fsync. Exact stored bytes may
be redelivered. Other envelopes must increase revision without decreasing entitlement
revision. Loading rechecks signature, recipient, WG key and lease. Expiry preserves
floors; observed backwards clock movement is rejected, including after expiry.

Missing/corrupt files, symlinks, hardlinks and unsafe permissions fail closed.
Reinitializing an existing directory is prohibited. File permissions cannot stop
an owner/root attacker restoring an entire old backup and are not hardware rollback
protection. Callers must supply trusted UTC `now`. Native DPAPI/Keystore and UI
integration remain pending. Revocation blocks server fetch immediately; offline
cache remains authorized until its signed lease expires. This module does not stop
an already running VPN tunnel.
