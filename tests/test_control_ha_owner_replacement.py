import copy
import hashlib
import json
import os

import pytest

from scripts import control_ha_owner_replacement as replacement
from tests.test_control_ha_owner_activation_plan import inputs


class Docker:
    def __init__(self, original, proposed):
        self.items = {original['Id']: copy.deepcopy(original)}
        self.proposed = proposed
        self.writes = []
        self.fail = None

    def inspect(self, reference):
        return copy.deepcopy(next((item for item in self.items.values()
                                   if reference in (item['Id'], item['Name'][1:])), None))

    def request(self, method, path):
        assert method == 'GET'
        if path.startswith('/networks/'):
            return dict(Name='private-network', Driver='bridge', Scope='local', Ingress=False)
        return dict(Id=path[len('/images/'): -len('/json')].replace('%3A', ':'))

    def dispatch(self, operation, apply):
        self.writes.append(operation)
        if self.fail == (operation, 'before'):
            raise TimeoutError
        apply()
        if self.fail == (operation, 'after'):
            raise TimeoutError
        if self.fail == (operation, 'crash'):
            raise KeyboardInterrupt

    def create(self, name, payload):
        assert payload == replacement.payload(self.proposed)
        def apply():
            assert self.inspect(name) is None
            item = copy.deepcopy(self.proposed)
            item.update(Id='d' * 64, Name='/' + name, State=stopped_state())
            self.items[item['Id']] = item
        self.dispatch('create', apply)

    def rename(self, container, name):
        def apply():
            assert self.inspect(name) is None
            self.items[container]['Name'] = '/' + name
        operation = 'restore-name' if container != 'd' * 64 and '-ha-' not in name else (
            'retain' if container != 'd' * 64 else 'promote')
        self.dispatch(operation, apply)

    def remove(self, container):
        assert container == 'd' * 64
        self.dispatch('remove', lambda: self.items.pop(container))


def stopped_state():
    return dict(Status='exited', Running=False, Paused=False, Restarting=False, Dead=False, Pid=0)


@pytest.fixture
def prepared(inputs, tmp_path, monkeypatch):
    role = 'console'
    original = inputs['containers'][role]
    original['State'] = stopped_state()
    original['HostConfig']['Binds'] = [str(tmp_path / 'token') + ':/run/token:ro']
    (tmp_path / 'token').write_text('synthetic')
    original['Mounts'] = [dict(Type='bind', Source=str(tmp_path / 'token'), Destination='/run/token', RW=False)]
    original['NetworkSettings']['Networks']['private-network']['NetworkID'] = 'b' * 64
    gates = copy.deepcopy(replacement.plan.GATES)
    gates[role]['source'] = str(tmp_path / 'gate')
    (tmp_path / 'gate').mkdir(mode=0o700)
    monkeypatch.setattr(replacement.plan, 'GATES', gates)
    proposed = replacement.plan.proposed_config(replacement.configuration(original), inputs['candidates'][role], role)
    root = tmp_path / 'journal'
    root.mkdir(mode=0o700)
    replacement.prepare(root, original, proposed, role)
    pin = hashlib.sha256((root / 'manifest.json').read_bytes()).hexdigest()
    docker = Docker(original, proposed)
    return root, pin, docker, replacement.Replacement(root, docker, pin)


def test_exact_stopped_stage_revert_and_idempotency(prepared):
    root, pin, docker, transaction = prepared
    before = copy.deepcopy(docker.items)
    receipt = transaction.stage()
    assert receipt['candidate_has_name'] and not receipt['original_has_name']
    assert all(receipt[key] is False for key in ('data_restored', 'service_started', 'work_settlement_proven',
                                                'runtime_qualified', 'capture_permitted'))
    assert docker.writes == ['create', 'retain', 'promote']
    assert transaction.stage() == receipt
    restored = replacement.Replacement(root, docker, pin).revert()
    assert restored['original_has_name'] and restored['candidate_id'] is None
    assert docker.items == before
    assert docker.writes == ['create', 'retain', 'promote', 'remove', 'restore-name']
    assert transaction.revert() == restored
    with pytest.raises(ValueError, match='REVERT_ALREADY_SELECTED'):
        transaction.stage()
    assert all(os.stat(path).st_mode & 0o777 == 0o600 for path in root.iterdir())
    assert 'private-secret' not in json.dumps(receipt)


