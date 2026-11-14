"""Trusted feed to durable support jobs. No public text-producing IPC operation."""
from datetime import datetime, timezone
import json
import os
import stat
import time
import uuid


def date(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime('%d.%m.%Y %H:%M:%S UTC')


def deadline(value):
    return value['grace_until'] if value.get('state', value.get('new_state')) == 'grace' else value['paid_until']


def ending(device, version, until):
    return 'end:' + device + ':' + str(version) + ':' + str(until)


def render(event):
    when = date(event['occurred_at'])
    if event['event_type'] == 'payment':
        prior = event['prior']
        extended = prior is not None and event['paid_until'] > max(prior['paid_until'], prior['grace_until'] or 0)
        fact = 'Оплаченный период продлён' if extended else 'Оплата учтена'
        return f"{fact} {when}. Подтверждённый период: {date(event['period_start'])} — {date(event['paid_until'])}."
    if event['event_type'] == 'grace':
        return f"Льготный период предоставлен {when} до {date(event['grace_until'])}."
    if event['event_type'] == 'expire':
        return f"Соответствующий период подписки завершён подтверждённой операцией {when}."
    if event['event_type'] == 'revoke':
        return f"Доступ отозван подтверждённой операцией {when}."
    raise ValueError('invalid_event')


class Notifications:
    def __init__(self, owner):
        self.owner, self.store = owner, owner.store
        self.current = None
        self.error = 'source_unavailable'

    def cursor(self):
        with self.store._lock:
            saved = self.store._get('subscription-cursor')
            return dict(cursor=saved['position'], anchor=saved['position_hash']) if saved else dict(cursor=-1, anchor=None)

    def jobs(self):
        return [self.store._get(row[0]) for row in self.store._db.execute(
            "SELECT id FROM records WHERE id LIKE 'subscription-job:%' ORDER BY rowid")]

    def save(self, job):
        key = 'subscription-job:' + job['key']
        if self.store._get(key) != job:
            self.store._put(key, job)

    def create(self, key, subscription, source, text, observed, *, expected=None, excluded=False):
        record = 'subscription-job:' + key
        previous = self.store._get(record)
        if previous is not None:
            if previous['status'] == 'baseline_excluded' and source.get('event_id'):
                return self.create('explicit:' + key, subscription, source, text, observed)
            if source.get('event_id') and source['event_id'] not in previous['events']:
                previous['events'].append(source['event_id'])
                previous['expected'] = None
                self.save(previous)
            return
        self.save(dict(key=key, request_id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'fc-subscription:' + key)),
            device=subscription['device'], pseudonym=subscription['pseudonym'], public=subscription['public'],
            source=source, events=[source['event_id']] if source.get('event_id') else [], text=text,
            created_at=observed, expires_at=observed + 7 * 86400, expected=expected, message_id=None,
            status='baseline_excluded' if excluded else 'saved', reason=None, attempt=0, retry_at=0))

    def ingest(self, feed, *, now=None):
        now = time.time() if now is None else now
        if (feed.get('schema') != 1 or not now < feed['expires_at'] <= now + 120
                or len(feed['events']) > 128 or len(feed['subscriptions']) > 10
                or feed['position'] > feed['highwater']):
            raise ValueError('invalid_subscription_feed')
        with self.store._lock, self.store._db:
            cursor = self.cursor()
            if (feed['cursor'], feed['anchor']) != (cursor['cursor'], cursor['anchor']):
                raise ValueError('stale_subscription_feed')
            subscriptions = {item['device']: item for item in feed['subscriptions']}
            if cursor['cursor'] == -1:
                if feed['events']:
                    raise ValueError('invalid_baseline')
                self.store._put('subscription-baseline', dict(position=feed['position'],
                    position_hash=feed['position_hash'], excluded_events=feed['baseline_count'],
                    observed_at=feed['observed_at'], status='baseline_excluded'))
                for item in subscriptions.values():
                    if item['state'] in ('active', 'trial', 'grace') and deadline(item) <= feed['observed_at']:
                        key = ending(item['device'], item['version'], deadline(item))
                        self.create(key, item, dict(kind='deadline', version=item['version'], deadline=deadline(item)),
                                    '', feed['observed_at'], excluded=True)
            position = cursor['cursor']
            for event in feed['events']:
                if event['result'] != 'APPLIED' or event['position'] <= position:
                    raise ValueError('invalid_event_order')
                position = event['position']
                item = subscriptions[event['device']]
                key = 'event:' + event['event_id']
                if event['event_type'] == 'expire':
                    prior = event['prior']
                    key = ending(event['device'], prior['version'], deadline(prior))
                self.create(key, item, dict(kind='event', event_id=event['event_id'],
                    event_type=event['event_type'], version=event['version'], occurred_at=event['occurred_at']),
                    render(event) + ' Это сообщение о зафиксированной операции. Текущее состояние — в «Подписка и доступ» после Refresh.',
                    feed['observed_at'])
            if cursor['cursor'] >= 0 and position != feed['position']:
                raise ValueError('invalid_event_position')
            saved = dict(position=feed['position'], position_hash=feed['position_hash'])
            if self.store._get('subscription-cursor') != saved:
                self.store._put('subscription-cursor', saved)
            if feed['position'] == feed['highwater']:
                for item in subscriptions.values():
                    if item['state'] in ('active', 'trial', 'grace') and deadline(item) <= now:
                        expected = {name: item[name] for name in ('version', 'state', 'paid_until', 'grace_until', 'last_event_id')}
                        kind = 'Льготный' if item['state'] == 'grace' else 'Оплаченный'
                        self.create(ending(item['device'], item['version'], deadline(item)), item,
                            dict(kind='deadline', version=item['version'], deadline=deadline(item)),
                            f'{kind} период до {date(deadline(item))} закончился. Текущее состояние — в «Подписка и доступ» после Refresh.',
                            feed['observed_at'], expected=expected)
        self.current, self.error = feed, None

    def blocked(self, job, now):
        if self.current is None or self.current['expires_at'] <= now:
            return 'source_unavailable'
        if self.current['position'] != self.current['highwater']:
            return 'source_catching_up'
        item = next((item for item in self.current['subscriptions'] if item['device'] == job['device']), None)
        if item is None:
            return 'subscription_missing'
        if job['expected'] and any(item[name] != value for name, value in job['expected'].items()):
            return 'superseded'
        if job['expected'] and self.current['observed_at'] <= job['created_at']:
            return 'awaiting_deadline_recheck'
        if job['expected'] and deadline(item) > now:
            return 'deadline_not_reached'
        if job['public'] is None:
            return 'identity_missing_at_capture'
        if item['public'] != job['public']:
            return 'identity_changed'
        if item['device_revoked'] or not item['invited']:
            return 'revoked'
        if item['support_sender'] != self.owner.chat.public.hex():
            return 'support_not_enrolled'
        binding = self.owner.binding(job['pseudonym'])
        if binding['state'] != 'verified':
            return binding['state']
        if binding['public'] != job['public']:
            return 'identity_changed'
        return None

    def dispatch(self, *, now=None):
        now = time.time() if now is None else now
        from messenger import codec
        from provisioning.support_worker import SupportError
        with self.store._lock, self.store._db:
            for job in self.jobs():
                if job['status'] in ('baseline_excluded', 'recipient_stored', 'expired', 'superseded'):
                    continue
                reason = self.blocked(job, now)
                if job['message_id']:
                    message = self.store._get('message:' + job['message_id'])
                    job['status'] = message['status']
                    if message['status'] == 'recipient_stored':
                        reason = None
                    elif reason == 'superseded':
                        job['status'] = 'superseded'
                elif now >= job['expires_at']:
                    job['status'], reason = 'expired', 'notification_ttl'
                elif reason:
                    job['status'] = 'superseded' if reason == 'superseded' else 'blocked'
                elif now < job['retry_at']:
                    reason = job['reason']
                elif now >= job['retry_at']:
                    try:
                        address = codec.address(bytes.fromhex(job['public'])).hex()
                        result = self.owner.enqueue(job['pseudonym'], address, job['request_id'],
                            dict(service='subscription-notifications-v1', source=job['source'], key=job['key']),
                            job['text'], expires_at=job['expires_at'])
                        job['message_id'], job['status'] = result['id'], 'queued'
                        self.store._put('subscription-message:' + result['id'], job['key'])
                    except SupportError as failure:
                        reason = str(failure)
                        job['status'] = 'blocked'
                        job['attempt'] += 1
                        job['retry_at'] = now + min(3600, 30 * 2 ** min(job['attempt'], 7))
                job['reason'] = reason
                self.save(job)

    def allow(self, message_id):
        with self.store._lock:
            key = self.store._get('subscription-message:' + message_id)
            if key is None:
                return True
            job = self.store._get('subscription-job:' + key)
            return job['status'] not in ('superseded', 'expired') and self.blocked(job, time.time()) is None

    def status(self, pseudonym):
        with self.store._lock:
            error = self.error or ('source_unavailable' if self.current is None or self.current['expires_at'] <= time.time() else None)
            return dict(baseline=self.store._get('subscription-baseline'), error=error,
                jobs=[{name: job[name] for name in ('key', 'source', 'status', 'reason', 'created_at', 'message_id')}
                      for job in self.jobs() if job['pseudonym'] == pseudonym])

    def refresh(self, path, *, uid=0):
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor, 'rb') as stream:
                info = os.fstat(stream.fileno())
                if (not stat.S_ISREG(info.st_mode) or info.st_uid != uid or info.st_mode & 0o027
                        or info.st_nlink != 1 or info.st_size > 512 * 1024):
                    raise ValueError('unsafe_subscription_feed')
                feed = json.loads(stream.read(512 * 1024 + 1))
            cursor = self.cursor()
            if (feed['cursor'], feed['anchor']) == (cursor['cursor'], cursor['anchor']):
                self.ingest(feed)
            elif self.current is None:
                raise ValueError('stale_subscription_feed')
            self.dispatch()
        except (OSError, ValueError, KeyError, TypeError):
            self.current, self.error = None, 'source_unavailable'
