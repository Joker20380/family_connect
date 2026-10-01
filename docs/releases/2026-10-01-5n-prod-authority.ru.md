# 5N-PROD-AUTHORITY — READY, preparation only

**Subsequent authorized refresh:** [deploy preflight / owner input pending](2026-10-01-5n-prod-deploy-preflight.ru.md)
preserves this Family/issuer/grant/gateway, advances CRL1→2 and renews short-lived
leaves without TTL changes. New CRL expiry01.10 11:26:23UTC, gateway12:11:23UTC.
Token not accessed/installed; services unchanged. The initial timestamps below
remain historical evidence and must not be used as current deployment material.

01.10.2026, authority/material validation completed10:52UTC. Entry HEAD
`584d252552ebd61e819032ec9453a52805c9bb5b`, clean worktree. Accepted production
implementation remains `ff9fb09` / runtime `bb71a3f`; no runtime source changed.
User explicitly authorized creation of the first canary Family and designation
of the existing Amsterdam identity after the previous missing-authority audit.
This is **not** deployment, physical readiness, FIELD-1 or permission to use OAuth.
[Previous BLOCKED evidence](2026-10-01-5n-prod-materials.ru.md) remains unchanged.

## Authority decision and identity preservation

- Created one new128-bit CSPRNG Family reference in the **existing Friends
  restricted-issuer/grant namespace**. Its authority is the ControlTrust-signed
  issuer delegation and matching `restricted_grants` row, not an unsigned label
  or a second root. This is deliberately **not a ProductStore `/v2` Family or
  entitlement**: no ProductStore lookup, enrollment or database mutation occurred.
  Friends already has its own invitation authorization; its activated identity
  is not enrolled again. Family public-reference SHA256:
  `c0a38c2d8653d92384d86a8ab5a411b4ba97124fb9a53414fbeafb6c6c469db6`.
- Bound only the previously resolved active `Owner` device administrator, checked
  against the protected operator record and retained public-identity fingerprint.
  Existing device/invitation must both remain active. No raw canary identifiers
  or invitation values printed. No phone access, reset, identity creation or
  fresh physical attestation; this is an operator-authorized server-side binding.
- Restricted grants **1**, other restricted devices admitted **0**. All26 other
  existing Friends devices rejected by the actual `_grant`/admission checks.
  Existing4 revoked device rows, all normal devices and invitations unchanged.
  Canary restricted grant expires with the short initial delegation; normal
  perpetual Friends authorization is not shortened or rewritten.
- Explicitly designated NL's **existing persistent Reticulum control-provider
  Device Identity** as this Family's restricted gateway, rather than the mailbox
  node or a temporary5N fixture. Exact source on186.246.45.246:
  `/opt/apps/family_connect/reticulum/state/identity/reticulum.key`.
  Public identity SHA256:
  `e504e0ef76a2b3bcc3f0c5add0760ff39e30808c6026fb597c996edc3ff6ff09`.
  New role/Family designation is now signed by the existing offline ControlTrust.
  Original64-byte key, UID999/0600 and existing control-provider service unchanged.
- This reuses one identity across control-provider and restricted-gateway roles;
  compromise affects both roles. It does **not** grant CA signing powers to that
  key. No mailbox/WG/Reality key substitution and no replacement gateway identity.
  The Ed25519 half is encoded into the accepted private `gateway.json` only on
  NL; original key never leaves NL. Owner Redmi private identity remains on-device.

## Namespace and lifetime derivation

Before initialization, verified no restricted tables, issuer/delegation/profile
or authority reservation at the staged/final production locations. Reserved the
first generation using exclusive-create files; no overwrite/retry fallback.
Protected immutable `authority-reservation.json` records source, canary/gateway
binding, Family, prior floors and proposed public delegation; separate completion
receipts record migration/signing/grant/CRL completion. An interrupted reservation
must be inspected, never regenerated blindly.

- Delegation domain remains `family-connect/restricted-issuer/v1\0`.
- Previous namespace sequence0 (absent) → first positive delegation sequence**1**.
- Empty restricted grant revisions → previous floor0 → minimum peer revision**1**;
  accepted `restricted_admin.grant()` creates initial canary revision**1**.
- CRL sequence**1** is returned by **`restricted_admin.publish_crl()`**, which
  initializes `restricted_crl_sequence` from the real DB and absent prior CRL.
  No fabricated CRL or manual sequence insert. Relay config maximum9, normal
  catalogs and release sequences are separate namespaces and were not reused.
- Initial issuer/CA/delegation and canary-grant window deliberately bounded to
  **24h**, expiry **02.10.2026 10:44:11UTC**. This is an explicit short canary
  preparation policy, not a new unlimited production default. Changing/renewing
  delegation requires increasing its sequence, preserving floors and offline
  signature; never restart the namespace at1.
