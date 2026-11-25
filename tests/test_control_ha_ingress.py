import copy
import json
import time

import pytest

from scripts import control_ha_ingress as ingress

TOKEN = 'a' * 32
TARGET = 'b' * 64
IMAGE = 'sha256:' + 'c' * 64
HELPER = 'd' * 64


def readback(seconds=5, remaining=4):
    request = ingress.create_request(TOKEN, seconds)
    rows = [copy.deepcopy(next(iter(row.values()))) for row in request['nftables']]
    rows[2]['set']['elem'] = [{'elem': {'val': 8000, 'expires': remaining}}] if remaining else []
    rows[3]['rule']['expr'][2] = {'counter': {'packets': 1, 'bytes': 60}}
    return {'nftables': [{'metainfo': {'version': '1.1.6'}}, *rows]}


@pytest.mark.parametrize('seconds', [1, 2, 3, 4, 5])
def test_exact_scoped_atomic_request(seconds):
    request = ingress.create_request(TOKEN, seconds)
    ingress.request_scope(request)
    assert request['nftables'][0] == {'create': {'table': {'family': 'inet', 'name': ingress.PREFIX + TOKEN}}}
    assert ingress.inspect_table(readback(seconds, 0), TOKEN) == dict(
        remaining_seconds=0, lease_seconds=seconds, rejected_packets=1)


@pytest.mark.parametrize('seconds', [0, 6, -1, True, 1.0, '5', None])
def test_lease_duration_is_bounded(seconds):
    with pytest.raises(ValueError):
        ingress.create_request(TOKEN, seconds)


@pytest.mark.parametrize('token', ['', 'A' * 32, 'a' * 31, 'a' * 33, '../table', None, 3])
def test_token_is_not_an_arbitrary_table(token):
    with pytest.raises(ValueError):
        ingress.table_name(token)


@pytest.mark.parametrize('change', ['family', 'port', 'timeout', 'chain', 'policy', 'priority', 'rule',
                                  'counter', 'comment', 'object', 'extra-field', 'extra-element', 'expiry',
                                  'counter-operation', 'metadata-operation'])
def test_changed_readback_refuses_cleanup(change):
    value = readback()
    table, chain, ports, rule = [next(iter(row.values())) for row in value['nftables'][1:]]
    if change == 'family':
        table['family'] = 'ip'
    elif change == 'port':
        ports['elem'][0]['elem']['val'] = 22
    elif change == 'timeout':
        ports['timeout'] = 6
    elif change == 'chain':
        chain['hook'] = 'forward'
    elif change == 'policy':
        chain['policy'] = 'drop'
    elif change == 'priority':
        chain['prio'] = 0
    elif change == 'rule':
        rule['expr'].pop()
    elif change == 'counter':
        rule['expr'][2]['counter']['packets'] = True
    elif change == 'comment':
        rule['comment'] = 'foreign'
    elif change == 'object':
        value['nftables'].append({'chain': copy.deepcopy(chain)})
    elif change == 'extra-field':
        table['flags'] = ['persist']
    elif change == 'extra-element':
        ports['elem'].append(copy.deepcopy(ports['elem'][0]))
    elif change == 'counter-operation':
        rule['expr'][2]['drop'] = None
    elif change == 'metadata-operation':
        value['nftables'][0]['table'] = copy.deepcopy(table)
    else:
        ports['elem'][0]['elem']['expires'] = 6
    with pytest.raises(ValueError):
        ingress.inspect_table(value, TOKEN)


@pytest.mark.parametrize('payload', [
    {'nftables': [{'flush': {'ruleset': None}}]},
    {'nftables': [{'delete': {'table': {'family': 'inet', 'name': 'firewall'}}}]},
    {'nftables': [{'list': {'ruleset': None}}]},
    {'nftables': [{'delete': {'table': {'family': 'ip', 'name': ingress.PREFIX + TOKEN}}}]},
])
def test_no_global_or_unowned_operations(payload):
    with pytest.raises((ValueError, KeyError)):
        ingress.request_scope(payload)


class Transport:
    def __init__(self, root):
        self.root, self.target = root, TARGET
        self.unconfirmed = False
        self.calls, self.cleaned = [], False
        self.value = readback()

    def run(self, request):
        self.calls.append(copy.deepcopy(request))
        return self.value if 'list' in request['nftables'][0] else {}

    def finished(self):
        pass

    def cleanup_helpers(self):
        self.cleaned = True


def test_normal_release_and_no_reuse(tmp_path):
    transport = Transport(tmp_path)
    with ingress.Lease(transport, token=TOKEN) as lease:
        assert lease.check()['remaining_seconds'] == 4
    assert transport.cleaned and not lease.active
    assert list(transport.calls[-1]['nftables'][0]) == ['delete']
    with pytest.raises(ValueError, match='NO_INGRESS_RETRY'):
        lease.__enter__()


@pytest.mark.parametrize('case', ['local-deadline', 'kernel-deadline', 'wrong-ttl', 'body-error'])
def test_failed_lease_releases_only_verified_owned_table(tmp_path, case):
    transport = Transport(tmp_path)
    with pytest.raises((ValueError, RuntimeError)):
        with ingress.Lease(transport, token=TOKEN) as lease:
            if case == 'local-deadline':
                lease.deadline = time.monotonic() - 1
            elif case == 'kernel-deadline':
                transport.value = readback(5, 0)
            elif case == 'wrong-ttl':
                transport.value = readback(3, 2)
            else:
                raise RuntimeError('synthetic failure')
            lease.check()
    assert transport.cleaned
    assert sum('delete' in request['nftables'][0] for request in transport.calls) == 1


