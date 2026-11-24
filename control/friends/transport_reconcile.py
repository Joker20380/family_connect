"""One bounded read-only reconciliation cycle over explicitly pinned commands."""
import argparse
import json
from pathlib import Path
import subprocess

from .transport_policy import NODES, snapshot


def cycle(registry, commands):
    if set(commands) != set(NODES):
        raise ValueError('COMPLETE_NODE_SET_REQUIRED')
    results = {}
    for node in NODES:
        try:
            command = commands[node]
            if not isinstance(command, list) or not command or not all(type(item) is str for item in command):
                raise ValueError('INVALID_NODE_COMMAND')
            envelope = snapshot(registry, node)
            reply = subprocess.run(command, input=json.dumps(dict(operation='reconcile', paid=envelope)).encode(),
                capture_output=True, timeout=12, check=True)
            if len(reply.stdout) > 1024 or json.loads(reply.stdout) != {'schema': 1, 'node': node, 'result': 'applied'}:
                raise ValueError('INVALID_NODE_ACK')
            results[node] = 'applied'
        except Exception:
            results[node] = 'unavailable'
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', required=True, type=Path)
    parser.add_argument('--commands', required=True, type=Path)
    args = parser.parse_args()
    if args.commands.is_symlink() or args.commands.stat().st_mode & 0o077:
        raise ValueError('PRIVATE_COMMANDS_REQUIRED')
    results = cycle(args.registry, json.loads(args.commands.read_text()))
    print(json.dumps(results))
    return int(any(value != 'applied' for value in results.values()))


if __name__ == '__main__':
    raise SystemExit(main())