- Gateway certificate expiry **01.10 11:47:45UTC** (≤1h).
- Initial CRL: issued **01.10 10:47:45UTC**, expires **11:02:45UTC** (15min).
  The recorded server-only canary validation certificate has the same expiry.
  **Effective validated profile readiness expires11:02:45UTC** even though the
  gateway leaf/issuer last longer. No refresh timer or background task was started.
- BOOT-1≤1h, bootstrap seed55min, dedicated descriptor60s and existing session
  lifetime unchanged. No directory, seed room or dedicated descriptor generated.

## Backup and additive migration

RU backup, created on-host only, root0700 directory/files0600:
`/opt/apps/family_connect/restricted-materials-stage-20261001/authority-backup/`.
Contains SQLite online backup `access-before-authority.db` (integrity_check=ok),
schema, prior deny-all admission, live API/Access source, ingress config and
relevant existing service definitions. No private DB/config copied to workstation,
Git or receipts. Later rollback must **not restore this DB over newer revocations**.

Executed the unchanged `restricted.migrate()` using an isolated staged copy of
accepted source and the existing RU venv (cryptography46.0.7/RNS1.5.1):

1. `restricted_grants`;
2. `restricted_challenges`;
3. `restricted_certificates`.

Three additive CREATE TABLE IF NOT EXISTS statements; no DROP, rename, existing
data rewrite or unrelated migration. Existing DB user_version not repurposed.
Later the accepted publisher adds only `restricted_crl_sequence`. No additional
authority tables or ProductStore schema changes. Migration duration **23.883ms**.

Malformed-empty ordinary `/friends/challenge` probes immediately before/after
returned the expected400 (11.428ms/2.247ms). Monitoring interval100ms exceeded the
migration duration, so no sample landed inside the23.883ms operation. **Zero failed
probes observed**, not proof of zero sub-sample lock latency. Final probe also400.
No Friends API restart/interruption requested; PID/start-time/NRestarts unchanged.
This bounded liveness probe is not an end-to-end activation/client acceptance.

## Delegated issuance and actual CRL

- Online Ed25519 CA key generated **on RU only**, PKCS8 PEM0600 in inert staging.
  CA built through the existing cryptography X.509 APIs: Ed25519, self-signed,
  BasicConstraints CA/pathLen0, cert-sign/CRL-sign KeyUsage, random serial and SKI.
  No diagnostic issuer helper or private fixture material used.
- Only the canonical public issuer payload was sent to the local signer. Used
  unchanged `python -m scripts.sign_restricted_issuer --input ... --output ...
  --key state-client-build/update-signing/ed25519.key`; public output returned to
  RU staging. Existing offline root never moved, printed or deployed.
- Root↔packaged anchor↔RU staged anchor verified; issuer verifies with accepted
  `delegation()`. Family/gateway/floors exactly match the protected reservation.
- Canary-only JSON admission installed **in the inactive stage**, no `*` or beta
  expansion. Grant created by accepted operator helper, not direct device insert.
- Issued one **public server-only validation certificate** for the existing canary
  Ed25519 public key, recording serial/revision/expiry in the real restricted
  certificate ledger before publishing CRL. No client proof fabricated and no
  claim the phone obtained/used this certificate. Native format checked with the
  existing key URI, Family/role/revision claims; owner private key never required.
- Gateway leaf produced with accepted `_issue(..., role='gateway')`, matching
  delegated full public Device Identity. Its private half stays on NL.
- Published signed CRL via the real publisher/state machinery: sequence1,
  **0 revoked certificate entries** because the only issued device certificate
  belongs to the valid canary. Existing revoked normal devices have no restricted
  certificates and remain denied. This is a legitimately computed initial list,
  not a fabricated empty snapshot or deletion of existing revocations.

## Prepared materials (not installed)

Both hosts: `/opt/apps/family_connect/restricted-materials-stage-20261001/`.
Directories root:root0700, data/source/config/backup files0600, staged executables
0700; regular/non-symlink/nlink1 verified. Final `friends-restricted/` remains
absent. Nothing points running services at this stage.

| Host | Material | Result |
| --- | --- | --- |
| RU | `issuer.json`, `issuer.key`, `anchor.pub` | READY, signed delegation/existing trust/key match |
| RU | `admission.json` | READY, only existing owner canary |
| RU | `revocations.pem` | READY at validation; initial expiry11:02:45UTC, refresh required later |
| RU | `sync.key`, `known_hosts` | READY, previous dedicated key/pins preserved |
| RU | `app/`, reservation/receipts, backup | Staged operator source/provenance/rollback evidence |
| NL | `gateway.json` | READY, original gateway identity/real CA/CRL, native parser PASS |
| NL | `bin/bootstrap-broker` + bootstrap unit | READY/staged, binary never started |
| NL | `app/`, `bin/restricted-sync-command` | READY/staged, accepted helper code and fixed wrapper |
| NL | `sync.key.pub`, `authorized_keys.fragment` | READY/staged; public key matches RU private counterpart |
| NL | `family-restricted.sysusers.conf`, `.tmpfiles.conf` | READY/staged deployment account/home specification; NOT installed |
| NL | `provider.env` / OAuth | EXCLUDED, not created/read/requested; owner reports token stored in KeePassXC |

