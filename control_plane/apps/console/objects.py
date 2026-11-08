"""Read-only object views over independently timestamped production observations."""
from datetime import datetime, timedelta, timezone as utc
import re

from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_safe

from .collector import ACTIVE_SOURCES, SOURCES
from .measurements import counter_rates
from .models import (AuditRecord, DeviceLabel, InventoryDevice, InventorySnapshot,
    MeasurementSnapshot, SubscriptionEventObservation, SubscriptionSnapshot, TransportSnapshot)
from .server_inventory import observation_state, STATE_LABELS
from .subscription_presentation import STATES, ATTEMPTS
from .subscriptions import display_rows, freshness
from .views import staff

PERIODS = {'1h': ('Час', 3600), '24h': ('Сутки', 86400), '7d': ('7 дней', 604800)}
SERVICE_LABELS = {
    'family-connect-friends-awg.service': 'AWG',
    'family-connect-friends-tcp.service': 'TCP',
    'family-connect-restricted-bootstrap.service': 'MESH · bootstrap',
}
PROCESS_LABELS = {'active': 'Процесс работает', 'inactive': 'Остановлен', 'failed': 'Ошибка службы',
    'activating': 'Запускается', 'deactivating': 'Останавливается', 'not_found': 'Нет службы', 'unknown': 'Неизвестно'}
EVENT_LABELS = {'payment': 'Предоставление / продление доступа', 'grace': 'Льготный период',
    'expire': 'Окончание доступа', 'revoke': 'Отзыв доступа'}


def moment(value):
    return datetime.fromtimestamp(value, utc.utc) if value is not None else None


def is_fresh(snapshot, now, seconds=300):
    return bool(snapshot and now - timedelta(seconds=seconds) <= snapshot.observed_at <= now + timedelta(seconds=15))


def latest_attempt(action, source=None):
    query = AuditRecord.objects.filter(action=action)
    if source:
        query = query.filter(details__source=source)
    return query.order_by('-pk').first()


def empty_device(pseudonym, labels):
    return dict(pseudonym=pseudonym, label=labels.get(pseudonym, 'Устройство ' + pseudonym[:10]),
        short_id=pseudonym[:12], inventory=None, subscription=None, event=None, cohort=None,
        state_key='unknown', state_label='Нет данных о подписке', nodes=[], issues=[], metadata={},
        last_seen=None, canonical_fresh=False, registry_fresh=False, remaining=None)


