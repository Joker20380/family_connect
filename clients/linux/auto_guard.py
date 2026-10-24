"""Root-owned traffic containment across Linux Auto transport handoffs."""
import copy
import fcntl
import ipaddress
import json
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import tempfile
import time

from mesh_system import private_read, private_write

TABLE = 'family_connect_auto'
DIRECTORY = Path('/run/family-connect-auto')
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'HOME': '/root', 'LANG': 'C'}
NAMES = {'awg': r'fcawg[0-9a-f]{8}', 'tcp': r'fctcp[0-9a-f]{8}', 'mesh': r'fcmesh0'}


def integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def candidate(kind, interface, endpoint=None, port=None):
    if kind not in NAMES or not isinstance(interface, str) or not re.fullmatch(NAMES[kind], interface):
        raise ValueError('Invalid Auto interface')
    if kind == 'mesh':
        if endpoint is not None or port is not None:
            raise ValueError('MESH has no caller-selected bypass endpoint')
    elif (not isinstance(endpoint, str) or str(ipaddress.IPv4Address(endpoint)) != endpoint or
          not ipaddress.IPv4Address(endpoint).is_global or ipaddress.IPv4Address(endpoint).is_multicast or
          not integer(port, 1, 65535)):
        raise ValueError('Invalid Auto gateway')
    return dict(kind=kind, interface=interface, endpoint=endpoint, port=port)


def policy(mode='blocked', selected=None, index=0, ipv6=False):
    if mode not in ('blocked', 'probe', 'ready') or type(ipv6) is not bool or not integer(index, 0, 2**31 - 1):
        raise ValueError('Invalid Auto guard state')
    if selected is not None:
        if not isinstance(selected, dict) or set(selected) != {'kind', 'interface', 'endpoint', 'port'}:
            raise ValueError('Invalid Auto candidate')
        selected = candidate(**selected)
    if mode != 'blocked' and selected is None:
        raise ValueError('Auto candidate required')
    if (mode == 'ready') != (index > 0) or (mode != 'ready' and ipv6) or (ipv6 and selected['kind'] == 'mesh'):
        raise ValueError('Invalid Auto packet allowance')
    return dict(mode=mode, selected=selected, index=index, ipv6=ipv6)


def match(key, value, protocol=None):
    left = {'payload': {'protocol': protocol, 'field': key}} if protocol else {'meta': {'key': key}}
    return {'match': {'op': '==', 'left': left, 'right': value}}


def objects(generation, state):
    state = policy(**state)
    if not isinstance(generation, str) or not re.fullmatch('[0-9a-f]{32}', generation):
        raise ValueError('Invalid Auto generation')
    result = [{'table': {'family': 'inet', 'name': TABLE, 'comment': 'fc-auto-v1:' + generation}}]
    for hook in ('output', 'forward'):
        result.append({'chain': {'family': 'inet', 'table': TABLE, 'name': hook,
                                'type': 'filter', 'hook': hook, 'prio': 10, 'policy': 'drop'}})

    def allow(label, expressions, chain='output'):
        result.append({'rule': {'family': 'inet', 'table': TABLE, 'chain': chain,
                               'expr': expressions + [{'accept': None}], 'comment': label}})

    allow('loopback', [match('oifname', 'lo')])
    root = [match('skuid', 0)]
    ipv4 = [match('nfproto', 2)]
    ipv6 = [match('nfproto', 10)]
    allow('service-mesh-bootstrap', root + ipv4 + [match('mark', 64640)])
    allow('dhcp4', root + ipv4 + [match('sport', 68, 'udp'), match('dport', 67, 'udp')])
    for prefix, bits in (('fe80::', 10), ('ff02::', 16)):
        scope = [match('daddr', {'prefix': {'addr': prefix, 'len': bits}}, 'ip6')]
        allow('dhcp6-' + str(bits), root + scope + [
              match('sport', 546, 'udp'), match('dport', 547, 'udp')])
        for kind, code in (('nd-router-solicit', 133), ('nd-neighbor-solicit', 135), ('nd-neighbor-advert', 136)):
            allow(kind + '-' + str(bits), scope + [match('hoplimit', 255, 'ip6'),
                  match('type', code, 'icmpv6'), match('code', 0, 'icmpv6')])
    selected = state['selected']
    if state['mode'] != 'blocked':
        interface = [match('oifname', selected['interface'])]
        if state['mode'] == 'probe':
            allow('privileged-probe', root + ipv4 + interface)
        if selected['kind'] != 'mesh':
            protocol = 'udp' if selected['kind'] == 'awg' else 'tcp'
            outer = root + [match('daddr', selected['endpoint'], 'ip'),
                                   match('dport', selected['port'], protocol)]
            if selected['kind'] == 'tcp':
                outer.append(match('mark', 64630))
            allow('service-' + selected['kind'], outer)
    if state['mode'] == 'ready':
        packet = [match('oif', state['index']), match('oifname', selected['interface'])]
        inbound = [match('iif', state['index']), match('iifname', selected['interface'])]
        families = [ipv4, ipv6] if state['ipv6'] else [ipv4]
        for family in families:
            suffix = 'ipv4' if family == ipv4 else 'ipv6'
            allow('packet-' + suffix, family + packet)
            allow('forward-packet-' + suffix, family + packet, 'forward')
            allow('forward-return-' + suffix, family + inbound +
                  [{'match': {'op': '==', 'left': {'ct': {'key': 'state'}},
                              'right': {'set': [2, 4]}}}], 'forward')
    return result


