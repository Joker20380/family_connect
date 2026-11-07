"""External, read-only collection of node application receipts; no web credentials."""
import hashlib
import hmac
import json
from pathlib import Path
import time


def collect_transport(source, key, expected_sha256, root=Path('/opt/apps/family_connect/friends-awg')):
    result = dict(schema=1, source=source, observed_at=int(time.time()), status='unavailable',
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
        state = json.loads(state_path.read_text())
        if state['schema'] != 1 or state['node'] != source:
            return result
        attempt = json.loads((root/'transport-attempt.json').read_text())
        config = json.loads((root/'transport-enforcement.json').read_text())
        result['observed_at'] = int(time.time())
        if (attempt != dict(schema=1, node=source, observed_at=attempt.get('observed_at'), result='applied')
                or config != dict(schema=1, profile='paid-transports-v1', node=source, enabled=True)):
            return result
        result['runtime_sha256'] = digest
        for device, cached in state['records'].items():
            applied = cached.get('applied')
            binding = {'device': device} if key is None else {'pseudonym': hmac.new(key, device.encode(), hashlib.sha256).hexdigest()}
            result['devices'].append(dict(**binding,
                expected_revision=cached['decision']['revision'], applied_revision=applied['applied_revision'] if applied else None,
                applied_at=applied['observed_at'] if applied else None,
                registered=applied['registered'] if applied else None,
                awg_allowed=applied['allowed'] if applied else None, tcp_allowed=applied['allowed'] if applied else None,
                result='applied' if applied else 'pending'))
        result['status'] = 'ok'
    except Exception:
        result.update(status='unavailable', devices=[])
    return result
