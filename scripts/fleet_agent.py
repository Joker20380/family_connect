"""Root-owned forced-command entry point. Installation is explicit and separate."""
import json
import os
from pathlib import Path
import signal
import stat
import sys
from typing import Annotated, Literal

# Supports an installed `python -I /trusted/app/scripts/fleet_agent.py` invocation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pydantic import Field
from control.fleet import Gateway
from control.fleet_gateway import FencedGateway
from control.fleet_ssh import request, unique
from control.fleet_wg import WGBackends, WGPeerBackend
from provisioning.models import FrozenModel

CONFIG = Path('/etc/family-connect/fleet-agent.json')


class Binding(FrozenModel):
    transport: Literal['wireguard', 'amneziawg']
    version: Literal['1', '2.0', '3.1']
    binary: str
    interface: str
    server_public: str
    port: Annotated[int, Field(strict=True, ge=1, le=65535)]


class AgentConfig(FrozenModel):
    schema_version: Annotated[int, Field(strict=True, ge=1, le=1)]
    gateway: Gateway
    state_directory: str
    bindings: Annotated[tuple[Binding, ...], Field(min_length=1, max_length=8)]


def protected(path):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('absolute operator path required')
    for item in (path, *path.parents):
        info = item.lstat()
        if (stat.S_ISLNK(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022):
            raise ValueError('unsafe operator path')
    return path


def build(config):
    if not Path(config.state_directory).is_absolute():
        raise ValueError('absolute state directory required')
    wanted = {(e.transport, e.version) for e in config.gateway.endpoints if e.transport != 'vless-reality'}
    bindings = {}
    for b in config.bindings:
        key = b.transport, b.version
        if key in bindings or key not in wanted:
            raise ValueError('invalid backend capability binding')
        if not any((e.transport, e.version, e.port) == (*key, b.port) for e in config.gateway.endpoints):
            raise ValueError('listen port does not match registry')
        bindings[key] = WGPeerBackend(binary=b.binary, interface=b.interface,
                                     server_public=b.server_public, port=b.port)
    if set(bindings) != wanted:
        raise ValueError('missing backend capability')
    return FencedGateway(config.state_directory, config.gateway, WGBackends(bindings))


def main():
    if os.geteuid() != 0:
        raise ValueError('privileged service required')
    os.umask(0o077)
    args = sys.argv[1:]
    if args:
        if args not in (['--initialize'], ['--recover']) or os.environ.get('SSH_CONNECTION'):
            raise ValueError('local operator action required')
    elif os.environ.get('SSH_ORIGINAL_COMMAND') != 'fleet-v1':
        raise ValueError('forced command required')
    path = protected(CONFIG)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1:
            raise ValueError('private config required')
        raw = os.read(fd, 65537)
    finally:
        os.close(fd)
    if len(raw) > 65536:
        raise ValueError('oversize config')
    config = AgentConfig.model_validate_json(json.dumps(json.loads(raw, object_pairs_hook=unique)))
    protected(Path(config.state_directory).parent)
    for binding in config.bindings:
        protected(binding.binary)
    agent = build(config)
    if args == ['--initialize']:
        agent.initialize()
        return {'initialized': True}
    if args == ['--recover']:
        return {'recovered': len(agent.recover())}
    def expired(*_):
        raise TimeoutError('request timeout')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(24)
    try:
        return request(sys.stdin.buffer.read(4097), agent)
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    try:
        print(json.dumps(main(), separators=(',', ':')))
    except Exception:
        print('{"error":"gateway-unavailable"}')
        raise SystemExit(1) from None
