import copy
import json
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'linux'))
import auto_guard as guard


class System:
    def __init__(self):
        self.actual = None
        self.interfaces = []
        self.operations = []
        self.failure = None

    def read(self):
        return copy.deepcopy(self.actual)

    def links(self):
        return copy.deepcopy(self.interfaces)

    def apply(self, commands):
        self.operations.append(copy.deepcopy(commands))
        if self.failure == 'before':
            self.failure = None
            raise OSError('synthetic transaction rejection')
        self.actual = [entry['add'] for entry in commands if 'add' in entry] or None
        if self.failure == 'after':
            self.failure = None
            raise TimeoutError('synthetic lost completion')


@pytest.fixture
def factory(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, 'private_read', lambda path: json.loads(path.read_text()))
    monkeypatch.setattr(guard, 'private_write', lambda path, value: path.write_text(json.dumps(value)))
    owners = []
    system = System()

    def create(uid=1000, generation='a' * 32):
        owner = object.__new__(guard.Guard)
        owner.system, owner.directory = system, tmp_path
        owner.uid, owner.generation = uid, generation
        owner.path, owner.record = tmp_path / 'guard.json', None
        owner.lock = os.open('/dev/null', os.O_RDONLY)
        owners.append(owner)
        return owner

    yield create
    for owner in owners:
        owner.close()


def link(name='fcmesh0', index=5, kind='tun', flags=None):
    return dict(ifname=name, ifindex=index, linkinfo=dict(info_kind=kind), flags=flags if flags is not None else ['UP'])


def rule(document, label):
    return next(entry['rule'] for entry in document if entry.get('rule', {}).get('comment') == label)


def test_initial_guard_is_owned_blocking_and_private_copy(factory):
    owner = factory()
    owner.acquire()
    state = owner.snapshot()
    assert state['current'] == guard.policy()
    state['current']['mode'] = 'ready'
    assert owner.snapshot()['current']['mode'] == 'blocked'
    objects = owner.system.read()
    assert objects[0]['table']['comment'] == 'fc-auto-v1:' + 'a' * 32
    assert [(entry['chain']['hook'], entry['chain']['policy']) for entry in objects if 'chain' in entry] == [
        ('output', 'drop'), ('forward', 'drop')]
    assert not any(entry.get('rule', {}).get('chain') == 'forward' for entry in objects)
    assert 'established' not in json.dumps(objects)
    bypass = rule(objects, 'service-mesh-bootstrap')['expr']
    assert bypass[:-1] == [guard.match('skuid', 0), guard.match('nfproto', 2), guard.match('mark', 64640)]


def test_handoff_blocks_before_cleanup_and_release(factory):
    owner = factory()
    owner.acquire()
    selected = guard.candidate('mesh', 'fcmesh0')
    owner.prepare(selected)
    owner.system.interfaces = [link()]
    owner.ready(5)
    assert rule(owner.system.read(), 'packet-ipv4')['expr'][:-1] == [
        guard.match('nfproto', 2), guard.match('oif', 5), guard.match('oifname', 'fcmesh0')]
    assert not any(entry.get('rule', {}).get('comment') == 'privileged-probe' for entry in owner.system.read())
    with pytest.raises(ValueError):
        owner.release()
    with pytest.raises(ValueError):
        owner.prepare(selected)
    owner.block()
    assert not any(entry.get('rule', {}).get('comment', '').startswith('packet-') for entry in owner.system.read())
    with pytest.raises(ValueError):
        owner.release()
    with pytest.raises(ValueError):
        owner.prepare(selected)
    owner.system.interfaces = []
    owner.release()
    assert owner.system.read() is None
    assert not owner.path.exists()
    for commands in owner.system.operations:
        assert all('flush' not in entry for entry in commands)
        assert all(entry['delete'] == {'table': {'family': 'inet', 'name': guard.TABLE}}
                   for entry in commands if 'delete' in entry)
    assert any('delete' in commands[0] and 'add' in commands[1] for commands in owner.system.operations if len(commands) > 1)


