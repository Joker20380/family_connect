# 5N-PROV-1 controlled deployment — authorization required

**Current preflight checkpoint,01.10:** [refresh / owner hidden-input boundary](../../../docs/releases/2026-10-01-5n-prod-deploy-preflight.ru.md).
Same authority/admission, publisher CRL sequence2 expires11:26:23UTC, gateway leaf
12:11:23UTC. Token access is now owner-interactive only: the staged
[`provision-provider-env.py`](provision-provider-env.py) requires root/TTY,
refuses echoed fallback/overwrite, writes only final root0600 provider.env and
checks schema without outputting the value. No agent unlock/export of KeePass.
Input pending; no runtime service/API/ingress deployment authorized by this step.
Recheck expiry after owner input; never extend TTL or reuse expired CRL to deploy.

**Authority checkpoint,01.10:** [5N-PROD-AUTHORITY READY](../../../docs/releases/2026-10-01-5n-prod-authority.ru.md)
prepared the first signed Friends restricted Family, sole owner grant, existing NL
control-provider gateway designation, issuer/CRL/profile and inactive runtime/sync
templates. Files remain under root-only `restricted-materials-stage-20261001/`,
not these final runtime paths. Only four accepted additive restricted tables were
created. Initial CRL expires01.10 11:02:45UTC; refresh it via the publisher (preserving
sequence) before later use. Do not regenerate Family/identity/floors or rerun first
initialization. Provider token was expressly excluded; do not access KeePass or
activate services/API merely because authority preparation is READY. Previous
implementation-only statements below describe the original checkpoint.

Local implementation only, 2026-10-01. **Do not execute this rollout without a
separate authorization.** No production keys/configuration have been generated
by this task. No diagnostic credentials may be reused. This is an owner-device
canary, not general rollout or Krasnodar FIELD-1.

## Production API and trust contract

The existing RU Friends HTTPS ingress and `family-connect-friends-access.service`
serve two bounded POSTs, using the existing activated Device Identity, not Family
mTLS (which cannot be a prerequisite for initial delivery):

1. `/friends/restricted-readiness/challenge`: existing `public_identity` and
   `wireguard_public_key`. Response: challenge, expires_at, existing enrollment
   audience. The stored nonce is purpose-bound to `restricted`, Family and grant
   revision; maximum eight outstanding device challenges, existing 100s TTL.
2. `/friends/restricted-readiness`: existing transport-key proof. Response keys:
   `version`, `device`, `challenge`, `issued_at`, `expires_at`, `revision`, `issuer`,
   `certificate`, `revocations`, `minimum_crl`, `directory`. No private keys,
   OAuth, dedicated room descriptors or normal transport credentials.

Existing HTTPS authenticates delivery. Proof possession, exact public identity/WG
binding, active invitation/device/grant, admission policy, expiry, nonce replay,
revision, signed CRL and issuer validity are rechecked before issuance. Requests
are at most 8KiB, responses at most 64KiB, existing concurrency limit four.
Responses are no-store. Authorization rejection is 403; unavailable configuration,
provider snapshot or CRL is 503, not evidence of device revocation.

An eligible **already activated** device gets a restricted grant automatically.
Existing Friends activation is perpetual, so this mapping has no invented billing
expiry; certificate/CRL/directory validity remains finite. Optional finite grants
and increasing revisions are supported by the operator CLI. A revoked, expired or
wrong-Family existing grant is never silently recreated. Start with only the
owner's verified device reference in `admission.json`; do not use `*` for the canary.

## Delegated issuer, not another trust root

The existing packaged `control-anchor.pub` authorizes an online Ed25519 Family CA
through a domain-separated offline signature. This bridge is needed because the
accepted Family issuer was an isolated fixture, not an existing production issuer.
The CA alone is **not** an additional trusted Android root. No root key goes to
RU/NL. No standalone BootstrapDirectory signature is introduced.

`issuer.json` is `{payload: base64, signature: base64}`. Decoded payload has exactly
`version:1, sequence, family, gateway, authority, minimum_revision, issued_at,
expires_at`. The authority is one canonical PEM CA certificate, with Ed25519,
CA/pathLen0, cert-sign/CRL-sign usage and validity covering the delegation. Family
and gateway are the selected authoritative 32-hex references, not arbitrary
request parameters. Sequence increases on delegation changes. `minimum_revision`
is the global peer floor; per-device grant revision is checked independently.

