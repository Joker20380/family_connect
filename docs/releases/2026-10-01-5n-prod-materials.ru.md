# 5N-PROD-MATERIALS — inert preparation, not deployment

## Subsequent explicit authority creation — READY, provider phase excluded

The next user authorization allowed creating the first Friends restricted Family
and designating the existing NL gateway identity, resolving the Phase A policy gap
below without inventing a ProductStore membership or replacing identities.
[5N-PROD-AUTHORITY](2026-10-01-5n-prod-authority.ru.md): one canary grant, four accepted
additive tables, signed delegation/real CRL and validated gateway profile staged.
Provider token explicitly excluded, runtime unchanged. Initial CRL expiry01.10
11:02:45UTC; refresh before future use. The following BLOCKED audit remains a
historically correct record before that authority-creation authorization.

## Continuation — Phase A BLOCKED, 01.10.2026 10:28UTC

**5N-PROD-MATERIALS = BLOCKED.** Entry HEAD
`9340931524a55d574f85baeffb27566bf6ae22b5`, clean worktree; accepted implementation
`ff9fb09af329402e538003a56eaefd0dce2b6c73` unchanged. User now authorizes the reviewed
additive migration and local offline-root signing, **conditional on unambiguous
existing Family/canary/gateway authority**. This supersedes the initial blanket
no-migration restriction below, but Phase A did not satisfy its prerequisite.
No migration, signing, private-key generation or production write was attempted.

### Actual authority investigation (not missing chat input)

- Read existing protected RU `friends-access/notices.sqlite` and `access.db` using
  SQLite `mode=ro`/query-only, and actual `state-product/db/product.db` (version3).
  Exactly **one active device administrator**, operator label `Owner`, maps to an
  active Friends device and one non-revoked invitation. This resolves the existing
  owner-canary **operator record** consistently with
  [accepted owner-phone administrator workflow](../testing/messenger-notices.ru.md).
  Phone state was not reread or changed; no fresh physical identity attestation is
  claimed. Raw device/public identity/invitation values were not printed.
- The older local protected `state-enroll/friends-pilot/phone-invitation` resolves
  to a different record, so it is **not used to select the current canary**. No
  newest-row heuristic, general-beta selection or admission mutation was used.
- Current owner identity has **zero ProductStore membership matches**, comparing
  both identity reference and full public identity. ProductStore has4 families and
  4 devices; **all Friends↔ProductStore device identity overlap is0**. Picking one
  of those unrelated Family records would invent an authorization relationship.
- Friends' active invitation is the existing perpetual product authorization; its
  `devices`/`invites` schema carries **no Family reference/revision**. None of the
  restricted tables exists. `restricted._enroll()` takes Family/minimum revision
  from an already-signed issuer delegation; migration only creates empty tables.
  Therefore neither migration nor `_enroll()` can discover the missing Family.
- NL current service definitions bind persistent64-byte Device Identities to
  **Reticulum control provider** and **mailbox node**, respectively. Public SHA256
  fingerprints derived in place (private keys never exported):

  | Existing role / protected path | Public identity SHA256 | Authority conclusion |
  | --- | --- | --- |
  | Control provider: `reticulum/state/identity/reticulum.key` | `e504e0ef76a2b3bcc3f0c5add0760ff39e30808c6026fb597c996edc3ff6ff09` | Existing identity, but no accepted restricted-gateway/Family designation found |
  | Mailbox node: `mailbox-pilot/node.identity` | `9de824cce8150a0378d956190204b621d6b2b2e0714746b94d98ac31ad93c60c` | Existing mailbox role, not authorization to issue a gateway certificate |

  Paths are relative to NL `/opt/apps/family_connect`. Existing ownership/modes
  retained (control UID999/0600; mailbox root/0640); no replacement/repermissioning.
  AWG/WG/Reality transport keys are not64-byte Device Identity signing keys and
  were not substituted. Prior5N.3 acceptance explicitly used an isolated fixture,
  not production issuance; prior mailbox pilot is not a restricted Family gateway.
- NL relay DB has2 devices/13 configs, maximum config sequence9, no Family/grant
  tables. That sequence belongs to a **different control-config namespace**, not
  a restricted-delegation sequence, global peer revision or CRL floor. No legal
  restricted delegation/revision number can be selected from these observations
  alone. No initial numeric value was guessed. The CRL publisher's atomic
  sequence initialization remains the required future mechanism.
