# L04.1-AUTH-PROVISION — один штатный nl assignment

25.10.2026. **DONE / review pending**. **L04.1-AUTH DONE**:
[identity/activation subset](2026-10-25-linux-test-activation-l04-1-auth.md)
принят, недостающий per-device assignment получен в отдельно разрешённом scope.
**L04.1 BLOCKED / live NOT_RUN**, L04 IN_PROGRESS; L04.2 QUEUED/NOT_RUN,
L05 не начат. L03.1/L03.2/parent L03 DONE, review accepted.

## Разрешённый scope и provenance

Вход `main` и проверенный `origin/main`:
`8fcba47bc844bfaa92e3061bbc475a740df8167c`. Checkout назад не выполнялся.
Только существующая **FC-3YSQ-BE2D**, country **nl**; новых identity/invite — **0**.
SHA256 публичной identity:
`d07d33a81728ff70aec350ae59785990c194d90ecd44574b0da28439189532de`.
Загрузка только `create=False`; личные identities не использованы.

Exact [final-2](2026-10-25-linux-candidate-l03-2.md) не изменён/не пересобран/
не установлен; state в VM/контейнер не переносился. Выполнены только unprivileged
packaged Python3.12.3 `-I -S`, offline/read-only preflight, один штатный fetch и
readback. Все707 членов user inventory повторно проверены по candidate manifest;
RNS/cryptography/httpx импортируются из exact vendor, не checkout/PYTHONPATH/site.

| Identity/artifact | Exact value |
|---|---|
| Product source | `cf66532c72548767f8ff4aa31faa7588b07eab54` |
| Candidate ID | `9d4b13cc106296264805402b42538b9fa94505433b1bbd239c82145966e22b81` |
| Embedded system build | `8708ba6d5e218f86b42d862dd5a66237e974a03d5434e8f1c30524b16720e2da` |
| AppImage SHA256 / bytes | `914f02ff10f31485c5a6b68a8ff41f5b168aaffc8f7f8241723365c40a9109e5` /57924088 |
| DEB SHA256 / bytes | `df13422321f6c5865f1ca1060fe221fbe21954c6981ab05cb2d173e7aa6e04ac` /55951120 |
| Running access archive SHA256 | `21d64558e542ff6ad80fb9b13799fbcb333167ffb5a79ec841e7c94dc65d71fa` |
| Deployed NL register helper SHA256 | `8e536367a391661f003d0725afc13f69c45a9e43bb1763b61fd21ce0b998035a` |

AppImage/DEB hashes/размеры повторно сверены с исходной review-парой; CI rebuild
не подставлялся. Исходная/public Linux version не менялась. В Git — только docs;
product source, protocol schemas, gateway scripts и deployment не менялись.

## Preflight и единственная mutation

До сети выполнен существующий `sh "$FC_L04_TEST_STATE/operator/preflight.sh"`:
Support ID/fingerprint/create=False PASS; owner1000, directories0700/files0600;
configuration cache отсутствовал. State остаётся по защищённому пути предыдущего
AUTH checkpoint вне checkout/синхронизации. Ни key, ни invite, ни profile не
передавались через argv/stdout; operator проверки получают bindings по SSH stdin
и сравнивают их в памяти, не печатают и не сохраняют raw binding в receipt.

Read-only registry подтвердил active/not revoked, одну точную публичную/WG/TCP
binding и одну consumed invitation. Registry totals54 devices/108 invites не
изменились; новых устройств/invitations не создано. Deployed running archive,
handler/access modules и NL helper сверены; helper совпадает с существующим
[register implementation](../../deploy/friends/awg-gateway.py).
Gateway/Xray API healthy; registration.lock доступен. До fetch для target:
peer row/live peer/persisted TCP/runtime TCP counts **0/0/0/0**; дубликатов нет.
Private exclusive intent/pre-state сохранены до mutation, fsync/0600;
повторный запуск fetch guard отказывает, неизвестный исход требует readback.

Ровно **1** вызов `FriendsOwner.configuration("nl")`, без driver:
fresh challenge/proof → `/friends/configuration/nl` → существующий gateway register
→ AWG peer + atomic TCP server.json + Xray API → verification →
`FriendsConfigurationStore.accept`. Challenge/configuration HTTP200; retry **0**.
Ручного `awg set`, редактирования server.json или прямого Xray apply со стороны
операторского harness не было: все изменения выполнил штатный endpoint/helper.

## Readback

| Gate | Результат |
|---|---|
| Peers DB / live AWG totals | 45→46 /45→46; target ровно1/1 |
| Persisted / runtime Xray totals | 45→46 /45→46; target ровно1/1, exact same binding |
| Stable address | DB row-derived address = live allowed-ip = verified client address; ожидаемая nl subnet; только один allowed-ip |
| Foreign bindings | Все45 прежних DB/live peers и persisted/runtime clients: canonical hashes неизменны |
| Temporary register files | server.pending/user-request.json отсутствуют после завершения |
| Global settings | Canonical Xray config без clients неизменён; settings/AWG server.conf/binary hashes неизменны |
| Service continuity | Active/running, MainPID/InvocationID hashes неизменны; restart/deployment NOT_RUN |
| Registry/catalog | Registry bindings/counts и signed catalog bytes неизменны |
| Client cache | Создан0600; только nl; exact device; AWG/TCP validation PASS |
| Signature/floor | Ed25519 common catalog verification, sequence/hash/same-floor повторный readback PASS |
| Reopen | Новый packaged Python3.12 процесс, create=False, тот же fingerprint/cache, PASS |
| Apply/connect | NOT_RUN; driver не передан, GUI/helper/setup не запускались |
| Traffic | Test AWG handshake0, RX0/TX0, endpoint отсутствует |