Forced wrapper enforces exact `SSH_ORIGINAL_COMMAND=restricted-sync`, zero args,
fixed Python module and fixed profile/directory paths. Public key fragment retains
`restrict`, RU-source restriction and that forced command; SSH-G verifies strict
existing host pins, identities-only/batch mode and no forwarding. Wrong command
returns126; correct sync **not run**. Account/authorized_keys not installed; source,
venv location and ownership handoff must be installed/verified during a separately
authorized deployment. Root-only staging is intentionally not service-readable yet.

Accepted Python source archive SHA256:
`2449914d7087d3d0c4a72868c2daf24f5fb9fe373862cd3e00e9a35254bb4abd`.
Fresh Linux amd64/CGO-disabled Go bootstrap binary built from entry HEAD with
locked Go1.26.0; SHA256
`c24cee818f226dce6864da0f4f1f6d8b891bf7deb8596f27db23531415d00a2c`.
First binary output under `/tmp` hit its quota; Go removed the failed output.
Rebuilt successfully in ignored `state-client-build/prod-authority-584d252/`.
No unrelated cleanup, dependency changes or secrets embedded. Secret-free binary
and source only were transferred; gateway private profile assembled on NL.

## Offline validation and production boundaries

- **18 tests PASS**: `tests/test_friends_restricted.py`, locked Python/Go tools,
  backend→native compatibility enabled. Test state under `/tmp`, not production.
- **Actual production materials PASS**: root delegation, matching online key/CA,
  signed CRL/floor/expiry and actual sole-canary grant. Corrupted delegation and CRL
  signatures rejected in memory; no production data changed for negative tests.
- On NL a secret-redacting native verifier calls the unchanged Family TLS parser
  on the actual `gateway.json`; verifies gateway/canary X.509 chains and accepted
  role/Family/public identity claims via native authorization callbacks. Wrong
  Family, stale revision and higher CRL-floor negatives rejected. This is offline
  parser/authorization validation, **not** a TLS possession handshake, new room,
  phone delivery or product restricted rehearsal.
- `bootstrap-broker` was built/staged but **never executed**. Only offline verifier
  and intentionally rejected forced-command checks ran. No sync, OAuth, Telemost,
  seed-directory export or dedicated-session request.
- RU API279974, AWG1515959/TCP1908885; NL AWG2729703/TCP2420425, existing control
  provider1295155/mailbox1295303: same PIDs/start times/NRestarts0. Existing API
  handler/Access source and ingress bytes match backup; new restricted runtime
  absent from the live API path. New units not-found. Normal devices/invites match
  pre-migration backup;4 original revoked devices preserved.
- No new private material in repository/task output. New issuer private key only
  RU; gateway private profile only NL; existing offline root only local. Public
  payload/certificates/receipts kept in owner-only `/tmp/fc-authority-public-20261001`;
  these are not private keys or a client credential bundle. No canary raw identifier,
  OAuth, room URL or private key printed. KeePassXC was not opened/searched.
- Documentation validation:411 files/2480 links/0 errors; staged source/secret
  guard1554 entries/0 blocked files, whitespace checks PASS. Eight Markdown files
  only in the evidence commit; no production DB, keys, certificate bundle, binary
  or operational receipt added to Git. Existing ignored offline signer remains in
  its original documented path; no assertion that all historical ignored stores
  under the checkout are secret-free.

Safe runtime receipts remain under `/tmp/fc-authority-public-20261001/`:
`prepare-safe.json`, `finalize-safe.json`, `nl-safe.json`,
`final-verification-safe.json`; protected server-side receipts stay with the
authority reservation in the stage. They contain status/public hashes, not secrets.

## Stop and future deployment requirements

**5N-PROD-AUTHORITY = READY**, meaning prepared authority/staged materials excluding
provider.env. It does not mean enduring offline recovery or deployment readiness
after expiry. Before any later controlled rollout, refresh the real signed CRL
through the same publisher and carry its increasing sequence to NL; renew expired
gateway/canary certificates and delegation as required without resetting floors.
Do not reuse this short-lived initial CRL after11:02:45UTC.

Rollback of preparation: keep runtime untouched, disable staged admission if
abandoning the canary, preserve authority/grants/certificate history/CRL floors and
private backup. Do not drop tables or restore old DB over later revocations. No
rollback was needed/performed; no observed normal-service regression.

Remaining actual deployment, service-account/venv installation, provider token,
READY seed publication/sync, API rollout and real-phone delivery/rehearsal remain
separate actions. **Stop before the provider-token phase**: no input procedure or
token request issued. No automatic deployment retry/refresh schedule.

Services started/reloaded: **no**. New API runtime deployed/routes enabled: **no**.
Token accessed/exported/deployed: **no**. Public release/catalog changes: **no**.
Phone changes/FIELD-1/git push: **no**. Previous BLOCKED/preflight evidence retained.
