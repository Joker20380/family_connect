# HTTPS-вход для Android регистрации — 2026-09-14

По разрешению пользователя используется IP без домена. Новый endpoint:
**https://185.251.89.19:8443**. Product API остаётся127.0.0.1:18082;
TCP443 занят существующим VPN transport и не менялся. Amsterdam relay/WG active.

## Развёртывание

Отдельный контейнер family-connect-product-https: nginx1.30.4, image
nginx@sha256:dc5069ad14f19660b141b21236140b91656bf89bbc3e2417c70ae650cd66104c.
Certbot5.4.0, image
certbot/certbot@sha256:c23159d30afdd9c97960578aa4654f5901de6cae394958f894074dedd55e599d.
Root-owned operator files: /opt/apps/family_connect/product-https-pilot/.
Private state: /opt/apps/family_connect/state-product-https/ (0700), certificates,
staging account, work, logs. Public config and webroot отдельно смонтированы
read-only в nginx; root FS read-only, /tmp16MiB, memory64MiB, pids32.
Template и точный операторский script: [deploy/product-https](../../deploy/product-https/README.md).

Добавлены только UFW IPv4 inbound rules к185.251.89.19 TCP80 (Family Connect ACME)
и8443 (Family Connect product HTTPS). HTTP80 отдаёт только ACME challenge path;
нет HTTP регистрации. HTTPS принимает только POST registration challenge/complete
и provisioning challenge/fetch. Нет публичных admin/health/debug/OpenAPI routes.
Body8KiB, header/body5s, upstream connect2s/read10s, per-IP/global limits;
query strings rejected, access logs disabled, request bodies не логируются.

Staging certificate issuance passed; production publicly trusted IP certificate
issued, expiry **2026-09-21 02:18:22 GMT**. Private TLS/account keys остаются на gateway,
не относятся к offline client/config signing key.
[Официальный порядок IP certificates](https://letsencrypt.org/2026/03/11/shorter-certs-certbot).

Отдельные family-connect-product-cert-renew.service/.timer установлены; два запуска
в сутки00/12 с jitter≤1800s, Persistent=true. renew --dry-run passed. Обычный renew
и nginx validation/reload passed, systemd Result=success/ExecMainStatus=0; timer active.
Следующий показанный системой запуск2026-09-15 00:22:02 MSK. Важная оставшаяся проверка:
наблюдать первый scheduled запуск и последующую настоящую замену истекающего сертификата;
dry-run и ручной service run не заменяют длительное наблюдение.

## Проверки и исправления

Первый nginx -t отказал из-за стандартных fastcgi/uwsgi/scgi temporary directories
на read-only FS. Все temporary directories перенесены в /tmp; вторая проверка passed.
До исправления listener не запускался. Первый staging ACME получил TCP80 timeout:
UFW ещё не пропускал порт. После двух scoped rules staging/production прошли.

Внешняя проверка с обычным системным CA store: TLS1.3, hostname/IP verification passed.
Корень/healthz404; GET registration405; пустой JSON400; query400;8193-byte body413.
Во всех случаях Cache-Control:no-store. Burst24 пустых POST:9×400,15×429, без5xx.
Product health после rollout: schema3/statusok. Исходный product API container
StartedAt2026-09-10T11:10:53.139051801Z: API не пересоздавался/не перезапускался.
Gateway WG/AWG/TCP и neighbouring services не менялись. Это ingress acceptance,
ещё не успешная Android регистрация или VPN-приёмка.

## Invitation и данные

Подготовлен отдельный entitlement на24h и одноразовое invitation на4h для Android.
До мутации сделана SQLite online backup в product state:
/opt/apps/family_connect/state-product/db/android-stage5-before-20260914.db (0600).
Receipt server-side android-stage5-pilot-20260914.json; local ignored
state-enroll/android-stage5-pilot/invitation.json (0600). Token/DB contents не попали
в Git/CI/вывод. Устройство ещё не зарегистрировано, peer не добавлен этим шагом.
Не восстанавливать DB backup вслепую поверх последующих регистраций; при отмене пилота
отозвать только новый entitlement существующим product admin API/CLI.

## Rollback

1. systemctl disable --now family-connect-product-cert-renew.timer
2. docker stop family-connect-product-https
3. `ufw delete allow proto tcp from any to 185.251.89.19 port 80`
   и `ufw delete allow proto tcp from any to 185.251.89.19 port 8443`.

Удалять только эти новые правила после сверки комментариев; сохранить private
certificate state. localhost API, DB и все прежние peers/routes оставлять. Не
останавливать Docker daemon или другие контейнеры. Возврат: docker start только
нового контейнера, scoped rules, timer, затем TLS и API checks.
