"""Fixed SSH command, strict host pins, bounded JSON; no remote shell arguments."""
import json
import os
from pathlib import Path
import re
import stat

from control.fleet import public_address
from control.fleet_gateway import PeerCommand, receipt
from control.fleet_process import run


def unique(pairs):
    value = {}
    for name, item in pairs:
        if name in value:
            raise ValueError('duplicate JSON field')
        value[name] = item
    return value


def request(raw, gateway):
    if type(raw) is not bytes or not 0 < len(raw) <= 4096:
        raise ValueError('invalid request size')
    value = json.loads(raw, object_pairs_hook=unique)
    return gateway.execute(PeerCommand.model_validate(value))


class SSHGateway:
    def __init__(self, *, host, key, known_hosts, user='fc-fleet', port=22):
        public_address(host)
        if (type(user) is not str or not re.fullmatch('[a-z_][a-z0-9_-]{0,31}', user)
                or type(port) is not int or not 1 <= port <= 65535):
            raise ValueError('invalid SSH destination')
        for path in (key, known_hosts):
            if not Path(path).is_absolute():
                raise ValueError('absolute pin paths required')
            info = os.stat(path, follow_symlinks=False)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
                raise ValueError('unsafe SSH pin file')
        self.argv = ['/usr/bin/ssh', '-F', '/dev/null', '-T', '-i', str(key), '-p', str(port)]
        for option in ('BatchMode=yes', 'IdentitiesOnly=yes', 'IdentityAgent=none',
                       'StrictHostKeyChecking=yes', 'UserKnownHostsFile='+str(known_hosts),
                       'GlobalKnownHostsFile=/dev/null', 'UpdateHostKeys=no', 'ForwardAgent=no',
                       'ClearAllForwardings=yes', 'ControlMaster=no', 'ControlPath=none',
                       'ProxyCommand=none', 'ProxyJump=none', 'PasswordAuthentication=no',
                       'KbdInteractiveAuthentication=no', 'ConnectTimeout=5', 'ConnectionAttempts=1'):
            self.argv += ['-o', option]
        self.argv += [user+'@'+host, 'fleet-v1']

    def execute(self, command):
        command = PeerCommand.model_validate({name: getattr(command, name) for name in PeerCommand.model_fields})
        raw = run(self.argv, payload=command.canonical().encode(), timeout=25, output_limit=4096)
        answer = json.loads(raw, object_pairs_hook=unique)
        if (type(answer) is not dict or type(answer.get('generation')) is not int
                or answer != receipt(command)):
            raise ValueError('invalid gateway receipt')
        return answer
