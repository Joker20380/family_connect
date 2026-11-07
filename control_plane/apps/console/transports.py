from datetime import datetime, timezone
import hashlib
import json

from .inventory import fields, require
from .models import AuditRecord, TransportSnapshot
from .subscriptions import epoch, hex_digest

NODES = ('gateway-ru', 'nl-amsterdam-1', 'nl-amsterdam-2')


def attempt(source, status, snapshot=None, *, schema=None):
    require(source in NODES and status in ('ok', 'not_installed', 'unavailable', 'collection_failed', 'import_failed'))
    details = dict(source=source, status=status, scope='production', synthetic=False)
    if schema is not None:
        require(type(schema) is int and schema in (1,2))
        details['schema'] = schema
    return AuditRecord.objects.create(action='transports.attempt', target=str(snapshot.pk) if snapshot else '',
        details=details)


def ingest(value, source):
    fields(value, 'schema source observed_at status runtime_sha256 devices')
    require(type(value['schema']) is int and value['schema'] in (1,2) and value['source'] == source and source in NODES)
    epoch(value['observed_at'])
    require(value['status'] in ('ok', 'not_installed', 'unavailable'))
    require(value['runtime_sha256'] is None or hex_digest(value['runtime_sha256']))
    require(value['status'] != 'ok' or hex_digest(value['runtime_sha256']))
    require(type(value['devices']) is list and len(value['devices']) <= 10000)
    require(value['status'] == 'ok' or not value['devices'])
    seen = set()
    for row in value['devices']:
        fields(row, 'pseudonym expected_revision applied_revision applied_at registered awg_allowed tcp_allowed result decision_observed_at valid_until reason' + (' managed' if value['schema']==2 else ''))
        require(hex_digest(row['pseudonym']) and row['pseudonym'] not in seen)
        seen.add(row['pseudonym'])
        require(type(row['expected_revision']) is int and row['expected_revision'] >= 0)
        require(row['result'] in ('applied', 'pending'))
        epoch(row['decision_observed_at'])
        require(row['decision_observed_at'] <= value['observed_at'])
        if value['schema']==2:
            require(type(row['managed']) is bool)
            require(row['managed'] or row['valid_until'] is None)
        if row['valid_until'] is None:
            require(value['schema']==2 and row['reason'] not in ('lease-valid','lease-expired'))
            require(not row['managed'] or row['awg_allowed'] is not True and row['tcp_allowed'] is not True)
        else:
            epoch(row['valid_until'])
            require(row['decision_observed_at'] < row['valid_until'] <= row['decision_observed_at']+120)
        require(row['reason'] in (None,'canonical','lease-valid','lease-expired','noncohort','membership-pending'))
        require(all(row[name] is None or type(row[name]) is bool for name in ('registered', 'awg_allowed', 'tcp_allowed')))
        if row['applied_revision'] is not None:
            require(type(row['applied_revision']) is int and 0 <= row['applied_revision'] <= row['expected_revision'])
            epoch(row['applied_at'])
            require(row['applied_at'] <= value['observed_at'])
            require(type(row['awg_allowed']) is bool and type(row['tcp_allowed']) is bool)
            require(type(row['registered']) is bool)
            require(row['registered'] or not row['awg_allowed'] and not row['tcp_allowed'])
        else:
            require(row['applied_at'] is None and row['awg_allowed'] is None and row['tcp_allowed'] is None)
    digest = hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    snapshot = TransportSnapshot.objects.get_or_create(digest=digest, defaults=dict(source=source,
        observed_at=datetime.fromtimestamp(value['observed_at'], timezone.utc), status=value['status'],
        runtime_sha256=value['runtime_sha256'], devices=value['devices']))[0]
    attempt(source, snapshot.status, snapshot, schema=value['schema'])
    return snapshot
