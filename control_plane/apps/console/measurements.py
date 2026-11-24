from datetime import datetime, timezone as utc
import hashlib
import json
import re

from django.db import transaction

from .collector import ACTIVE_SOURCES
from .inventory import fields, require, timestamp
from .models import MeasurementSnapshot
from .subscriptions import hex_digest


def counter(value):
    require(type(value) is int and 0 <= value <= 2**64 - 1)


@transaction.atomic
def ingest(data, source):
    fields(data, 'schema source observed_at node awg_status devices unknown_peers tcp_status mesh_status')
    require(type(data['schema']) is int and data['schema'] == 1 and source in ACTIVE_SOURCES and data['source'] == source)
    counter(data['observed_at'])
    require(data['observed_at'] < 253402300799)
    observed = timestamp(datetime.fromtimestamp(data['observed_at'], utc.utc).isoformat())
    require(data['tcp_status'] == data['mesh_status'] == 'not_collected')
    node = data['node']
    if node is not None:
        fields(node, 'boot interface ifindex rx tx cpu_total cpu_idle cpu_count')
        require(hex_digest(node['boot']) and isinstance(node['interface'], str)
                and re.fullmatch(r'[a-zA-Z0-9_.-]{1,32}', node['interface']))
        for name in ('ifindex', 'rx', 'tx', 'cpu_total', 'cpu_idle', 'cpu_count'):
            counter(node[name])
        require(node['cpu_idle'] <= node['cpu_total'] and 0 < node['cpu_count'] <= 4096)
    require(data['awg_status'] in ('ok', 'unavailable') and type(data['devices']) is list and len(data['devices']) <= 10000)
    require(data['awg_status'] == 'ok' or not data['devices'] and data['unknown_peers'] is None)
    if data['awg_status'] == 'ok':
        counter(data['unknown_peers'])
    seen = set()
    for row in data['devices']:
        fields(row, 'pseudonym rx tx epoch last_handshake')
        require(hex_digest(row['pseudonym']) and row['pseudonym'] not in seen)
        seen.add(row['pseudonym'])
        require(isinstance(row['epoch'], str) and re.fullmatch(r'[0-9a-f]{64}:[0-9]{1,12}', row['epoch']))
        counter(row['rx']); counter(row['tx'])
        if row['last_handshake'] is not None:
            counter(row['last_handshake'])
            require(row['last_handshake'] <= data['observed_at'])
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    snapshot, _ = MeasurementSnapshot.objects.get_or_create(digest=digest, defaults=dict(
        source=source, observed_at=observed, **{name: data[name] for name in (
            'node', 'devices', 'awg_status', 'unknown_peers', 'tcp_status', 'mesh_status')}))
    return snapshot


def counter_rates(samples, *, max_gap=300):
    """Missing/reset/gap observations break lines, never become zero traffic."""
    previous = None
    result = []
    for sample in samples:
        point = dict(at=sample['at'], rx=None, tx=None, cpu=None, seconds=None, reason='Первое измерение')
        if sample.get('epoch') is None:
            point['reason'] = 'Измерение недоступно'
            previous = None
        else:
            if previous:
                seconds = sample['at'] - previous['at']
                if seconds <= 0:
                    continue
                if seconds > max_gap:
                    point['reason'] = 'Пропуск измерений'
                elif sample['epoch'] != previous['epoch']:
                    point['reason'] = 'Перезапуск счётчика'
                elif any(sample[name] < previous[name] for name in ('rx', 'tx')):
                    point['reason'] = 'Сброс счётчика'
                else:
                    point.update(rx=(sample['rx'] - previous['rx']) / seconds,
                                 tx=(sample['tx'] - previous['tx']) / seconds, seconds=seconds, reason=None)
                if seconds <= max_gap and sample['epoch'] == previous['epoch'] and 'cpu_total' in sample and 'cpu_total' in previous:
                    total = sample['cpu_total'] - previous['cpu_total']
                    idle = sample['cpu_idle'] - previous['cpu_idle']
                    if total > 0 and 0 <= idle <= total:
                        point['cpu'] = 100 * (1 - idle / total)
            previous = sample
        result.append(point)
    return result
