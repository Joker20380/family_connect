# 25.09.2026 — публикация proprietary source-available лицензии

По прямому запросу владельца подготовлена публикация согласованной LICENSE
из локального b6112ad поверх актуального GitHub main139f7da. Отдельный checkout
исключает незавершённые Reticulum/WebRTC изменения и накопленный рабочий diff.

Добавлены LICENSE, THIRD_PARTY_NOTICES.md, docs/legal/DEPENDENCY_LICENSE_AUDIT.md;
обновлены README.md/README.ru.md/README.en.md, docs/licensing.md, STATUS и PLAN.
Формулировка отдельно проверена: original project material only, без чужих прав,
без отмены prior valid grants, с исключением applicable law/platform viewing/forking.
Нет компании с вымышленным названием. Root license не подменяет Reticulum/MIT/MPL
или другие third-party terms. ICQ asset provenance и полный transitive audit открыты.

Перед публикацией: whitespace и локальные ссылки проверены, public-source guard
по индексу пройден. Runtime tests не требуются для документационного изменения.
Код/dependency pins/secrets не менялись. Android beta50/code50, Linux0.2.10,
Windows0.2.14 остаются прежними; binaries/deploy/signing не выполнялись.
Точный publication commit фиксируется в Git history; факт push и наличие LICENSE
в опубликованном commit проверяются отдельно после отправки. Runtime rollback
не требуется; корректировки условий/атрибуции — отдельным reviewed commit.
