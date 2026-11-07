"""Executed only by the operator collector, never by the web process."""
import hashlib
import hmac
import importlib
from pathlib import Path
import sys
import time


def collect_subscriptions(config, registry, key):
    observed = int(time.time())
    result = dict(schema=1, scope='production', source='gateway-ru', observed_at=observed,
                  status='unavailable', runtime_sha256=None, devices=[])
    try:
        archive = Path(config['archive'])
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != config['archive_sha256']:
            return result
        result['runtime_sha256'] = digest
        sys.path.insert(0, str(archive))
        paid = importlib.import_module('control.friends.paid_beta')
        subscription = importlib.import_module('control.friends.subscription')
        with paid.connection(registry) as database:
            if not paid.schema_present(database):
                result['status'] = 'unsupported'
                return result
            devices = database.execute('SELECT device FROM devices ORDER BY device LIMIT 10001').fetchall()
            if len(devices) > 10000:
                return result
            rows = []
            for device in devices:
                value = subscription.snapshot(database, device['device'], observed)
                pseudonym = hmac.new(key, device['device'].encode(), hashlib.sha256).hexdigest()
                entry = dict(pseudonym=pseudonym, cohort=value['cohort'], subscription=None, event=None)
                if value['subscription'] is not None:
                    entry['subscription'] = {name: value['subscription'][name] for name in (
                        'state', 'period_start', 'paid_until', 'grace_until', 'version',
                        'effective_state', 'paid_allow', 'entitlement_until')}
                if value['event'] is not None:
                    entry['event'] = dict(value['event'])
                    entry['event']['event_id'] = hmac.new(key,
                        ('event:' + value['event']['event_id']).encode(), hashlib.sha256).hexdigest()
                rows.append(entry)
            result.update(status='ok', devices=rows)
    except Exception:
        result.update(status='unavailable', devices=[])
    return result
