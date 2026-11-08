"""Operator-only SSH read; no SSH key or production DB is mounted in Django."""
import argparse
from datetime import datetime, timezone
import json
import hashlib
import hmac
import os
import re
from pathlib import Path
import secrets
import shlex
import subprocess

if __package__:
    from .apps.console.collector import ACTIVE_SOURCES, SOURCES
else:
    from apps.console.collector import ACTIVE_SOURCES, SOURCES

HOSTS = {source: SOURCES[source]['host'] for source in ACTIVE_SOURCES}
BASE = Path(__file__).resolve().parent


def transport_pin(config, source):
    if set(config) == {'archive_sha256'}:
        value = config['archive_sha256']
    elif set(config) == {'archives'} and type(config['archives']) is dict and set(config['archives']) == set(HOSTS):
        if not all(isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) for value in config['archives'].values()):
            raise ValueError('Invalid node archive pins')
        value = config['archives'][source]
    else:
        raise ValueError('Complete exact node archive pins required')
    if not isinstance(value, str) or not re.fullmatch('[a-f0-9]{64}', value):
        raise ValueError('Invalid node archive pin')
    return value


def ssh_command(source, known_hosts=None):
    if source not in HOSTS:
        raise ValueError('Inactive inventory source')
    command = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10']
    if known_hosts is not None:
        path = Path(known_hosts).expanduser().absolute()
        if not path.is_file() or path.is_symlink() or any(character.isspace() for character in str(path)):
            raise ValueError('Expected an existing approved known-hosts file')
        command += ['-o', 'UserKnownHostsFile=' + str(path)]
    return command + ['root@' + HOSTS[source], 'python3 -B -']


def main():
    parser = argparse.ArgumentParser(description='Read-only инвентаризация разрешённых шлюзов; без remote файлов и команд изменения')
    parser.add_argument('source', choices=HOSTS)
    parser.add_argument('--known-hosts', type=Path, help='Существующий файл проверенных SSH host pins; доверие не добавляется автоматически')
    args = parser.parse_args()
    try:
        command = ssh_command(args.source, args.known_hosts)
    except ValueError:
        parser.error('Требуется существующий файл проверенных host pins без симлинка или пробелов в пути')
    local = BASE / '.local'
    key_path = local / 'inventory-hmac.key'
    if any(parent.is_symlink() for parent in (key_path, *key_path.parents)):
        parser.error('Симлинки запрещены')
    local.mkdir(mode=0o700, exist_ok=True)
    if SOURCES[args.source]['registry'] and not key_path.exists():
        descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(secrets.token_bytes(32))
    key_expression = 'None'
    if SOURCES[args.source]['registry']:
        if key_path.stat().st_mode & 0o077 or key_path.stat().st_size != 32:
            parser.error('Ключ HMAC должен содержать 32 байта и иметь права 0600')
        key_expression = f'bytes.fromhex({key_path.read_bytes().hex()!r})'
    source = (BASE / 'apps/console/collector.py').read_text()
    source += f'\ndocument = collect({args.source!r}, {key_expression})\n'
    config_path = local / 'subscriptions-source.json'
    if args.source == 'gateway-ru' and config_path.exists():
        if config_path.is_symlink() or config_path.stat().st_mode & 0o077:
            parser.error('Subscription source configuration must be private (0600)')
        config = json.loads(config_path.read_text())
        if set(config) != {'python', 'archive', 'archive_sha256'} or not all(isinstance(value, str) for value in config.values()):
            parser.error('Invalid subscription source configuration')
        if not all(Path(config[name]).is_absolute() for name in ('python', 'archive')):
            parser.error('Absolute operator runtime paths required')
        command[-1] = shlex.quote(config['python']) + ' -I -B -'
        source += (BASE / 'apps/console/subscription_collector.py').read_text()
        source += f'\ndocument["subscription_observation"] = collect_subscriptions({config!r}, REGISTRY, {key_expression}, include_history=True)\n'
        source += 'document["schema"] = 2\n'
    transport_config = local / 'transport-source.json'
    expected_transport = None
    if transport_config.exists():
        if transport_config.is_symlink() or transport_config.stat().st_mode & 0o077:
            parser.error('Transport source configuration must be private')
        expected_transport = transport_pin(json.loads(transport_config.read_text()), args.source)
    source += (BASE / 'apps/console/transport_collector.py').read_text()
    source += f'\ndocument["transport_observation"] = collect_transport({args.source!r}, None, {expected_transport!r})\n'
    source += (BASE / 'apps/console/metrics_collector.py').read_text()
    source += f'\ndocument["metrics"] = collect_metrics({args.source!r}, {expected_transport!r})\n'
    source += 'document["schema"] = 4\nprint(json.dumps(document, allow_nan=False))\n'
    try:
        result = subprocess.run(command, input=source.encode(), capture_output=True, timeout=45)
        if result.returncode:
            parser.error('Read-only сбор не выполнен. Проверьте SSH доступ; предыдущие снимки не заменены.')
        data = json.loads(result.stdout)
        if type(data) is not dict or data.get('source') != args.source or data.get('scope') != 'production':
            raise ValueError('Wrong source binding')
        for transport in (data.get('transport_observation'), data.get('metrics')):
            if not transport or not transport['devices']:
                continue
            if (not key_path.is_file() or key_path.is_symlink() or key_path.stat().st_mode & 0o077
                    or key_path.stat().st_size != 32):
                raise ValueError('Missing shared HMAC key')
            else:
                key = key_path.read_bytes()
                for row in transport['devices']:
                    device = row.pop('device')
                    if type(device) is not str or len(device) != 32 or any(value not in '0123456789abcdef' for value in device):
                        raise ValueError('Invalid transport binding')
                    row['pseudonym'] = hmac.new(key, device.encode(), hashlib.sha256).hexdigest()
        raw = json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2).encode()
    except (OSError, ValueError, subprocess.TimeoutExpired):
        parser.error('Снимок не получен; предыдущие данные не изменены.')
    destination = local / (args.source + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as handle:
        handle.write(raw + b'\n')
    print(destination)


if __name__ == '__main__':
    main()
