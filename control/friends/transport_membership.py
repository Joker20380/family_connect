"""Prepare durable node fences before the canonical first payment can commit."""
import json
import os
from pathlib import Path
import subprocess

from . import paid_beta, transport_policy as policy


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
            request = dict(operation='prepare', token=token,
                paid=policy.read_snapshot(database, node, now, device=device))
            reply = subprocess.run(command, input=json.dumps(request).encode(), capture_output=True, timeout=12, check=True)
            if len(reply.stdout) > 1024 or json.loads(reply.stdout) != dict(schema=1,node=node,result='prepared',token=token):
                raise ValueError('INVALID_PREPARATION_ACK')
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise paid_beta.PaidBetaError('TRANSPORT_PREPARATION_REQUIRED') from error