@pytest.mark.parametrize('failure', ['before', 'after'])
def test_unknown_atomic_outcome_recovers_to_blocked(factory, failure):
    owner = factory()
    owner.acquire()
    owner.system.failure = failure
    with pytest.raises(OSError):
        owner.prepare(guard.candidate('awg', 'fcawg12345678', '8.8.8.8', 51820))
    with pytest.raises(ValueError):
        owner.block()
    owner.close()
    restarted = factory()
    restarted.acquire()
    assert restarted.snapshot()['current']['mode'] == 'blocked'
    assert 'service-awg' not in json.dumps(restarted.system.read())
    restarted.release()


@pytest.mark.parametrize('failure', ['before', 'after'])
def test_initial_apply_failure_retains_journal(factory, failure):
    owner = factory()
    owner.system.failure = failure
    with pytest.raises(OSError):
        owner.acquire()
    assert owner.path.exists()
    owner.close()
    restarted = factory()
    restarted.acquire()
    assert restarted.snapshot()['current']['mode'] == 'blocked'


@pytest.mark.parametrize('failure', ['before', 'after'])
def test_unknown_release_never_automatically_reopens_traffic(factory, failure):
    owner = factory()
    owner.acquire()
    owner.system.failure = failure
    with pytest.raises(OSError):
        owner.release()
    assert owner.path.exists()
    owner.close()
    restarted = factory()
    restarted.acquire()
    assert restarted.snapshot()['current']['mode'] == 'blocked'
    restarted.release()


def test_restart_does_not_restore_ready_allowance(factory):
    owner = factory()
    owner.acquire()
    owner.prepare(guard.candidate('mesh', 'fcmesh0'))
    owner.system.interfaces = [link()]
    owner.ready(5)
    owner.close()
    restarted = factory()
    restarted.acquire()
    assert restarted.snapshot()['current']['mode'] == 'blocked'
    assert 'packet-ipv4' not in json.dumps(restarted.system.read())
    with pytest.raises(ValueError):
        restarted.release()


@pytest.mark.parametrize('uid,generation', [(1001, 'a' * 32), (1000, 'b' * 32)])
def test_other_identity_or_generation_cannot_adopt_or_delete(factory, uid, generation):
    owner = factory()
    owner.acquire()
    before = owner.system.read()
    owner.close()
    restarted = factory(uid, generation)
    with pytest.raises(ValueError):
        restarted.acquire()
    assert restarted.system.read() == before


@pytest.mark.parametrize('mutation', ['table', 'rule', 'extra', 'policy'])
def test_conflicting_firewall_is_not_modified(factory, mutation):
    owner = factory()
    owner.acquire()
    actual = owner.system.actual
    if mutation == 'table':
        actual[0]['table']['comment'] = 'different owner'
    elif mutation == 'rule':
        rule(actual, 'service-mesh-bootstrap')['expr'].pop(0)
    elif mutation == 'extra':
        actual.append(copy.deepcopy(actual[-1]))
    else:
        actual[1]['chain']['policy'] = 'accept'
    before = owner.system.read()
    for action in (owner.snapshot, owner.block, owner.release):
        with pytest.raises(ValueError):
            action()
        assert owner.system.read() == before


def test_unjournaled_table_is_not_adopted(factory):
    owner = factory()
    owner.system.actual = guard.objects(owner.generation, guard.policy())
    with pytest.raises(ValueError):
        owner.acquire()
    assert not owner.path.exists()
    assert not owner.system.operations


def test_changed_journal_stops_old_callback(factory):
    owner = factory()
    owner.acquire()
    record = json.loads(owner.path.read_text())
    record['generation'] = 'b' * 32
    owner.path.write_text(json.dumps(record))
    count = len(owner.system.operations)
    with pytest.raises(ValueError):
        owner.block()
    assert len(owner.system.operations) == count


