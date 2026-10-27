from datetime import datetime, timedelta, timezone as utc
import hashlib
import json
import math
import re

from django.db import transaction
from django.utils import timezone

from .observability_models import InventorySnapshot, InventoryDevice, ServerObservation
from .collector import SERVICES


class SnapshotError(ValueError):
    pass


def require(condition):
    if not condition:
        raise SnapshotError('Недопустимый снимок: проверьте схему, типы, источник и время. Импорт не выполнен.')


def fields(value, expected):
    require(type(value) is dict and set(value) == set(expected.split()))


def timestamp(value):
    require(isinstance(value, str))
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise SnapshotError('Требуется точное время UTC.') from None
    require(parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0)
    require(datetime(2020, 1, 1, tzinfo=utc.utc) <= parsed <= timezone.now() + timedelta(minutes=5))
    return parsed


def strict_load(raw):
    require(len(raw) <= 4 * 1024 * 1024)
    def pairs(items):
        result = {}
        for name, value in items:
            require(name not in result)
            result[name] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda value: require(False))
    except (ValueError, UnicodeError):
        raise SnapshotError('Недопустимый строгий JSON.') from None


@transaction.atomic
def ingest(data):
    fields(data, 'schema scope source observed_at registry_status devices server')
    require(type(data['schema']) is int and data['schema'] == 1 and data['scope'] == 'production')
    require(data['source'] in ('gateway-ru', 'gateway-nl'))
    observed = timestamp(data['observed_at'])
    require(data['registry_status'] in ('ok', 'unavailable', 'not_collected'))
    require(type(data['devices']) is list and len(data['devices']) <= 10000)
    require(data['registry_status'] == 'ok' or not data['devices'])
    seen, devices = set(), []
    for entry in data['devices']:
        fields(entry, 'pseudonym activated revoked version_code version_source last_seen')
        require(isinstance(entry['pseudonym'], str) and re.fullmatch(r'[0-9a-f]{64}', entry['pseudonym']) is not None)
        require(entry['pseudonym'] not in seen)
        seen.add(entry['pseudonym'])
        require(all(type(entry[name]) is bool or entry[name] is None for name in ('activated', 'revoked')))
        require(entry['version_code'] is None or type(entry['version_code']) is int and 0 <= entry['version_code'] <= 2147483647)
        require(entry['version_source'] in ('support', 'readiness_ack', 'unknown'))
        last_seen = timestamp(entry['last_seen']) if entry['last_seen'] is not None else None
        require(last_seen is None or last_seen <= observed)
        devices.append(dict(entry, last_seen=last_seen))
    server = data['server']
    fields(server, 'load_1m memory_used_percent disk_used_percent uptime_seconds services')
    for name in ('load_1m', 'memory_used_percent', 'disk_used_percent', 'uptime_seconds'):
        value = server[name]
        require(value is None or type(value) in (int, float) and 0 <= value <= 2**63 - 1 and math.isfinite(value))
        if name.endswith('percent'):
            require(value is None or value <= 100)
    require(server['uptime_seconds'] is None or type(server['uptime_seconds']) is int and server['uptime_seconds'] <= 2**63 - 1)
    require(type(server['services']) is dict and bool(server['services']))
    require(set(server['services']) <= set(SERVICES) | {'nginx.service'})
    require(all(value in ('active', 'inactive', 'failed', 'activating', 'deactivating', 'unknown', 'not_found') for value in server['services'].values()))
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    snapshot, created = InventorySnapshot.objects.get_or_create(digest=digest, defaults=dict(
        scope='production', source=data['source'], observed_at=observed, registry_status=data['registry_status']))
    if created:
        InventoryDevice.objects.bulk_create([InventoryDevice(snapshot=snapshot, **entry) for entry in devices])
        ServerObservation.objects.create(snapshot=snapshot, **server)
        from .models import AuditRecord
        AuditRecord.objects.create(action='inventory.import', target=str(snapshot.pk),
            details={'scope': 'production', 'source': snapshot.source, 'synthetic': False})
    return snapshot