def production(now):
    registry = InventorySnapshot.objects.filter(scope='production', source='gateway-ru', registry_status='ok').order_by('-imported_at').first()
    current_registry = InventorySnapshot.objects.filter(scope='production', source='gateway-ru').order_by('-imported_at').first()
    canonical = SubscriptionSnapshot.objects.filter(status='ok').order_by('-pk').first()
    attempt = latest_attempt('subscriptions.attempt')
    canonical_ok = is_fresh(canonical, now) and (attempt is None or attempt.details.get('status') == 'ok')
    registry_ok = is_fresh(registry, now) and current_registry == registry
    registry_attempt = latest_attempt('transports.attempt', 'gateway-ru')
    if registry_attempt and registry_attempt.details.get('status') in ('collection_failed', 'import_failed'):
        registry_ok = False
    labels = dict(DeviceLabel.objects.values_list('pseudonym', 'label'))
    rows = {}

    def device(pseudonym):
        if pseudonym not in rows:
            rows[pseudonym] = empty_device(pseudonym, labels)
        return rows[pseudonym]

    if registry:
        for entry in registry.devices.all():
            row = device(entry.pseudonym)
            row.update(inventory=entry, metadata=entry.metadata, last_seen=entry.last_seen)
            if entry.revoked:
                row['issues'].append('Наблюдался отзыв identity / приглашения')
    for entry in display_rows(canonical):
        row = device(entry['pseudonym'])
        state = entry['subscription']['effective_state'] if entry['cohort'] else 'noncohort'
        row.update(subscription=entry['subscription'], cohort=entry['cohort'], event=entry['event'],
                   state_key=state, state_label=STATES[state])
        if entry['cohort'] and not entry['subscription']['paid_allow']:
            row['issues'].append('Paid-слой: доступ ограничен')
    servers = []
    for source in ACTIVE_SOURCES:
        snapshot = InventorySnapshot.objects.filter(scope='production', source=source).select_related('server').order_by('-imported_at').first()
        transport = TransportSnapshot.objects.filter(source=source, status='ok').order_by('-pk').first()
        application_attempt = latest_attempt('transports.attempt', source)
        fresh = is_fresh(transport, now, 90) and bool(application_attempt and application_attempt.details['status'] == 'ok')
        state = observation_state(source, snapshot, now)
        metrics = MeasurementSnapshot.objects.filter(source=source).order_by('-pk').first()
        issue = None if state == 'observed_active' else STATE_LABELS[state]
        if application_attempt and application_attempt.details.get('status') not in ('ok', 'not_installed'):
            issue = ATTEMPTS.get(application_attempt.details['status'], 'Ошибка сбора / применения')
        elif not fresh:
            issue = issue or 'Нет свежего подтверждения применения'
        services = snapshot.server.services if snapshot else {}
        for unit in ('family-connect-friends-awg.service', 'family-connect-friends-tcp.service'):
            if snapshot and services.get(unit) in ('failed', 'inactive', 'deactivating'):
                issue = SERVICE_LABELS[unit] + ': ' + PROCESS_LABELS[services[unit]]
        server = dict(source=source, label=SOURCES[source]['label'], address=SOURCES[source]['host'],
            snapshot=snapshot, state=state, state_label=STATE_LABELS[state], issue=issue, transport=transport,
            transport_fresh=fresh, attempt=application_attempt, devices=[], metrics=metrics, pending_count=0,
            services=[dict(name=label, state=services.get(unit, 'unknown'), text=PROCESS_LABELS.get(services.get(unit, 'unknown'), 'Неизвестно'))
                      for unit, label in SERVICE_LABELS.items()])
        measured = {entry['pseudonym']: entry for entry in metrics.devices} if metrics and metrics.awg_status == 'ok' else {}
        for entry in transport.devices if transport else []:
            row = device(entry['pseudonym'])
            if not entry['registered'] and not entry.get('managed'):
                continue
            revision = row['subscription']['version'] if row['subscription'] else 0 if row['cohort'] is False else None
            matches = entry['result'] == 'applied' and entry['expected_revision'] == entry['applied_revision'] == revision
            applied_fresh = entry['applied_at'] is not None and now - timedelta(seconds=90) <= moment(entry['applied_at']) <= now + timedelta(seconds=15)
            text = 'Применение неизвестно'
            if fresh and applied_fresh and matches:
                text = 'Наборы подтверждены' if entry['registered'] else 'Профиль не зарегистрирован'
            elif fresh:
                text = 'Ожидается сверка ревизии'
            binding = dict(server=server, observation=entry, text=text, fresh=fresh and applied_fresh and matches,
                applied_at=moment(entry['applied_at']), measured=measured.get(entry['pseudonym']))
            row['nodes'].append(binding)
            server['devices'].append(row)
            if not binding['fresh']:
                row['issues'].append(SOURCES[source]['label'] + ': ' + text.lower())
                server['pending_count'] += 1
            elif canonical_ok and row['cohort'] and entry['registered'] and any(
                    entry[name] != row['subscription']['paid_allow'] for name in ('awg_allowed', 'tcp_allowed')):
                row['issues'].append(SOURCES[source]['label'] + ': paid-разрешение и применение различаются')
                server['pending_count'] += 1
        if server['pending_count']:
            server['issue'] = server['issue'] or 'Есть неподтверждённые или расходящиеся применения'
        servers.append(server)
    for row in rows.values():
        if not canonical_ok:
            row['issues'].append('Нет свежего канонического ответа')
        if not registry_ok:
            row['issues'].append('Реестр отсутствует, устарел или недоступен')
        row['issues'] = list(dict.fromkeys(row['issues']))
        row['canonical_fresh'] = canonical_ok
        row['registry_fresh'] = registry_ok
        row['short_id'] = row['pseudonym'][:12]
        row['remaining'] = None
        if row['subscription'] and row['subscription']['entitlement_until']:
            seconds = (row['subscription']['entitlement_until'] - now).total_seconds()
            row['remaining'] = ('Срок наступил' if seconds <= 0 else f'Осталось ≈ {int(seconds // 3600)} ч')
        row['problem'] = bool(row['issues'])
    return dict(devices=sorted(rows.values(), key=lambda row: row['label'].casefold()), servers=servers,
        registry=registry, canonical=canonical, canonical_fresh=canonical_ok, registry_fresh=registry_ok,
        subscription_attempt=attempt, subscription_attempt_text=ATTEMPTS.get(attempt.details.get('status'), 'Нет попытки') if attempt else 'Нет попытки',
        canonical_age=freshness(canonical, now), registry_age=freshness(registry, now))


