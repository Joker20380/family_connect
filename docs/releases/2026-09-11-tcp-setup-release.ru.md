# TCP Setup0.1.0 опубликован с офлайн-подписью — 11.09.2026

Новый отдельный immutable release
[tcp-setup-v0.1.0](https://github.com/Joker20380/family_connect/releases/tag/tcp-setup-v0.1.0),
source7eee3c3e153319aa62d32123e8c92a33f9f4cdb3. Desktop0.2.9 и TCP component0.1.0
не перевыпускались; профильные/серверные настройки не менялись.

## Что добавлено

scripts/tcp_setup_signature.py: офлайн Ed25519 подпись и non-root проверка архива
до запуска bootstrap. Отдельный domain family-connect/tcp-setup-release/v1,
строгие поля schema/component/architecture/version/size/SHA256, ограничения размера,
защита от duplicate fields, отказ unsafe signing key/перезаписи подписи.
Verifier не исполняет и не распаковывает архив. Явная ожидаемая версия обязательна.
Это detached release attestation без срока/sequence, не автоматический update catalog;
TCP component floors остаются отдельными и не сбрасываются.

Доверие на первом устройстве: verifier и public anchor получают заранее доверенным
каналом. Нельзя доверять ключу/верификатору только потому, что они скачаны вместе с
архивом. На существующем Linux можно использовать anchor установленного приложения.
[Runbook с загрузками и fingerprint](../tcp-setup-trust.ru.md).

TCP workflow получил отдельный setup_release job для tcp-setup-v* и версию packager
из тега. После build/tests он публикует archive/SHA256SUMS; подпись выпускается локально
только после проверки скачанных assets. Старые desktop/tcp tags не заменяются.

## Проверки и публикация

-281 Python tests passed,2 прежних deprecation warnings.8 новых signature cases:
  корректная подпись, expected version, tampered bytes/key/signature, cross-domain,
  duplicate fields, unsafe key/overwrite и size bounds. Негативные варианты параметризованы.
- Exact-source main CI: [clients](https://github.com/Joker20380/family_connect/actions/runs/34621236227),
  [TCP](https://github.com/Joker20380/family_connect/actions/runs/34621236240),
  [AWG](https://github.com/Joker20380/family_connect/actions/runs/34621236231),
  [phase0](https://github.com/Joker20380/family_connect/actions/runs/34621236219) — success.
- Tag CI: [TCP+setup publication](https://github.com/Joker20380/family_connect/actions/runs/34621232658),
  [AWG](https://github.com/Joker20380/family_connect/actions/runs/34621232428),
  [phase0](https://github.com/Joker20380/family_connect/actions/runs/34621232587) — success.
- Published archive8214B скачан; SHA256SUMS совпал с локальной повторной сборкой и
  прежней VM/Ubuntu acceptance: c16c924cac52acc5d3555c38a5260b6f4cdc530b4484a831dc35a47dab025c17.
  Bootstrap payload не менялся, VM/устройства повторно не устанавливались.
- После всех CI и скачивания подпись создана существующим локальным ключом, проверена
  production anchor. Private key не передавался в CI/сеть и не выводился.
  Подпись updates/tcp-setup-0.1.0.json опубликована commit e6752df.
  Канонический public URL скачан; verify с anchor уже установленного Linux-клиента
  прошёл для архива0.1.0. Установленный клиент и его состояние не менялись.

## Состояние и откат

Installed Linux0.2.7, Windows last reported0.2.7; published desktop0.2.9/catalogseq8,
TCP component0.1.0, server0.2.1 unchanged. На host/VPS не выполнялись новые сетевые
эксперименты. Прикладная устойчивость всё ещё открыта, user load-test deferral сохраняется.
Android без кнопки проверки обновлений; пользователь подтвердил ручной APK и отложил
обновление Android. Google Play distribution не используется в текущем процессе.

Новых установок нет — deployment rollback не требуется. При последующей установке
bootstrap сохраняет /var/backups/family-connect/tcp-updater-*/restore.json; сохранять
профили/update floors, не делать общий reset. Published setup immutable; дальнейшие
изменения только новым version/tag. Подпись конкретного setup не является механизмом
revocation уже установленного updater.

Evidence/scripts/public artifacts локально в ignored
state-client-build/session-2026-09-11-setup-release; рабочая папка /tmp/fc-setup-release.
Production key туда не копировался. git diff --check прошёл.

Далее: native Windows AWG/TCP integration, затем Android transport work/device acceptance.
Reticulum delivery/независимый gateway впереди. Android updater и новые сетевые load
эксперименты не возобновлять без изменения пользовательского приоритета.
