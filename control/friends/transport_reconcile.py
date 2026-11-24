"""One bounded canonical-read reconciliation cycle over explicitly pinned commands."""
import argparse
import json
from pathlib import Path
import subprocess

from .transport_policy import NODES, snapshot
from control.capture_gate import Busy, Gate, external_operation


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('DUPLICATE_NODE_ACK_FIELD')
        result[key] = value
    return result


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
            with external_operation():
                reply = subprocess.run(command, input=json.dumps(dict(operation='reconcile', paid=envelope)).encode(),
                    capture_output=True, timeout=12, check=True)
                if len(reply.stdout) > 1024:
                    raise ValueError('INVALID_NODE_ACK')
                acknowledgement = json.loads(reply.stdout, object_pairs_hook=unique)
                if (type(acknowledgement) is not dict or type(acknowledgement.get('schema')) is not int or
                        acknowledgement != {'schema': 1, 'node': node, 'result': 'applied'}):
                    raise ValueError('INVALID_NODE_ACK')
            results[node] = 'applied'
        except Exception:
            results[node] = 'unavailable'
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', required=True, type=Path)
    parser.add_argument('--commands', required=True, type=Path)
    parser.add_argument('--capture-gate', type=Path)
    args = parser.parse_args(argv)
    try:
        with Gate(args.capture_gate).operation():
            if args.commands.is_symlink() or args.commands.stat().st_mode & 0o077:
                raise ValueError('PRIVATE_COMMANDS_REQUIRED')
            results = cycle(args.registry, json.loads(args.commands.read_text()))
    except Busy:
        print(json.dumps(dict(result='CAPTURE_BUSY')))
        return 75
    except OSError:
        print(json.dumps(dict(result='RECONCILIATION_UNAVAILABLE')))
        return 1
    print(json.dumps(results))
    return int(any(value != 'applied' for value in results.values()))


if __name__ == '__main__':
    raise SystemExit(main())