def test_missing_guard_is_not_ready_but_block_can_repair_it(factory):
    owner = factory()
    owner.acquire()
    owner.prepare(guard.candidate('mesh', 'fcmesh0'))
    owner.system.interfaces = [link()]
    owner.system.actual = None
    with pytest.raises(ValueError):
        owner.snapshot()
    with pytest.raises(ValueError):
        owner.ready(5)
    owner.block()
    assert owner.snapshot()['current']['mode'] == 'blocked'


def test_interface_name_in_nft_readback_resolves_to_observed_index():
    original = guard.objects('a' * 32, guard.policy('ready', guard.candidate('mesh', 'fcmesh0'), 5))
    decorated = copy.deepcopy(original)
    for entry in decorated:
        for expression in entry.get('rule', {}).get('expr', []):
            value = expression.get('match', {})
            if value.get('left') in ({'meta': {'key': 'oif'}}, {'meta': {'key': 'iif'}}):
                value['right'] = 'fcmesh0'
    assert guard.canonical({'nftables': decorated}, {'fcmesh0': 5}) == original
    assert guard.canonical({'nftables': decorated}, {'fcmesh0': 6}) != original
    with pytest.raises(ValueError):
        guard.canonical({'nftables': decorated}, {})
    for entry in decorated:
        for expression in entry.get('rule', {}).get('expr', []):
            value = expression.get('match', {})
            if value.get('left') in ({'meta': {'key': 'oif'}}, {'meta': {'key': 'iif'}}):
                value['right'] = '5'
    assert guard.canonical({'nftables': decorated}, {}) == original
    with pytest.raises(ValueError):
        guard.canonical({'nftables': decorated}, {'5': 7})


@pytest.mark.parametrize('changed', [dict(schema=True), dict(uid=True), dict(extra=1),
    dict(current={'mode': 'ready'}), dict(pending={'operation': 'exec', 'state': None})])
def test_invalid_persistent_state_is_rejected(factory, changed):
    owner = factory()
    owner.acquire()
    record = json.loads(owner.path.read_text())
    record.update(changed)
    owner.path.write_text(json.dumps(record))
    owner.close()
    restarted = factory()
    count = len(owner.system.operations)
    with pytest.raises((ValueError, TypeError)):
        restarted.acquire()
    assert len(owner.system.operations) == count


@pytest.mark.parametrize('interface', [link(index=6), link(kind='dummy'), link(flags=[]), link(name='outer0')])
def test_ready_requires_exact_active_tun(factory, interface):
    owner = factory()
    owner.acquire()
    owner.prepare(guard.candidate('mesh', 'fcmesh0'))
    owner.system.interfaces = [interface]
    with pytest.raises(ValueError):
        owner.ready(5)
    assert owner.snapshot()['current']['mode'] == 'probe'


@pytest.mark.parametrize('kind,name,address,port', [
    ('mesh', 'eth0', None, None), ('mesh', 'fcmesh0', '8.8.8.8', 443),
    ('awg', 'fcawg12345678; exec', '8.8.8.8', 123), ('tcp', 'fctcp12345678', 'localhost', 443),
    ('tcp', 'fctcp12345678', '127.0.0.1', 443), ('tcp', 'fctcp12345678', '::1', 443),
    ('tcp', 'fctcp12345678', '224.0.0.1', 443),
    ('tcp', 'fctcp12345678', '8.8.8.8', True), ('tcp', 'fctcp12345678', '8.8.8.8', 65536),
    ('wg', 'wg0', '8.8.8.8', 51820)])
def test_no_arbitrary_interface_endpoint_or_command(kind, name, address, port):
    with pytest.raises(ValueError):
        guard.candidate(kind, name, address, port)