def canonical(document, interfaces=None):
    if not isinstance(document, dict) or set(document) != {'nftables'} or not isinstance(document['nftables'], list):
        raise ValueError('Invalid Auto firewall readback')
    result = []
    for entry in document['nftables']:
        if isinstance(entry, dict) and set(entry) == {'metainfo'}:
            continue
        if not isinstance(entry, dict) or len(entry) != 1 or next(iter(entry)) not in ('table', 'chain', 'rule'):
            raise ValueError('Unexpected Auto firewall object')
        name, fields = next(iter(entry.items()))
        if not isinstance(fields, dict):
            raise ValueError('Invalid Auto firewall object')
        fields = copy.deepcopy({key: value for key, value in fields.items() if key != 'handle'})
        if name == 'rule':
            for expression in fields.get('expr', []):
                comparison = expression.get('match', {})
                if (comparison.get('left') in ({'meta': {'key': 'iif'}}, {'meta': {'key': 'oif'}}) and
                        isinstance(comparison.get('right'), str)):
                    value = comparison['right']
                    if re.fullmatch('[1-9][0-9]{0,9}', value) and integer(int(value), 1, 2**31 - 1):
                        if interfaces and value in interfaces and interfaces[value] != int(value):
                            raise ValueError('Ambiguous Auto interface index')
                        comparison['right'] = int(value)
                    elif interfaces is None or value not in interfaces:
                        raise ValueError('Auto interface index readback unavailable')
                    else:
                        comparison['right'] = interfaces[value]
        result.append({name: fields})
    return result


class System:
    def __init__(self, nft=('/usr/sbin/nft',)):
        self.nft = tuple(nft)

    def run(self, arguments, payload=None):
        if payload is not None and len(payload) > 65536:
            raise ValueError('Oversized Auto firewall transaction')
        deadline = time.monotonic() + 5
        output = bytearray()
        with tempfile.TemporaryFile() as source:
            if payload:
                source.write(payload)
            source.seek(0)
            with subprocess.Popen(arguments, stdin=source, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=ENV) as process:
                try:
                    with selectors.DefaultSelector() as poll:
                        poll.register(process.stdout, selectors.EVENT_READ)
                        while True:
                            remaining = deadline - time.monotonic()
                            if remaining <= 0 or not poll.select(remaining):
                                raise RuntimeError('Auto firewall operation timed out')
                            part = os.read(process.stdout.fileno(), min(4096, 65537 - len(output)))
                            if not part:
                                break
                            output.extend(part)
                            if len(output) > 65536:
                                raise RuntimeError('Oversized Auto firewall response')
                    if process.wait(timeout=max(.001, deadline - time.monotonic())):
                        raise RuntimeError('Auto firewall operation failed')
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait(timeout=1)
        return json.loads(output) if output else None

    def read(self):
        tables = self.run(self.nft + ('-j', 'list', 'tables'))
        if not isinstance(tables, dict) or not isinstance(tables.get('nftables'), list):
            raise ValueError('Invalid firewall table inventory')
        if not any(entry.get('table', {}).get('family') == 'inet' and
                   entry.get('table', {}).get('name') == TABLE for entry in tables['nftables']):
            return None
        before = {link['ifname']: link['ifindex'] for link in self.links()}
        result = self.run(self.nft + ('-j', '-n', 'list', 'table', 'inet', TABLE))
        after = {link['ifname']: link['ifindex'] for link in self.links()}
        if before != after:
            raise ValueError('Auto interface inventory changed during readback')
        return canonical(result, before)

    def apply(self, commands):
        self.run(self.nft + ('-j', '-f', '-'), json.dumps({'nftables': commands}, separators=(',', ':')).encode())

    def links(self):
        return self.run(('/usr/sbin/ip', '-j', '-d', 'link', 'show'))