- Existing local offline signer public key matches packaged ControlTrust **and**
  the RU staged `anchor.pub`; raw public SHA256 remains
  `6a09fb42468acdb4cfcb4f0888e27c13705ac437a45a6624fc21dddbe83fed83`.
  Root private key stayed local and was used only for public-key derivation,
  **not signing**. No new root or delegated private key was created.

These are bounded findings in the documented production databases, configured
identity paths and prior accepted reports, not a claim to have searched every
possible offline owner archive. A different protected authoritative register may
resolve the gap; its location/provenance must be established before continuing.

### Phase gates and current file inventory

The exact `restricted.migrate()` was reread: three additive `CREATE TABLE IF NOT
EXISTS` statements (grants/challenges/certificates), no DROP/rename/data rewrite.
It was **not applied**, because the explicit ambiguity stop precedes Phase B.
Migration duration/interruption: N/A, not executed. No backup/rollback operation
was necessary for this read-only continuation. Publisher did not initialize CRL
sequence, and no invented empty CRL was signed.

All READY entries below mean **inert staging**, not deployed/usable runtime.
Stage on each host: `/opt/apps/family_connect/restricted-materials-stage-20261001`.
The final `friends-restricted/` directory remains absent on both hosts.

| Host / required material | Status at stop |
| --- | --- |
| RU `issuer.json` | MISSING — authoritative Family/gateway/floors unresolved |
| RU `issuer.key` | MISSING — no unbound issuer generated |
| RU `anchor.pub` | READY — matches existing root and packaged anchor |
| RU `admission.json` | READY as deny-all only; **canary admission NOT READY** |
| RU `revocations.pem` | MISSING — migration/publisher/signing not run |
| RU `sync.key` | READY — retained existing staged key, public match verified |
| RU `known_hosts` | READY — retained strict existing pins, not TOFU |
| NL `gateway.json` | MISSING — existing restricted-gateway binding unresolved |
| NL `provider.env` | MISSING; Yandex token present: **no** |
| NL bootstrap unit/config | Unit template READY/staged; full configuration MISSING |
| NL sync authorization/helper config | Restricted public fragment READY/staged; account/helper installation MISSING |

Authoritative Family resolved: **no**. Owner canary operator record resolved:
**yes** (fresh physical confirmation not run). Existing *restricted gateway*
resolved: **no**; two other existing roles identified above. CRL initialized,
delegation signed, issuer ready, gateway binding ready, canary-only admission ready,
complete sync material ready, provider.env ready: **no**.

### Validation and unchanged production state

- Complete production offline validation: **FAIL / incomplete prerequisites**, not
  an observed cryptographic rejection of an issued production certificate.
  Available anchor, SSH effective options/key consistency, deny-all JSON and
  stage permissions: **PASS**. Issuer/CRL/native certificate/gateway/provider
  validation cannot run without the missing real material; no synthetic identity
  used to turn those checks green. Prior18 backend/native tests below are retained
  evidence, **not rerun nor production-material acceptance** in this continuation.
- Root-owned staging directories0700 and every existing staged file root:root0600,
  regular/non-symlink/nlink1 verified. Sync key was not regenerated. NL fragment
  retains `restrict`, source restriction and fixed forced-command path. Effective
  SSH config enforces pinned host, `IdentitiesOnly`, `BatchMode`, no forwarding.
  No synchronization connection/helper execution was attempted.
- RU API PID279974, RU AWG1515959/TCP1908885, NL AWG2729703/TCP2420425 remained
  active with NRestarts0, identical to entry baseline. Restricted units remain
  not-found; Friends restricted table count0. No process interruption caused by
  this task; no claim of a continuous external availability measurement.
- No secret files added to repository or task artifacts. Probes return schema,
  counts/booleans and public fingerprints only; no private key, OAuth, device proof,
  full credential bundle or room URL printed. Existing ignored private stores
  remain untouched. No new bootstrap room/directory or dedicated session created.
- Safe receipts: `/tmp/fc-materials-authority-discovery-safe.json`,
  `/tmp/fc-materials-canary-safe.json`, `/tmp/fc-materials-gateway-safe.json`,
  `/tmp/fc-materials-phase-a-close-safe.json`, and refreshed staged verification
  `/tmp/fc-prod-materials-verify-safe.json`. No DB copy/private profile in receipts.