def test_entry_readback_failure_never_deletes_changed_table(tmp_path):
    transport = Transport(tmp_path)
    transport.value['nftables'][4]['rule']['comment'] = 'foreign'
    with pytest.raises(ValueError):
        with ingress.Lease(transport, token=TOKEN):
            pytest.fail('invalid lease admitted')
    assert not transport.cleaned
    assert not any('delete' in request['nftables'][0] for request in transport.calls)


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    target = dict(Id=TARGET, State=dict(Running=True, Paused=False, Restarting=False, Pid=123, StartedAt='start'),
                  RestartCount=0, HostConfig=dict(NetworkMode='isolated'), NetworkSettings=dict(SandboxID='sandbox'))
    helper = dict(Id=HELPER, Image=IMAGE, Mounts=[],
                  Config=dict(Labels={ingress.LABEL: TARGET}, Entrypoint=ingress.ENTRYPOINT, Env=ingress.TOOL_ENV),
                  State=dict(Running=False, Status='created', ExitCode=0, OOMKilled=False),
                  HostConfig=dict(NetworkMode='container:' + TARGET, ReadonlyRootfs=True, Privileged=False,
                                  PidMode='', CapDrop=['ALL'], CapAdd=['CAP_NET_ADMIN'], RestartPolicy=dict(Name='no'),
                                  SecurityOpt=['no-new-privileges'], Memory=64 * 1024 * 1024, PidsLimit=8))
    class API:
        members, removed = [dict(Id=TARGET)], []

        def inspect(self, reference):
            return copy.deepcopy({TARGET: target, HELPER: helper}.get(reference))

        def request(self, method, path):
            assert method == 'GET'
            if path == '/containers/json':
                return self.members
            return dict(Id=IMAGE, Config=dict(Entrypoint=ingress.ENTRYPOINT, Env=ingress.TOOL_ENV))

        def remove(self, identifier):
            self.removed.append(identifier)

    api = API()
    calls = []
    def docker(*args, **kwargs):
        calls.append(args)
        if args[0] == 'create':
            return HELPER.encode()
        assert args[0] == 'start' and json.loads(kwargs['data'])
        helper['State']['Status'] = 'exited'
        return b'{}'
    monkeypatch.setattr(ingress, 'Docker', lambda: api)
    monkeypatch.setattr(ingress, 'docker', docker)
    transport = ingress.Transport(TARGET, IMAGE, tmp_path)
    return transport, target, helper, api, calls


def test_helper_capabilities_mounts_and_network_are_confined(runtime):
    transport, _, _, api, calls = runtime
    transport.run(ingress.create_request(TOKEN, 5))
    assert calls[0][calls[0].index('--network') + 1] == 'container:' + TARGET
    assert '--privileged' not in calls[0] and '--mount' not in calls[0] and '--pid' not in calls[0]
    transport.cleanup_helpers()
    assert api.removed == [HELPER]


@pytest.mark.parametrize('field,value', [('Pid', 999), ('StartedAt', 'restarted'), ('Running', False),
                                       ('Paused', True), ('Restarting', True)])
def test_changed_runtime_refuses_before_mutation(runtime, field, value):
    transport, target, _, _, calls = runtime
    target['State'][field] = value
    with pytest.raises(ValueError, match='INGRESS_RUNTIME_CHANGED'):
        transport.run(ingress.create_request(TOKEN, 5))
    assert not calls


@pytest.mark.parametrize('field,value', [('NetworkMode', 'host'), ('Privileged', True), ('ReadonlyRootfs', False),
                                       ('PidMode', 'host'), ('CapAdd', ['CAP_SYS_ADMIN']), ('SecurityOpt', []),
                                       ('Memory', 0), ('PidsLimit', 0)])
def test_misconfigured_helper_is_never_started(runtime, field, value):
    transport, _, helper, _, calls = runtime
    helper['HostConfig'][field] = value
    with pytest.raises(ValueError, match='HELPER_SCOPE'):
        transport.run(ingress.create_request(TOKEN, 5))
    assert [call[0] for call in calls] == ['create']
    assert transport.unconfirmed


@pytest.mark.parametrize('stage', ['create', 'start'])
def test_unknown_mutation_cannot_be_retried_or_released(runtime, monkeypatch, stage):
    transport, _, _, _, calls = runtime
    real = ingress.docker
    def docker(*args, **kwargs):
        result = real(*args, **kwargs)
        if args[0] == stage:
            raise TimeoutError('lost response')
        return result
    monkeypatch.setattr(ingress, 'docker', docker)
    lease = ingress.Lease(transport, token=TOKEN)
    with pytest.raises(TimeoutError):
        lease.__enter__()
    previous = len(calls)
    with pytest.raises(ValueError, match='UNCONFIRMED'):
        transport.run(ingress.create_request(TOKEN, 5))
    with pytest.raises(ValueError, match='UNCONFIRMED'):
        lease.release()
    assert len(calls) == previous
    assert list(transport.root.glob('intent-*.json'))


def test_other_container_sharing_network_blocks_mutation(runtime):
    transport, _, helper, api, calls = runtime
    helper['NetworkSettings'] = dict(SandboxID='')
    api.members.append(dict(Id=HELPER))
    with pytest.raises(ValueError, match='SHARED_TARGET_NETWORK'):
        transport.run(ingress.create_request(TOKEN, 5))
    assert not calls


@pytest.mark.parametrize('state', ['running', 'created'])
def test_incomplete_helper_prevents_followup(runtime, state):
    transport, _, helper, _, calls = runtime
    transport.helpers = [HELPER]
    helper['State'].update(Status=state, Running=state == 'running')
    with pytest.raises(ValueError, match='HELPER_RESULT_UNKNOWN'):
        transport.run(ingress.create_request(TOKEN, 5))
    assert not calls