class Guard:
    def __init__(self, uid, generation, directory=DIRECTORY, system=None):
        if os.geteuid() != 0 or not integer(uid, 1, 2**31 - 1):
            raise ValueError('Root Auto owner required')
        objects(generation, policy())
        self.system = system or System()
        self.uid, self.generation = uid, generation
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700, exist_ok=True)
        info = self.directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError('Unsafe Auto ownership directory')
        self.lock = os.open(self.directory / 'lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            info = os.fstat(self.lock)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
                raise ValueError('Unsafe Auto ownership lock')
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            self.close()
            raise
        self.path = self.directory / 'guard.json'
        self.record = None

    def close(self):
        if self.lock is not None:
            os.close(self.lock)
            self.lock = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _owned(self):
        if self.lock is None or self.record is None:
            raise ValueError('Auto guard not acquired')
        if private_read(self.path) != self.record:
            raise ValueError('Auto journal changed')

    def _save(self, current, pending):
        value = dict(schema=1, uid=self.uid, generation=self.generation, current=current, pending=pending)
        private_write(self.path, value)
        self.record = value

    def _read_owned(self, allow_missing=False):
        actual = self.system.read()
        if actual is None and self.record['current'] is not None and not allow_missing:
            raise ValueError('Auto firewall disappeared')
        choices = [self.record['current']]
        if self.record['pending'] is not None:
            choices.append(self.record['pending']['state'])
        if actual is not None and not any(state is not None and actual == objects(self.generation, state) for state in choices):
            raise ValueError('Auto firewall ownership mismatch')
        return actual

    def _apply(self, state):
        self._owned()
        actual = self._read_owned(allow_missing=state['mode'] == 'blocked')
        self._save(self.record['current'], dict(operation='apply', state=state))
        commands = [{'delete': {'table': {'family': 'inet', 'name': TABLE}}}] if actual is not None else []
        commands += [{'add': entry} for entry in objects(self.generation, state)]
        self.system.apply(commands)
        if self.system.read() != objects(self.generation, state):
            raise ValueError('Auto firewall verification failed')
        self._save(state, None)

    def acquire(self):
        if self.lock is None or self.record is not None:
            raise ValueError('Auto guard already acquired or closed')
        try:
            value = private_read(self.path)
        except FileNotFoundError:
            if self.system.read() is not None:
                raise ValueError('Auto firewall namespace occupied')
            self._save(None, None)
        else:
            if (not isinstance(value, dict) or set(value) != {'schema', 'uid', 'generation', 'current', 'pending'} or
                    type(value['schema']) is not int or value['schema'] != 1 or value['uid'] != self.uid or
                    type(value['uid']) is not int or value['generation'] != self.generation):
                raise ValueError('Auto journal owner mismatch')
            if value['current'] is not None:
                policy(**value['current'])
            pending = value['pending']
            if pending is not None:
                if not isinstance(pending, dict) or set(pending) != {'operation', 'state'}:
                    raise ValueError('Invalid pending Auto operation')
                if pending['operation'] == 'apply':
                    policy(**pending['state'])
                elif pending != dict(operation='release', state=None):
                    raise ValueError('Invalid pending Auto operation')
            self.record = value
        self._read_owned(allow_missing=True)
        pending = self.record['pending']
        previous = (pending['state'] if pending and pending['state'] else self.record['current'])
        self._apply(policy(selected=previous['selected'] if previous else None))

    def block(self):
        self._owned()
        if self.record['pending'] is not None:
            raise ValueError('Auto pending operation requires recovery')
        self._apply(policy(selected=self.record['current']['selected']))

    def _absent(self, selected):
        if selected and any(link.get('ifname') == selected['interface'] for link in self.system.links()):
            raise ValueError('Auto candidate cleanup not complete')

    def prepare(self, selected):
        next_state = policy('probe', selected)
        self._owned()
        if self.record['pending'] is not None or self.record['current']['mode'] != 'blocked':
            raise ValueError('Block Auto before preparing a candidate')
        self._absent(self.record['current']['selected'])
        self._absent(selected)
        self._apply(next_state)

    def ready(self, index, ipv6=False):
        self._owned()
        current = self.record['current']
        if self.record['pending'] is not None or current['mode'] != 'probe':
            raise ValueError('Auto candidate not preparing')
        next_state = policy('ready', current['selected'], index, ipv6)
        self._verify_tun(next_state)
        self._apply(next_state)

    def _verify_tun(self, state):
        found = [link for link in self.system.links() if link.get('ifname') == state['selected']['interface']]
        kinds = ('tun', 'wireguard') if state['selected']['kind'] == 'awg' else ('tun',)
        if (len(found) != 1 or found[0].get('ifindex') != state['index'] or 'UP' not in found[0].get('flags', []) or
                found[0].get('linkinfo', {}).get('info_kind') not in kinds):
            raise ValueError('Auto packet interface is not a live TUN')

    def release(self):
        self._owned()
        if self.record['pending'] is not None or self.record['current']['mode'] != 'blocked':
            raise ValueError('Block Auto before release')
        self._absent(self.record['current']['selected'])
        actual = self._read_owned(allow_missing=True)
        self._save(self.record['current'], dict(operation='release', state=None))
        if actual is not None:
            self.system.apply([{'delete': {'table': {'family': 'inet', 'name': TABLE}}}])
        if self.system.read() is not None:
            raise ValueError('Auto firewall release not verified')
        self.path.unlink()
        descriptor = os.open(self.directory, os.O_DIRECTORY | os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        self.record = None

    def snapshot(self):
        self._owned()
        if self.record['pending'] is not None or self.record['current'] is None:
            raise ValueError('Auto pending operation requires recovery')
        self._read_owned()
        if self.record['current']['mode'] == 'ready':
            self._verify_tun(self.record['current'])
        return copy.deepcopy(self.record)