- TLS housekeeping remains the separate earlier inspection below; no renewal,
  timer/service action or new TLS acceptance claimed during Phase A.
- Documentation validation:410 documents/2472 links/0 errors; diff whitespace
  check PASS. Source-path guard1553 index entries/0 blocked files; rerun against
  the staged documentation before commit. Only four Markdown evidence/status/plan
  files changed; runtime/build artifacts and private stores are not part of patch.

### Exact remaining owner action / stop

1. Identify the **protected authoritative operator record/location** that assigns
   the already-resolved active Owner Friends record to an existing Family. Do not
   paste device identifiers/private keys into chat. If no such assignment exists,
   explicitly resolve that authority-model gap first; this continuation is not
   permission to create a Family or borrow an unrelated ProductStore entitlement.
2. Identify the accepted production restricted-gateway binding to an **existing**
   NL identity (safe role/fingerprints above allow disambiguation). An explicit,
   reviewed role/Family designation is needed if it was never recorded; service
   location alone is not such authority. Do not reuse a diagnostic fixture or
   silently promote the control-provider/mailbox identity.
3. Establish the authoritative delegation/peer revision ledger and validity policy
   for that binding. Then resume the authorized migration/publisher/signing steps
   using implementation monotonic rules, not a guessed relay number.

**Token-input phase H was not reached.** It would be misleading to report only a
missing token while Family/gateway authority remains unresolved. Provider schema
is unchanged (`YANDEX_TELEMOST_OAUTH_TOKEN`, server-only root0600); provide the one
safe interactive input procedure only when earlier gates can proceed. Do not ask
the owner to supply a token now or start bootstrap rooms.

Services started/reloaded: **no**. Restricted API enabled: **no**. Migration: **no**.
Production changed beyond inert staging: **no** (no new staging in this turn).
Production rollout, phone changes, FIELD-1, git push: **no**. Stop before Phase B;
no automatic deployment retry. Historical preparation and preflight evidence follows.

## Historical initial contract inventory before generation

Source: implementation `ff9fb09`, evidence HEAD `f082c10`;
[authoritative deployment contract](../../deploy/friends/restricted/README.md).
No service start/reload, migration, ingress change, provider room creation, phone
action, git push or FIELD-1 is authorized by this preparation task.

Notation: `R=/opt/apps/family_connect/friends-restricted` on each respective host.
Final paths below are **deployment destinations**, not permission to activate them.
Until deployment use separate root-owned0700 staging directories, files0600.
RU API/sync units run as root under the accepted unit contract. NL gateway/profile
must ultimately be owned by `family-restricted` in its0700 directory; provider.env
may remain root0600 (systemd reads EnvironmentFile before dropping privileges).
No ownership/account/service installation changes during preparation.