@pytest.mark.parametrize('operation', ['create', 'retain', 'promote', 'remove', 'restore-name'])
def test_accepted_write_with_lost_response_is_read_back_not_replayed(prepared, operation):
    root, pin, docker, transaction = prepared
    if operation in ('remove', 'restore-name'):
        transaction.stage()
    docker.fail = operation, 'after'
    result = transaction.revert() if operation in ('remove', 'restore-name') else transaction.stage()
    assert result['original_has_name'] if operation in ('remove', 'restore-name') else result['candidate_has_name']
    assert docker.writes.count(operation) == 1


@pytest.mark.parametrize('operation', ['create', 'retain', 'promote', 'remove', 'restore-name'])
def test_unknown_write_is_not_blindly_retried(prepared, operation):
    root, pin, docker, transaction = prepared
    if operation in ('remove', 'restore-name'):
        transaction.stage()
    docker.fail = operation, 'before'
    action = 'revert' if operation in ('remove', 'restore-name') else 'stage'
    with pytest.raises(ValueError, match='UNKNOWN_MUTATION_OUTCOME'):
        getattr(transaction, action)()
    docker.fail = None
    with pytest.raises(ValueError, match='UNKNOWN_MUTATION_OUTCOME'):
        getattr(replacement.Replacement(root, docker, pin), action)()
    assert docker.writes.count(operation) == 1


@pytest.mark.parametrize('operation', ['create', 'retain', 'promote', 'remove', 'restore-name'])
def test_process_crash_after_mutation_resumes_from_private_journal(prepared, operation):
    root, pin, docker, transaction = prepared
    if operation in ('remove', 'restore-name'):
        transaction.stage()
    docker.fail = operation, 'crash'
    action = 'revert' if operation in ('remove', 'restore-name') else 'stage'
    with pytest.raises(KeyboardInterrupt):
        getattr(transaction, action)()
    docker.fail = None
    result = getattr(replacement.Replacement(root, docker, pin), action)()
    assert result['original_has_name'] if action == 'revert' else result['candidate_has_name']
    assert docker.writes.count(operation) == 1


@pytest.mark.parametrize('change', ['running', 'paused', 'restarting', 'dead', 'pid', 'exec', 'config', 'mount', 'network'])
@pytest.mark.parametrize('target', ['original', 'candidate'])
def test_unsettled_runtime_or_config_drift_refuses_before_any_mutation(prepared, change, target):
    root, pin, docker, transaction = prepared
    if target == 'candidate':
        transaction.stage()
    item = docker.items['d' * 64 if target == 'candidate' else transaction.manifest['original_id']]
    if change in ('running', 'paused', 'restarting', 'dead'):
        item['State'][change.title()] = True
    elif change == 'pid':
        item['State']['Pid'] = 123
    elif change == 'exec':
        item['ExecIDs'] = ['unknown']
    elif change == 'config':
        item['Config']['Env'].append('UNREVIEWED=value')
    elif change == 'mount':
        item['Mounts'][0]['RW'] = True
    else:
        item['NetworkSettings']['Networks']['private-network']['NetworkID'] = 'c' * 64
    writes = docker.writes[:]
    with pytest.raises(ValueError):
        transaction.revert() if target == 'candidate' else transaction.stage()
    assert docker.writes == writes


def test_pending_markers_and_post_upgrade_data_are_not_rollback_targets(prepared):
    root, pin, docker, transaction = prepared
    transaction.stage()
    pending = root.parent / 'gate' / 'pending-operation'
    pending.write_bytes(b'unknown')
    data = root.parent / 'product.sqlite'
    data.write_bytes(b'new acknowledged product state')
    transaction.revert()
    assert pending.read_bytes() == b'unknown'
    assert data.read_bytes() == b'new acknowledged product state'


def test_gate_source_missing_refuses_without_docker_writes(prepared):
    root, pin, docker, transaction = prepared
    (root.parent / 'gate').rmdir()
    with pytest.raises(ValueError, match='BIND_SOURCE_MISSING'):
        transaction.stage()
    assert not docker.writes


