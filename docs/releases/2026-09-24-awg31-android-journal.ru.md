# 5.3а: Android identity/journal и проверка состояния GitHub

24.09.2026. Локальные исходники, без выпуска и production rollout.
Версии неизменны: Android0.1.18-beta50/code50, Linux0.2.10, Windows0.2.13.

## Изменения и проверка

ControlIdentity.verify и ControlJournal получили overload с явным supportsAwg31.
Прежние сигнатуры оставлены с false. Способность задаётся доверенным вызывающим
кодом и не загружается из профиля/журнала. Все проверки сохранённых envelopes
проходят через ту же capability, включая повторное открытие журнала.

Новый тест использует подписанный общий AWG3.1 fixture, существующие ControlIdentity,
ControlJournal, ControlTransaction и ControlApplication. Host/storage имитируются:
это Java unit-test, не Android Keystore/VpnService/native engine acceptance.
Проверены commit, подстановка локального WG key, сохранение защиты в ProfileValidator,
выбор dynamic-node-47, повторное открытие журнала без повторного запуска, revision floor,
rollback с восстановлением прежних профилей и отказ legacy journal читать сохранённую
AWG3.1 конфигурацию без capability. Ключи только публичные тестовые.

Все110 Java tests прошли,0 failures/errors/skipped. Команда:

```sh
JAVA_HOME=/tmp/fc-chat-tools/jdk/jdk-17.0.20.1+1 GRADLE_USER_HOME=/tmp/fc-chat-tools/gradle-home /tmp/fc-chat-tools/gradle-8.11.1/bin/gradle -p clients/android/control-tests test --offline --no-daemon
```

Gradle запускался с разрешением вне sandbox из-за необходимости localhost socket.
Рабочие Android callers остаются с false до device acceptance и привязки Friends identity.
Следом — native integration/service routing/health/recovery на телефоне, Linux application
проверки и Windows journal/broker integration.5.3а ещё не закрыт,5.2 ACK/relay также открыт.
Серверы не менялись, серверный откат не нужен. Не откатывать floors/сохранённые envelopes.

## Документация: локальная и опубликованная

По вопросу пользователя проверен GitHub origin/main через ls-remote и fetch.
На момент проверки remote main=b5f486444c66f3093cdc49ecbd30cc8fcc5da901,
последний коммит `docs: scope stage 5 milestones and estimates`.
Удалённый docs/STATUS.md датирован23.09 и описывает этап5 как следующий.
Отчётов24.09 managed-awg31 и managed-awg31-native-verifiers в этом дереве нет.

Последние документы24.09 пополнялись локально, но не были закоммичены/отправлены.
Нельзя называть эти checkpoint опубликованными на GitHub. В этой работе выполнен
fetch; commit/push не выполнялись. Локальный checkout существенно отличается от
remote main и содержит большую незакоммиченную работу; его нельзя выравнивать reset
или принудительной отправкой. Для публикации нужен отдельный согласованный docs
checkpoint на основе актуальной remote ветки, с сохранением локальных изменений
и проверкой ссылок на ещё неопубликованные исходники.
