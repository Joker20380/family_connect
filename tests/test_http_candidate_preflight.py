import contextlib
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import pytest

from scripts import friends_http_transition as transition
from test_friends_http_runtime import nginx_sections, port, request, running, runtime
from test_http_transition import Ingress, evidence_records, validate_delivery


@pytest.fixture
def evidence(tmp_path):
    value = transition.Evidence(tmp_path / 'receipts', 'candidate-preflight')
    yield value
    value.close()


@pytest.fixture
def candidate(runtime):
    artifact = runtime['artifact'] / 'friends-http.pyz'
    return transition.Candidate(18086, 'candidate', artifact, hashlib.sha256(artifact.read_bytes()).hexdigest())


@contextlib.contextmanager
def occupied(port=18086, address='127.0.0.1'):
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((address, port))
        listener.listen()
        yield listener


def test_policy_records_existing_owners_and_has_one_explicit_candidate_port(candidate, evidence):
    assert transition.PORT_OWNERS[18085] == 'friends_tcp_xray_api'
    assert transition.PORT_OWNERS[18084] == 'ordinary_friends_http'
    assert transition.PORT_OWNERS[18444] == 'restricted_bootstrap_broker'
    assert transition.CANDIDATE_PORTS == {18086}
    candidate.preflight(evidence)
    assert evidence_records(evidence)[-1]['classification'] == 'free_at_preflight'
    template = Path('deploy/friends/restricted/family-connect-friends-http-candidate.service').read_text()
    assert '--port 18086' in candidate.render_unit(template)
    assert '@CANDIDATE_PORT@' not in candidate.render_unit(template)


@pytest.mark.parametrize('port', [18085, 18084, 18082, 18444, 0, 443, 18087, True, '18086'])
def test_unauthorized_ports_never_reach_inspection(port, candidate):
    with pytest.raises(ValueError):
        transition.Candidate(port, 'candidate', candidate.artifact, candidate.sha256)


@pytest.mark.parametrize('address', ['127.0.0.1', '0.0.0.0', '127.0.0.2'])
def test_existing_listener_is_never_replaced(candidate, evidence, address):
    with occupied(address=address) as listener:
        with pytest.raises(transition.ProbeFailed):
            candidate.preflight(evidence)
        assert listener.fileno() >= 0
    assert not candidate.free
    assert evidence_records(evidence)[-1]['classification'] == 'occupied_other_or_unknown'


def test_previous_candidate_is_classified_but_never_reused(candidate, evidence):
    with occupied():
        with pytest.raises(transition.ProbeFailed):
            candidate.preflight(evidence, previous=(os.getpid(), transition.process_start(os.getpid())))
    assert evidence_records(evidence)[-1]['classification'] == 'occupied_previous_candidate'


def test_policy_and_evidence_failure_prevent_start(candidate, evidence, monkeypatch):
    calls = []
    arguments = callbacks(calls)
    with occupied():
        with pytest.raises(transition.ProbeFailed):
            transition.transaction(evidence, candidate=candidate, **arguments)
    assert calls == ['old_healthy']
    monkeypatch.setattr(evidence, 'persist', lambda record: (_ for _ in ()).throw(OSError()))
    with pytest.raises(OSError):
        transition.transaction(evidence, candidate=candidate, **arguments)
    assert calls == ['old_healthy', 'old_healthy']


def callbacks(calls):
    def action(name):
        def invoke(*args):
            calls.append(name)
            return True
        return invoke
    return {name: action(name) for name in ('old_healthy', 'prepare', 'ready', 'render', 'switch',
            'accept', 'owner_prewarm', 'commit', 'restore', 'restored', 'drain', 'stop_candidate', 'old_drained', 'retire_old')}