@pytest.mark.parametrize('change', ['anonymous', 'inherit', 'auto-remove', 'host-network', 'namespace', 'endpoint', 'volume'])
def test_unsupported_docker_features_fail_closed(prepared, change):
    item = copy.deepcopy(prepared[-1].manifest['proposed'])
    if change == 'anonymous':
        item['HostConfig']['Mounts'] = [{'Type': 'volume', 'Target': '/unknown'}]
    elif change == 'inherit':
        item['HostConfig']['VolumesFrom'] = ['other']
    elif change == 'auto-remove':
        item['HostConfig']['AutoRemove'] = True
    elif change == 'host-network':
        item['HostConfig']['NetworkMode'] = 'host'
    elif change == 'namespace':
        item['HostConfig']['PidMode'] = 'container:other'
    elif change == 'endpoint':
        item['NetworkSettings']['Networks']['private-network']['Unreviewed'] = 1
    else:
        item['Config']['Volumes'] = {'/implicit': {}}
    with pytest.raises(ValueError):
        replacement.payload(item)


def test_dynamic_network_identity_is_not_copied_but_policy_is(prepared):
    expected = copy.deepcopy(prepared[-1].manifest['proposed'])
    network = expected['NetworkSettings']['Networks']['private-network']
    network.update(EndpointID='a' * 64, IPAddress='192.0.2.3', MacAddress='02:42:ac:10:00:01', DNSNames=['old-id'])
    actual = copy.deepcopy(expected)
    actual['NetworkSettings']['Networks']['private-network'].update(
        EndpointID='b' * 64, IPAddress='192.0.2.4', MacAddress='02:42:ac:10:00:02', DNSNames=['new-id'])
    replacement.equivalent(actual, expected)
    endpoint = replacement.payload(expected)['NetworkingConfig']['EndpointsConfig']['private-network']
    assert set(endpoint) & set(replacement.ENDPOINT_RUNTIME) == {'NetworkID'}
    assert endpoint['Aliases'] == ['private-alias']


def test_manifest_pin_and_private_record_permissions(prepared):
    root, pin, docker, transaction = prepared
    with pytest.raises(ValueError, match='INPUT_CHANGED'):
        replacement.Replacement(root, docker, '0' * 64)
    transaction.stage()
    (root / 'candidate.json').chmod(0o644)
    with pytest.raises(ValueError, match='PRIVATE_RECORD'):
        transaction.revert()


def test_unknown_create_blocks_revert_without_forgetting_the_journal(prepared):
    root, pin, docker, transaction = prepared
    docker.fail = 'create', 'before'
    with pytest.raises(ValueError):
        transaction.stage()
    with pytest.raises(ValueError, match='UNKNOWN_CREATE_OUTCOME'):
        transaction.revert()
    assert (root / 'create-intent.json').exists() and docker.writes == ['create']


@pytest.mark.parametrize('expected,actual,accepted', [(None, False, True), (False, None, False),
                                                    (True, False, False), (None, True, False)])
def test_only_observed_unset_to_false_oom_default_is_normalized(prepared, expected, actual, accepted):
    before = copy.deepcopy(prepared[-1].manifest['proposed'])
    after = copy.deepcopy(before)
    before['HostConfig']['OomKillDisable'] = expected
    after['HostConfig']['OomKillDisable'] = actual
    if accepted:
        replacement.equivalent(after, before)
    else:
        with pytest.raises(ValueError, match='EFFECTIVE_CONFIG_CHANGED'):
            replacement.equivalent(after, before)


def test_sudden_process_start_after_prepare_prevents_stage(prepared):
    root, pin, docker, transaction = prepared
    docker.items[transaction.manifest['original_id']]['State'].update(Status='running', Running=True, Pid=123)
    with pytest.raises(ValueError, match='STOPPED_REQUIRED'):
        transaction.stage()
    assert docker.writes == []


def test_candidate_missing_after_stage_never_recreates_or_claims_revert(prepared):
    root, pin, docker, transaction = prepared
    transaction.stage()
    docker.items.pop('d' * 64)
    writes = docker.writes[:]
    for action in ('stage', 'revert'):
        with pytest.raises(ValueError, match='CANDIDATE_REMOVED_EXTERNALLY'):
            getattr(transaction, action)()
    assert docker.writes == writes


