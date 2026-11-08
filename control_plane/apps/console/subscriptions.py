from datetime import datetime, timedelta, timezone as utc
import hashlib
import json
import re

from django.db import transaction
from .inventory import fields, require, timestamp
from .models import AuditRecord, SubscriptionSnapshot, SubscriptionEventObservation


def record_attempt(status, snapshot=None):
    require(status in ('ok', 'unsupported', 'unavailable', 'collection_failed', 'import_failed'))
    require((snapshot is None) == (status in ('collection_failed', 'import_failed')))
    return AuditRecord.objects.create(action='subscriptions.attempt', target=str(snapshot.pk) if snapshot else '',
        details={'scope': 'production', 'synthetic': False, 'status': status})


def hex_digest(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def epoch(value):
    require(type(value) is int and 0 <= value <= 253402300799)


def import_event(event, pseudonym, observed_at):
    fields(event, 'event_id event_type occurred_at previous_state new_state result')
    require(hex_digest(pseudonym) and hex_digest(event['event_id']))
    require(event['event_type'] in ('payment', 'grace', 'expire', 'revoke') and event['result'] == 'APPLIED')
    epoch(event['occurred_at'])
    require(event['occurred_at'] <= observed_at)
    states = ('trial', 'active', 'grace', 'expired', 'revoked')
    require(event['new_state'] in states and event['previous_state'] in (*states, None))
    record, created = SubscriptionEventObservation.objects.get_or_create(event_id=event['event_id'], defaults=dict(
        pseudonym=pseudonym, occurred_at=datetime.fromtimestamp(event['occurred_at'], utc.utc), details=event))
    require(created or record.pseudonym == pseudonym and record.details == event)


@transaction.atomic
def ingest(data, *, attempt=False):
    require(type(data) is dict and type(data.get('schema')) is int and data['schema'] in (1, 2))
    fields(data, 'schema scope source observed_at status runtime_sha256 devices' + (' history' if data['schema'] == 2 else ''))
    require(data['scope'] == 'production' and data['source'] == 'gateway-ru')
    epoch(data['observed_at'])
    observed = timestamp(datetime.fromtimestamp(data['observed_at'], utc.utc).isoformat())
    require(data['status'] in ('ok', 'unsupported', 'unavailable'))
    require(data['runtime_sha256'] is None or hex_digest(data['runtime_sha256']))
    require(data['status'] == 'unavailable' or hex_digest(data['runtime_sha256']))
    require(type(data['devices']) is list and len(data['devices']) <= 10000)
    require(data['status'] == 'ok' or not data['devices'])
    seen = set()
    for row in data['devices']:
        fields(row, 'pseudonym cohort subscription event')
        require(hex_digest(row['pseudonym']) and row['pseudonym'] not in seen)
        seen.add(row['pseudonym'])
        require(type(row['cohort']) is bool)
        if not row['cohort']:
            require(row['subscription'] is None and row['event'] is None)
            continue
        subscription = row['subscription']
        fields(subscription, 'state period_start paid_until grace_until version effective_state paid_allow entitlement_until')
        states = ('trial', 'active', 'grace', 'expired', 'revoked')
        require(subscription['state'] in states and subscription['effective_state'] in states)
        require(type(subscription['paid_allow']) is bool)
        require(type(subscription['version']) is int and 0 < subscription['version'] <= 2**63 - 1)
        for name in ('period_start', 'paid_until'):
            epoch(subscription[name])
        require(subscription['period_start'] < subscription['paid_until'])
        for name in ('grace_until', 'entitlement_until'):
            if subscription[name] is not None:
                epoch(subscription[name])
        require(subscription['grace_until'] is None or subscription['grace_until'] >= subscription['paid_until'])
        require(subscription['state'] != 'grace' or subscription['grace_until'] is not None)
        event = row['event']
        if event is not None:
            fields(event, 'event_id event_type occurred_at previous_state new_state result')
            require(hex_digest(event['event_id']) and event['event_type'] in ('payment', 'grace', 'expire', 'revoke'))
            epoch(event['occurred_at'])
            require(event['occurred_at'] <= data['observed_at'] and event['result'] == 'APPLIED')
            require(event['new_state'] == subscription['state'] and event['previous_state'] in (*states, None))
            import_event(event, row['pseudonym'], data['observed_at'])
    history = data.get('history')
    require(data['schema'] == 1 or type(history) is dict)
    if history is not None:
        fields(history, 'events truncated')
        require(data['status'] == 'ok' and type(history['truncated']) is bool and type(history['events']) is list and len(history['events']) <= 1000)
        event_ids = set()
        for row in history['events']:
            require(type(row) is dict and 'pseudonym' in row and row['pseudonym'] in seen)
            require(row.get('event_id') not in event_ids)
            event_ids.add(row['event_id'])
            import_event({name: value for name, value in row.items() if name != 'pseudonym'}, row['pseudonym'], data['observed_at'])
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    snapshot, created = SubscriptionSnapshot.objects.get_or_create(digest=digest, defaults=dict(
        observed_at=observed, status=data['status'], runtime_sha256=data['runtime_sha256'], devices=data['devices'], history=history))
    if created:
        AuditRecord.objects.create(action='subscriptions.import', target=str(snapshot.pk),
                                   details={'scope': 'production', 'synthetic': False})
    if attempt:
        record_attempt(snapshot.status, snapshot)
    return snapshot


def freshness(snapshot, now):
    if snapshot is None:
        return 'Нет наблюдений'
    if snapshot.observed_at > now + timedelta(seconds=15):
        return 'Ошибка часов · актуальность неизвестна'
    if snapshot.observed_at < now - timedelta(minutes=5):
        return 'Устарело · более 5 минут'
    return 'Свежее наблюдение · не live-статус'


def display_rows(snapshot):
    rows = []
    if snapshot is None or snapshot.status != 'ok':
        return rows
    for entry in snapshot.devices:
        row = dict(entry)
        if row['subscription'] is not None:
            row['subscription'] = dict(row['subscription'])
            for name in ('period_start', 'paid_until', 'grace_until', 'entitlement_until'):
                value = row['subscription'][name]
                row['subscription'][name] = datetime.fromtimestamp(value, utc.utc) if value is not None else None
        if row['event'] is not None:
            row['event'] = dict(row['event'], occurred_at=datetime.fromtimestamp(row['event']['occurred_at'], utc.utc))
        rows.append(row)
    return sorted(rows, key=lambda row: (not row['cohort'], row['pseudonym']))
