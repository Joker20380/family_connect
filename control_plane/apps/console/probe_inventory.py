import hashlib
import json
import math

from django.db import transaction

from .inventory import fields, require, timestamp
from .network_probe import ENDPOINTS
from .observability_models import NetworkProbe


@transaction.atomic
def ingest(data):
    fields(data, 'schema scope source probe vantage address port observed_at outcome duration_ms')
    require(type(data['schema']) is int and data['schema'] == 1 and data['scope'] == 'production')
    require(type(data['source']) is str and data['source'] in ENDPOINTS)
    require(data['probe'] == 'tcp_connect' and data['vantage'] == 'operator-workstation')
    require(type(data['port']) is int and (data['address'], data['port']) == ENDPOINTS[data['source']])
    require(data['outcome'] in ('reachable', 'refused', 'timeout', 'network_error'))
    duration = data['duration_ms']
    require(type(duration) in (int, float) and math.isfinite(duration) and 0 <= duration <= 60000)
    observed = timestamp(data['observed_at'])
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    values = {key: value for key, value in data.items() if key not in ('schema', 'observed_at', 'source')}
    sample, created = NetworkProbe.objects.get_or_create(source=data['source'], observed_at=observed,
        defaults=dict(values, digest=digest))
    require(sample.digest == digest)
    if created:
        from .models import AuditRecord
        AuditRecord.objects.create(action='network_probe.import', target=str(sample.pk),
            details={'scope': 'production', 'source': sample.source, 'automatic_action': False})
    return sample
