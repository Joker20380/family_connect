# Android Auto — 2026-09-12

Статус: принята в изолированном CI. База e894d06.
Auto выбирает сохранённые профили WG→AWG→TCP; отсутствующие/повреждённые пропускает,
не меняя файлы. Отдельный переключатель Auto; импорт/удаление относится к выбранному
в списке протоколу, новый общий профиль не создаётся.

DNS reachability: Network с TRANSPORT_VPN и адресом текущего TUN, explicit
Network.bindSocket и bind исходного IPv4, без fallback на физическую сеть.
Два адреса 1.1.1.1 и9.9.9.9:53, случайные transaction ID и label под example.com,
проверяются ответ/rcode/полный вопрос; один корректный ответ достаточен.
Тайм-аут2500ms на адрес; начальная проверка через1s, затем через15s при успехе,
через1s при отказе. Два последовательных провала вызывают переход; успех обнуляет
счётчик. До первичного успеха состояние connecting. Это доступность DNS через
туннель, а не HTTPS/full-Internet health и не защита от поддельных ответов resolver.

Один последовательный worker, поколение callbacks, отмена закрывает текущий socket,
cleanup отменяет расписание до engine.down. При ошибке cleanup — cleanup-required,
следующий движок не запускается. Бюджет: каждый транспорт не более одного раза за
команду Connect; исчерпание останавливает соединение. Возврата к WG по кругу нет.
Системный отзыв VPN завершает соединение; автоматического permission prompt нет.

CI проверил реальные отказы peer на runner: WG без ответов→AWG, потеря ответов
при работающем AWG→TCP, приоритет WG, исчерпание, отмена и системный отзыв.
Control HTTP и drop-files существуют только в синтетическом стенде, APK их не содержит.
Обычные WG/AWG/TCP сценарии сохраняются; проверка идёт на API35 x86_64, сборка4ABI.

Android0.1.0/versionCode1; debug APK не публикуется и не устанавливается.
Desktop0.2.9/catalogseq8, Linux0.2.7 installed, Windows0.2.7 last reported,
gateway0.2.1/TCPSetup0.1.0 не меняются. Rollout отсутствует; откат исходников e894d06,
откат установленного APK не требуется. Телефон, нагрузка, сон/Doze, смена сети,
реальный gateway/Интернет отложены. После Auto — этап5 Reticulum; Google Play и
Android updater не являются условием его начала.

## Подтверждённый результат

Код приложенияa51aa52, расширенные тесты6fa2bc7.
[Clients34679094884](https://github.com/Joker20380/family_connect/actions/runs/34679094884)
и [phase034679094921](https://github.com/Joker20380/family_connect/actions/runs/34679094921): success.
Предыдущие clients34676944535/34677017326 отменены новыми коммитами, не считаются приёмкой.
Полная приёмка60697d0/clients34677285505 уже прошла до последней lifecycle-поправки.
cf5f7c0/a51aa52 добавили ожидание VpnService.onDestroy до смены WG/AWG;
тайм-аут3s оставляет cleanup-required, повторная очистка ждёт ту же future.
Промежуточный clients34679037433 отменён новым коммитом.
60697d0 сохраняет ручные IPv6-профили: требование IPv4 применяется только в Auto.
Локальные325 Python tests passed,2 dependency deprecation warnings.
Four ABI build;23 JUnit methods;lint0 errors/10 warnings;3 instrumentation methods на API35 x86_64.
Auto: WG без ответов→AWG, потеря данных при живом AWG→TCP, приоритет WG,
пропуск отсутствующего WG, исчерпание всех трёх, отмена через1.5s после Connect (<5s до off),
системный отзыв в Auto.12 UDP,6 REALITY HTTP,1 OS DNS,5 завершающих очисток.
С учётом прежних тестов:48 UDP,24 REALITY HTTP,4 OS resolver вызова,18 cleanup
сценариев. Проверены отсутствие VPN/внешних TCP-соединений после остановки,
сохранность раздельных профилей, отсутствие позднего запуска после отмены.

APK SHA-256 `7d79204dec7c3f8e2fa265282d3b79c819edd33ab95aa2574da410f3ee15b4f0`, 185981772 bytes.
Fixture HTTP24, DNS62 (включая health/фон ОС).
SHA-256 архива совпал с опубликованным GitHub digest; скачанный APK/native manifest сверен; один Go runtime и четыре лицензии,
instrumentation/control helpers отсутствуют в основном APK.
[Машинный результат](../android-auto-result.json); ignored архив
state-client-build/session-2026-09-12-android-auto. Runtime проверен только x86_64,
побайтовая воспроизводимость сборок не заявляется.

Привязка socket следует [Android Network API](https://developer.android.com/reference/android/net/Network#bindSocket(java.net.DatagramSocket)).
Контрольный канал отказов и DNS synthetic responses существуют только на CI runner;
в приложении нет test health overrides и endpoint-настроек из Intent.
Следующая разработка — Reticulum; выпуск/обновление устройств остаются отложены.
