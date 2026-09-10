# Device registration: single-host product-plane stage

Update 2026-09-10: [provisioning delivery, migration v2 and cache](provisioning-provider.en.md) are implemented. The v1 registration stage is described below; the current migrator upgrades the database to [v3](gateway-reconciliation.en.md).

Date: 2026-09-09. Implemented in source and tested locally; not deployed to the public gateway. Existing Linux/Android/Windows clients still use their previous onboarding. [Identity/provisioning ADR](adr/001-identity-provisioning.en.md).

## What is working

A separate service authorizes a new independent Reticulum identity through a family invitation. The operator grants a family entitlement locally. The device generates its own identity and WireGuard key, obtains a server challenge using an invitation, signs its key binding, and completes registration. The database stores public keys only. No configuration file or client private key is accepted by this API.

The invitation is an enrollment bearer capability, not a VPN credential or shared identity. A 256-bit random invitation token and 256-bit random challenge are stored only as SHA-256 hashes. Challenge validity is at most 120 seconds and is clipped to invitation/entitlement expiry. A challenge is bound to one invitation and both public keys. Completion rechecks current authorization inside the same transaction as device insertion, key registration, invitation usage increment, challenge consumption and technical audit insertion.

Concurrent requests cannot spend one challenge or invitation use twice, or exceed the family device limit. Duplicate identities cannot silently move families, re-enroll after revocation, or share the same WG public key. Invalid signatures and failed transactions do not partially enroll devices. Independent device revocation leaves other family devices authorized. Entitlement revocation invalidates the entire family grant and increments its revision.

**Revocation in this stage affects the product database only. It does not remove existing WireGuard peers or stop existing VPN tunnels.** Gateway reconciliation and provisioning issuance are subsequent stages. Account login, billing/subscription webhooks, family-owner self-service and authenticated registration recovery after a lost success response are also not implemented. A replay receives 403; clients must not interpret a network timeout as proof that registration failed.

## Storage decision and migration

`control/migrations/001_product.sql` creates families, entitlements, invitations, challenges, devices, device-entitlement membership, independent public transport keys and bounded audit event types. There are no account credentials or payment records yet. An operator-created family is a pilot grant, not evidence of a paid subscription.

Use a **dedicated local SQLite database for this single-host stage**, never another application's database or the lab's signed catalog. Transactions use `BEGIN IMMEDIATE`, foreign keys and unique constraints. SQLite permits one writer at a time; write-lock wait is bounded to five seconds. This is not a multi-host storage design. Before multiple control replicas, introduce PostgreSQL migrations/row locking and rerun concurrency tests; this SQLite migration must not be applied to PostgreSQL. See [SQLite transactions](https://www.sqlite.org/lang_transaction.html).

The containing directory must be owned by the service user and mode 0700; the DB must be an owned regular 0600 file, not a symlink/hardlink. Use local disk and trusted parent directories. Data is protected by filesystem access, not database encryption. Installation explicitly runs the migration; HTTP startup never grants access or initializes a schema. `PRAGMA user_version` tracks migration version. Re-running v1 is harmless; newer schema versions are rejected by migration.

Back up this separate DB using SQLite's online backup facility, or stop the product process and copy the DB and any journal consistently. Protect backup permissions identically. Do not restore while writes are active. Restoring an old backup can resurrect invitations/revocations: invalidate outstanding invitations and review authorization before reopening registration. Old v1 lab files are never migrated. Rollback means stop the new service and retain its DB; do not downgrade schema or erase registered identities.

## Local operator runbook

Run from the repository in a dedicated Python virtual environment. Commands below create new product state only; they do not connect a VPN or update peers.

```sh
pip install -r control/requirements.lock -r device_identity/requirements.lock
mkdir -m 700 state-product
python -m control.product.admin --database state-product/product.db migrate
python -m control.product.admin --database state-product/product.db create-entitlement --days 7 --devices 5
```

The last command prints public family/entitlement identifiers. Use the returned entitlement ID:

```sh
python -m control.product.admin --database state-product/product.db create-invitation --entitlement ENTITLEMENT_ID --hours 24 --uses 1 --output state-product/invitation.json
```

The new 0600 output file contains the secret invitation token; it is not printed. Transfer it only through the intended private invitation flow. Do not paste its contents in logs, issue trackers, shell arguments or source control. The output file must not already exist. If output writing fails after issuance, treat the invitation as unissued to the user and revoke it via operator review before retrying.

Start a loopback-only development service:

```sh
FC_PRODUCT_DB="$PWD/state-product/product.db" python -m uvicorn control.product.api:app_from_env --factory --host 127.0.0.1 --port 18081 --no-access-log
```

Never expose this HTTP listener directly. Public integration requires TLS termination, request/header/body timeouts, request-rate and concurrent-connection limits, and redaction/disabled body logging at proxy and APM layers. Tokens belong in a JSON POST body, not a URL. The service provides no public admin routes and no CORS enablement. Application body parsing is limited to 8192 bytes, duplicate fields rejected, errors fixed, and responses `Cache-Control: no-store`. There are at most 16 live challenges per invitation; this is not a substitute for global ingress rate limits.

Maintenance and trusted operator revocation:

```sh
python -m control.product.admin --database state-product/product.db prune-challenges
python -m control.product.admin --database state-product/product.db revoke-invitation INVITATION_ID
python -m control.product.admin --database state-product/product.db revoke-device DEVICE_IDENTITY
python -m control.product.admin --database state-product/product.db revoke-entitlement ENTITLEMENT_ID
```

Schedule challenge pruning before deployment. Expired challenges are removable without enabling replay. Audit records contain only fixed event type, subject reference and server timestamp; no IP, token, proof, exception text or traffic. These references are linkable product data, not anonymous beta analytics. Set audit/backup retention before a real-user rollout; this stage does not implement automatic audit retention.

## API contract

`POST /v2/registration/challenge`, `Content-Type: application/json`:

```json
{
  "invitation_token": "<64 lowercase hex characters>",
  "public_identity": "<canonical base64 of 64-byte RNS public identity>",
  "wireguard_public_key": "<canonical base64 of 32-byte WG public key>"
}
```

Success: `challenge` (base64), `expires_at` (Unix seconds), `audience` (`family-connect/enrollment/v1`). Call `DeviceIdentity.prove_transport_key(challenge)` locally. Submit that exact signed proof as the body of `POST /v2/registration/complete`.

Success: `device_identity`, `entitlement_id`, `entitlement_revision`, `status: enrolled`. This receipt is not a bearer access token and does not authorize future provisioning requests by itself. Future fetches need independent ownership authentication.

Errors: 400 `INVALID_REQUEST` for malformed bodies; 403 `REGISTRATION_REJECTED` for invalid/expired/consumed authorization or proofs; 503 `REGISTRATION_UNAVAILABLE` for SQLite failures. Rejection does not disclose which invitation/device exists. Do not retry 403 indefinitely; 503/timeouts need bounded backoff and eventual authenticated recovery.

## Validation and compatibility

New tests cover restart persistence, idempotent migration, wrong identity/key/signature, expired and revoked grants, replay races, invitation/family capacity races, no partial writes, independent revocation, cross-family/key reuse prevention, secret-free DB records, pruning, HTTP flow, error redaction and malformed bodies.

The legacy Docker control build now runs tests in a separate stage with all required new modules/dependencies, then retains the original control runtime and operator scripts. No new API is mounted on v1 and no live Compose service is changed. The existing client engines are untouched. See the implementation log for actual test outcomes and remaining gates.