After authorization, generate the **delegated issuer** key in protected server
storage (0600, no stdout), transfer only its public CA to the offline signer,
prepare bounded delegation metadata and use, from the repository root:

```sh
python -m scripts.sign_restricted_issuer --input /protected/issuer-payload.json \
  --output /protected/issuer.json --key /protected/existing-control-root.key
```

The signer requires the exact existing packaged root; a different key is rejected.
Use the existing protected signing-key/vault workflow, not a new root. Review
Family/gateway identity, sequence, peer floor and delegation duration explicitly;
there are deliberately no production default IDs or private keys in these files.

Device certificate: existing Ed25519 public identity, full public-identity URI,
Family/role/device-revision claims, existing `family-connect-5n3-test-v1` protocol
and TLS1.3. The name is historical, not a request to use diagnostic credentials.
Android assembles the accepted `familysession.Credentials` in memory using the
**existing** encrypted Device Identity secret. No delivered/private second identity,
static APK credentials or plaintext SharedPreferences key.

## Exact deployment scope and order

Before changing anything, verify live paths/service definitions/ports and available
disk on the two authorized hosts; take private SQLite online backup plus saved API,
ingress and unit artifacts. The last deployment receipt is historical; a local
commit/build is not proof that a host runs it. Excluded host `186.246.51.201` and
neighbouring services are out of scope. Do not run first-install scripts over the
existing Friends deployment.

### RU — 185.251.89.19:/opt/apps/family_connect

- Deploy reviewed `control/friends/restricted*.py`, unchanged required packages
  (`control`, `device_identity`, `provisioning`) and `deploy/friends/access-api.py`
  into the existing `friends-access/app`/handler layout. Use existing control and
  identity lockfiles in `friends-access/venv`; verify cryptography compatibility.
- Create protected `friends-restricted/` (0700): `anchor.pub`, `issuer.json`,
  `issuer.key` (0600), `admission.json` with **only owner device**, initial
  `revocations.pem`, subsequent `directory.json`, dedicated `sync.key` and pinned
  `known_hosts`. Public delegation/CA are not secrets; directories/CRL seed URLs
  are still private operational state. Never print responses or profiles.
- With `FC_FRIENDS_RESTRICTED_DIR=/opt/apps/family_connect/friends-restricted`, run
  `python -m control.friends.restricted_admin --db
  /opt/apps/family_connect/friends-access/access.db migrate` using that venv.
  Same-DB additive tables: restricted_grants, restricted_challenges,
  restricted_certificates; publisher creates restricted_crl_sequence. No existing
  rows/identity/configuration are reset. Migration is explicit, never at request
  time. Run `publish-crl` action to initialize the signed CRL.
- Install the `access.conf` drop-in for `family-connect-friends-access.service`
  only after the seed/sync is ready. Insert `nginx-location.conf` into the existing
  `family-connect-product-https` vhost; validate and reload, not replace the vhost.
  It proxies only the new paths to existing loopback 18084.
- Install the new `family-connect-restricted-sync.service` and `.timer`.
  Every 30s after completion it publishes a 15-minute signed CRL, sends **only CRL**
  to NL and imports the READY directory. SSH timeout15s, unit timeout25s, output
  cap, exact known-host pin, no agent/port forwarding, no provider request here.

### NL — 186.246.45.246:/opt/apps/family_connect

- Deploy a fresh reviewed host `bootstrap-broker` binary under
  `friends-restricted/bin/`, Python sync helper/dependencies in
  `friends-access/app`/`venv` (reuse only if verified present and compatible), and a
  dedicated `family-restricted` service account. Do not change AWG/TCP services.
- Use the selected **existing gateway Device Identity**, keeping its secret on NL.
  Send only public identity to RU; `restricted_admin gateway-certificate
  --public-identity ... --expires ... --output /protected/gateway.pem` enforces
  the delegated gateway reference. Assemble accepted `gateway.json` (0600) on NL
  with that certificate, existing gateway Ed25519 private key, delegated public
  authority, initial signed CRL, Family/gateway and revision/CRL floors. No fixture
  issuer/profile or owner-device private key. Renewal of the gateway certificate
  is operational PKI maintenance before expiry, not Android enrollment.
