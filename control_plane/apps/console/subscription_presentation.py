from datetime import datetime, timedelta, timezone as utc

from django import forms

from .collector import SOURCES
from .models import AuditRecord, TransportSnapshot
from .transports import NODES

STATES = {'active': 'Активна', 'trial': 'Пробный период', 'grace': 'Льготный период',
          'expired': 'Истекла', 'revoked': 'Отозвана', 'noncohort': 'Вне пилота'}
ATTEMPTS = {'ok': 'Успешно', 'collection_failed': 'Ошибка сбора', 'import_failed': 'Ошибка импорта',
            'unavailable': 'Источник недоступен', 'unsupported': 'Источник не поддерживает подписки'}


class SubscriptionFilters(forms.Form):
    state = forms.ChoiceField(label='Состояние', required=False, choices=[('', 'Все состояния'), *STATES.items()])
    query = forms.RegexField(label='Псевдоним устройства', required=False, regex=r'^[a-f0-9]{4,64}$', max_length=64,
        widget=forms.TextInput(attrs={'placeholder': 'Первые 4 или более символов', 'autocomplete': 'off'}))


def present(rows, request, now):
    form = SubscriptionFilters(request.GET)
    counts = dict.fromkeys(STATES, 0)
    nodes = []
    for source in NODES:
        attempt = AuditRecord.objects.filter(action='transports.attempt', details__source=source).order_by('-pk').first()
        snapshot = TransportSnapshot.objects.filter(pk=attempt.target).first() if attempt and attempt.target else None
        previous = TransportSnapshot.objects.filter(source=source,status__in=('ok','not_installed')).order_by('-pk').first()
        previous_attempt = AuditRecord.objects.filter(action='transports.attempt', target=str(previous.pk)).order_by('-pk').first() if previous else None
        fresh = snapshot and now - timedelta(seconds=90) <= snapshot.observed_at <= now + timedelta(seconds=15)
        status = attempt.details['status'] if attempt else 'unknown'
        text = {'not_installed': 'Контроль AWG/TCP не установлен', 'ok': 'Применение наблюдается',
                'unavailable': 'Ошибка источника', 'collection_failed': 'Ошибка сбора',
                'import_failed': 'Ошибка импорта', 'unknown': 'Нет наблюдений применения'}.get(status, 'Неизвестно')
        if status in ('ok','not_installed') and snapshot and not fresh:
            text = 'Наблюдение устарело · применение неизвестно'
        nodes.append(dict(source=source, label=SOURCES[source]['label'], text=text, snapshot=snapshot,
            fresh=fresh, status=status, attempt=attempt, previous=previous,
            previous_schema=previous_attempt.details.get('schema') if previous_attempt else None))
    for row in rows:
        state = row['subscription']['effective_state'] if row['cohort'] else 'noncohort'
        row.update(state_key=state, state_label=STATES[state], transports=[])
        counts[state] += 1
        for node in nodes:
            observation = next((item for item in node['snapshot'].devices if item['pseudonym'] == row['pseudonym']), None) if node['snapshot'] else None
            text = 'Неизвестно'
            if node['fresh'] and node['status'] == 'not_installed':
                text = 'Не включён'
            elif node['fresh'] and node['status'] == 'ok' and observation:
                revision = row['subscription']['version'] if row['cohort'] else 0
                applied_at = datetime.fromtimestamp(observation['applied_at'], utc.utc) if observation['applied_at'] else None
                if (observation['result'] == 'applied' and observation['applied_revision'] == observation['expected_revision'] == revision
                        and applied_at and now - timedelta(seconds=90) <= applied_at <= now + timedelta(seconds=15)):
                    text = ('AWG: peer присутствует' if observation['awg_allowed'] else 'AWG: peer удалён') + ' · ' + (
                        'TCP: пользователь включён' if observation['tcp_allowed'] else 'TCP: пользователь удалён')
                    if not observation['registered']:
                        text = 'Профиль не зарегистрирован на этом узле'
                else:
                    text = 'Ожидается сверка актуальной ревизии'
            detail = dict(label=node['label'], text=text, observation=observation)
            if observation:
                detail.update(applied_time=datetime.fromtimestamp(observation['applied_at'], utc.utc) if observation['applied_at'] else None,
                    decision_time=datetime.fromtimestamp(observation['decision_observed_at'],utc.utc),
                    valid_until=datetime.fromtimestamp(observation['valid_until'],utc.utc) if observation['valid_until'] is not None else None,
                    reason={'canonical':'Каноническое решение','lease-valid':'Локальное разрешение действительно',
                            'lease-expired':'Срок локального разрешения истёк',
                            'noncohort':'Вне пилота: paid-таймер не применяется',
                            'membership-pending':'Первое включение: узел подготовлен, ожидается каноническая подписка'}.get(observation['reason'],'Ожидается применение'))
            row['transports'].append(detail)
    selected = rows
    if form.is_valid():
        if form.cleaned_data['state']:
            selected = [row for row in selected if row['state_key'] == form.cleaned_data['state']]
        if form.cleaned_data['query']:
            selected = [row for row in selected if row['pseudonym'].startswith(form.cleaned_data['query'])]
    else:
        selected = []
    return dict(rows=selected, total_count=len(rows), counts=counts, filter_form=form, transport_nodes=nodes)
