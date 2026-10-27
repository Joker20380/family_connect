LABELS = {
    'api_latency_ms': 'Задержка API, мс', 'inactive': 'Не работает', 'failed': 'Ошибка службы',
    'activating': 'Запускается', 'deactivating': 'Останавливается', 'unknown': 'Неизвестно',
    'trial': 'Пробный период', 'active': 'Активна', 'grace': 'Льготный период',
    'expired': 'Срок истёк', 'revoked': 'Отозвана', 'non-cohort': 'Вне платной группы',
    'DRAFT': 'Черновик', 'PREVIEWED': 'Предпросмотр готов', 'RUNNING': 'Выполняется',
    'APPLIED': 'Применено', 'REJECTED': 'Отклонено', 'STALE': 'Устарело', 'UNKNOWN': 'Результат неизвестен',
    'activate': 'Активировать / продлить', 'grace_action': 'Выдать льготный период',
    'expire': 'Завершить срок', 'revoke': 'Отозвать навсегда',
    'activation': 'Активация', 'mesh_connect': 'Подключение MESH', 'crash': 'Сбой приложения',
    'payment': 'Оплата', 'version': 'Версия', 'support': 'Поддержка',
    'low': 'Низкая', 'high': 'Высокая', 'critical': 'Критическая',
    'open': 'Открыт', 'triage': 'Разбор', 'resolved': 'Решён',
    'production': 'Рабочие серверы · только чтение', 'synthetic': 'Синтетическое демо',
    'ok': 'Наблюдается', 'unavailable': 'Недоступно', 'not_collected': 'Не собирается',
    'device': 'Устройство', 'label': 'Название', 'observed_at': 'Время наблюдения',
    'readback': 'Снимок ответа backend', 'opted_in': 'Согласие получено',
    'handoff_verified': 'Передача APK проверена', 'owner': 'Ответственный',
    'updated_at': 'Обновлено', 'amount_minor': 'Сумма в минимальных единицах',
    'currency': 'Валюта', 'reference_hash': 'Хеш основания', 'created_by': 'Создал',
    'created_at': 'Создано', 'confirmed_by': 'Подтвердил', 'confirmed_at': 'Подтверждено',
    'action': 'Действие', 'period_start': 'Начало периода', 'paid_until': 'Оплачено до',
    'grace_until': 'Льготный период до', 'status': 'Состояние', 'preview': 'Предпросмотр',
    'previewed_by': 'Предпросмотр выполнил', 'previewed_at': 'Время предпросмотра',
    'receipt': 'Квитанция', 'failure_code': 'Причина отказа', 'completed_at': 'Завершено',
    'category': 'Категория', 'severity': 'Важность', 'actor': 'Оператор',
    'target': 'Объект', 'occurred_at': 'Время события', 'details': 'Безопасные сведения',
    'version_name': 'Версия приложения', 'version_code': 'Код версии', 'package_id': 'Пакет',
    'size': 'Размер в байтах', 'sha256': 'SHA256', 'signer_sha256': 'SHA256 сертификата',
    'channel': 'Канал передачи', 'id': 'Идентификатор',
    'payment.create': 'Запись оплаты', 'payment.confirm': 'Подтверждение оплаты',
    'operation.create': 'Создание запроса', 'operation.preview': 'Предпросмотр операции',
    'operation.dispatch': 'Отправка операции', 'operation.result': 'Результат операции',
    'operation.readback_absent': 'Квитанция пока не найдена', 'projection.refresh': 'Обновление снимков',
    'device.lookup': 'Поиск устройства', 'inventory.import': 'Импорт read-only снимка', 'cohortmetadata.create': 'Создание метаданных группы',
    'cohortmetadata.update': 'Изменение метаданных группы', 'incident.create': 'Создание обращения',
    'incident.update': 'Изменение обращения', 'switch.stop': 'Остановка новых операций',
    'switch.resume': 'Возобновление новых операций',
    'EMERGENCY_STOP': 'Новые операции остановлены оператором.',
    'PREVIEW_STALE': 'Данные изменились: выполните новый предпросмотр.',
    'REVOCATION_TERMINAL': 'Отзыв окончателен; повторная активация запрещена.',
    'PAID_COHORT_LIMIT': 'Достигнут предел: 10 устройств в платной группе.',
    'NO_RECEIPT_KEEP_UNCERTAIN_NO_NEW_EVENT': 'Квитанции нет: результат остаётся неизвестным. Не создавайте новое событие.',
}


def label(value):
    return LABELS.get(str(value), value)


def error_label(value):
    return LABELS.get(str(value), f'Операция отклонена. Технический код: {value}')
