"""Display-only projection of canonical paid_beta status/event records.

This is not authentication or an entitlement source. Only the authenticated Friends
HTTP adapter may call accept(); public notices, chat text, payment links and the JSON
UI API must not. Wire decoding is strict and precedes the existing projection reducer.
"""
import json
import re


def require(condition):
    if not condition:
        raise ValueError('Invalid confirmed subscription')


def instant(value):
    require(type(value) is int and 0 <= value <= 253402300799)
    return value


def recipient(device):
    require(type(device) is str and re.fullmatch('[0-9a-f]{32}', device) is not None)
    return device


def fields(value, names):
    require(type(value) is dict and set(value) == set(names.split()))


def decode_response(raw, device):
    def unique(pairs):
        result = {}
        for name, value in pairs:
            require(name not in result)
            result[name] = value
        return result

    require(type(raw) in (str, bytes))
    encoded = raw.encode('utf-8') if type(raw) is str else raw
    require(len(encoded) <= 16384)
    wire = json.loads(encoded.decode('utf-8'), object_pairs_hook=unique)
    fields(wire, 'schema device observed_at cohort subscription event')
    require(type(wire['schema']) is int and wire['schema'] == 1)
    require(wire['device'] == recipient(device) and type(wire['cohort']) is bool)
    observed = instant(wire['observed_at'])
    status = dict(schema=1, device=device, cohort=wire['cohort'])
    if not wire['cohort']:
        require(wire['subscription'] is None and wire['event'] is None)
        return status, observed, None
    row = wire['subscription']
    fields(row, 'state effective_state paid_allow period_start paid_until grace_until entitlement_until version last_event_id updated_at')
    status.update(effective_state=row['effective_state'], paid_allow=row['paid_allow'],
                  entitlement_until=row['entitlement_until'])
    status['subscription'] = {name: value for name, value in row.items()
                              if name not in ('effective_state', 'paid_allow', 'entitlement_until')}
    status['subscription']['device'] = device
    current = snapshot(status, device)
    require(current['period_start'] <= current['updated_at'] <= observed)
    boundary = current['grace_until'] if current['state'] == 'grace' else current['paid_until']
    require(current['state'] != 'grace' or boundary is not None)
    expected = current['state']
    if expected in ('active', 'trial', 'grace') and observed >= boundary:
        expected = 'expired'
    require(current['effective_state'] == expected)
    event = wire['event']
    if event is not None:
        fields(event, 'event_id event_type occurred_at previous_state new_state result')
        require(type(event['event_id']) is str and type(event['event_type']) is str
                and type(event['new_state']) is str and type(event['result']) is str
                and (event['previous_state'] is None or type(event['previous_state']) is str))
        event = dict(event, device=device, period_start=current['period_start'],
                     paid_until=current['paid_until'], grace_until=current['grace_until'],
                     applied_at=instant(event['occurred_at']))
        event_projection(event, current)
    return status, observed, event


def snapshot(status, device):
    recipient(device)
    require(type(status) is dict and type(status.get('schema')) is int and status['schema'] == 1)
    require(status.get('device') == device and status.get('cohort') is True)
    row = status.get('subscription')
    require(type(row) is dict and row.get('device') == device)
    require(type(row.get('version')) is int and 1 <= row['version'] <= 2147483647)
    event_id = row.get('last_event_id')
    require(type(event_id) is str and re.fullmatch('[A-Za-z0-9_-]{8,128}', event_id) is not None)
    states = {'trial', 'active', 'grace', 'expired', 'revoked'}
    require(type(row.get('state')) is str and type(status.get('effective_state')) is str)
    require(row['state'] in states and status['effective_state'] in states)
    require(type(status.get('paid_allow')) is bool)
    result = {name: row[name] for name in ('device', 'version', 'last_event_id', 'state')}
    for name in ('period_start', 'paid_until', 'updated_at'):
        result[name] = instant(row.get(name))
    require(result['period_start'] < result['paid_until'])
    result['grace_until'] = row.get('grace_until')
    if result['grace_until'] is not None:
        require(instant(result['grace_until']) >= result['paid_until'])
    result['effective_state'] = status['effective_state']
    result['entitlement_until'] = status.get('entitlement_until')
    if status['paid_allow']:
        require(status['effective_state'] in ('trial', 'active', 'grace'))
        require(status['effective_state'] == row['state'])
        boundary = result['grace_until'] if row['state'] == 'grace' else result['paid_until']
        require(instant(result['entitlement_until']) == boundary)
    else:
        require(status['effective_state'] in ('expired', 'revoked') and result['entitlement_until'] is None)
    return result