Подпись относится к common catalog/templates. Device-specific address/TCP binding
приходят по штатному authenticated HTTPS; packaged verifier проверяет exact device,
country, address и профиль совместно с подписанным catalog. Отдельная Ed25519
подпись per-device assignment не заявляется. Отсутствующий legacy gateway_id
не добавлялся. Entitlement остаётся обычным FAMILY, assignment не active/applied
session. Test-device VPN остаётся DISCONNECTED: owner/session/intent не создавались.

Хостовые links/routes4/6/rules4/6/DNS/domains pre/post hashes совпали; новых TUN,
route/rule/DNS операций нет. На NL совпали address/routes/rules hashes.
**Ограничение firewall evidence:** raw `iptables-save` hashes pre/post отличаются;
они включают текущие chain counters и timestamps. Попытка timestamp-only сверки
не доказала byte equality; нормализованный структурный baseline до fetch не был
сохранён. Поэтому полный firewall ruleset pre/post comparison **NOT_RUN**, а не
ложный PASS. Это не наблюдение apply: register path не вызывает routing/firewall
часть `run()`, settings и foreign resources readback сохранены. Полный network
baseline/cleanup gate всё ещё принадлежит установленному L04.1.

## Sanitized hashes

| Объект | SHA256 |
|---|---|
| server.json до | `ffa07f57452a12e30649d8fd17d38b013d78af0ddda525cdc3d69473af23a20f` |
| server.json после | `107d6b9b21b6b699693e95ece553302b8f1b56ac3ccf5872789eb536fc0bc9bd` |
| Signed catalog payload | `f4d812db722705d8fc853a1a1afd454922cd2bca71175db025f40b9a58c3628d` |
| Verified cache file | `d05447cea81d06e7d2a7266e70a53e5787b6ec9ff84c398b3be00e154f239049` |
| WG public binding, canonical text | `9a1b3cc0107d71dfa88cabdcfe519b10e9ba0ad6017956859fe8b66f6cc16bd4` |
| TCP UUID text | `f3848f2dee8e7cf738b20c2013be7be7bd3fc07c5a3cfc3a2896ab53a272a52b` |
| TCP email text | `b80335fa461b5cf2450177134101905a1f592a25bc5f4331618039ff8088c5c4` |
| Private teardown receipt | `d31a648a007d8706073b88c72ed6f59909121a36fa012791290c7a4e33407b7a` |

## Private retention и обязательный teardown

State не экспортирован/не перенесён. Existing `FC_L04_TEST_STATE` и offline
preflight используются без вывода содержимого. Private helper preflight дополнен
проверкой уже существующего cache; не делает fetch/apply и не создаёт identity.
Каталоги0700/файлы0600, UID1000, no symlinks/hardlinks; повторная проверка PASS.

Private receipt расположен только в
`$FC_L04_TEST_STATE/operator/nl-provision-20261025/teardown-receipt.json`.
Он содержит country/registry device ID/peer row/address/binding hashes/pre-post
server.json hashes и точные read-only проверки, но не raw keys/UUID/email/profile
или activation code. Материалы operation/receipt/state не входят в Git/CI.

Будущий обязательный gate, сейчас **QUEUED / NOT_RUN**:
**device-scoped gateway cleanup → readback → registry revoke**.
Текущий helper не имеет штатного unregister. Требуется отдельный reviewed cleanup
только этого device, с новым private baseline перед удалением, проверкой отсутствия
target DB/live AWG и persisted/runtime TCP и сохранности чужих bindings/settings.
Нельзя откатывать целиком старую DB/server.json или перезапускать сервис ради cleanup.
Сейчас cleanup/revoke **NOT_RUN**: assignment сохранён для L04.1 после review.

## Проверки и stop boundary

Packaged inventory/import/state/assignment readback PASS. Stdout содержит только
sanitized counters/hashes/status. Private operation files проверены на отсутствие
raw WG/TCP/email material. Broad unit journal queries timeout; повторная bounded
проверка конкретных изменявшихся journal files: по1 файлу на gateway, за окно
операции для проверенных services записей0, secret matches0. Это не аудит всех
исторических/system/nginx logs; отсутствие секретов вне этого окна не заявляется.

Docs-only checkpoint: staged allowlist6 files,12 added relative links, content,
whitespace и secret scan PASS; scan staged files/all-ref patch history — target
WG/TCP/email matches0, staged secret-pattern matches0. Private state/operator receipts/build outputs не
стейджатся; параллельные ops-hunks и ops report остаются вне commit.
Full desktop/native/root→UID/Auto/DIRECT/Client Linux/full-suite gates не отключены,
но здесь не перезапускались: product code не менялся. D01 открыт с54 residual
failures; D02.1-R PARTIAL/NOT_RUN; Windows/voice observations сохранены.

NOT_RUN: final-2 install/pkexec/setup; AWG/TCP connect, VPN DNS/HTTPS/transfers,
live acceptance; L04.2 MESH/Auto, L05, cleanup/revoke, public release/catalog/landing,
gateway deployment/restart, policy/floors/trust/signing changes. RU provisioning —
NOT_RUN; access/challenge handler использован штатно, без RU peer/configuration fetch.

**STOP. NEXT — review L04.1-AUTH-PROVISION.**
