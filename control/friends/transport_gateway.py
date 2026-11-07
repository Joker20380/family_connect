"""Gateway decision cache and bounded application, not a subscription authority."""
import fcntl
import json
import os
from pathlib import Path
import socket
import subprocess
import time

from . import transport_policy as policy

SERVICES = ('family-connect-friends-awg.service', 'family-connect-friends-tcp.service')


def unique(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('DUPLICATE_JSON_FIELD')
        result[name] = value
    return result


def read(path):
    info = path.lstat()
    if path.is_symlink() or not path.is_file() or info.st_uid != os.geteuid() or info.st_mode & 0o077 or info.st_size > 8_000_000:
        raise ValueError('UNSAFE_GATEWAY_STATE')
    return json.loads(path.read_text(), object_pairs_hook=unique)


def write(path, value, mode=0o600):
    temporary = path.with_suffix('.pending')
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, mode)
    os.fchmod(descriptor, mode)
    with os.fdopen(descriptor, 'w') as handle:
        json.dump(value, handle, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def execute(arguments):
    return subprocess.run(arguments, capture_output=True, timeout=8, check=True).stdout


def boot_id():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


class Gateway:
    def __init__(self, gateway, *, clock=time.time, monotonic=time.monotonic, run=execute):
        self.gateway, self.root, self.clock, self.monotonic, self.run = gateway, gateway.ROOT, clock, monotonic, run
        self.path = self.root / 'transport-state.json'
        config = read(self.root / 'transport-enforcement.json')
        if (set(config) != {'schema', 'profile', 'node', 'enabled'} or config['schema'] != 1
                or config['profile'] != policy.PROFILE or config['node'] not in policy.NODES or config['enabled'] is not True):
            raise ValueError('INVALID_GATEWAY_POLICY')
        self.node = config['node']

    def load(self):
        value = read(self.path)
        if (set(value) != {'schema', 'node', 'records', 'observed_at'} or value['schema'] != 1
                or value['node'] != self.node or type(value['records']) is not dict
                or len(value['records']) > 10000 or self.clock() + policy.CLOCK_SKEW_SECONDS < value['observed_at']):
            raise ValueError('INVALID_GATEWAY_CACHE')
        for device, cached in value['records'].items():
            decision = cached['decision']
            if device != decision['device']:
                raise ValueError('INVALID_GATEWAY_BINDING')
            policy.validate(dict(schema=1, profile=policy.PROFILE, node=self.node,
                observed_at=decision['observed_at'], decisions=[decision]), self.node, decision['observed_at'])
        return value

    def allowed(self, cached):
        decision = cached['decision']
        if not decision['allowed']:
            return False
        return (cached['boot'] == boot_id() and self.clock() < decision['valid_until']
                and self.monotonic() < cached['deadline'])

    def accept(self, envelope):
        policy.validate(envelope, self.node, self.clock())
        state = self.load()
        for decision in envelope['decisions']:
            old = state['records'].get(decision['device'])
            policy.successor(old['decision'] if old else None, decision)
            for device, cached in state['records'].items():
                if device != decision['device'] and any(cached['decision'][name] == decision[name] for name in ('public_key', 'tcp_id')):
                    raise ValueError('DUPLICATE_GATEWAY_BINDING')
            if old and decision == old['decision']:
                continue
            state['records'][decision['device']] = dict(decision=decision, boot=boot_id(),
                deadline=self.monotonic() + min(policy.LEASE_SECONDS, max(0, decision['valid_until'] - self.clock())),
                applied=old.get('applied') if old else None)
        state['observed_at'] = max(state['observed_at'], int(self.clock()))
        write(self.path, state)
        return state

    def peer_allowed(self, public):
        state = self.load()
        found = [cached for cached in state['records'].values() if cached['decision']['public_key'] == public]
        return not found or self.allowed(found[0])

    def stop_all(self):
        for service in SERVICES:
            try:
                self.run(['systemctl', 'stop', service])
            except (OSError, subprocess.SubprocessError):
                self.run(['systemctl', 'kill', '--signal=KILL', service])

    def failure(self):
        write(self.root/'transport-attempt.json', dict(schema=1, node=self.node,
            observed_at=int(self.clock()), result='error'))

    def apply(self, *, starting=False):
        state = self.load()
        tcp_path = self.root.parent / 'friends-tcp/server.json'
        info = tcp_path.stat()
        config = json.loads(tcp_path.read_text(), object_pairs_hook=unique)
        inbound = next(item for item in config['inbounds'] if item.get('tag') == 'friends')
        clients = inbound['settings']['clients']
        with self.gateway.database() as database:
            peers = {public: self.gateway.address(index) for index, public in database.execute('SELECT id,public FROM peers')}
        changed, observations = False, {}
        for device, cached in state['records'].items():
            decision = cached['decision']
            email = device + '@family.test'
            matching = [client for client in clients if client.get('email') == email or client.get('id') == decision['tcp_id']]
            expected = dict(id=decision['tcp_id'], email=email, flow='xtls-rprx-vision')
            if matching and matching != [expected]:
                raise ValueError('TCP_BINDING_CONFLICT')
            registered = decision['public_key'] in peers
            if not registered and matching:
                raise ValueError('INCOMPLETE_NODE_BINDING')
            allowed = self.allowed(cached)
            if not allowed and matching:
                clients.remove(matching[0])
                changed = True
            if allowed and registered and not matching:
                clients.append(expected)
                changed = True
            observations[device] = dict(expected_revision=decision['revision'], applied_revision=None,
                observed_at=int(self.clock()), registered=registered, allowed=None, result='pending',
                reason='canonical' if not decision['allowed'] else 'lease-expired' if not allowed else 'lease-valid')
        if changed:
            write(tcp_path, config, info.st_mode & 0o777)
            os.chown(tcp_path, info.st_uid, info.st_gid)
        if starting:
            return
        if changed:
            self.run(['systemctl', 'restart', SERVICES[1]])
        live = self.run([str(self.root / 'awg'), 'show', self.gateway.IFACE, 'peers']).decode().split()
        for device, cached in state['records'].items():
            decision, observation = cached['decision'], observations[device]
            public, allowed = decision['public_key'], self.allowed(cached)
            if public in peers:
                if allowed:
                    self.gateway.add_peer(public, peers[public])
                elif public in live:
                    self.run([str(self.root / 'awg'), 'set', self.gateway.IFACE, 'peer', public, 'remove'])
            runtime = json.loads(self.run([str(self.root.parent / 'friends-tcp/xray'), 'api', 'inbounduser',
                '--server=127.0.0.1:18085', '-tag=friends', '-email='+device+'@family.test']))
            serialized = json.dumps(runtime)
            tcp_present = decision['tcp_id'] in serialized and device+'@family.test' in serialized
            awg_present = public in self.run([str(self.root / 'awg'), 'show', self.gateway.IFACE, 'peers']).decode().split()
            expected = observation['registered'] and allowed
            if tcp_present != expected or awg_present != expected:
                raise ValueError('ENGINE_READBACK_MISMATCH')
            observation.update(applied_revision=decision['revision'], allowed=expected, result='applied')
            cached['applied'] = observation
        state['observed_at'] = int(self.clock())
        write(self.path, state)
        write(self.root/'transport-attempt.json', dict(schema=1, node=self.node,
            observed_at=int(self.clock()), result='applied'))


def notify(value):
    address = os.environ.get('NOTIFY_SOCKET')
    if address:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as channel:
            channel.connect('\0'+address[1:] if address.startswith('@') else address)
            channel.sendall(value.encode())


def watch(gateway, *, run=execute):
    engine = Gateway(gateway, run=run)
    try:
        with (gateway.ROOT / 'registration.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            engine.apply(starting=True)
        notify('READY=1')
        for attempt in range(15):
            try:
                for service in SERVICES:
                    engine.run(['systemctl', 'is-active', '--quiet', service])
                break
            except subprocess.SubprocessError:
                notify('WATCHDOG=1')
                time.sleep(policy.TICK_SECONDS)
        else:
            raise ValueError('ENGINE_START_TIMEOUT')
        while True:
            with (gateway.ROOT / 'registration.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                engine.apply()
            notify('WATCHDOG=1')
            time.sleep(policy.TICK_SECONDS)
    except BaseException:
        try:
            engine.stop_all()
        finally:
            engine.failure()
        raise
