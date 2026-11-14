"""Replaceable support observations, separate from append-only inventory history."""
from datetime import datetime, timezone as utc
import re

from django.db import transaction
from django.utils import timezone

from control.friends import technical_metadata as contract
from .inventory import fields, require
from .models import TechnicalMetadata, TechnicalMetadataSource

LABELS = {'not_received': 'Ещё не получено', 'unsupported': 'Не поддерживается этой версией',
          'revoked': 'Сбор выключен', 'stale': 'Устарело', 'unavailable': 'Источник недоступен',
          'available': 'Получено', 'clock_skew': 'Часы устройства не согласованы'}


def prune(now=None):
    now = int((now or timezone.now()).timestamp())
    for row in TechnicalMetadata.objects.exclude(observations={}):
        retained = {name: value for name, value in row.observations.items() if value['expires_at'] > now}
        if retained != row.observations:
            row.observations = retained
            row.save(update_fields=['observations'])


@transaction.atomic
def ingest(data):
    fields(data, 'schema source observed_at status devices')
    require(type(data['schema']) is int and data['schema'] == 1 and data['source'] == 'gateway-ru')
    require(data['status'] in ('ok', 'unavailable', 'unsupported'))
    now = int(timezone.now().timestamp())
    require(type(data['observed_at']) is int and now - 300 <= data['observed_at'] <= now + 15)
    require(type(data['devices']) is list and len(data['devices']) <= contract.MAX_DEVICES)
    require(data['status'] == 'ok' or not data['devices'])
    source, created = TechnicalMetadataSource.objects.get_or_create(source='gateway-ru')
    source = TechnicalMetadataSource.objects.select_for_update().get(pk=source.pk)
    require(source.observed_at <= data['observed_at'])
    seen = set()
    for entry in data['devices']:
        fields(entry, 'pseudonym consent_epoch sequence consent received_at observations')
        require(isinstance(entry['pseudonym'], str) and re.fullmatch('[0-9a-f]{64}', entry['pseudonym']) is not None)
        require(entry['pseudonym'] not in seen)
        seen.add(entry['pseudonym'])
        require(entry['consent'] in ('enabled', 'revoked'))
        require(contract.integer(entry['received_at']) and entry['received_at'] <= data['observed_at'])
        observations = entry['observations']
        require(type(observations) is dict and set(observations) <= set(contract.SOURCES))
        require(entry['consent'] == 'enabled' or not observations)
        for group, observation in observations.items():
            fields(observation, 'sampled_at_ms age_ms source status reason values received_at age_at_receive_ms clock_status expires_at')
            require(all(contract.integer(observation[name]) for name in ('received_at', 'age_at_receive_ms', 'expires_at')))
            require(observation['received_at'] <= entry['received_at'])
            require(observation['expires_at'] <= observation['received_at'] + contract.RETENTION)
            require(observation['age_at_receive_ms'] >= observation['age_ms'])
            require(observation['clock_status'] in ('consistent', 'clock_skew'))
        raw_observations = {name: {key: value for key, value in observation.items() if key not in {
            'received_at', 'age_at_receive_ms', 'clock_status', 'expires_at'}} for name, observation in observations.items()}
        try:
            require(contract.integer(entry['consent_epoch'], 1) and contract.integer(entry['sequence'], 1))
            contract.validate_observations(raw_observations, complete=False)
        except (ValueError, TypeError, KeyError):
            require(False)
        row = TechnicalMetadata.objects.select_for_update().filter(pseudonym=entry['pseudonym']).first()
        if row:
            require((entry['consent_epoch'], entry['sequence']) >= (row.consent_epoch, row.sequence))
            require(entry['consent_epoch'] > row.consent_epoch or row.consent != 'revoked' or entry['consent'] == 'revoked')
            if (entry['consent_epoch'], entry['sequence']) == (row.consent_epoch, row.sequence):
                require(entry['consent'] == row.consent and entry['received_at'] == row.received_at)
                require({name: value for name, value in observations.items() if value['expires_at'] > now} ==
                        {name: value for name, value in row.observations.items() if value['expires_at'] > now})
                continue
        TechnicalMetadata.objects.update_or_create(pseudonym=entry['pseudonym'], defaults={
            key: value for key, value in entry.items() if key != 'pseudonym'})
    prune()
    source.observed_at, source.status = data['observed_at'], data['status']
    source.save(update_fields=['observed_at', 'status'])
    return len(data['devices'])


def presentation(row, now, source=None, supported=None):
    current = int(now.timestamp())
    observations = {} if row is None else {name: dict(value) for name, value in row.observations.items() if value['expires_at'] > current}
    status = 'not_received'
    if row is not None:
        status = 'revoked' if row.consent == 'revoked' else 'available' if observations else 'stale'
    elif supported is False:
        status = 'unsupported'
    if status not in ('revoked', 'unsupported') and (source is None or source.status != 'ok' or current - source.observed_at > 300):
        status = 'unavailable'
    for value in observations.values():
        value['age_seconds'] = max(0, current - value['received_at']) + value['age_at_receive_ms'] // 1000
        value['sampled_at'] = datetime.fromtimestamp(value['sampled_at_ms'] / 1000, utc.utc) if value['sampled_at_ms'] < 253402300799000 else None
        value['received'] = datetime.fromtimestamp(value['received_at'], utc.utc)
        value['clock_label'] = LABELS.get(value['clock_status'], '')
    profile = observations.get('profile', {}).get('values', {})
    network = observations.get('network', {}).get('values', {})
    mobile = observations.get('mobile', {}).get('values', {})
    session = observations.get('session', {}).get('values', {})
    terms = [profile.get(name) for name in ('manufacturer', 'model', 'android_version', 'app_version', 'version_code')]
    terms += [network.get('kind'), mobile.get('sim_operator'), mobile.get('registered_operator'), session.get('transport')]
    return dict(status=status, label=LABELS[status], observations=observations, profile=profile,
                network=network, mobile=mobile, session=session,
                search=' '.join(str(value) for value in terms if value is not None).casefold())


def matches(value, query):
    filters = {'model': value['profile'].get('model'), 'android': value['profile'].get('android_version'),
               'app': value['profile'].get('app_version'), 'network': value['network'].get('kind'),
               'operator': ' '.join(value['mobile'].get(name) or '' for name in ('sim_operator', 'registered_operator')),
               'transport': value['session'].get('transport')}
    return all(not query.get(name) or query[name][:128].casefold() in str(actual or '').casefold()
               for name, actual in filters.items())
