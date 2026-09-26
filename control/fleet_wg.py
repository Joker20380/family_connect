"""WG/AWG peer backend for an operator-pinned existing interface.

Never reads a private key, rewrites whole configs, changes routes, or restarts an
engine. FencedGateway owns persistence/recovery. All writers must share its lock.
"""
import ipaddress
from pathlib import Path
import re
import time

from control.fleet_gateway import FenceRejected
from control.fleet_process import run
from provisioning.models import GatewayCandidate


class WGPeerBackend:
    def __init__(self, *, binary, interface, server_public, port):
        if (type(binary) is not str or not Path(binary).is_absolute()
                or type(interface) is not str or not re.fullmatch(r'[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,14}', interface)
                or type(port) is not int or not 1 <= port <= 65535):
            raise ValueError('invalid interface pin')
        GatewayCandidate.valid_key(server_public)
        self.binary, self.interface = binary, interface
        self.server_public, self.port = server_public, port

    def _run(self, args, lock_fd, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise FenceRejected('backend-timeout')
        return run([self.binary, *args], timeout=min(remaining, 10),
                   output_limit=4*1024*1024, pass_fds=(lock_fd,)).decode('ascii')

    def _pin(self, lock_fd, deadline):
        if (self._run(['show', self.interface, 'public-key'], lock_fd, deadline).strip() != self.server_public
                or self._run(['show', self.interface, 'listen-port'], lock_fd, deadline).strip() != str(self.port)):
            raise FenceRejected('interface-pin')

    def _peers(self, lock_fd, deadline):
        peers = {}
        for line in self._run(['show', self.interface, 'allowed-ips'], lock_fd, deadline).splitlines():
            key, raw = line.split('\t', 1)
            GatewayCandidate.valid_key(key)
            if key in peers:
                raise FenceRejected('duplicate-live-key')
            peers[key] = {ipaddress.ip_network(x, strict=True) for x in raw.replace(',', ' ').split() if x != '(none)'}
        return peers

    @staticmethod
    def _conflicts(peers, command):
        address = ipaddress.ip_network(command.address)
        for key, routes in peers.items():
            if key != command.wg and any(route.version == address.version and route.overlaps(address) for route in routes):
                raise FenceRejected('live-address-owned')
        if command.wg in peers and peers[command.wg] != {address}:
            raise FenceRejected('live-binding-changed')

    def preflight(self, command, *, lock_fd):
        """First claim only: never silently adopt an unmanaged matching peer."""
        deadline = time.monotonic() + 10
        self._pin(lock_fd, deadline)
        peers = self._peers(lock_fd, deadline)
        if command.wg in peers:
            raise FenceRejected('unmanaged-live-key')
        self._conflicts(peers, command)

    def ensure(self, command, *, lock_fd):
        deadline = time.monotonic() + 10
        self._pin(lock_fd, deadline)
        before = self._peers(lock_fd, deadline)
        self._conflicts(before, command)
        if command.operation == 'present':
            if command.wg not in before:
                self._run(['set', self.interface, 'peer', command.wg, 'allowed-ips', command.address], lock_fd, deadline)
        elif command.wg in before:
            self._run(['set', self.interface, 'peer', command.wg, 'remove'], lock_fd, deadline)
        after = self._peers(lock_fd, deadline)
        self._pin(lock_fd, deadline)
        others = lambda peers: {key: routes for key, routes in peers.items() if key != command.wg}
        if others(before) != others(after):
            raise FenceRejected('other-peers-changed')
        if command.operation == 'present':
            if after.get(command.wg) != {ipaddress.ip_network(command.address)}:
                raise FenceRejected('peer-not-confirmed')
        elif command.wg in after:
            raise FenceRejected('removal-not-confirmed')


class WGBackends:
    def __init__(self, bindings):
        self.bindings = dict(bindings)

    def preflight(self, command, *, lock_fd):
        self.bindings[command.transport, command.version].preflight(command, lock_fd=lock_fd)

    def ensure(self, command, *, lock_fd):
        self.bindings[command.transport, command.version].ensure(command, lock_fd=lock_fd)