def launch(candidate, runtime):
    command = [sys.executable, '-I', str(candidate.artifact), '--root', str(runtime['state']),
               '--port', str(candidate.port)]
    process = subprocess.Popen(command, env=runtime['environment'], cwd=runtime['temporary'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + 5
    while process.poll() is None:
        if any(row['pids'] == {process.pid} for row in transition.listeners(candidate.port)):
            break
        assert time.monotonic() < deadline
        time.sleep(.02)
    return process


def stop(process):
    if process.poll() is None:
        process.terminate()
    process.wait(timeout=5)


def test_toctou_bind_collision_never_switches_or_kills_owner(candidate, evidence, runtime):
    calls = []
    arguments = callbacks(calls)
    held = []
    processes = []
    def start():
        calls.append('prepare')
        listener = socket.socket()
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(('127.0.0.1', candidate.port))
        listener.listen()
        held.append(listener)
        process = launch(candidate, runtime)
        processes.append(process)
        return process
    arguments['prepare'] = start
    try:
        with pytest.raises(transition.ProbeFailed):
            transition.transaction(evidence, candidate=candidate, **arguments)
        assert calls == ['old_healthy', 'prepare']
        assert held[0].fileno() >= 0 and processes[0].poll() is not None
        assert any(record.get('event') == 'failure' for record in evidence_records(evidence))
    finally:
        for process in processes:
            stop(process)
        for listener in held:
            listener.close()


@pytest.mark.parametrize('address', ['0.0.0.0', '127.0.0.2', '::'])
def test_wrong_binding_is_rejected_after_start(tmp_path, evidence, address):
    artifact = tmp_path / 'wrong-bind.pyz'
    artifact.write_text('import socket,sys,time\n'
                        'listener=socket.socket(socket.AF_INET6 if ":" in sys.argv[1] else socket.AF_INET)\n'
                        'listener.bind((sys.argv[1],int(sys.argv[3])))\n'
                        'listener.listen()\ntime.sleep(20)\n')
    candidate = transition.Candidate(18086, 'candidate', artifact, hashlib.sha256(artifact.read_bytes()).hexdigest())
    candidate.preflight(evidence)
    process = subprocess.Popen([sys.executable, '-I', str(artifact), address, '--port', '18086'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 5
        while not transition.listeners(18086):
            assert process.poll() is None and time.monotonic() < deadline
            time.sleep(.02)
        with pytest.raises(transition.ProbeFailed, match='loopback'):
            candidate.capture(process)
    finally:
        stop(process)


def test_route_ownership_cannot_conflate_static_status(candidate, evidence):
    assert transition.ROUTES['status'] == dict(method='GET', path='/status/server-load.json', expected=200, owner='nginx_static')
    assert set(transition.DIRECT_PROBES) == set(transition.EXTERNAL_PROBES) - {'status'}
    assert all(transition.ROUTES[label]['owner'] == 'friends_application' for label in transition.DIRECT_PROBES)
    session = transition.Session('http://127.0.0.1:18086', evidence, layer='direct_candidate',
                                 candidate=candidate, generation=candidate.generation)
    with pytest.raises(ValueError, match='Ingress-owned'):
        session.probe('status')
    assert not evidence_records(evidence)
    with pytest.raises(transition.ProbeFailed):
        candidate.upstream()


@pytest.mark.parametrize('interval', [0, .9])
def test_direct_probes_cannot_disable_pacing(candidate, evidence, interval):
    with pytest.raises(ValueError):
        transition.Session('http://127.0.0.1:18086', evidence, layer='direct_candidate',
                           candidate=candidate, generation=candidate.generation, interval=interval)


def test_direct_process_and_artifact_identity_are_required(candidate, runtime, evidence):
    candidate.preflight(evidence)
    process = launch(candidate, runtime)
    try:
        candidate.capture(process)
        candidate.verify()
        assert request(candidate.port, '/status/server-load.json', 'GET')[0] == 501
        candidate.start = 'incorrect-start'
        with pytest.raises(transition.ProbeFailed, match='generation'):
            candidate.verify()
        candidate.start = transition.process_start(process.pid)
        candidate.sha256 = '0' * 64
        with pytest.raises(transition.ProbeFailed, match='artifact'):
            candidate.verify()
    finally:
        stop(process)


def test_public_transaction_rejects_incomplete_direct_matrix(candidate, runtime, evidence):
    calls = []
    arguments = callbacks(calls)
    processes = []
    def prepare():
        calls.append('prepare')
        process = launch(candidate, runtime)
        processes.append(process)
        return process
    def cleanup(process):
        calls.append('stop_candidate')
        assert any(record.get('event') == 'failure' for record in evidence_records(evidence))
        stop(process)
    arguments.update(prepare=prepare, stop_candidate=cleanup)
    try:
        with pytest.raises(transition.ProbeFailed):
            transition.transaction(evidence, candidate=candidate, **arguments)
        assert calls == ['old_healthy', 'prepare', 'ready', 'stop_candidate']
    finally:
        for process in processes:
            stop(process)


def test_old_health_failure_is_pre_mutation(candidate, evidence):
    calls = []
    arguments = callbacks(calls)
    arguments['old_healthy'] = lambda: False
    with pytest.raises(transition.ProbeFailed):
        transition.transaction(evidence, candidate=candidate, **arguments)
    assert not calls and evidence_records(evidence)[-1]['event'] == 'old_generation_unhealthy'


def test_source_unit_route_and_immutable_archive_guards(candidate):
    assert candidate.sha256 == os.environ['FC_TEST_HTTP_SHA256']
    unit = Path('deploy/friends/restricted/family-connect-friends-http-candidate.service').read_text()
    assert unit.count('@CANDIDATE_PORT@') == 1 and '18085' not in unit
    ordinary, status = nginx_sections()
    assert 'alias /etc/fc/server-load/snapshot.json;' in status and 'proxy_pass' not in status
    assert 'proxy_pass http://127.0.0.1:18084;' in ordinary
    source = Path(transition.__file__).read_text()
    assert 'systemctl' not in source and "['ssh'" not in source and 'SO_REUSEPORT' not in source


@pytest.mark.parametrize('failure', [None, 'accept', 'restore', 'render', 'incomplete_external', 'owner', 'incomplete_owner', 'old_drain'])
def test_verified_blue_green_direct_and_external_contracts(candidate, runtime, evidence, failure):
    old = dict(runtime, environment={key: value for key, value in runtime['environment'].items()
                                    if key != 'FC_FRIENDS_RESTRICTED_DIR'})
    calls = []
    processes = []
    with running(old), Ingress(runtime, old['backend'], enabled=False, generation='old') as ingress:
        external = transition.Session(ingress.origin, evidence, generation='old')
        def old_healthy():
            return all(request(old['backend'],path)[0]==400 for path in ('/friends/challenge','/friends/chat/challenge'))
        def prepare():
            calls.append('prepare')
            process = launch(candidate, runtime)
            processes.append(process)
            return process
        def ready():
            calls.append('ready')
            fixture_runtime=dict(runtime,backend=port())
            fixture_runtime['command']=runtime['command'][:-1]+[str(fixture_runtime['backend'])]
            with running(fixture_runtime):
                fixture=transition.Session('http://127.0.0.1:'+str(fixture_runtime['backend']),evidence,layer='server_contract_fixture')
                contract=fixture.fixture_matrix(candidate.artifact,runtime['identities'],
                    lambda value:runtime['canary'].prove_transport_key(value['challenge']),lambda value:validate_delivery(runtime,value))
            direct = transition.Session('http://127.0.0.1:' + str(candidate.port), evidence,
                                        layer='direct_candidate', candidate=candidate, generation=candidate.generation)
            direct.server_matrix(runtime['identities']['non_canary'],fixture=contract,
                                 current_authority=lambda:bool(runtime['restricted']._trust(int(time.time()))))
            return True
        def render(upstream):
            calls.append('render')
            assert upstream == 'http://127.0.0.1:18086' and candidate.direct_pass
            ordinary, status = nginx_sections()
            restricted = Path('deploy/friends/restricted/nginx-location.conf').read_text()
            template = (ordinary + restricted).replace('http://127.0.0.1:18084', '@FRIENDS_HTTP_UPSTREAM@')
            rendered = candidate.render_upstreams(template)
            assert rendered.count('http://127.0.0.1:18086') == 2
            assert 'proxy_pass' not in status
            validation = Ingress(runtime, candidate.port, generation=candidate.generation)
            validation.write()
            assert rendered.strip().splitlines()[0] in validation.config.read_text()
            return failure != 'render'
        def switch():
            calls.append('switch')
            ingress.reload(candidate.port, True, candidate.generation)
            external.generation = candidate.generation
            external.candidate = candidate
        def accept():
            calls.append('accept')
            if failure == 'incomplete_external':
                return True
            if failure in ('accept', 'restore'):
                return False
            external.server_matrix(runtime['identities']['non_canary'])
            return True
        def owner_prewarm(product):
            calls.append('owner_prewarm')
            assert processes[0].poll() is None and request(old['backend'],'/friends/challenge')[0]==400
            if failure=='incomplete_owner':return True
            from test_owner_proof_handoff import product_observation
            app,server=product_observation(product)
            if failure=='owner':app['import_result']='failed'
            return product.observe(app,server)
        def restore():
            calls.append('restore')
            assert any(record.get('event') == 'failure' for record in evidence_records(evidence))
            ingress.reload(old['backend'], False, 'old')
            external.generation, external.candidate = 'old', None
        def restored():
            calls.append('restored')
            for label in ('status','ordinary_challenge','ordinary_chat'):
                external.probe(label)
            return False if failure == 'restore' else old_healthy()
        def stop_candidate(process):
            calls.append('stop_candidate')
            assert failure == 'render' or calls[-2] == 'drain'
            stop(process)
        def action(name):
            def invoke():
                calls.append(name)
                return not (name == 'old_drained' and failure == 'old_drain')
            return invoke
        try:
            arguments = dict(candidate=candidate, old_healthy=old_healthy, prepare=prepare, ready=ready,
                             render=render, switch=switch, accept=accept, owner_prewarm=owner_prewarm, commit=action('commit'), restore=restore,
                             restored=restored, drain=action('drain'), stop_candidate=stop_candidate,
                             old_drained=action('old_drained'), retire_old=action('retire_old'))
            if failure:
                with pytest.raises(transition.ProbeFailed):
                    transition.transaction(evidence, **arguments)
                assert 'retire_old' not in calls
                if failure == 'restore':
                    assert 'stop_candidate' not in calls and processes[0].poll() is None
                elif failure in ('accept', 'incomplete_external', 'owner', 'incomplete_owner'):
                    assert calls[-4:] == ['restore', 'restored', 'drain', 'stop_candidate']
                    if failure in ('owner','incomplete_owner'):
                        assert 'commit' not in calls
                        assert any(record.get('event')=='owner_prewarm_failed' and record.get('receipt_class')=='real_owner_product'
                                   for record in evidence_records(evidence))
                elif failure == 'old_drain':
                    assert 'commit' in calls and 'restore' not in calls and processes[0].poll() is None
                else:
                    assert 'switch' not in calls
            else:
                assert transition.transaction(evidence, **arguments)
                assert calls == ['prepare', 'ready', 'render', 'switch', 'accept', 'owner_prewarm', 'commit', 'old_drained', 'retire_old']
            assert request(old['backend'], '/friends/challenge')[0] == 400
            records = [record for record in evidence_records(evidence) if 'probe_id' in record]
            direct = [record for record in records if record['layer'] == 'direct_candidate']
            assert len(direct) == 4 and all(record['route_owner'] == 'friends_application' for record in direct)
            assert all(record['candidate_port'] == 18086 and record['active_generation'] == 'candidate' for record in direct)
            assert all(record['rate_limit_class'] == 'not_applicable' and record['response_origin'] == 'direct_application' for record in direct)
            assert all(record['valid'] for record in records)
            if failure in (None, 'old_drain'):
                switched = [record for record in records if record['layer'] == 'ingress_external' and record['active_generation'] == 'candidate']
                assert [record['status'] for record in switched] == [200, 400, 400, 400, 403]
                assert switched[0]['route_owner'] == 'nginx_static' and switched[0]['response_origin'] == 'ingress'
                assert all(record['response_origin'] == 'upstream' for record in switched[1:])
            assert not any(secret in json.dumps(records) for secret in ('private_key', 'public_identity', 'chat_signature'))
        finally:
            for process in processes:
                stop(process)
