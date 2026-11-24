"""Native panel ingestion on an owned network-none PostgreSQL lab; stdin entrypoint only."""
from copy import deepcopy
import ctypes.util
import json
import os
from pathlib import Path
import sys

ROOT = Path('/app/control_plane/.local')
CHANGED = {'console_subscriptionsnapshot', 'console_subscriptioneventobservation', 'console_auditrecord'}


def require(condition, code):
    if not condition:
        raise ValueError(code)


def probe():
    require(os.getuid() != 0, 'NONROOT_REQUIRED')
    config = json.loads((ROOT / 'probe.json').read_bytes())
    attempted = []

    def audit(event, args):
        if event.startswith(('subprocess.', 'os.exec', 'os.spawn')) or event == 'os.system':
            attempted.append(event)
            raise RuntimeError('DISPATCH_FORBIDDEN')

    sys.addaudithook(audit)
    ctypes.util.find_library = lambda name: 'libc.so.6' if name == 'c' else None
    os.environ.update(DJANGO_SETTINGS_MODULE='fc_control_plane.settings', CONTROL_PLANE_MODE='synthetic',
        DJANGO_SECRET_KEY=config['secret'], POSTGRES_PASSWORD=config['password'], POSTGRES_HOST='127.0.0.1',
        POSTGRES_PORT='5432', FC_SUPPORT_SOCKET='', FC_PSEUDONYM_ALIASES=str(ROOT / 'panel-aliases.json'))
    import django
    django.setup()
    from django.db import connection
    from apps.console import subscriptions
    from apps.console.models import TechnicalMetadata, TechnicalMetadataSource
    from control.friends import pseudonyms

    def fingerprints():
        result = {}
        with connection.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
            names = [row[0] for row in cursor.fetchall()]
            require(len(names) == 39, 'OWNER_SCHEMA_COVERAGE')
            for name in names:
                table = connection.ops.quote_name(name)
                cursor.execute("SELECT json_build_object('rows',count(*),'sha256',encode(sha256(convert_to("
                    "coalesce(string_agg(row_hash,'' ORDER BY row_hash),''),'UTF8')),'hex')) FROM (SELECT "
                    "encode(sha256(convert_to(to_jsonb(row_value)::text,'UTF8')),'hex') AS row_hash FROM public."
                    + table + ' row_value) hashed')
                result[name] = cursor.fetchone()[0]
        return result

    before = fingerprints()
    if config['mode'] == 'baseline':
        require(all(before[name] == value for name,value in config['expected'].items()), 'OWNER_RESTORE_MISMATCH')
        require(not TechnicalMetadata.objects.exists() and not TechnicalMetadataSource.objects.exists(), 'METADATA_NOT_EMPTY')
        for row in config['floors']:
            TechnicalMetadata.objects.create(**row, observations={}, geoip=None)
        before = fingerprints()
        return dict(result='OWNER_JOINT_BASELINE_PASS', fingerprints=before)
    if config['mode'] == 'stale':
        require(before != config['expected'], 'STALE_COPY_NOT_DISTINGUISHED')
        require(any(before[name] != config['expected'][name] for name in CHANGED), 'STALE_ACK_NOT_DISTINGUISHED')
        return dict(result='STALE_OWNER_RESTORE_REFUSED')
    require(before == config['expected'], 'ACKNOWLEDGED_OWNER_STATE_CHANGED')
    aliases = pseudonyms.load(ROOT / 'panel-aliases.json')
    envelope = json.loads((ROOT / 'envelope.json').read_bytes())
    payload = pseudonyms.unseal(envelope, 'subscriptions', aliases)
    first = subscriptions.ingest(payload)
    require(first.devices == payload['devices'] and first.history == payload['history'], 'NATIVE_PROJECTION_MISMATCH')
    after = fingerprints()
    require(all(after[name] == before[name] for name in before if name not in CHANGED), 'UNRELATED_OWNER_STATE_CHANGED')
    duplicate = subscriptions.ingest(payload)
    require(duplicate.pk == first.pk and fingerprints() == after, 'DUPLICATE_OWNER_INGEST_CHANGED')
    if config['mode'] == 'readback':
        require(after == before, 'RESTORED_ACK_DUPLICATED')
    else:
        require(config['mode'] == 'ingest' and after['console_subscriptionsnapshot']['rows'] ==
                before['console_subscriptionsnapshot']['rows'] + 1, 'NEW_OWNER_ACK_REQUIRED')
    bad = deepcopy(envelope)
    bad['generation'] += 1
    try:
        pseudonyms.unseal(bad, 'subscriptions', aliases)
    except ValueError:
        pass
    else:
        raise ValueError('WRONG_ALIAS_GENERATION_ACCEPTED')
    conflict = deepcopy(payload)
    require(conflict['history']['events'], 'HISTORY_REQUIRED')
    event = conflict['history']['events'][0]
    event['new_state'] = 'revoked' if event['new_state'] != 'revoked' else 'active'
    try:
        subscriptions.ingest(conflict)
    except ValueError:
        pass
    else:
        raise ValueError('CONFLICTING_PAID_HISTORY_ACCEPTED')
    require(fingerprints() == after and not attempted, 'REJECTED_IMPORT_CHANGED_STATE')
    require(not TechnicalMetadata.objects.exclude(observations={}).exists() and
            not TechnicalMetadata.objects.filter(geoip__isnull=False).exists() and
            not TechnicalMetadataSource.objects.exists(), 'METADATA_OBSERVATIONS_RESTORED')
    return dict(result='NATIVE_OWNER_JOINT_PASS', fingerprints=after, devices=len(payload['devices']),
                paid_events=len(payload['history']['events']), duplicate='UNCHANGED', conflict='REFUSED',
                wrong_alias_generation='REFUSED', dispatch_calls=0, activation=False, full_recovery=False)


if __name__ == '__main__':
    try:
        print(json.dumps(probe(), sort_keys=True))
    except Exception as error:
        frames = []
        trace = error.__traceback__
        while trace is not None:
            frames.append((Path(trace.tb_frame.f_code.co_filename).name, trace.tb_lineno))
            trace = trace.tb_next
        print(json.dumps(dict(result='OWNER_JOINT_REFUSED', error=type(error).__name__, frames=frames)), file=sys.stderr)
        raise SystemExit(1) from None