def test_probe_and_native_outer_exemptions_are_root_only_and_exact():
    selected = guard.candidate('tcp', 'fctcp12345678', '8.8.8.8', 443)
    objects = guard.objects('a' * 32, guard.policy('probe', selected))
    assert rule(objects, 'privileged-probe')['expr'][:-1] == [guard.match('skuid', 0),
        guard.match('nfproto', 2), guard.match('oifname', selected['interface'])]
    assert rule(objects, 'service-tcp')['expr'][:-1] == [guard.match('skuid', 0),
        guard.match('daddr', '8.8.8.8', 'ip'), guard.match('dport', 443, 'tcp'), guard.match('mark', 64630)]
    assert not any(entry.get('rule', {}).get('chain') == 'forward' for entry in objects)


def test_ipv6_is_opt_in_only_for_normal_tun_not_underlay():
    mesh = guard.candidate('mesh', 'fcmesh0')
    with pytest.raises(ValueError):
        guard.policy('ready', mesh, 5, True)
    selected = guard.candidate('awg', 'fcawg12345678', '8.8.8.8', 51820)
    objects = guard.objects('a' * 32, guard.policy('ready', selected, 5, True))
    assert rule(objects, 'packet-ipv6')['expr'][:-1] == [guard.match('nfproto', 10),
        guard.match('oif', 5), guard.match('oifname', selected['interface'])]
    assert rule(objects, 'dhcp4')['expr'][:-1] == [guard.match('skuid', 0), guard.match('nfproto', 2),
        guard.match('sport', 68, 'udp'), guard.match('dport', 67, 'udp')]
    for entry in objects:
        value = entry.get('rule', {})
        if value.get('comment', '').startswith('nd-'):
            assert guard.match('hoplimit', 255, 'ip6') in value['expr']
            assert guard.match('code', 0, 'icmpv6') in value['expr']


def test_canonical_readback_does_not_discard_unknown_fields():
    original = guard.objects('a' * 32, guard.policy())
    decorated = copy.deepcopy(original)
    for entry in decorated:
        next(iter(entry.values()))['handle'] = 19
    assert guard.canonical({'nftables': [{'metainfo': {}}, *decorated]}) == original
    decorated[0]['table']['flags'] = ['dormant']
    assert guard.canonical({'nftables': decorated}) != original
    with pytest.raises(ValueError):
        guard.canonical({'nftables': [{'set': {}}]})


def test_unprivileged_owner_rejected_before_any_system_mutation(tmp_path, monkeypatch):
    monkeypatch.setattr(guard.os, 'geteuid', lambda: 1000)
    with pytest.raises(ValueError):
        guard.Guard(1000, 'a' * 32, tmp_path / 'absent', System())
    assert not (tmp_path / 'absent').exists()


def test_system_output_and_input_are_bounded_without_network_commands():
    system = guard.System()
    assert system.run((sys.executable, '-c', 'print("{}")')) == {}
    with pytest.raises(RuntimeError, match='Oversized'):
        system.run((sys.executable, '-c', 'import sys; sys.stdout.write("x" * 1000000)'))
    with pytest.raises(ValueError, match='Oversized'):
        system.run(('/does/not/exist',), b'x' * 65537)
    with pytest.raises(RuntimeError, match='operation failed'):
        system.run((sys.executable, '-c', 'raise SystemExit(1)'))


@pytest.mark.parametrize('persist', [False, True])
def test_lost_journal_commit_recovers_without_restoring_user_traffic(factory, monkeypatch, persist):
    owner = factory()
    owner.acquire()
    writer = guard.private_write

    def failing_write(path, value):
        if value['pending'] is None:
            if persist:
                writer(path, value)
            raise OSError('synthetic journal commit failure')
        writer(path, value)

    monkeypatch.setattr(guard, 'private_write', failing_write)
    with pytest.raises(OSError):
        owner.prepare(guard.candidate('mesh', 'fcmesh0'))
    owner.close()
    monkeypatch.setattr(guard, 'private_write', writer)
    restarted = factory()
    restarted.acquire()
    assert restarted.snapshot()['current']['mode'] == 'blocked'
    assert 'privileged-probe' not in json.dumps(restarted.system.read())
