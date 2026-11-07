from datetime import datetime, time, timedelta, timezone as utc

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, Max
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import workflow
from .models import DeviceProjection, InventorySnapshot, InventoryDevice, TechnicalSample, OperationSwitch, NetworkProbe
from .views import staff
from .collector import SOURCES
from .server_inventory import server_cards, observation_state
from .recovery_policy import assess


@staff('view_inventorysnapshot')
def subscriptions(request):
    from django.views.decorators.http import require_safe
    from .models import AuditRecord, SubscriptionSnapshot
    from .subscriptions import freshness, display_rows

    @require_safe
    def read_only(request):
        attempt = AuditRecord.objects.filter(action__in=('subscriptions.attempt', 'subscriptions.import')).order_by('-pk').first()
        snapshot = SubscriptionSnapshot.objects.filter(pk=attempt.target).first() if attempt and attempt.target else None
        previous = SubscriptionSnapshot.objects.filter(status='ok').order_by('-pk').first()
        rows = display_rows(snapshot)
        attempt_status = attempt.details.get('status', snapshot.status if snapshot else 'unknown') if attempt else None
        return render(request, 'console/subscriptions.html', dict(snapshot=snapshot, attempt=attempt,
            attempt_status=attempt_status,
            freshness=freshness(previous, timezone.now()), rows=rows, previous=previous,
            cohort_count=sum(row['cohort'] for row in rows), outside_count=sum(not row['cohort'] for row in rows)))
    return read_only(request)