| Material / producer | Type and trust / consumer | Final location, classification, mode | Rotation, regeneration and authority |
|---|---|---|---|
| `anchor.pub`: copy exact packaged ControlTrust anchor | Base64 raw32-byte Ed25519 public key; verifier of issuer delegation, read by RU API/admin/sync | RU `R/anchor.pub`, root0600; cryptographically public | Recopy same bytes safely; **never regenerate root**. Root rotation is separate approved trust migration |
| `issuer.key`: generate on RU, never transfer private bytes | Ed25519 PEM private key accepted by `load_pem_private_key`; online CA signs device/gateway certificates and CRL | RU `R/issuer.key`, root0600, secret; API/admin/sync only | Fresh candidate key is not trusted until existing offline root delegates its matching CA. After activation replacement requires new delegation, monotonic floors and certificate migration; no silent regeneration |
| public CA + unsigned issuer payload: RU CA producer/operator | Canonical Ed25519 self-signed X509 CA, BasicConstraints CA/pathLen0, cert/CRL signing usage; payload v1 fields exactly defined in `restricted.delegation()` | Protected staging, public but operational metadata; no private identity | CA must match issuer.key; Family/gateway refs, validity, sequence and minimum peer revision require authoritative production selection, not fixture defaults |
| `issuer.json`: `scripts.sign_restricted_issuer` on offline operator host | Base64 payload + Ed25519 signature over `family-connect/restricted-issuer/v1` domain; existing packaged control-root delegation, **not directory signature** | RU `R/issuer.json`, root0600; public trust envelope, API/admin/sync/Android | Must be signed by existing root; changed payload requires new signature/increasing sequence. Do not reset stored sequence/revision/CRL floors |
| `admission.json`: operator from verified production authority | Exact `{devices:[...]}`, ≤256 refs; eligible already-activated Friends devices still require DB invite/device/grant/proof checks | RU `R/admission.json`, root0600; access-control metadata, device refs kept private | Empty list valid and deny-all; no `*` for canary. Only verified owner device may be added; removal participates in next CRL publication. Recreate only from approved policy, never inferred IDs |
| `revocations.pem`: `restricted_admin publish-crl` | Canonical signed X509 CRL, monotonically increasing CRLNumber; production validity15min, bounded by delegation | RU `R/revocations.pem`, root0600; public signed artifact with sensitive operational metadata; included in NL gateway profile/Android delivery | Publisher reads actual grants/revisions/certificate serials and maintains DB sequence. Requires accepted schema; **cannot run live publisher in this no-migration task**. No fabricated empty CRL/sequence rollback. Refresh just before deployment |
| `sync.key`: OpenSSH `ssh-keygen` on RU | Dedicated asymmetric Ed25519 SSH identity, **not symmetric shared secret**; sync process authenticates to NL forced command | RU `R/sync.key`, root0600 secret; public `.pub` may go to NL protected staging | Can regenerate safely only before installation. Active rotation replaces exact authorized public key; private half never copied to NL |
| sync public authorization: operator | Public OpenSSH key with `restrict`, RU source restriction and root-owned forced-command wrapper to accepted `restricted_sync gateway` | NL staged authorization snippet0600; later approved account authorized_keys path | This is SSH trust, not a Family CA. Do not install/enable authorization during preparation; no password auth or forwarding |
| `known_hosts`: copy pre-existing verified NL pins | OpenSSH host-key records for exact NL address; `StrictHostKeyChecking=yes`, `UserKnownHostsFile` enforced by sync code | RU `R/known_hosts`, root0600; public host keys, integrity critical | No fresh keyscan/TOFU/accept-new. Rotation requires independent verified identity; copying the already pinned bytes is safe |
| `gateway.json`: selected existing NL Device Identity + `restricted_admin gateway-certificate` | Existing Family Credentials JSON: certificate/private_key/authority/revocations/family/gateway/minimum_revision/minimum_crl. Gateway Ed25519 key belongs to selected existing64-byte public Device Identity URI and role=gateway | NL `R/gateway.json`, ultimately family-restricted0600; secret profile, only NL gateway/sync helper | CA issues public leaf for pinned existing identity. Renewal preserves identity; key/family/gateway replacement is not a routine regeneration. No diagnostic/chat/WG identity substitution without authoritative binding |
| `provider.env`: owner supplies token securely on NL | systemd EnvironmentFile setting `YANDEX_TELEMOST_OAUTH_TOKEN`; provider requires nonempty ≤4096 bytes, no CR/LF/NUL | NL `R/provider.env`, root0600; secret, consumed by bootstrap service only | Provider-account rotation/revocation via owner; never mint/retrieve OAuth automatically, never placeholder token marked READY |
| bootstrap unit/config: copy accepted repository template | systemd unit, User=family-restricted, protected profile/env, loopback18444,55min seed; directory export only after READY | NL protected staging only now; later `/etc/systemd/system/family-connect-restricted-bootstrap.service` root0644 | Public configuration. May restage exact template; no daemon-reload/enable/start/container/binary rollout here |
| `directory.json`: running READY bootstrap, **later** | Unchanged BOOT-1 v1, ≤1h/8KiB/4 seeds including required seed join_url; authenticated delivery, no standalone signature | NL `R/directory.json`, later RU `R/directory.json`,0600; private operational seed URLs | Cannot pre-generate without server room/gateway READY. No room creation during this task; never include dedicated-session descriptors |

## Dependency boundary

Exact issuer payload fields: `version=1`, `sequence` integer in(0,2^53),
`family`/`gateway` lowercase32-hex refs, `authority` one canonical PEM certificate,
`minimum_revision` integer in(0,2^31), `issued_at`/`expires_at` integer Unix seconds.
Issued time≤now<expiry≤CA expiry. Envelope has only base64 `payload` and64-byte
base64 `signature`; the signed domain is the implementation's **NUL-terminated**
`DOMAIN` constant, not a hand-assembled replacement. Offline root loader expects
the existing32-byte Ed25519 seed. Gateway reference is SHA256(existing64-byte
X25519+Ed25519 public identity)[:16]; TLS private PEM uses that identity's Ed25519
half, not its separate WireGuard transport key.

