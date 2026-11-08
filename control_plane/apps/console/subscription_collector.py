"""Executed only by the operator collector, never by the web process."""
import hashlib
import hmac
import importlib
from pathlib import Path
import sys
import time
import zipfile
import zipimport


def canonical_modules(archive):
    names = ('control.friends.paid_beta', 'control.friends.subscription')
    if any(name in sys.modules for name in names):
        raise ValueError('Canonical module was loaded before archive verification')
    with zipfile.ZipFile(archive) as package:
        for name in names:
            package.getinfo(name.replace('.', '/') + '.py')
    sys.path.insert(0, str(archive))
    try:
        modules = [importlib.import_module(name) for name in names]
        for name, module in zip(names, modules):
            expected = str(archive / (name.replace('.', '/') + '.py'))
            spec = module.__spec__
            if (module.__file__ != expected or spec.origin != expected
                    or not isinstance(spec.loader, zipimport.zipimporter)
                    or Path(spec.loader.archive).resolve() != archive):
                raise ValueError('Canonical module is outside the verified archive')
        if modules[1].paid_beta is not modules[0]:
            raise ValueError('Canonical module binding mismatch')
        return modules
    finally:
        sys.path.pop(0)


def collect_subscriptions(config, registry, key, *, include_history=False):
    observed = int(time.time())
    result = dict(schema=1, scope='production', source='gateway-ru', observed_at=observed,
                  status='unavailable', runtime_sha256=None, devices=[])
    try:
        archive = Path(config['archive']).resolve(strict=True)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != config['archive_sha256']:
            return result
        result['runtime_sha256'] = digest
        paid, subscription = canonical_modules(archive)
        with paid.connection(registry) as database:
            present = paid.schema_present(database)
            observed = int(time.time())
            result['observed_at'] = observed
            if not present:
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
            if include_history:
                events = database.execute('SELECT event_id,device,event_type,occurred_at,previous_state,new_state,result '
                    'FROM paid_beta_events WHERE result=? ORDER BY occurred_at DESC,event_id DESC LIMIT 1001', ('APPLIED',)).fetchall()
                history = []
                for event in events[:1000]:
                    value = dict(event)
                    value['pseudonym'] = hmac.new(key, value.pop('device').encode(), hashlib.sha256).hexdigest()
                    value['event_id'] = hmac.new(key, ('event:' + value['event_id']).encode(), hashlib.sha256).hexdigest()
                    history.append(value)
                result.update(schema=2, history=dict(events=history, truncated=len(events) > 1000))
    except Exception:
        result.update(status='unavailable', devices=[])
    return result
