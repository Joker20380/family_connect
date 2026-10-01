# 5N-PROV-1 controlled deployment — authorization required

## Directory validation gate — corrected locally after attempt #4

Attempt #4's producer emitted valid BOOT-1 v1; the old inline Python operator
rounded its current clock down with `int(time.time())`, falsely treating a
same-second nanosecond `issued_at` as future. Production remains rolled back;
this local fix does not authorize attempt #5. Attempt #3 HTTP cause remains UNKNOWN.

Use the corrected committed-source closed runtime, not the archived operator's
inline directory call/imports. Candidate built from `29d15d7`:
`state-client-build/directory-validation/final-sync-bundle/restricted-sync.pyz`,
SHA256 `cb6f050ec49ee4b65fa65c5327e32d6271d714ef6f8e695f16cb3c85b60f386f`;
all17 inventory entries pinned. Producer binary/native consumer unchanged.
The previously accepted HTTP archive is not rewritten: future HTTP packaging must
include the corrected shared Python consumer and pass its own activation gate.

After separate authorization, the NL validation step is:

```sh
venv/bin/python -I /path/to/pinned/restricted-sync.pyz directory-check \
  --profile /protected/gateway.json --directory /protected/directory.json \
  --receipt /protected/attempt-evidence/nl-directory.json --generation attempt-N
```

This command reads existing inputs and writes only a redacted receipt. It never
starts a service, publishes a CRL, fetches provider data or enrolls a device. It
does not replace authority/native/CRL validation. Sample the real nanosecond clock
after reading the directory; do not pass truncated seconds or alter wire timestamps.
There is no clock-override CLI option or skew allowance. The legacy integer-second
library argument is only for deliberately exact whole-second test snapshots;
use `now_ns` for injected precise test clocks and the default for live checking.

`directory_validation_failed: stage=time predicate=issued_in_future field=issued_at`
is a bounded category, not a dump of the field value. Parse/schema/binding/seed/
expiry/lifetime failures also have bounded categories. Receipt includes safe time,
generation and verdict/category, never URL/profile/identity/proof/body. Keep the
owner-only receipt path outside replaced/rolled-back runtime directories. The
file and containing directory are fsynced before a failure exits; persistence
failure itself forbids acceptance. Only after a successful verdict may the operator
advance; otherwise preserve receipt, perform the scoped rollback and stop. Never
catch-and-ignore the error or retry until a clock boundary happens to pass.