def test_prepare_rejects_changes_outside_reviewed_delta(prepared, tmp_path):
    root, pin, docker, transaction = prepared
    journal = tmp_path / 'other'
    journal.mkdir(mode=0o700)
    original = transaction.original()
    after = copy.deepcopy(transaction.manifest['proposed'])
    after['Config']['Cmd'] = ['unreviewed']
    with pytest.raises(ValueError, match='UNREVIEWED_CONFIG_DELTA'):
        replacement.prepare(journal, original, after, 'console')
    assert list(journal.iterdir()) == []


def test_api_delete_never_forces_or_deletes_volumes(monkeypatch):
    calls = []
    docker = replacement.Docker()
    monkeypatch.setattr(docker, 'request', lambda *args: calls.append(args))
    docker.remove('a' * 64)
    assert calls == [('DELETE', '/containers/' + 'a' * 64 + '?force=false&v=false')]


def test_cli_status_and_revert_require_original_manifest_pin(prepared, monkeypatch, capsys):
    root, pin, docker, transaction = prepared
    transaction.stage()
    monkeypatch.setattr(replacement, 'Docker', lambda: docker)
    monkeypatch.setattr(replacement.sys, 'argv', ['replacement', 'status', '--journal', str(root)])
    assert replacement.main() == 1
    assert 'OWNER_REPLACEMENT_REFUSED' in capsys.readouterr().err
    before = docker.writes[:]
    monkeypatch.setattr(replacement.sys, 'argv', ['replacement', 'status', '--journal', str(root), '--journal-sha256', pin])
    assert replacement.main() == 0
    assert json.loads(capsys.readouterr().out)['candidate_has_name']
    assert docker.writes == before
    monkeypatch.setattr(replacement.sys, 'argv', ['replacement', 'revert', '--journal', str(root), '--journal-sha256', pin])
    assert replacement.main() == 0
    assert json.loads(capsys.readouterr().out)['original_has_name']


def test_cli_exclusive_journal_lock(prepared, monkeypatch, capsys):
    root, pin, docker, transaction = prepared
    monkeypatch.setattr(replacement, 'Docker', lambda: docker)
    monkeypatch.setattr(replacement.sys, 'argv', ['replacement', 'status', '--journal', str(root), '--journal-sha256', pin])
    descriptor = os.open(root / 'lock', os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        replacement.fcntl.flock(descriptor, replacement.fcntl.LOCK_EX | replacement.fcntl.LOCK_NB)
        assert replacement.main() == 1
    finally:
        os.close(descriptor)
    assert 'OWNER_REPLACEMENT_REFUSED' in capsys.readouterr().err and not docker.writes


def test_private_record_fifo_and_symlink_never_read(prepared):
    root, pin, docker, transaction = prepared
    os.mkfifo(root / 'fifo.json', 0o600)
    with pytest.raises(ValueError, match='PRIVATE_RECORD'):
        replacement.load(root, 'fifo')
    (root / 'symlink.json').symlink_to(root / 'manifest.json')
    with pytest.raises(ValueError, match='PRIVATE_PATH'):
        replacement.load(root, 'symlink')


@pytest.mark.parametrize('operation', ['retain', 'promote'])
def test_revert_cannot_race_an_unresolved_forward_rename(prepared, operation):
    root, pin, docker, transaction = prepared
    docker.fail = operation, 'before'
    with pytest.raises(ValueError, match='UNKNOWN_MUTATION_OUTCOME'):
        transaction.stage()
    writes = docker.writes[:]
    with pytest.raises(ValueError, match='UNKNOWN_FORWARD_MUTATION'):
        transaction.revert()
    assert docker.writes == writes and not (root / 'revert-intent.json').exists()
    docker.fail = None
    if operation == 'retain':
        docker.items[transaction.manifest['original_id']]['Name'] = '/' + transaction.manifest['retained']
    else:
        docker.items['d' * 64]['Name'] = '/' + transaction.manifest['name']
    assert transaction.revert()['original_has_name']