def selected_period(request):
    selected = request.GET.get('period', '24h')
    return selected if selected in PERIODS else '24h'


def graph_data(source, now, period, pseudonym=None):
    since = now - timedelta(seconds=PERIODS[period][1])
    snapshots = list(MeasurementSnapshot.objects.filter(source=source, observed_at__gte=since, observed_at__lte=now)
        .only('observed_at', 'devices' if pseudonym else 'node').order_by('-observed_at', '-pk')[:10000])
    samples = []
    for snapshot in reversed(snapshots):
        entry = next((row for row in snapshot.devices if row['pseudonym'] == pseudonym), None) if pseudonym else snapshot.node
        sample = dict(at=snapshot.observed_at.timestamp(), epoch=None)
        if entry:
            sample.update(entry)
            sample['epoch'] = entry['epoch'] if pseudonym else f"{entry['boot']}:{entry['interface']}:{entry['ifindex']}"
        samples.append(sample)
    points = counter_rates(samples)
    graphs = [dict(title=('AWG · ' if pseudonym else '') + SOURCES[source]['label'], unit='Б/с',
        series=[dict(key='rx', label='RX · вход на сервер'), dict(key='tx', label='TX · выход с сервера')], points=points)]
    if not pseudonym:
        graphs.append(dict(title=SOURCES[source]['label'] + ' · CPU', unit='%', series=[dict(key='cpu', label='CPU · занято')], points=points))
        history = InventorySnapshot.objects.filter(scope='production', source=source, observed_at__gte=since, observed_at__lte=now).select_related('server').order_by('-observed_at')[:10000]
        resource_points = [dict(at=snapshot.observed_at.timestamp(), memory=snapshot.server.memory_used_percent,
                               disk=snapshot.server.disk_used_percent, load=snapshot.server.load_1m) for snapshot in reversed(list(history))]
        graphs.append(dict(title='Память и диск', unit='%', series=[dict(key='memory', label='Память'), dict(key='disk', label='Диск')], points=resource_points))
        graphs.append(dict(title='Очередь CPU · load average', unit='задач', series=[dict(key='load', label='Load 1m')], points=resource_points))
    for graph in graphs:
        graph['observation'] = snapshots[0].observed_at if snapshots else None
        graph['source_status'] = ('Нет снимка' if not snapshots else
            'Ошибка измерения' if (snapshots[0].awg_status != 'ok' if pseudonym else snapshots[0].node is None) else
            'Свежий сбор' if is_fresh(snapshots[0], now) else 'Снимок устарел')
        graph['start'] = moment(graph['points'][0]['at']) if graph['points'] else None
        graph['end'] = moment(graph['points'][-1]['at']) if graph['points'] else None
        if graph['series'][0]['key'] in ('memory', 'load'):
            graph['observation'] = graph['end']
            graph['source_status'] = ('Нет снимка' if not graph['points'] else
                'Ошибка измерения' if not any(graph['points'][-1].get(series['key']) is not None for series in graph['series']) else
                'Свежий сбор' if now - timedelta(seconds=300) <= graph['end'] <= now + timedelta(seconds=15) else 'Снимок устарел')
        graph['count'] = sum(any(point.get(series['key']) is not None for series in graph['series']) for point in graph['points'])
        graph['rx_bytes'] = sum(point['rx'] * point['seconds'] for point in graph['points'] if point.get('rx') is not None)
        graph['tx_bytes'] = sum(point['tx'] * point['seconds'] for point in graph['points'] if point.get('tx') is not None)
        graph['measured_seconds'] = sum(point.get('seconds') or 0 for point in graph['points'])
    return graphs