Generating a new gateway identity, selecting an arbitrary Family/device reference,
signing fixture defaults, or migrating a temporary copy and presenting its CRL as
production authority would not satisfy this inventory. Missing authoritative
bindings are owner decisions, not permission to invent them. Empty admission is
a safe staged deny-all policy, **not** owner canary readiness.

Offline root access is checked using the repository signer loader and comparison
to the existing packaged anchor; only validity booleans/public fingerprints may
leave that check. No private root export, replacement or server transfer.

## Preparation outcome

**5N-PROD-MATERIALS = OWNER ACTION REQUIRED.** Partial inert material preparation
completed; not an issuer/CRL/gateway provisioning PASS and not deployment READY.
Starting clean HEAD `f082c1039046707a1300d92a274cf8003cc0f44b`; runtime implementation
remains `ff9fb09af329402e538003a56eaefd0dce2b6c73`/`bb71a3f`. No runtime edits.

### Staged files, 01.10.2026 09:58:25 UTC

Both hosts use **only**:
`/opt/apps/family_connect/restricted-materials-stage-20261001`.
Directory root:root0700; every staged file root-owned0600, regular, nlink1,
no symlink. Post-staging readback validated those permissions and exact file sets.
Final live `friends-restricted/` remains absent on both hosts. Existing unit
configuration did not reference the staging path. No account, live authorized_keys,
forced wrapper, systemd installation/daemon-reload/enable/start, ingress or DB write.

| Host/item | Status | Actual preparation |
|---|---|---|
| RU `issuer.json` | OWNER ACTION | Not generated: authoritative Family/gateway binding, sequence/floor/validity selection not supplied; no invented/fixture claims signed |
| RU `issuer.key` | MISSING | Generation deferred with its production CA/delegation binding; no independent unanchored Family authority created |
| RU `anchor.pub` | READY — staged | Exact existing packaged anchor copied; public, no private-root transfer |
| RU `admission.json` | READY — deny-all only | `{devices:[]}`; not a populated owner canary allowlist |
| RU `revocations.pem` | MISSING | Existing production publisher depends on migrated DB/monotonic sequence; not run in no-migration task |
| RU `sync.key` | READY — staged | Dedicated Ed25519 OpenSSH key generated directly on RU with ssh-keygen; private half never leaves RU |
| RU `known_hosts` | READY — staged | Three pre-existing verified local NL host-key records copied, no new keyscan/accept-new |
| RU `sync.key.pub` | READY — staged | Public counterpart, match checked by deriving public half remotely; not a client/device credential |
| NL `gateway.json` | OWNER ACTION | Accepted existing NL gateway Device Identity location and authoritative Family/gateway binding not supplied; no alternate/diagnostic identity substituted |
| NL `provider.env` | OWNER ACTION | Not created with dummy/empty credential. Yandex token available: **no** |
| NL bootstrap service | READY template / installation MISSING | Exact accepted `.service` file staged, not installed or enabled; service account remains absent |
| NL `sync.key.pub`, `authorized_keys.fragment` | READY — staged only | Same public sync key; restrict/from-RU/forced-command restrictions present; not installed as live authorization |

Public fingerprints (not private device identifiers):

- Existing raw32-byte control anchor SHA256:
  `6a09fb42468acdb4cfcb4f0888e27c13705ac437a45a6624fc21dddbe83fed83`.
- New SSH synchronization public key:
  `SHA256:vsx7bv16e5HxKPEt56tki5sj7zlvJZr+tKiIYhlI4gI`.
- Existing pinned NL Ed25519 host key:
  `SHA256:TA7zrfD44kXhvR1k2aW8JHNtWIuLFfP8m6yxzV6+drk`.
  It matches both the **pre-existing** local pin and the server's public host key;
  trust did not originate from a new SSH connection or keyscan.
- Staged NL unit SHA256:
  `306aef9328bac4ae2fca2d2b4b6f17d1f87315d192e5f5b6e7906a6c20ae5f68`.

### Existing signer and remaining authority decisions