- The dedicated RU sync public key must have an sshd forced command invoking
  `python -m control.friends.restricted_sync gateway --profile
  /opt/apps/family_connect/friends-restricted/gateway.json --directory
  /opt/apps/family_connect/friends-restricted/directory.json` with the verified
  NL venv and app working directory. Use a root-owned wrapper, `restrict`, source
  address restriction to RU, no shell/PTY/forwarding, no access to other services.
  This helper accepts a signed monotonic CRL and exports only a validated directory;
  it does not receive private keys. Do not repurpose existing peer-registration keys.
- Install `family-connect-restricted-bootstrap.service`, preflight new loopback
  `127.0.0.1:18444` unused (no public port). Protected `provider.env` supplies
  **server-only** `YANDEX_TELEMOST_OAUTH_TOKEN`; token rotation/revocation stays in
  the existing provider operational process. Neither APK nor RU API receives it.
- Start seed service, wait for READY and bounded directory export, then enable RU
  sync and API drop-in/ingress. No seed directory is published before READY. Rooms
  for dedicated sessions are created only on an admitted recovery request.

The templates are reviewed local artifacts, **not installed units**. Ensure NL
bootstrap process and forced helper can access only the intended private directory.
Current CRL/profile is reloaded on Family admission; no gateway restart per CRL.
Do not expose the legacy mTLS cache-preparation listener publicly.

## Lifetime, refresh, and revocation limitations

- BOOT-1 v1 unchanged: <=1h directory, 8KiB, up to four bootstrap seeds with
  authenticated Telemost `join_url`. Deployment seed process55min; restart30s.
  Export occurs only after READY. A dead seed may remain in a valid cached snapshot
  until expiry; single-seed rotation/restart can temporarily reduce availability.
- Device certificate <=1h and bounded by grant/delegation/current CRL. This CRL
  publisher uses **15min**, so actual readiness is at most15min and may be shorter.
  Dedicated unused descriptor remains60s, established session default10min;
  dedicated descriptor is never stored as readiness or LKG.
- Android refresh: activation, successful normal profile acquisition, foreground
  resume/60s maintenance checks; **not 60s network polling**. Missing/invalid or
  <=300s remaining triggers one worker, persistent300s attempt cooldown,30s network
  deadline. No alarms/background polling. Valid cache doesn't block CONNECT.
- 403 tombstones usability durably; timeout/503/invalid/stale refresh leaves valid
  old response intact. Higher issued/revision/CRL/delegation/directory floors
  prevent replay even after expiry. Restart keeps encrypted state and cooldown.
- Revocation reaches the gateway on the next successful server sync, normally
  about30–45s; failed sync is bounded by the **previous signed CRL's expiry**, up to
 15min, not instantaneous offline revocation. API checks current DB immediately.
  Existing sessions additionally obey the accepted Family session expiry policy.
- Prewarm immediately before an authorized local/field attempt. Offline recovery
  hours after last control contact is **not supported by this gate**. Extending
  seed/CRL/directory validity needs separate security/product review.

## Acceptance, downtime, rollback

Expected impact: one short Friends API restart (seconds expected, not measured),
validated ingress reload, new isolated NL seed service; no AWG/TCP restart or planned
data-plane outage. Canary operational checks must confirm this expectation.

After authorized server deployment: build a **private validation** Friends APK with
fresh normal/restricted JNI, same signing certificate, increasing private version;
install in place (no uninstall/pm clear). Ordinary Internet + actual identity must
produce READY, then process restart must retain READY. Only then run the separately
described local forced-normal-failure rehearsal: Wi-Fi off, cellular on, Auto,
no manual room URL/diagnostic credentials/traffic forwarding; browser, Family DNS
and retained-TUN fail-closed must pass. Only **after** this live integration passes
may the final shareable FIELD APK be produced. Existing field52 is not that artifact.

Rollback: disable new ingress routes/drop-in and stop only the new sync timer/seed
service; restore saved API/ingress artifacts and restart control. Preserve additive
DB tables, latest revisions, certificate serial history and CRL/issuer floors;
**never restore an old full DB over new revocations**. Preserve protected identity
and key material. Existing Android normal paths remain usable; correct Android via
same-signature forward update, not downgrade/data clear. A cached seed may stop
working after rollback; the existing Orchestrator must fail closed on exhaustion.

No deployment, root signing, live proof, APK release, push or FIELD-1 was performed
while writing this runbook. See the [gate report](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).