def timeline(pseudonym=None, source=None):
    result = []
    events = SubscriptionEventObservation.objects.all()
    if pseudonym:
        events = events.filter(pseudonym=pseudonym)
    if not source:
        for event in events.order_by('-occurred_at', '-pk')[:500]:
            result.append(dict(at=event.occurred_at, kind='event', label=EVENT_LABELS[event.details['event_type']],
                pseudonym=event.pseudonym, source=None, details=event.details, event_id=event.event_id))
    if pseudonym:
        observations = list(InventoryDevice.objects.filter(pseudonym=pseudonym, snapshot__scope='production',
            snapshot__source='gateway-ru').select_related('snapshot').order_by('-snapshot__imported_at')[:2000])
        previous = None
        for entry in reversed(observations):
            signature = (entry.version_code, entry.activated, entry.revoked)
            if signature != previous:
                result.append(dict(at=entry.snapshot.observed_at, kind='observation', label='Наблюдение реестра · версия ' + str(entry.version_code or 'неизвестна'),
                    pseudonym=pseudonym, source=None, details=dict(version=entry.version_code, activated=entry.activated, revoked=entry.revoked), event_id=None))
            previous = signature
    if not pseudonym:
        for node in [source] if source else ACTIVE_SOURCES:
            previous_services = None
            samples = InventorySnapshot.objects.filter(scope='production', source=node).select_related('server').order_by('-imported_at')[:1000]
            for sample in reversed(list(samples)):
                services = {label: sample.server.services.get(unit, 'unknown') for unit, label in SERVICE_LABELS.items()}
                if services != previous_services:
                    result.append(dict(at=sample.observed_at, kind='observation', source=node, pseudonym=None,
                        label=SOURCES[node]['label'] + (' · изменение наблюдаемых процессов' if previous_services is not None else
                            ' · первое доступное наблюдение процессов'), details=services, event_id=None))
                previous_services = services
            previous = None
            for entry in reversed(list(AuditRecord.objects.filter(action='transports.attempt', details__source=node).order_by('-pk')[:2000])):
                status = entry.details.get('status', 'unknown')
                if status != previous:
                    result.append(dict(at=entry.occurred_at, kind='observation', source=node, pseudonym=None,
                        label=SOURCES[node]['label'] + ' · ' + ATTEMPTS.get(status, status), details=entry.details, event_id=None))
                previous = status
    return sorted(result, key=lambda row: row['at'], reverse=True)


def filtered(rows, request):
    query = request.GET.get('q', request.GET.get('query', '')).strip()[:128].casefold()
    state = request.GET.get('state', '')
    return [row for row in rows if (not query or query in row['label'].casefold() or query in row['pseudonym'])
            and (not request.GET.get('source') or request.GET['source'] == 'gateway-ru'
                 or any(binding['server']['source'] == request.GET['source'] for binding in row['nodes']))
            and (not state or row['state_key'] == state) and (request.GET.get('problem') != '1' or row['problem'])
            and (request.GET.get('registry') != '1' or row['inventory'] is not None)]


def page_context(request, data, section):
    return dict(data, section=section, production_page=True, period=selected_period(request),
                periods=PERIODS, state_options=STATES, query=request.GET.get('q', ''), selected_state=request.GET.get('state', ''),
                observed_now=timezone.now())


@staff('view_inventorysnapshot')
@require_safe
def overview(request):
    now = timezone.now()
    data = production(now)
    data.update(device_count=data['registry'].devices.count() if data['registry'] else None,
        cohort_count=sum(row['cohort'] is True for row in data['devices']) if data['canonical'] else None,
        problem_count=sum(row['problem'] for row in data['devices']) if data['registry'] or data['canonical'] else None,
        graphs=[graph_data(source, now, selected_period(request))[0] for source in ACTIVE_SOURCES], events=timeline()[:8])
    return render(request, 'console/production_overview.html', page_context(request, data, 'overview'))