The documented existing offline signing file was checked through
`scripts.signing_key.load`: regular file, correct owner,0600,nlink1; derived public
key **matches existing ControlTrust anchor**. Private contents were not printed,
copied, exported or changed. Offline root is available; no owner unlock or new root
is needed. An initial audit harness invocation omitted an optional Namespace field;
the corrected loader invocation succeeded. That probe error was not missing key
evidence and did not generate a signature.

Root availability is not authorization to choose arbitrary certificate claims.
The runbook requires a selected existing production gateway identity and Family
binding but does not supply those values/identity location. No authoritative owner
device selection was supplied either. We did not search unrelated private stores,
read diagnostic identities or reinterpret a chat/WireGuard identity as the gateway.

Before issuer/key/CA/delegation/gateway certificate preparation, owner must identify:

1. Authoritative production Family reference and the existing NL gateway Device
   Identity's protected location/public64-byte binding. If no accepted production
   gateway identity exists, explicitly resolve its enrollment procedure; do not
   silently generate/relabel a diagnostic identity.
2. Approved delegation sequence, minimum peer revision and validity interval.
   These are trust-policy selections; no arbitrary long-lived defaults signed.
3. The owner canary's verified already-activated Friends device reference through
   protected operator state, not printed in this report. Admission remains deny-all
   until selected against real active/nonrevoked state; never change to `*` here.
4. Supply the existing provider token directly to protected NL staging using a
   hidden local-terminal/secret-manager workflow, **not chat, argv, shell history,
   APK, logs or Git**. `provider.env` must use systemd EnvironmentFile syntax;
   token nonempty,≤4096 bytes,no CR/LF/NUL. Do not obtain/mint a replacement token
   automatically. Neither current process nor required NL service configuration
   had a usable token.

Only public CA + approved metadata may return from RU to the offline signer. The
unsigned payload must have exactly the inventory's existing v1 fields, validated
by `restricted.delegation()`, not an invented alternate credential format. No
unsigned payload with guessed identity claims has been created. Once that public
input is prepared in an owner0700 directory outside the repository, the exact
existing signing helper invocation is:

```sh
cd /home/joker/PycharmProjects/family_connect
/tmp/fc-boot1-venv/bin/python -m scripts.sign_restricted_issuer \
  --input /protected/prov1/issuer-payload.json \
  --output /protected/prov1/issuer.json \
  --key state-client-build/update-signing/ed25519.key
```

`/protected/prov1` denotes the owner-selected protected public-artifact directory,
not a directory created in this task. This command was **not run**; input does not
yet exist. It signs only a delegation, not a catalog/release/directory. The helper
rejects any signer other than the packaged existing root and uses exclusive output.

### Initial CRL sequencing — must not be hidden

`restricted_admin.publish_crl` signs from real grant/revision/certificate history
and writes `restricted_crl_sequence` in the production access DB. Current DB has
no restricted tables. Running migration or this publisher is forbidden in this
preparation task; no copied/synthetic DB was represented as production authority.
The accepted helper has no read-only initial-CRL preparation mode. A hand-made
empty CRL or reset sequence would bypass this authority bookkeeping and was not
substituted. Moreover a prepared15min CRL would expire while waiting for deployment.

Owner must explicitly resolve the earlier preflight requirement (CRL present before
deployment) versus the accepted runbook's order (additive migration, then initial
CRL publication). A later narrowly authorized migration/initial-CRL stage, or a
separately reviewed offline preparation mechanism, is required. **No automatic
deployment retry** and no migration authorization inferred from material staging.

### Validation and security scope

- Real offline root→packaged anchor match: PASS, without signing.
- Staged anchor, deny-all JSON and permissions: PASS. No private device IDs added.
- SSH private/public parsing and correspondence, identical RU/NL public key,
  strict pre-existing host pins: PASS. Effective `ssh -G` settings match exact NL
  host/account, identitiesOnly/batchMode/strictHostKeyChecking, no agent or port
  forwarding. `ssh -G` does **not** connect; actual forced-command authentication
  is NOT RUN because authorization/account/helper are intentionally not installed.
- Accepted backend/native contract suite `tests/test_friends_restricted.py`:
  **18 passed**, including backend→native compatibility, revoked/stale revision/
  expiry/CRL-signature checks. `FC_TEST_GO` set to locked Go; ephemeral test state
  under `/tmp/fc-prod-materials-tests`, not production. This is not validation of
  a production issuer/gateway/CRL that does not yet exist.
