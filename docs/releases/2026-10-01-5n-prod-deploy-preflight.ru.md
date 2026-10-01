# 5N-PROD-DEPLOY-PREFLIGHT — BLOCKED on owner token input

Entry HEAD `c0da8da8421fbe71f15350664fff639fd83e1352`, clean worktree.
01.10.2026 refresh completed11:11:23UTC; final non-token checks11:12UTC.
**BLOCKED only at the requested interactive input boundary**, not an authority
failure or a deployment attempt. No token was accessed, entered or installed by
the agent. No runtime deployment/service/ingress action or physical prewarm.
[Previous authority READY](2026-10-01-5n-prod-authority.ru.md) and earlier BLOCKED
evidence are retained; their initial short-lived CRL is no longer current.

## Authority revalidation and refresh

- Same signed production Friends restricted Family and sole active Owner canary;
  same protected operator record/public identity and normal invitation. Other
  admitted devices **0**, actual restricted grant count1; original4 revoked normal
  device records preserved. No ProductStore access/new Family/identity/admission.
- Same designated NL control-provider Device Identity, same original private key
  and gateway binding; existing profile private-key public half and new gateway
  certificate public key match that identity. No private key exported.
- Same delegated issuer key, public CA, root anchor and signed delegation. No
  issuer rotation, offline-root signing or new authority reservation required.
- Delegation sequence **1**, global peer/canary revision **1** remain unchanged:
  these signed authorization objects were not changed/reissued. Calling `grant()`
  merely to renew a certificate would incorrectly bump its revision; not done.
- Read real DB `restricted_crl_sequence` and verified prior signed CRL both1.
  Accepted **`restricted_admin.publish_crl()` advances1→2**. No reset, direct
  sequence write, hand-edited signed CRL or silent replay of sequence1.
- Fresh gateway and public server-only canary validation certificates issued with
  accepted `_issue()` under the same authority; fresh random certificate serials.
  Canary serial/revision/expiry recorded in the existing certificate ledger, old
  history retained. This is not a phone request/proof or evidence of delivery.
- Real publisher signs updated CRL using current grants/certificates; NL signature,
  binding and strictly increasing floor validated before atomic profile replacement
  with accepted `restricted_sync.atomic()`. Signed bytes were replaced only with
  new issuer/publisher output; JSON replacement preserves private key/identity.
  The synchronization service/helper was not run, and no seed directory fabricated.

| Material | Current safe validity / sequence |
| --- | --- |
| CRL | sequence **2**, issued01.10 **11:11:23UTC**, expires **11:26:23UTC** |
| Gateway certificate | expires01.10 **12:11:23UTC**, TTL1h unchanged |
| Canary validation certificate | expires01.10 **11:26:23UTC**, TTL15min unchanged |
| Effective native profile | expires01.10 **11:26:23UTC**, CRL-bound |
| Existing delegation/CA | expires02.10 **10:44:11UTC**, unchanged |
| Existing canary grant | expires02.10 **10:44:11UTC**, revision1 unchanged |

CRL15min, directory≤1h, grant/delegation expiry and certificate limits unchanged.
No readiness-window redesign. **Do not deploy any of these files after their
applicable expiry.** If owner input/approval takes past11:26:23UTC, another accepted
publisher refresh and validation is necessary before a later rollout; preserve
sequence progression. No scheduled refresh or automatic deployment was enabled.

Public old CRL/certificates and new refresh receipt saved root0600 below each
existing protected stage's `deploy-preflight-refresh-20261001/`. No private key
backup/export was needed. Existing issuer/grant/admission bytes/state preserved;
no migration or schema change in this refresh.

## Exact owner-interactive token procedure

Public helper source:
[`deploy/friends/restricted/provision-provider-env.py`](../../deploy/friends/restricted/provision-provider-env.py).
Staged on NL root-owned0700 at
`/opt/apps/family_connect/restricted-materials-stage-20261001/bin/provision-provider-env.py`.
Helper SHA256 `d1b6567344e52ae087e60b048ca65c73d100a8449937f801825d2ebe4d03da6d`.

The owner manually retrieves the token from KeePassXC, then runs **one command in
their own unrecorded local terminal**, not in ChatGPT/tool stdin. Existing host
verification stays strict; do not accept a different host key:

```sh
ssh -tt -o StrictHostKeyChecking=yes -o UpdateHostKeys=no root@186.246.45.246 \
  'env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 /opt/apps/family_connect/restricted-materials-stage-20261001/bin/provision-provider-env.py'
```

Only when this hidden prompt appears, paste the token and press Enter:

```text
Yandex Telemost OAuth (hidden; paste token, then Enter):
```

- Requires root/real TTY. Echo-free `getpass`; **GetPassWarning becomes an error**,
  never an echoed fallback. No token argv, shell assignment/history, environment
  export, subprocess argument, output, log, hash, metric or temporary file.
  Core dumps disabled; helper itself never contacts provider or unlocks KeePass.
- Enforces the existing provider constructor's nonempty/UTF-8 byte-bound/no
  CR-LF-NUL contract without displaying/recording token size. Strict single-field
  systemd EnvironmentFile encoding uses escaped double quotes/backslashes;
  canonical parser roundtrip before writing, rejects extra fields/control lines.
  This is schema validation, not OAuth-account validity verification.