@staff('view_inventorysnapshot')
@require_safe
def devices(request):
    data = production(timezone.now())
    rows = filtered(data['devices'], request)
    data.update(page=Paginator(rows, 25).get_page(request.GET.get('page')), total=len(rows))
    query = request.GET.copy(); query.pop('page', None)
    data['querystring'] = query.urlencode()
    return render(request, 'console/object_devices.html', page_context(request, data, 'devices'))


@staff('view_inventorysnapshot')
@require_safe
def device(request, pseudonym):
    if not re.fullmatch('[0-9a-f]{64}', pseudonym):
        raise Http404
    now = timezone.now()
    data = production(now)
    row = next((entry for entry in data['devices'] if entry['pseudonym'] == pseudonym), None)
    if row is None:
        history = InventoryDevice.objects.filter(pseudonym=pseudonym, snapshot__scope='production',
            snapshot__source='gateway-ru').select_related('snapshot').order_by('-snapshot__imported_at').first()
        canonical = SubscriptionSnapshot.objects.filter(status='ok', devices__contains=[dict(pseudonym=pseudonym)]).order_by('-pk').first()
        if history is None and canonical is None and not SubscriptionEventObservation.objects.filter(pseudonym=pseudonym).exists():
            raise Http404
        row = empty_device(pseudonym, dict(DeviceLabel.objects.values_list('pseudonym', 'label')))
        if history:
            row.update(inventory=history, metadata=history.metadata, last_seen=history.last_seen)
        if canonical:
            entry = next(entry for entry in display_rows(canonical) if entry['pseudonym'] == pseudonym)
            row.update(entry)
            row['state_key'] = entry['subscription']['effective_state'] if entry['cohort'] else 'noncohort'
            row['state_label'] = STATES[row['state_key']]
        row['issues'] = ['Устройство отсутствует в текущих снимках. Показаны исторические данные.']
        data.update(canonical=canonical, registry=history.snapshot if history else None,
            canonical_age='Историческое наблюдение', registry_age='Историческое наблюдение')
    data.update(device=row, events=timeline(pseudonym=pseudonym),
        graphs=[graph_data(binding['server']['source'], now, selected_period(request), pseudonym)[0] for binding in row['nodes']])
    if request.GET.get('kind') in ('event', 'observation'):
        data['events'] = [entry for entry in data['events'] if entry['kind'] == request.GET['kind']]
    return render(request, 'console/object_device.html', page_context(request, data, 'devices'))


@staff('view_inventorysnapshot')
@require_safe
def servers(request):
    data = production(timezone.now())
    return render(request, 'console/object_servers.html', page_context(request, data, 'servers'))


@staff('view_inventorysnapshot')
@require_safe
def server(request, source):
    if source not in ACTIVE_SOURCES:
        from .observability import server as legacy_server
        return legacy_server(request, source)
    now = timezone.now()
    data = production(now)
    row = next(entry for entry in data['servers'] if entry['source'] == source)
    from .observability import filters, network_assessment
    form = filters(request)
    data['network'] = network_assessment(form, source, row['state'], now) if form.is_valid() else None
    data.update(server=row, graphs=graph_data(source, now, selected_period(request)), events=timeline(source=source))
    return render(request, 'console/object_server.html', page_context(request, data, 'servers'))


@staff('view_inventorysnapshot')
@require_safe
def events(request):
    data = production(timezone.now())
    labels = {row['pseudonym']: row['label'] for row in data['devices']}
    rows = timeline()
    query = request.GET.get('q', '').casefold()[:128]
    for row in rows:
        row['label_device'] = labels.get(row['pseudonym'], (row['pseudonym'] or '')[:12])
    rows = [row for row in rows if (not query or query in row['label_device'].casefold() or query in (row['pseudonym'] or ''))
            and (not request.GET.get('kind') or row['kind'] == request.GET['kind'])]
    querystring = request.GET.copy(); querystring.pop('page', None)
    data.update(events=Paginator(rows, 40).get_page(request.GET.get('page')), querystring=querystring.urlencode())
    return render(request, 'console/object_events.html', page_context(request, data, 'events'))
