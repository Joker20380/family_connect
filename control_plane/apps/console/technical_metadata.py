"""Replaceable support observations, separate from append-only inventory history."""
from datetime import datetime, timezone as utc
import json
import re

from django.db import transaction
from django.utils import timezone

from control.friends import technical_metadata as contract
from control.friends import geoip
from .inventory import fields, require
from .models import TechnicalMetadata, TechnicalMetadataSource

MAX_EXPORT_BYTES = 64 * 1024 * 1024

LABELS = {'not_received': 'Ещё не получено', 'unsupported': 'Не поддерживается этой версией',
          'revoked': 'Сбор выключен', 'stale': 'Устарело', 'unavailable': 'Источник недоступен',
          'available': 'Получено', 'clock_skew': 'Часы устройства не согласованы'}


def load_export(raw):
    require(len(raw) <= MAX_EXPORT_BYTES)
    return json.loads(raw, object_pairs_hook=contract.unique,
                      parse_constant=lambda value: require(False))


def prune(now=None):
    now = int((now or timezone.now()).timestamp())
    for row in TechnicalMetadata.objects.all():
        retained = {name: value for name, value in row.observations.items() if value['expires_at'] > now}
        location = row.geoip if row.geoip and row.geoip['expires_at'] > now else None
        if retained != row.observations or location != row.geoip:
            row.observations = retained
            row.geoip = location
            row.save(update_fields=['observations', 'geoip'])


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
        fields(entry, 'pseudonym consent_epoch sequence consent received_at observations' + (' geoip' if 'geoip' in entry else ''))
        location = entry.get('geoip')
        if location is not None:
            fields(location, ' '.join(geoip.FIELDS))
            require(location['source'] == 'db_ip_lite' and location['status'] in ('available', 'partial', 'unavailable'))
            require(location['origin'] in ('authenticated_awg_peer', 'authenticated_direct_service', 'vpn_exit', 'relay', 'unknown'))
            require(location['reason'] in ('none', 'no_city', 'no_asn', 'lookup_miss', 'lookup_failed', 'origin_unverified',
                'non_public_address', 'known_vpn_exit', 'peer_observation_stale', 'database_missing', 'database_stale',
                'database_invalid', 'reader_unavailable', 'no_suitable_direct_observation', 'peer_source_unavailable'))
            require(all(contract.integer(location[name]) for name in ('sampled_at', 'received_at', 'expires_at')))
            require(location['sampled_at'] <= location['received_at'] <= data['observed_at'])
            require(location['sampled_at'] < location['expires_at'] <= location['sampled_at'] + contract.RETENTION)
            require(location['received_at'] - location['sampled_at'] <= 180)
            require(location['retail_isp'] is None)
            require(location['asn'] is None or type(location['asn']) is int and 0 < location['asn'] <= 4294967295)
            for name in ('country', 'region', 'city', 'organization'):
                require(location[name] is None or geoip.text(location[name]) == location[name])
            require(location['country'] is None or re.fullmatch('[A-Z]{2}', location['country']))
            require(location['status'] != 'unavailable' or all(location[name] is None for name in ('country', 'region', 'city', 'asn', 'organization')))
            require(location['status'] != 'available' or location['city'] is not None and location['asn'] is not None and location['reason'] == 'none')
            if location['database'] is not None:
                fields(location['database'], 'version city_sha256 asn_sha256')
                require(isinstance(location['database']['version'], str) and re.fullmatch(r'20\d{2}-\d{2}', location['database']['version']))
                require(all(isinstance(location['database'][name], str) and re.fullmatch('[0-9a-f]{64}', location['database'][name])
                            for name in ('city_sha256', 'asn_sha256')))
            require(location['status'] not in ('available', 'partial') or
                    location['origin'] in ('authenticated_awg_peer', 'authenticated_direct_service') and location['database'] is not None)
        require(isinstance(entry['pseudonym'], str) and re.fullmatch('[0-9a-f]{64}', entry['pseudonym']) is not None)
        require(entry['pseudonym'] not in seen)
        seen.add(entry['pseudonym'])
        require(entry['consent'] in ('enabled', 'revoked'))
        require(contract.integer(entry['received_at']) and entry['received_at'] <= data['observed_at'])
        observations = entry['observations']
        require(type(observations) is dict and set(observations) <= set(contract.SOURCES))
        require(entry['consent'] == 'enabled' or not observations)
        require(entry['consent'] == 'enabled' or location is None)
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
        if entry['consent'] == 'enabled' and (location is None or location['status'] == 'unavailable') and row and row.consent_epoch == entry['consent_epoch']:
            if row.geoip and row.geoip['status'] in ('available', 'partial') and row.geoip['expires_at'] > now:
                location = row.geoip
        if row:
            require((entry['consent_epoch'], entry['sequence']) >= (row.consent_epoch, row.sequence))
            require(entry['consent_epoch'] > row.consent_epoch or row.consent != 'revoked' or entry['consent'] == 'revoked')
            if (entry['consent_epoch'], entry['sequence']) == (row.consent_epoch, row.sequence):
                require(entry['consent'] == row.consent and entry['received_at'] == row.received_at)
                require({name: value for name, value in observations.items() if value['expires_at'] > now} ==
                        {name: value for name, value in row.observations.items() if value['expires_at'] > now})
                row.geoip = location
                row.save(update_fields=['geoip'])
                continue
        TechnicalMetadata.objects.update_or_create(pseudonym=entry['pseudonym'], defaults={
            **{key: value for key, value in entry.items() if key not in ('pseudonym', 'geoip')}, 'geoip': location})
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
    error_at = observations.get('diagnostic', {}).get('values', {}).get('error_at_ms')
    error_time = datetime.fromtimestamp(error_at / 1000, utc.utc) if error_at is not None and 0 <= error_at < 253402300799000 else None
    terms = [profile.get(name) for name in ('manufacturer', 'model', 'android_version', 'app_version', 'version_code')]
    terms += [network.get('kind'), mobile.get('sim_operator'), mobile.get('registered_operator'), session.get('transport')]
    location = dict(row.geoip) if row and row.geoip and row.geoip['expires_at'] > current else None
    if location:
        location['age_seconds'] = max(0, current - location['sampled_at'])
        location['sampled'] = datetime.fromtimestamp(location['sampled_at'], utc.utc)
        terms += [location.get(name) for name in ('city', 'country', 'region', 'asn', 'organization')]
    return dict(status=status, label=LABELS[status], observations=observations, profile=profile,
                network=network, mobile=mobile, session=session, geoip=location, error_time=error_time,
                search=' '.join(str(value) for value in terms if value is not None).casefold())


def matches(value, query):
    filters = {'model': value['profile'].get('model'), 'android': value['profile'].get('android_version'),
               'app': value['profile'].get('app_version'), 'network': value['network'].get('kind'),
               'operator': ' '.join(value['mobile'].get(name) or '' for name in ('sim_operator', 'registered_operator')),
               'city': (value.get('geoip') or {}).get('city'),
               'transport': value['session'].get('transport')}
    return all(not query.get(name) or query[name][:128].casefold() in str(actual or '').casefold()
               for name, actual in filters.items())
