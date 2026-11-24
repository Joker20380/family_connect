"""Prepare durable node fences before the canonical first payment can commit."""
import json
import os
from pathlib import Path
import re
import subprocess

from . import paid_beta, transport_policy as policy
from control.capture_gate import external_operation


def unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('DUPLICATE_PREPARATION_ACK_FIELD')
        value[key] = item
    return value


def prepare_nodes(database, device, token, now, exchange):
    try:
        if type(token) is not str or re.fullmatch('[a-f0-9]{64}', token) is None or not callable(exchange):
            raise ValueError('INVALID_PREPARATION_REQUEST')
        for node in policy.NODES:
            request = dict(operation='prepare', token=token,
                paid=policy.read_snapshot(database, node, now, device=device))
            with external_operation():
                reply = exchange(node, request)
                if type(reply) is not bytes or len(reply) > 1024:
                    raise ValueError('INVALID_PREPARATION_ACK')
                acknowledgement = json.loads(reply.decode('utf-8'), object_pairs_hook=unique)
                if (type(acknowledgement) is not dict or type(acknowledgement.get('schema')) is not int
                        or acknowledgement != dict(schema=1, node=node, result='prepared', token=token)):
                    raise ValueError('INVALID_PREPARATION_ACK')
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise paid_beta.PaidBetaError('TRANSPORT_PREPARATION_REQUIRED') from error


def prepare(database, device, token, now):
    path = next(row[2] for row in database.execute('PRAGMA database_list') if row[1] == 'main')
    try:
        if not path or not policy.enabled(Path(path).parent):
            return
        commands_path = Path(path).parent/'transport-commands.json'
        if (commands_path.is_symlink() or commands_path.stat().st_uid != os.geteuid()
                or commands_path.stat().st_mode & 0o077):
            raise ValueError('PRIVATE_COMMANDS_REQUIRED')
        commands = json.loads(commands_path.read_text())
        if set(commands) != set(policy.NODES):
            raise ValueError('COMPLETE_NODE_SET_REQUIRED')
        for node in policy.NODES:
            command = commands[node]
            if not isinstance(command, list) or not command or not all(type(item) is str for item in command):
                raise ValueError('INVALID_NODE_COMMAND')

        def exchange(node, request):
            return subprocess.run(commands[node], input=json.dumps(request).encode(),
                capture_output=True, timeout=12, check=True).stdout

        prepare_nodes(database, device, token, now, exchange)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise paid_beta.PaidBetaError('TRANSPORT_PREPARATION_REQUIRED') from error
