# Исходники этапа5 и хранение секретов —24.09.2026

Подготовлен checkpoint поверх GitHub main b5f486444c66f3093cdc49ecbd30cc8fcc5da901.
Публикация в Git разрешена пользователем и выполнена: main `86eb24e`.
Push завершился успешно; GitHub Actions API подтвердил9 queued workflows для этого
SHA. Завершение CI пока не проверено.120 файлов,8142 добавленных/80 удалённых строк.
Документационные проверки:325 файлов,1911 ссылок,0 ошибок; diff whitespace check passed.

## Состав

Fleet inventory/leases/IPAM, fencing/SSH adapters, scheduler, offline publication;
managed AWG3.1 verifier в Python/Java/C#, Android gateway transaction/service/UI,
тестовые vectors, результаты4 проверок на Redmi Note 9 Pro, карты кода и отчёты24.09.
Рабочая копия отставала на38 коммитов. Инвентаризация публичных файлов и сравнение
base/local/remote выявили118 файлов с оставшимися изменениями; они перенесены
в отдельный worktree поверх текущего main. Существующие remote-only изменения
сохранены, исходное грязное дерево не сбрасывалось. Дополнительно включены этот
отчёт и согласованная политика секретов. Никаких force-push или переписывания истории.

Пользователь выбрал [хранение секретов](../secrets-and-recovery.ru.md) на компьютере
и отдельном офлайн-носителе с шифрованием; пароль отдельно. Это выбранная схема,
не выполненная настройка: хранилище, резервирование и восстановление ещё предстоят.
Секреты не читались и не переносились. Публичный Git содержит только политику.

## Проверки дерева публикации

- Python:890 passed,2 deprecation warnings; fleet/AWG31 subset209 passed отдельно.
- Java isolated control suite:124 passed,0 failures/errors/skips.
- .NET10 runner: exit0, включая8 AWG31 vectors ×2 capabilities и legacy corpus;
  Windows DPAPI checks skipped на Linux. Сначала восстановлен NuGet cache для новой
  рабочей копии; NuGetAudit=false использован только при offline/cache restore.
- Новый device test и исходники Android совпадают с ранее собранными и проверенными
  на Redmi файлами; отдельная APK сборка из worktree не выполнялась.
- Проверен перечень включённых путей и известные шаблоны PEM private keys, GitHub/AWS
  credentials и длинных literal passwords/tokens: совпадений нет. Это ограниченная
  проверка, не доказательство отсутствия любого секрета. State/build/DB/private-key
  файлы исключены; публичные TEST ONLY fixtures отмечены отдельно.

## Оставшиеся работы

Service/UI acceptance с тестовым enrollment и реальным VPN gateway, process restart,
permission/cancel и полезный трафик. Текущий pilot пустой, synthetic corpus не даёт
рабочих серверов. Рабочая AWG3.1 capability по-прежнему выключена; Friends identity
integration не выполнена. Следующий полевой тест требует отдельной тестовой identity,
краткоживущей подписанной конфигурации с двумя gateway и проверки пути rollback;
не использовать публичные fixture keys для выдачи рабочего доступа.

Не опубликованы новые APK/installer и не менялись серверы. Версии:
Android0.1.18-beta50/code50, Linux0.2.10, Windows0.2.13.
Откат исходников — отдельный revert коммита; он не откатывает live state. Нельзя
сбрасывать replay floor или подменять уже опубликованные подписанные артефакты.
