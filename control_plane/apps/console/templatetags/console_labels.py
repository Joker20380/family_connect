from django import template
from apps.console.labels import label, error_label

register = template.Library()
register.filter('ru', label)
register.filter('ru_error', error_label)


@register.filter
def service_state(value):
    return {'active': 'Работает', 'inactive': 'Не работает', 'failed': 'Ошибка',
        'activating': 'Запускается', 'deactivating': 'Останавливается',
        'unknown': 'Неизвестно', 'not_found': 'Не установлена на этом узле'}.get(value, 'Неизвестно')