- Refuses if restricted units have appeared since preparation; checks before and
  after hidden input. Does not install units, reload systemd or start any process
  that creates rooms. No shell `source`/`eval` of secret configuration.
- Creates only the runbook-approved final destination directory if absent,
  root0700, and **`/opt/apps/family_connect/friends-restricted/provider.env`**,
  root:root0600, exclusive-create/no-symlink. Existing file is never overwritten.
  No `.tmp` secret file or local token copy; flush/fsync and file/schema checks.
  Failed partial write removes only the newly created destination. Host/service
  guards establish the destination cannot currently be consumed automatically.
- Successful output contains only:
  `Provider configuration: exists=yes owner=root mode=0600 nonempty=yes schema=PASS`.
  Owner then confirms completion **without sending the token**. Agent subsequently
  validates only existence/ownership/mode/nonempty/schema and reruns freshness
  checks; no value/hash/size or provider request.

**The command has not been run by the agent. Token installed: no.** Owner input
is pending. KeePassXC/database/entry were not opened, unlocked, searched or exported.
No `provider.env` created yet, including no empty placeholder.

## Material inventory at the stop

Stages remain `/opt/apps/family_connect/restricted-materials-stage-20261001` on
both hosts. READY here means prepared/staged, not installed or currently serving.

| Host | Required material | State |
| --- | --- | --- |
| RU | `issuer.json`, `issuer.key`, `anchor.pub` | READY, unchanged valid delegation/key/anchor |
| RU | `admission.json` | READY, sole Owner canary |
| RU | `revocations.pem` | READY, fresh signed sequence2, expiry11:26:23UTC |
| RU | `sync.key`, `known_hosts` | READY, same private/public key pair and strict pins |
| NL | `gateway.json` | READY, renewed leaf/CRL, same identity/binding/private key |
| NL | bootstrap binary/unit/config | READY/staged, not executed/installed |
| NL | sync helper/authorization/account configuration | READY/staged; actual service account/authorization not installed |
| NL | `provider.env` | **MISSING — owner interactive input pending** |

Final live-destination directories were absent at validation; the owner helper
will create only NL's private provider destination. Remaining material installation,
service-user ownership handoff, venv layout and activation stay separate authorized
deployment steps in the existing runbook. The helper must not be interpreted as
authorization to activate the staged API or bootstrap/sync infrastructure.

## Checks and security evidence

- **32 tests PASS**:18 accepted Friends restricted tests with native compatibility
  enabled +14 input-helper tests (quoting/schema rejection, non-TTY refusal and
  refusal to overwrite existing destination). Synthetic values only; no token in
  tests/fixtures. Temp test state does not contain the owner's OAuth credential.
- Actual staged delegation/CRL/expiry/key binding and native Family TLS parser:
  **PASS**. Wrong Family, stale revision and higher CRL-floor negative checks PASS.
  Complete preflight validation: **FAIL/incomplete only because provider.env is
  missing**; no claimed provider-authentication or live client integration PASS.
- Same RU/NL normal service PIDs/start times/NRestarts; no new units installed.
  API handler/Access code/ingress match pre-authority backup; normal device/invite
  rows unchanged. Malformed-empty ordinary API liveness probe expected400; no
  claimed end-to-end activation acceptance or runtime configuration deployment.
- Root staging directories0700, data0600, executables0700 validated; no symlinks
  or extra hard links. SSH key fingerprint matches both hosts; strict host checks,
  identities-only/batch mode/no forwarding; wrong forced command rejected126.
- Initial read-only preflight mistakenly required the longstanding RU application
  parent to be root-owned. Existing UID1000/mode0775 is not new authority drift;
  no data was changed by the failed guard. Corrected check preserves existing RU
  application ownership and verifies root0700 private staging. NL provider parent
  is root0755 and final destination guard remains root-only. No unrelated chmod.
- Receipts with only public/status metadata:
  `/tmp/fc-deploy-refresh-preflight-safe.json`,
  `/tmp/fc-deploy-refresh-public-20261001/ru-safe.json`, `nl-safe.json`,
  `final-verification-safe.json`; public certificate bundle in the same0700 local
  directory. These are not token/private-key artifacts. Runtime private keys stay
  on their respective hosts; offline root not accessed in this refresh.
- Documentation validation:412 documents/2488 links/0 errors; staged source/secret
  guard1557 entries/0 blocked files; whitespace checks PASS. Only helper source,
  synthetic tests and Markdown evidence are committed. No actual provider.env,
  authority bundle, key, database, token or runtime binary enters Git.

## Stop boundary

**5N-PROD-DEPLOY-PREFLIGHT = BLOCKED — owner hidden input required.** Family unchanged:
yes; canary unchanged:yes; other admissions0; issuer ready:yes; provider.env ready:no;
Yandex token installed:no. Services started/reloaded:no; production runtime changed:no.
CRL/certificate staging and existing authority-ledger refresh are the only production
state writes. No successful sync, room creation, API deployment/routes, ingress
reload, phone prewarm, public release, FIELD-1 or git push. No automatic retry.
