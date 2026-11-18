"""External, read-only collection of node application receipts; no web credentials."""
import hashlib
import hmac
import json
import fcntl
import math
import os
from contextlib import ExitStack
from pathlib import Path
import time


def read_transport_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('DUPLICATE_OBSERVATION_FIELD')
            result[key] = value
        return result
    info = path.lstat()
    if path.is_symlink() or not path.is_file() or info.st_uid != os.geteuid() or info.st_mode & 0o077 or info.st_size > 8_000_000:
        raise ValueError('UNSAFE_OBSERVATION')
    return json.loads(path.read_text(), object_pairs_hook=unique)


def read_current_observation(root, source, state, attempt):
    observation = read_transport_json(root/'transport-observation.json')
    digest = hashlib.sha256(json.dumps(state, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    binding = dict(schema=2, node=source, result='applied', boot=boot,
        producer=attempt.get('producer'), state_sha256=digest)
    if attempt != dict(binding, observed_at=attempt.get('observed_at')):
        raise ValueError('UNCONFIRMED_STATE')
    if observation != dict(binding, observed_at=observation.get('observed_at'),
            monotonic=observation.get('monotonic'), records=observation.get('records')):
        raise ValueError('OBSERVATION_BINDING_MISMATCH')
    producer = binding['producer']
    if (type(producer) is not dict or set(producer) != {'pid', 'start', 'generation'}
            or type(producer['pid']) is not int or producer['pid'] <= 0
            or type(producer['generation']) is not str or len(producer['generation']) != 32):
        raise ValueError('INVALID_OBSERVER')
    process = Path(f"/proc/{producer['pid']}/stat").read_text().rsplit(')', 1)[1].split()
    if process[0] == 'Z' or process[19] != producer['start']:
        raise ValueError('OBSERVER_GENERATION_CHANGED')
    now, monotonic = time.time(), time.monotonic()
    timestamp, tick = observation['observed_at'], observation['monotonic']
    if (type(timestamp) is not int or type(tick) not in (int, float) or not math.isfinite(tick)
            or not 0 <= monotonic-tick <= 12 or not 0 <= now-timestamp <= 12
            or abs((now-timestamp)-(monotonic-tick)) > 5
            or type(attempt['observed_at']) is not int or attempt['observed_at'] > timestamp
            or type(observation['records']) is not dict or observation['records'].keys() != state['records'].keys()):
        raise ValueError('STALE_OBSERVATION')
    for device, cached in state['records'].items():
        applied = observation['records'][device]
        decision = cached['decision']
        proof = hashlib.sha256(json.dumps(decision, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        if (type(applied) is not dict or applied.get('observed_at') != timestamp
                or {key: value for key, value in applied.items() if key != 'observed_at'} !=
                    {key: value for key, value in (cached['applied'] or {}).items() if key != 'observed_at'}
                or applied.get('decision_sha256') != proof or applied.get('result') != 'applied'
                or applied.get('applied_revision') != decision['revision']
                or applied.get('expected_revision') != decision['revision']):
            raise ValueError('UNCONFIRMED_APPLICATION')
        if applied['allowed'] and (not decision['allowed'] or not applied['registered']
                or not decision['cohort'] and cached.get('prepared')
                or decision['cohort'] and (cached['boot'] != boot
                    or now >= decision['valid_until'] or monotonic >= cached['deadline'])):
            raise ValueError('EXPIRED_OBSERVATION')
    return observation


def collect_transport(source, key, expected_sha256, root=Path('/opt/apps/family_connect/friends-awg')):
    try:
        with ExitStack() as locks:
            config_path = root/'transport-enforcement.json'
            candidate = config_path.exists() and json.loads(config_path.read_text()).get('readback_mode') == 'observations-v1'
            if candidate:
                for name in ('application.lock', 'registration.lock'):
                    lock = locks.enter_context((root/name).open('r'))
                    fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
                if os.path.lexists(root/'application-incomplete'):
                    raise ValueError('TRANSPORT_RECOVERY_REQUIRED')
            return collect_locked_transport(source, key, expected_sha256, root, candidate)
    except Exception:
        return dict(schema=2, source=source, observed_at=int(time.time()), status='unavailable', runtime_sha256=None, devices=[])


def collect_locked_transport(source, key, expected_sha256, root, candidate):
    result = dict(schema=2, source=source, observed_at=int(time.time()), status='unavailable',
                  runtime_sha256=None, devices=[])
    try:
        archive, state_path = root/'paid-transport.pyz', root/'transport-state.json'
        if not archive.exists() and not state_path.exists() and not (root/'transport-enforcement.json').exists():
            result['status'] = 'not_installed'
            return result
        if not expected_sha256 or key is not None and (type(key) is not bytes or len(key) != 32):
            return result
        if any(path.is_symlink() or not path.is_file() for path in (archive, state_path)):
            return result
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != expected_sha256 or state_path.stat().st_size > 8_000_000:
            return result
        state = read_transport_json(state_path) if candidate else json.loads(state_path.read_text())
        if state['schema'] != 1 or state['node'] != source:
            return result
        reader = read_transport_json if candidate else lambda path: json.loads(path.read_text())
        attempt = reader(root/'transport-attempt.json')
        config = reader(root/'transport-enforcement.json')
        result['observed_at'] = int(time.time())
        expected_config = dict(schema=1, profile='paid-transports-v2', node=source, enabled=True)
        if candidate:
            expected_config['readback_mode'] = 'observations-v1'
            observation = read_current_observation(root, source, state, attempt)
            result['observed_at'] = observation['observed_at']
        elif attempt != dict(schema=1, node=source, observed_at=attempt.get('observed_at'), result='applied'):
            return result
        if config != expected_config:
            return result
        result['runtime_sha256'] = digest
        for device, cached in state['records'].items():
            applied = observation['records'][device] if candidate else cached.get('applied')
            binding = {'device': device} if key is None else {'pseudonym': hmac.new(key, device.encode(), hashlib.sha256).hexdigest()}
            result['devices'].append(dict(**binding,
                expected_revision=cached['decision']['revision'], applied_revision=applied['applied_revision'] if applied else None,
                managed=bool(cached['decision']['cohort'] or cached.get('prepared')),
                decision_observed_at=cached['decision']['observed_at'],
                valid_until=cached['decision']['valid_until'] if cached['decision']['cohort'] else None,
                reason=applied['reason'] if applied else None,
                applied_at=applied['observed_at'] if applied else None,
                registered=applied['registered'] if applied else None,
                awg_allowed=applied['allowed'] if applied else None, tcp_allowed=applied['allowed'] if applied else None,
                result='applied' if applied else 'pending'))
        result['status'] = 'ok'
    except Exception:
        result.update(status='unavailable', devices=[])
    return result