class Filters(forms.Form):
    scope = forms.ChoiceField(label='Контур', choices=[('production', 'Рабочие серверы · только чтение'), ('synthetic', 'Синтетическое демо')])
    source = forms.ChoiceField(label='Источник', required=False,
        choices=[('', 'Все')] + [(source, value['label']) for source, value in SOURCES.items()] + [('demo-v1', 'Демо-телеметрия')])
    start = forms.DateField(label='С даты (UTC)', widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    end = forms.DateField(label='По дату (UTC)', widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    query = forms.RegexField(label='Псевдоним устройства', regex=r'^[0-9a-f]{4,64}$', required=False, max_length=64,
        help_text='Не менее 4 символов HMAC-псевдонима. Без Support ID и персональных данных.')

    def clean(self):
        values = super().clean()
        if values.get('start') and values.get('end'):
            if not 0 <= (values['end'] - values['start']).days <= 90 or values['end'] > timezone.now().date():
                raise forms.ValidationError('Выберите период от 1 до 91 дня, не в будущем.')
        return values


def filters(request):
    today = timezone.now().date()
    values = {'scope': 'production', 'source': '', 'query': '', 'start': (today - timedelta(days=6)).isoformat(), 'end': today.isoformat()}
    values.update({key: request.GET[key] for key in values if key in request.GET})
    form = Filters(values)
    form.is_valid()
    return form


def bounds(form):
    return (datetime.combine(form.cleaned_data['start'], time.min, utc.utc),
        datetime.combine(form.cleaned_data['end'] + timedelta(days=1), time.min, utc.utc))


def snapshot_query(form):
    start, end = bounds(form)
    rows = InventorySnapshot.objects.filter(scope=form.cleaned_data['scope'], observed_at__gte=start, observed_at__lt=end)
    if form.cleaned_data['source']:
        rows = rows.filter(source=form.cleaned_data['source'])
    return rows


def latest_snapshots(form):
    return snapshot_query(form).order_by('source', '-observed_at', '-imported_at').distinct('source')


def annotate_age(snapshot):
    snapshot.stale = snapshot.observed_at < timezone.now() - timedelta(minutes=5)
    return snapshot


def telemetry_data(form, device=None):
    start, end = bounds(form)
    rows = TechnicalSample.objects.filter(scope=form.cleaned_data['scope'], observed_at__gte=start, observed_at__lt=end)
    if form.cleaned_data['source']:
        rows = rows.filter(source=form.cleaned_data['source'])
    if device:
        rows = rows.filter(device=device)
    if form.cleaned_data['query']:
        rows = rows.none()
    totals = {row['metric']: row for row in rows.values('metric').annotate(count=Count('id'), average=Avg('value'), last=Max('observed_at'))}
    metrics = []
    for metric, title in TechnicalSample.METRICS:
        result = totals.get(metric)
        metrics.append(dict(key=metric, title=title, count=result['count'] if result else None,
            value=round(result['average'] * (1 if metric == 'api_latency_ms' else 100), 2) if result else None,
            last=result['last'] if result else None, unit='мс' if metric == 'api_latency_ms' else '%',
            availability='observed' if result else 'not_collected'))
    series = list(rows.annotate(day=TruncDate('observed_at')).values('day', 'metric').annotate(count=Count('id'), average=Avg('value')).order_by('day', 'metric'))
    for row in series:
        latency = row['metric'] == 'api_latency_ms'
        row['value'] = round(row['average'] * (1 if latency else 100), 2)
        row['unit'] = 'мс' if latency else '%'
        row['width'] = round(min(100, row['average'] / 10 if latency else 100 * row['average']), 2)
    return dict(scope=form.cleaned_data['scope'], metrics=metrics, series=series)


def network_assessment(form, source, service_state, now):
    if form.cleaned_data['scope'] != 'production' or SOURCES[source]['host'] is None:
        return None
    if form.cleaned_data['source'] and form.cleaned_data['source'] != source:
        return None
    start, end = bounds(form)
    samples = list(NetworkProbe.objects.filter(source=source, scope='production',
        observed_at__gte=start, observed_at__lt=end).order_by('-observed_at')[:3])
    return assess(source, samples, service_state, now)


@staff('view_inventorysnapshot')
def overview(request):
    form = filters(request)
    snapshots, data, versions, servers = [], None, [], []
    if form.is_valid():
        snapshots = [annotate_age(item) for item in latest_snapshots(form).select_related('server')]
        if form.cleaned_data['scope'] == 'production':
            now = timezone.now()
            servers = server_cards(snapshots, now, form.cleaned_data['source'])
            for card in servers:
                card['network'] = network_assessment(form, card['source'], card['state'], now)
        data = telemetry_data(form)
        rows = InventoryDevice.objects.filter(snapshot__in=[item.pk for item in snapshots])
        if form.cleaned_data['query']:
            rows = rows.filter(pseudonym__startswith=form.cleaned_data['query'])
        versions = list(rows.values('version_code').annotate(count=Count('id')).order_by('version_code'))
        maximum = max([row['count'] for row in versions] + [1])
        for row in versions:
            row['width'] = round(100 * row['count'] / maximum)
    return render(request, 'console/observability.html', {'form': form, 'snapshots': snapshots,
        'servers': servers, 'data': data, 'versions': versions})


@staff('view_inventorydevice')
def inventory(request):
    form = filters(request)
    rows = InventoryDevice.objects.none()
    snapshots = []
    if form.is_valid():
        snapshots = [annotate_age(item) for item in latest_snapshots(form)]
        rows = InventoryDevice.objects.filter(snapshot__in=[item.pk for item in snapshots]).select_related('snapshot').order_by('pseudonym', 'snapshot__source')
        if form.cleaned_data['query']:
            rows = rows.filter(pseudonym__startswith=form.cleaned_data['query'])
    query = request.GET.copy()
    query.pop('page', None)
    return render(request, 'console/inventory.html', dict(form=form, snapshots=snapshots,
        page=Paginator(rows, 25).get_page(request.GET.get('page')), querystring=query.urlencode()))


@staff('view_inventorydevice')
def inventory_device(request, pseudonym):
    rows = InventoryDevice.objects.filter(pseudonym=pseudonym).select_related('snapshot').order_by('-snapshot__observed_at')[:100]
    if not rows:
        from django.http import Http404
        raise Http404
    return render(request, 'console/inventory_device.html', dict(pseudonym=pseudonym, observations=rows))


@staff('view_serverobservation')
def server(request, source):
    if source not in SOURCES:
        from django.http import Http404
        raise Http404
    form = filters(request)
    snapshots = []
    network = None
    if form.is_valid():
        snapshots = [annotate_age(item) for item in snapshot_query(form).filter(source=source).select_related('server')[:100]]
        now = timezone.now()
        network = network_assessment(form, source, observation_state(source, snapshots[0] if snapshots else None, now), now)
    return render(request, 'console/server.html', dict(source=source, source_label=SOURCES[source]['label'],
        retired=SOURCES[source]['host'] is None, form=form, snapshots=snapshots, network=network))


@staff('view_technicalsample')
def telemetry_json(request):
    form = filters(request)
    if not form.is_valid():
        return JsonResponse({'error': 'Некорректный фильтр'}, status=400)
    return JsonResponse(telemetry_data(form), json_dumps_params={'allow_nan': False})


@staff('view_technicalsample')
def device_telemetry(request, device):
    record = get_object_or_404(DeviceProjection, pk=device)
    form = filters(request)
    data = telemetry_data(form, record) if form.is_valid() else None
    return render(request, 'console/observability.html', dict(form=form, snapshots=[], data=data, demo_device=record))


@staff('view_operationswitch')
def stop_screen(request):
    return render(request, 'console/stop.html', dict(switch=OperationSwitch.objects.get(pk=1)))


@require_POST
@staff('control_operations')
@transaction.atomic
def stop_change(request):
    if request.POST.get('confirmed') != 'on' or request.POST.get('action') not in ('stop', 'resume'):
        messages.error(request, 'Необходимо явное подтверждение действия.')
        return redirect('console:stop')
    switch = OperationSwitch.objects.select_for_update().get(pk=1)
    switch.stopped = request.POST['action'] == 'stop'
    switch.save(update_fields=['stopped'])
    workflow.audit(request.user, 'switch.' + request.POST['action'], 'synthetic-workflow')
    return redirect('console:stop')
