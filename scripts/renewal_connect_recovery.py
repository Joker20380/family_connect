"""One fresh scheduled operation; retry TCP establishment, never an RPC result."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import stat
import subprocess
import sys


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned(path):
    require(path.is_absolute() and path.resolve() == path, 'RECOVERY_PATH')
    for parent in path.parents:
        metadata = parent.stat()
        require(metadata.st_uid == 0 and not metadata.st_mode & 0o022, 'RECOVERY_PARENT')
    metadata = path.stat()
    require(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == 0 and
            not metadata.st_mode & 0o022 and metadata.st_size <= 4 * 1024 * 1024,
            'RECOVERY_FILE')
    return path.read_bytes()


@contextmanager
def bounded_connections(transport):
    original = transport.snapshot_command

    def command(route, *, executable='/usr/bin/ssh'):
        require(executable == '/usr/bin/ssh', 'RECOVERY_SSH_EXECUTABLE')
        result = original(route, executable=executable)
        require(result[:3] == ['/usr/bin/ssh', '-F', '/dev/null'] and
                result.count('ConnectTimeout=8') == 1 and
                not any('ConnectionAttempts' in part or 'ProxyCommand' in part or
                        'ProxyJump' in part or 'ControlMaster' in part for part in result),
                'RECOVERY_SSH_COMMAND')
        return result[:1] + ['-o', 'ConnectionAttempts=3'] + result[1:]

    transport.snapshot_command = command
    try:
        yield
    finally:
        transport.snapshot_command = original


def quiescent_units():
    for name in ('credential-renewal', 'restricted-directory-sync'):
        for suffix in ('timer', 'service'):
            unit = 'family-connect-' + name + '.' + suffix
            raw = subprocess.check_output(['systemctl', 'show', unit, '-p', 'LoadState',
                '-p', 'ActiveState', '-p', 'MainPID'], text=True, timeout=10)
            fields = dict(line.split('=', 1) for line in raw.splitlines())
            require(fields.get('LoadState') == 'loaded' and
                    fields.get('ActiveState') in ('inactive', 'failed') and
                    fields.get('MainPID', '0') == '0', 'RECOVERY_OWN_HOLDS_REQUIRED')


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--transaction-sha256', required=True)
    parser.add_argument('--operation', required=True)
    parser.add_argument('--journal', type=Path, required=True)
    args = parser.parse_args()
    require(os.geteuid() == 0, 'RECOVERY_ROOT_REQUIRED')
    require(re.fullmatch('[a-z0-9-]{16,96}', args.operation), 'RECOVERY_OPERATION')
    raw = pinned(args.config)
    require(digest(raw) == args.config_sha256, 'RECOVERY_CONFIG_CHANGED')
    config = json.loads(raw)
    require(config.get('approved_leaf_crl_schedule') is True, 'RECOVERY_SCHEDULE_REQUIRED')
    node = json.loads(pinned(Path(config['node_config'])))
    sources = {name: digest(pinned(args.runtime / name)) for name in node['source_files']
               if re.fullmatch(r'[a-z][a-z0-9_]*\.py', name)}
    require(sources == node['source_files'] and
            digest(canonical(sources)) == node['source_sha256'] == args.source_sha256 and
            {'runtime_controller.py', 'production_transport.py'} <= sources.keys(),
            'RECOVERY_SOURCE_CHANGED')
    transaction = pinned(Path(config['coordinator_state']) / 'transaction.json')
    previous = json.loads(transaction)
    require(digest(transaction) == args.transaction_sha256 and previous['state'] == 'COMMITTED'
            and previous['commit_decided'] is True
            and previous['operation_id'] != args.operation, 'RECOVERY_FRESH_STATE_REQUIRED')
    quiescent_units()
    require(args.journal.is_absolute(), 'RECOVERY_JOURNAL')
    args.journal.mkdir(mode=0o700)
    (args.journal / 'intent.json').write_bytes(canonical(dict(operation=args.operation,
        config_sha256=args.config_sha256, source_sha256=args.source_sha256,
        predecessor_sha256=args.transaction_sha256, connection_attempts=3, rpc_retry=False)))
    sys.path.insert(0, str(args.runtime))
    import production_transport
    import runtime_controller
    sys.argv = ['runtime_controller.py', '--config', str(args.config), '--mode', 'scheduled',
                '--operation', args.operation]
    with bounded_connections(production_transport):
        runtime_controller.main()


if __name__ == '__main__':
    main()