Tests cover receipt ordering, nonzero shell/EXIT trap/rollback marker, hard process
exit, exact issuance/expiry ±1ns, URL/security bounds and real SeedManager serialized
publication through the isolated Python archive back to native validation.
[Detailed proof and limits](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

## Попытка №3 — rolled back, 01.10.2026 14:40UTC

Source `2705db4`: закрытый archive установлен на RU/NL, RU `python -I ... --check`
и live sync PASS; ModuleNotFoundError не повторился. NL READY/UTC-Z/Python PASS,
generic shell и stale CRL отклонены. После включения API провалился normal HTTP
smoke; немедленный rollback вернул API/ingress, выключил sync timer/NL seed/auth.
AWG/TCP не перезапускались, Redmi не трогали. Причина HTTP failure не установлена;
probe observations потеряны при assertion, точный downtime/zero downtime не доказан.
[Полный порядок, ограничения evidence и финальное состояние](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

DB/live CRL на RU и NL сохранены на sequence11 (expiry14:55:41UTC), root-only JIT
stage остаётся на6. Не откатывать DB/monotonic floors и не использовать stage6 как
текущий sequence при следующем refresh. Следующий шаг — локально проверить API/
ingress transition и crash-safe probe receipt; **не автоматический deployment retry**.
Ниже сохранены предыдущие checkpoints и контракт поставки.

## 5N-RUNTIME-PACKAGING — локальное исправление, не deployment

После попытки №2 исходники sync поставляются только по
[`runtime-files.json`](runtime-files.json), builder —
[`scripts/package_restricted_runtime.py`](../../../scripts/package_restricted_runtime.py).
Manifest содержит10 Python-файлов, включая единственный чистый stdlib-модуль
`clients/desktop/profile_config.py`; GUI/backend/client state не поставляются.
Он намеренно используется для строгой проверки AWG/TCP templates. Перенос этого
парсера сейчас затронул бы несколько desktop/TCP packagers и шестифайловый legacy
archive; поэтому выбран явный lightweight dependency, без копии реализации.

Локальная сборка из checkout с venv, установленным по обоим существующим lockfiles:

```sh
python scripts/package_restricted_runtime.py \
  --output state-client-build/restricted-runtime \
  --python /path/to/locked-venv/bin/python
```

Builder отказывается перезаписывать output, проверяет каждый source и запускает
`--help`, `sync --help`, `gateway --help` из готового `restricted-sync.pyz` с
`python -I`. Это стандартный stdlib zipapp, не sys.path/PYTHONPATH workaround.
Python внутри архива — тот же source, что в `app/`; внешние RNS/cryptography и их
зависимости остаются в venv по поставляемым `control.lock`/`identity.lock`.
`sha256.json` фиксирует bytes всех outputs. Сборка не включает runtime state,
fixtures, ключи, provider.env, authority или комнаты.

**Только при следующем отдельно разрешённом rollout:**

- Overlay `app/` из bundle в `friends-access/app/`, сохранив существующие обычные
  API модули; **не заменять весь app** минимальным sync-набором. Отдельно поставить
  reviewed API handler как прежде. Не делать ручной выбор Python-папок.
- Один и тот же `restricted-sync.pyz` разместить на RU/NL по
  `/opt/apps/family_connect/friends-access/restricted-sync.pyz`, root-owned0644;
  родительские каталоги должны быть traversable сервисному пользователю NL.
  В read-only backup включить старые app/архив (если есть), unit и helper.
- RU использует unit из **того же bundle**: `venv/bin/python -I .../restricted-sync.pyz sync ...`.
  NL root-owned0755 helper — [`restricted-sync-command`](restricted-sync-command)
  из bundle, тот же archive с `gateway`; прежние SSH `restrict`/source restriction/
  forced-command сохраняются. Никакого `PYTHONPATH` или зависимости от cwd checkout.
- До старта sync выполнить его точный `ExecStart` с добавленным `--check` и
  `FC_FRIENDS_RESTRICTED_DIR`. Проверка только локально читает/валидирует
  delegation/key/admission/CRL, CRL sequence/SQLite integrity и bounded key/host
  files. БД открывается `mode=ro`; publisher, SSH и writes не вызываются.
  Успех выводит только `Restricted runtime pre-network check passed`.
  Это **не** проверка SSH-аутентификации/удалённого consumer и не обновление
  истёкшего CRL; JIT freshness и последующие live checks всё ещё обязательны.

Regression: `tests/test_restricted_runtime.py` строит точный bundle и читает его
unit/helper, проверяет imports/CLI вне checkout, без/с посторонним PYTHONPATH,
отрицательное удаление каждой runtime dependency, fixture-only `--check`,
неизменность файлов/БД и запрет publisher/socket/subprocess. CI path filters
включают manifest, helper, builder и server modules. Android/shared parser source
не изменены, новый APK для этого исправления не требуется.

**Production остаётся в состоянии rollback попытки №2.** В этой локальной задаче
нет SSH/deploy/start/authority refresh/phone testing/push/FIELD-1.

### Исторический блокер и откат попытки №2

**Попытка №2,01.10 13:39UTC: DEPLOYMENT FAILED / ROLLED BACK.**
Source `e808f50`: NL READY и живой UTC `Z` → Python PASS. RU sync остановлен:
`provisioning.friends_catalog` импортирует `clients.desktop.profile_config`,
которого нет в описанном минимальном RU bundle. Полный authority staging скрывал
зависимость. **Не повторять rollout до локального исправления runtime manifest
и isolated import/CLI smoke точного deployment bundle.** Не добавлять зависимости
ad hoc на production. API/routes не включались; RU API/ingress восстановлены без
restart, NL bootstrap/sync authorization выключены. CRL sequence5 сохранён;
перед новым разрешённым retry нужен JIT refresh, не reset.
В sticky NL directory обновление service-owned gateway.json требует atomic
create/fsync/chown/rename, не copyfile поверх старого файла: сохраняем
`fs.protected_regular=2`, owner/mode. [Доказательства/откат](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

### Исторические checkpoint до попытки №2

**Local repair checkpoint: 5N-TIME-COMPAT PASS, not deployed.** Go seed export
and Directory serialization now emit UTC `Z`; Python/native consumers validate
offset-aware RFC3339 instants with unchanged lifetime/replay/trust bounds.
Before any separately authorized retry, rebuild/re-stage the modified Go/Python
artifacts and JIT refresh expired material. Do not start the inert old NL binary.
[Contract and regression evidence](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

**Current rollout checkpoint,01.10 11:48UTC: [DEPLOYMENT FAILED / ROLLED BACK](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).**
NL seed joined READY, but generated `expires_at` retained host offset `+03:00`,
rejected by the Python `Z`-only timestamp parser. NL unit/auth disabled and directory
quarantined; RU runtime/routes/sync never deployed. Normal production unchanged.
Do not repeat this rollout until local timestamp compatibility/regression coverage
is fixed and a new controlled retry is authorized. No manual directory rewrite or
TTL extension. Actual ingress validation command: `nginx -t -c /etc/fc/nginx.conf`
inside `family-connect-product-https`, not nginx's unused default configuration.

### Historical preflight

**Current checkpoint,01.10 11:21UTC: [DEPLOY-PREFLIGHT READY](../../../docs/releases/2026-10-01-5n-prod-deploy-preflight.ru.md),
not deployed.** Owner-installed final NL provider.env passes metadata/schema-only
checks; token never returned/hash/size-reported. Same authority, CRL3 expires
11:35:38UTC, gateway leaf12:20:38UTC; no TTL extension. Other material remains
inactive staging, account/units not installed. Stop before deployment; refresh
through the publisher again if this short validity window is missed.

### Historical input checkpoint

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

- Deploy the checked bundle described above: explicit `app/` overlay, the same
  `restricted-sync.pyz` and unit/helper templates on RU/NL; preserve existing API
  modules. Deploy reviewed `deploy/friends/access-api.py` to the existing handler
  path. Use the bundle's existing control/identity lockfiles in `friends-access/venv`;
  verify cryptography compatibility. Never copy only three guessed source folders.
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
- The dedicated RU sync public key must have the root-owned `restricted-sync-command`
  wrapper from the checked bundle as its sshd forced command. It invokes the verified
  NL venv with `-I /opt/apps/family_connect/friends-access/restricted-sync.pyz gateway`
  and the existing profile/directory paths, independently of cwd. Use `restrict`, source
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