def event_projection(event, current):
    require(type(event) is dict and event.get('result') == 'APPLIED')
    for name, field in (('event_id', 'last_event_id'), ('device', 'device'), ('new_state', 'state'),
                        ('period_start', 'period_start'), ('paid_until', 'paid_until'),
                        ('grace_until', 'grace_until'), ('applied_at', 'updated_at')):
        require(event.get(name) == current[field])
    require(instant(event.get('occurred_at')) == current['updated_at'])
    kind = event.get('event_type')
    require(kind in ('payment', 'grace', 'expire', 'revoke'))
    require(event['new_state'] == {'payment': 'active', 'grace': 'grace', 'expire': 'expired', 'revoke': 'revoked'}[kind])
    require('previous_state' in event and event['previous_state'] in (None, 'trial', 'active', 'grace', 'expired', 'revoked'))
    return {name: event[name] for name in ('event_id', 'event_type', 'occurred_at', 'previous_state')}


def accept(previous, status, *, device, confirmed_at, event=None):
    """Consume trusted backend evidence, never a UI action or public service notice."""
    instant(confirmed_at)
    require(type(status) is dict)
    if status.get('cohort') is False:
        require(status == dict(schema=1, device=recipient(device), cohort=False) and event is None)
        if previous is not None:
            require(previous.get('device') == device and previous.get('cohort') is False)
            if confirmed_at < previous['confirmed_at']:
                return previous
        return dict(device=device, cohort=False, snapshot=None, confirmed_at=confirmed_at, event=None, notice=None)
    current = snapshot(status, device)
    require(confirmed_at >= current['updated_at'])
    incoming = event_projection(event, current) if event is not None else None
    old = previous['snapshot'] if previous is not None else None
    if previous is not None and old is None:
        require(previous['device'] == device)
        if confirmed_at < previous['confirmed_at']:
            return previous
    if old is not None:
        require(old['device'] == device)
        if current['version'] < old['version']:
            return previous
        if current['version'] == old['version']:
            mutable = {'effective_state', 'entitlement_until'}
            require({key: value for key, value in current.items() if key not in mutable}
                    == {key: value for key, value in old.items() if key not in mutable})
            if confirmed_at < previous['confirmed_at']:
                return previous
            if confirmed_at == previous['confirmed_at']:
                require(current == old)
            if old['effective_state'] in ('expired', 'revoked'):
                require(current['effective_state'] == old['effective_state'])
        else:
            require(confirmed_at >= previous['confirmed_at'] and current['last_event_id'] != old['last_event_id'])
    same = old is not None and old['version'] == current['version']
    saved_event = previous['event'] if same else None
    if saved_event is not None and incoming is not None:
        require(saved_event == incoming)
    notice = previous['notice'] if same else None
    if incoming is not None and saved_event is None:
        kind = incoming['event_type']
        if kind == 'payment':
            kind = 'activated' if incoming['previous_state'] is None else 'confirmed'
            if old is not None and not same and current['paid_until'] > max(old['paid_until'], old['grace_until'] or 0):
                kind = 'renewed'
        notice = dict(id='subscription:' + str(current['version']) + ':' + current['last_event_id'],
                      kind='subscription', subscription_event=kind, created=incoming['occurred_at'],
                      author='Family Connect', read=False, notified=False)
    return dict(device=device, cohort=True, snapshot=current, confirmed_at=confirmed_at, event=incoming or saved_event, notice=notice)


def view(record, device, now):
    recipient(device)
    if record is None or (record.get('device') or record['snapshot']['device']) != device:
        return dict(snapshot=None, confirmed_at=None, notice=None)
    if record.get('cohort') is False:
        return dict(cohort=False, snapshot=None, confirmed_at=record['confirmed_at'], notice=None)
    result = dict(cohort=True, snapshot=dict(record['snapshot']), confirmed_at=record['confirmed_at'], notice=None)
    if record['notice'] is not None:
        notice = dict(record['notice'])
        boundary = record['snapshot']['entitlement_until']
        confirmation = notice['subscription_event'] in ('activated', 'renewed', 'confirmed', 'grace')
        notice['notification_suppressed'] = (now - notice['created'] > 86400 or
            confirmation and (boundary is None or now >= boundary))
        result['notice'] = notice
    return result