- Actual issuer delegation/certificate/gateway identity/CRL validation: PENDING
  missing production inputs and sequencing. No false production crypto PASS.
- Provider config completeness: NOT READY, token missing. No provider/API room
  request. BOOT-1 v1 unchanged; no directory or dedicated-session URL generated.
- Post-staging RU DB read-only: restricted table count0. Existing API PID279974
  and RU/NL normal services active/NRestarts0; new restricted units not-found.
- Only generated private material is RU staged `sync.key`,0600 under0700. No new
  private key/secret/token files created under the repository or copied to task
  artifacts. Local receipts contain whitelisted metadata/public fingerprints only.
  Private root/key bytes and token values never appeared in shell/task output.
- **Pre-existing exception:** the documented offline root already resides in the
  ignored `state-client-build/update-signing/ed25519.key` under the repository.
  Thus a literal claim that the entire repository tree contains zero private files
  would be false. It was not moved/deleted/duplicated to satisfy a cosmetic check.
  If zero private files anywhere beneath the checkout is required, owner must
  authorize relocation of the existing signer/workflow separately. Git contains
  no new secret; ignored historical private stores were not exhaustively scanned.

Safe receipts: `/tmp/fc-prod-materials-stage-safe.json`,
`/tmp/fc-prod-materials-verify-safe.json`, `/tmp/fc-prod-materials-audit-safe.json`,
`/tmp/fc-prod-materials-tls-safe.json`. No private bundle in those files.
Documentation checks:410 files/2469 links/0 errors; staged source guard1553 index
entries/0 blocked files; working/staged diff checks PASS. These guards cover tracked
publication content, not a claim that all pre-existing ignored files are secret-free.

## HTTPS renewal — independent read-only housekeeping

No Certbot invocation, certificate write, timer change or nginx reload was performed.
Read existing script and bounded server-private log outcomes without exporting logs.

- `family-connect-product-cert-renew.timer`: **enabled, active/waiting**;
  OnCalendar00,12 local MSK, randomized delay≤30min, persistent scheduling.
- Renewal service is a **oneshot**, inactive/dead between runs is normal. Latest
  successful cycle01.10 **09:07:36–09:07:44UTC**, exit0/Result=success. Its private
  renew.log reports **not due / no renewal attempted**, no failure. Do not call
  this a newly issued certificate.
- Next scheduled attempt from systemd: **01.10 21:16:13UTC**
  (02.10 00:16:13MSK), subject to scheduler timing.
- Served certificate verified via normal CA/hostname checks, TLS1.3, at
  **01.10 09:59:39UTC**. Expiry unchanged **05.10 12:25:56UTC**;
  remaining354376s, approximately **4 days 2 hours 26 minutes**.
- Latest archived public leaf `cert5.pem` mtime28.09 21:24:29UTC, matching current
  certificate validity. Journal contains failed renewal-service cycles28.09
  09:15:38 and21:24:30UTC, then completed cycles from29.09 08:32:25UTC onward.
  Therefore latest certificate file generation is **not** proof that its original
  renewal-and-reload cycle succeeded. Bounded logs don't establish an exact last
  successful *new issuance plus reload* timestamp; last successful scheduled
  check above and currently served valid certificate are confirmed separately.
- Live renewal script hash matches repository `deploy/product-https/pilot.py`;
  AST confirms checked subprocess execution, nginx validation and HUP reload after
  successful renew. Initial crude text matching missed function-call syntax;
  corrected AST check passed. Two broad journal probes timed out read-only; smaller
  bounded query succeeded. No operational fix made or inferred from probe failures.
- **No current evidence of broken renewal or need for manual renewal before05.10**.
  Monitor next scheduled cycle and expiry; past28.09 failures are preserved, not
  erased. No guarantee of future ACME success and no unrelated infrastructure change.

## Stop boundary

Overall materials READY: **no**. Owner actions above are required; staged key/pins
and deny-all policy can be retained safely. Existing production authentication and
client traffic are unchanged. No broad admission, user identity reset or new root.
Production services started/reloaded: **no**. Migration applied: **no**.
Production changed beyond inert secure staging: **no**. Git push: **no**.
FIELD-1 started: **no**. Deployment retry: **not performed / not authorized by this task**.
