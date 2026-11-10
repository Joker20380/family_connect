import io
import json
import tarfile
import zipfile

import pytest

from scripts import prepare_ru_replacement as package
from scripts.ru_replacement_qualification import call_summary, qualify, registration_sets
from scripts.run_ru_replacement import verify_distribution


def test_registration_overlap_and_unique_rules():
    groups = registration_sets(list(range(63)))
    assert tuple(map(len, groups)) == (20, 49, 5)
    assert len(set(groups[0]) & set(groups[1])) == 6
    assert set().union(*map(set, groups)) == set(range(63))
    assert all(len(set(group)) == len(group) for group in groups)
    with pytest.raises(ValueError):
        registration_sets([0]*63)
    with pytest.raises(ValueError):
        registration_sets(list(range(62)))


def test_input_digest_and_symlink_rejected(tmp_path):
    path = tmp_path/'node'
    path.write_bytes(b'accepted')
    assert package.checked(path, package.digest(b'accepted')) == b'accepted'
    with pytest.raises(ValueError, match='HASH_MISMATCH'):
        package.checked(path, package.digest(b'other'))
    link = tmp_path/'link'
    link.symlink_to(path)
    with pytest.raises(ValueError, match='REGULAR_INPUT'):
        package.checked(link, package.digest(b'accepted'))


@pytest.mark.parametrize('name,kind', [('../escape', tarfile.REGTYPE), ('inventory.json', tarfile.SYMTYPE)])
def test_archive_rejects_paths_and_links(name, kind):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as archive:
        member = tarfile.TarInfo(name)
        member.type = kind
        archive.addfile(member)
    with pytest.raises(ValueError):
        package.validate_bundle(output.getvalue(), dict(files={}))


def test_distribution_detects_modified_inputs(tmp_path):
    path = tmp_path/'payload'
    path.write_bytes(b'accepted')
    (tmp_path/'distribution-inventory.json').write_text(json.dumps(dict(files={
        'payload': package.digest(path.read_bytes())})))
    verify_distribution(tmp_path)
    path.write_bytes(b'changed')
    with pytest.raises(ValueError, match='HASH_MISMATCH'):
        verify_distribution(tmp_path)


def test_runtime_pair_comes_from_immutable_bundle_not_mutable_fixture(tmp_path, monkeypatch):
    accepted = tmp_path/'accepted'
    accepted.mkdir()
    fixture = accepted/'systemd-kit-check'
    fixture.mkdir()
    node = io.BytesIO()
    with zipfile.ZipFile(node, 'w') as archive:
        archive.writestr('control/friends/transport_gateway.py', b'accepted module')
    members = {'paid-transport.pyz': node.getvalue(), 'family-connect-paid-watch.service': b'Restart=no'}
    inventory = dict(source_sha=package.SOURCE, files={name: package.digest(raw) for name, raw in members.items()},
        after_modules={'control/friends/transport_gateway.py': package.digest(b'accepted module')})
    raw_inventory = json.dumps(inventory).encode()
    (accepted/'full-inventory.json').write_bytes(raw_inventory)
    monkeypatch.setattr(package, 'INVENTORY_SHA', package.digest(raw_inventory))
    members['inventory.json'] = raw_inventory
    with tarfile.open(accepted/package.BUNDLE, 'w:gz') as archive:
        for name, raw in members.items():
            member = tarfile.TarInfo(name)
            member.size = len(raw)
            archive.addfile(member, io.BytesIO(raw))
    monkeypatch.setattr(package, 'BUNDLE_SHA', package.digest((accepted/package.BUNDLE).read_bytes()))
    pins = {}
    for name in package.KIT_FILES:
        raw = members.get(name, b'qualified helper')
        pins[name] = package.digest(raw)
        (fixture/name).write_bytes(b'later unrelated node' if name == 'paid-transport.pyz' else raw)
    raw_receipt = json.dumps(dict(result='PASS', kit=pins)).encode()
    (accepted/'systemd-qualified.private.json').write_bytes(raw_receipt)
    monkeypatch.setattr(package, 'QUALIFICATION_SHA', package.digest(raw_receipt))
    monkeypatch.setattr(package, 'SOURCE_FILES', ())
    destination = tmp_path/'result'
    package.prepare(accepted, destination)
    assert (destination/'kit/paid-transport.pyz').read_bytes() == node.getvalue()
    assert (fixture/'paid-transport.pyz').read_bytes() == b'later unrelated node'
    (fixture/'awg-gateway.py').write_bytes(b'unknown gateway')
    with pytest.raises(ValueError, match='HASH_MISMATCH'):
        package.prepare(accepted, tmp_path/'rejected')
    assert not (tmp_path/'rejected').exists()


def test_call_metrics_do_not_sum_nested_intervals():
    journal = json.dumps(dict(transport_progress=dict(calls=[dict(kind='tcp-query', role=None,
        duration=3.5, remaining=7, completed=True, process=dict(
            spawn=dict(duration=1), communicate=dict(duration=2.5)))]))).encode()
    row = call_summary(journal)['tcp-query:None']
    assert row['maximum_seconds'] == 3.5
    assert row['process_maxima'] == dict(spawn=1, communicate=2.5)
    assert row['count'] == 1 and row['incomplete'] == 0
    with pytest.raises(AssertionError):
        call_summary(b'no progress')


def test_bounded_profile_plan_without_executing_engines():
    class Clock:
        now = 10000

        def time(self):
            return self.now

        monotonic = time

        def sleep(self, seconds):
            assert 0 <= seconds <= 124
            self.now += seconds

    clock = Clock()
    state = dict(end=0, valid=0, revision=0, revoked=False)
    nodes = ('gateway-ru', 'nl-amsterdam-1', 'nl-amsterdam-2')
    actions = []

    def operator(kind, event, **values):
        if kind == 'activate':
            assert values['end'] >= state['end']
            state['end'] = values['end']
        else:
            assert kind == 'revoke'
            state['revoked'] = True
        state['revision'] += 1

    def cycle():
        state['valid'] = min(clock.now+120, state['end'])
        return dict.fromkeys(nodes, 'applied')

    def inner(node, action, document=None):
        actions.append((node, action))
        if action == 'info':
            return dict(services={'same': 'active'}, state=dict(records={'paid': dict(decision=dict(
                paid_until=state['end'], valid_until=state['valid'], revision=state['revision']))}))
        if action in ('probe', 'dns-probe'):
            allowed = not state['revoked'] and clock.now < state['valid']
            assert document['allowed'] == allowed
        return dict(simulated=True)

    receipt = dict(checks={})
    qualify(receipt, inner, operator, cycle, nodes, 'paid', clock=clock)
    assert receipt['checks']['ordinary_window']['seconds'] == 600
    assert clock.now-10000 < 1000
    assert actions.count(('gateway-ru', 'restart')) == 1
    assert not any('fault' in action for node, action in actions)


def test_failed_cycle_stops_profile_without_retry():
    calls = []

    def failed_cycle():
        calls.append(1)
        return {'gateway-ru': 'unavailable'}

    with pytest.raises(AssertionError, match='STOP_NO_RETRY'):
        qualify(dict(checks={}), lambda *args: {}, lambda *args, **kwargs: None,
            failed_cycle, ('gateway-ru',), 'paid')
    assert len(calls) == 1
