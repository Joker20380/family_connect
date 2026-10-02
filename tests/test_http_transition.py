from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import subprocess
import sys
import threading
import time

from cryptography import x509
import pytest

from control.friends.restricted import delegation, directory
from scripts.friends_http_transition import Evidence, ProbeFailed, Session, response_metadata, transaction
from test_friends_http_runtime import ROOT, nginx_sections, port, request, running, runtime
from test_friends_http_evidence import responder


CONTRACT = ROOT / 'deploy/friends/restricted'
PIN = '460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71'


class Ingress:
    def __init__(self, material, backend, enabled=True, generation='candidate'):
        executable = os.environ.get('FC_TEST_NGINX')
        if not executable:
            pytest.skip('FC_TEST_NGINX required for real transition reproduction')
        self.material, self.backend, self.enabled, self.generation = material, backend, enabled, generation
        self.root = material['temporary'] / ('ingress-' + str(port()))
        self.root.mkdir()
        self.port = port()
        self.origin = 'http://127.0.0.1:' + str(self.port)
        self.config = self.root / 'nginx.conf'
        self.command = shlex.split(executable) + ['-p', str(self.root), '-c', str(self.config)]
        self.process = None

    def write(self):
        assert re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', self.generation)
        snapshot = self.root / 'snapshot.json'
        snapshot.write_text('{"version":1,"gateways":[]}')
        ordinary, status = nginx_sections()
        status = status.replace('/etc/fc/server-load/snapshot.json', str(snapshot))
        headers = (CONTRACT / 'http-transition-headers.conf').read_text()
        status = status.replace('add_header Cache-Control', headers + '\nadd_header Cache-Control')
        restricted = (CONTRACT / 'nginx-location.conf').read_text() if self.enabled else ''
        routes = (status + ordinary + restricted).replace('127.0.0.1:18084', '127.0.0.1:' + str(self.backend))
        template = (ROOT / 'deploy/product-https/nginx.conf.template').read_text()
        limits = '\n'.join(line.strip() for line in template.splitlines()
                           if line.strip().startswith(('map ', 'limit_req_zone ', 'limit_conn_zone ', 'limit_req_status ', 'limit_conn_status ')))
        server_limits = '\n'.join(line.strip() for line in template.splitlines()
                                  if line.strip().startswith(('limit_req zone=', 'limit_conn ')))
        content = ('pid ' + str(self.root/'nginx.pid') + ';\nerror_log ' + str(self.root/'errors.log') + ' info;\n'
                   'events {}\nhttp { access_log off; client_body_temp_path ' + str(self.root/'body') + ';'
                   + ''.join(kind + '_temp_path ' + str(self.root/kind) + ';' for kind in ('proxy', 'fastcgi', 'uwsgi', 'scgi'))
                   + limits + '\nmap $server_name $fc_http_generation {default ' + self.generation + ';}\n'
                   + (CONTRACT/'http-transition-trace.conf').read_text()
                   + '\nserver {listen 127.0.0.1:' + str(self.port) + ';server_name localhost;\n' + server_limits
                   + '\naccess_log ' + str(self.root/'probes.jsonl') + ' fc_probe if=$fc_probe_log;\n'
                   + 'add_header Cache-Control no-store always;add_header X-Content-Type-Options nosniff always;'
                   + headers + routes + '\nlocation / {return 404;} }}')
        pending = self.config.with_suffix('.pending')
        pending.write_text(content)
        check = self.command[:-1] + [str(pending), '-t']
        assert subprocess.run(check, capture_output=True, timeout=5).returncode == 0, 'nginx config rejected'
        pending.replace(self.config)

    def reload(self, backend, enabled, generation):
        previous = self.children()
        self.backend, self.enabled, self.generation = backend, enabled, generation
        self.write()
        subprocess.run(self.command + ['-s', 'reload'], check=True, capture_output=True, timeout=5)
        deadline = time.monotonic() + 5
        while not self.children() or self.children() & previous:
            assert time.monotonic() < deadline
            time.sleep(.01)

    def children(self):
        return set((Path('/proc')/str(self.process.pid)/'task'/str(self.process.pid)/'children').read_text().split())

    def __enter__(self):
        self.write()
        self.process = subprocess.Popen(self.command + ['-g', 'daemon off;'], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        deadline = time.monotonic() + 5
        while True:
            assert self.process.poll() is None, 'nginx startup failed'
            try:
                with socket.create_connection(('127.0.0.1', self.port), timeout=.1):
                    return self
            except OSError:
                assert time.monotonic() < deadline
                time.sleep(.01)

    def __exit__(self, *unused):
        self.process.terminate()
        self.process.communicate(timeout=5)


def evidence_records(evidence):
    return [json.loads(path.read_text()) for path in sorted(evidence.directory.glob('*.json'))]


def record_measurement(material, label, record):
    output = os.environ.get('FC_TRANSITION_RESULTS')
    if output:
        path = Path(output)
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (path/(label+'.json')).open('x') as stream:
            json.dump(record, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())


@pytest.mark.parametrize('lane', ['matrix', 'observer'])
def test_exact_attempt9_cadence_reproduces_shared_per_ip_limit(runtime, lane):
    assert hashlib.sha256((runtime['artifact']/'friends-http.pyz').read_bytes()).hexdigest() == PIN
    fixtures = json.loads((ROOT/'tests/fixtures/http_attempt9_transition.json').read_text())[lane]
    fixtures = [record for record in fixtures if record['transport_error'] != 'interrupted']
    reference = datetime.fromisoformat(fixtures[0]['timestamp']).timestamp()
    with running(runtime), Ingress(runtime, runtime['backend']) as ingress:
        started = time.monotonic()
        observed = []
        for record in fixtures:
            offset = datetime.fromisoformat(record['timestamp']).timestamp() - reference
            time.sleep(max(0, started + offset - time.monotonic()))
            label = record['label']
            path = {'status':'/status/server-load.json','ordinary_challenge':'/friends/challenge',
                    'ordinary_chat':'/friends/chat/challenge','restricted_malformed':'/friends/restricted-readiness/challenge',
                    'restricted_non_canary':'/friends/restricted-readiness/challenge'}[label]
            body = runtime['identities']['non_canary'][0] if label == 'restricted_non_canary' else {}
            direct = None if label == 'status' else request(runtime['backend'], path, body=body)[0]
            status, _ = request(ingress.port, path, 'GET' if label == 'status' else 'POST', body)
            observed.append(dict(offset=offset, drift_ms=round((time.monotonic()-started-offset)*1000,3),
                                 label=label, historical_status=record['status'], direct_status=direct, ingress_status=status))
        logs = (ingress.root/'errors.log').read_text()
        zones = re.findall(r'limiting requests.*?by zone "([a-z_]+)"', logs)
        assert 'per_ip' in zones and set(zones) == {'per_ip'}
        assert any(record['ingress_status'] == 429 for record in observed)
        if lane == 'matrix':
            assert [record['ingress_status'] for record in observed] == [record['historical_status'] for record in observed]
        else:
            assert sum(record['ingress_status'] == 429 for record in observed) == 7
        assert all(record['direct_status'] in (None, 400, 403) for record in observed)
        assert 'limiting connections' not in logs
        record_measurement(runtime, 'cadence-'+lane, dict(observed=observed, rejected_zones=zones,
                           historical_exact_bucket_known=False, other_traffic_simulated=False))


def test_stop_before_start_reproduces_refused_socket_and_nginx_502(runtime):
    manager = running(runtime)
    manager.__enter__()
    try:
        with Ingress(runtime, runtime['backend'], enabled=False, generation='old') as ingress:
            assert request(runtime['backend'], '/friends/chat/challenge')[0] == 400
            manager.__exit__(None, None, None)
            with pytest.raises(ConnectionRefusedError):
                request(runtime['backend'], '/friends/chat/challenge')
            status, _ = request(ingress.port, '/friends/chat/challenge')
            assert status == 502
            logs = (ingress.root/'errors.log').read_text()
            assert 'connect() failed (111: Connection refused) while connecting to upstream' in logs
            with running(runtime):
                assert request(runtime['backend'], '/friends/chat/challenge')[0] == 400
                ingress.reload(runtime['backend'], True, 'candidate')
                assert request(ingress.port, '/friends/chat/challenge')[0] == 400
            record_measurement(runtime, 'stop-start', dict(before=400, direct_gap='connection_refused',
                               ingress_gap=502, nginx_error='connect_refused_111', after=400,
                               historical_kernel_error_recorded=False))
    finally:
        manager.__exit__(None, None, None)


def validate_delivery(material, value):
    now = int(time.time())
    import base64
    anchor = base64.b64decode((material['state']/'anchor.pub').read_bytes())
    trust, authority = delegation(value['issuer'], anchor, now)
    certificate = x509.load_pem_x509_certificate(value['certificate'].encode())
    certificate.verify_directly_issued_by(authority)
    crl = x509.load_pem_x509_crl(value['revocations'].encode())
    assert crl.is_signature_valid(authority.public_key())
    assert crl.get_revoked_certificate_by_serial_number(certificate.serial_number) is None
    assert value['device'] == material['canary'].reference
    assert certificate.public_key().public_bytes_raw() == base64.b64decode(material['canary'].public_identity)[32:]
    assert now < value['expires_at'] <= min(certificate.not_valid_after_utc.timestamp(), crl.next_update_utc.timestamp())
    directory(json.dumps(value['directory']).encode(), trust['family'], trust['gateway'])
    assert value['minimum_crl'] == 1 and value['revision'] == 1
    return True


def test_readiness_first_switch_and_three_paced_complete_matrices(runtime):
    old = dict(runtime, environment={key:value for key,value in runtime['environment'].items() if key != 'FC_FRIENDS_RESTRICTED_DIR'})
    candidate = dict(runtime, backend=port())
    candidate['command'] = runtime['command'][:-1] + [str(candidate['backend'])]
    evidence = Evidence(runtime['temporary']/'transaction-receipts', 'isolated-switch')
    with running(old), Ingress(runtime, old['backend'], enabled=False, generation='old') as ingress:
        session = Session(ingress.origin, evidence, generation='old')
        for label in ('status','ordinary_challenge','ordinary_chat'):
            session.probe(label)
        session.probe('restricted_malformed', expected=404)
        manager = running(candidate)
        def ready():
            assert request(old['backend'], '/friends/challenge')[0] == 400
            assert request(candidate['backend'], '/friends/challenge')[0] == 400
            assert request(candidate['backend'], '/friends/chat/challenge')[0] == 400
            assert request(candidate['backend'], '/friends/restricted-readiness/challenge')[0] == 400
            assert request(candidate['backend'], '/friends/restricted-readiness/challenge',body=runtime['identities']['non_canary'][0])[0] == 403
            status,raw=request(candidate['backend'],'/friends/restricted-readiness/challenge',body=runtime['identities']['canary'])
            assert status==200
            proof=runtime['canary'].prove_transport_key(json.loads(raw)['challenge'])
            status,raw=request(candidate['backend'],'/friends/restricted-readiness',body=proof)
            assert status==200 and validate_delivery(runtime,json.loads(raw))
            return True
        def switch():
            ingress.reload(candidate['backend'], True, 'candidate')
            session.generation = 'candidate'
        def accept():
            for iteration in range(3):
                session.matrix(runtime['identities'], lambda value: runtime['canary'].prove_transport_key(value['challenge']),
                               lambda value: validate_delivery(runtime, value))
            return True
        try:
            assert transaction(evidence, prepare=manager.__enter__, ready=ready, switch=switch, accept=accept,
                               commit=lambda: None, restore=lambda: ingress.reload(old['backend'], False, 'old'),
                               restored=lambda: True, drain=lambda: True,
                               stop_candidate=lambda: manager.__exit__(None,None,None))
            records = evidence_records(evidence)
            probes = [record for record in records if 'probe_id' in record]
            assert len(probes) == 25 and all(record['valid'] for record in probes)
            assert all(record['status'] not in (429,502) for record in probes)
            assert sum(record['label']=='restricted_readiness' for record in probes) == 3
            assert 'limiting requests' not in (ingress.root/'errors.log').read_text()
            logged = [json.loads(line) for line in (ingress.root/'probes.jsonl').read_text().splitlines()]
            assert {record['probe_id'] for record in probes} <= {record['probe_id'] for record in logged}
            assert all(set(record) == {'probe_id','timestamp','generation','status','upstream_status','upstream_connect_seconds','upstream_header_seconds','request_limit','connection_limit'} for record in logged)
            assert request(old['backend'], '/friends/challenge')[0] == 400
            record_measurement(runtime, 'paced-matrix', dict(pre_switch=[200,400,400,404], complete_matrices=3,
                               probe_count=len(probes), statuses=[record['status'] for record in probes],
                               old_listener_kept=True, sensitive_fields_logged=False))
        finally:
            manager.__exit__(None,None,None)
            evidence.close()


@pytest.mark.parametrize('stage', ['prepare','ready','switch','accept','commit'])
def test_transaction_failure_order_is_receipt_restore_drain_stop(tmp_path, stage):
    evidence = Evidence(tmp_path/'evidence', 'failure')
    order = []
    def action(name, result=None):
        def invoke():
            order.append(name)
            if name == stage:
                raise RuntimeError('failure')
            if name in ('restore','stop_candidate'):
                assert any(record.get('event')=='failure' for record in evidence_records(evidence))
            return result
        return invoke
    try:
        with pytest.raises(RuntimeError):
            transaction(evidence, **{name:action(name, True if name in ('ready','accept','restored','drain') else None)
                                    for name in ('prepare','ready','switch','accept','commit','restore','restored','drain','stop_candidate')})
        if stage in ('switch','accept','commit'):
            assert order[-4:] == ['restore','restored','drain','stop_candidate']
        else:
            assert 'restore' not in order and order[-1] == 'stop_candidate'
    finally:
        evidence.close()


def test_uncertain_restoration_never_stops_referenced_candidate(tmp_path):
    evidence = Evidence(tmp_path/'evidence', 'uncertain')
    stopped=[]
    try:
        with pytest.raises(ProbeFailed):
            transaction(evidence, prepare=lambda:None, ready=lambda:True, switch=lambda:None,
                        accept=lambda:False, commit=lambda:None, restore=lambda:None, restored=lambda:False,
                        drain=lambda:True, stop_candidate=lambda:stopped.append(True))
        assert not stopped
        assert evidence_records(evidence)[-1]['candidate_retained']
    finally:
        evidence.close()


def test_response_metadata_does_not_guess_origin_or_capture_headers():
    probe_id='a'*32
    assert response_metadata({'Server':'nginx'},probe_id)['response_origin']=='unknown'
    headers={'X-FC-Ingress':'nginx','X-FC-Probe-ID':probe_id,'X-FC-Generation':'candidate',
             'X-FC-Request-Limit':'REJECTED','X-FC-Upstream-Status':'-', 'Authorization':'never-persist'}
    record=response_metadata(headers,probe_id)
    assert record['response_origin']=='ingress' and record['rate_limit_class']=='request_rejected'
    assert record['rate_limit_rule_id']=='request_policy:per_ip_or_global_rate'
    assert 'never-persist' not in json.dumps(record)
    headers.update({'X-FC-Request-Limit':'PASSED','X-FC-Upstream-Status':'502'})
    assert response_metadata(headers,probe_id)['upstream_error']=='proxy_failure_unresolved'
    headers['X-FC-Probe-ID']='wrong'
    assert response_metadata(headers,probe_id)['active_generation'] is None


def test_session_refuses_unpaced_or_unprotected_origins(tmp_path):
    evidence=Evidence(tmp_path/'evidence','policy')
    try:
        with pytest.raises(ValueError):Session('http://example.test',evidence)
        with pytest.raises(ValueError):Session('http://127.0.0.1',evidence,interval=.1)
    finally:
        evidence.close()


def test_user_like_ordinary_challenges_do_not_hit_limits(runtime):
    evidence=Evidence(runtime['temporary']/'user-cadence','user-like')
    try:
        with running(runtime), Ingress(runtime,runtime['backend']) as ingress:
            session=Session(ingress.origin,evidence,generation='candidate',interval=2)
            body=dict(runtime['identities']['canary'],purpose='ru',invitation='')
            for iteration in range(3):
                session.probe('ordinary_challenge',body,expected=200)
            assert [record['status'] for record in evidence_records(evidence)]==[200]*3
            record_measurement(runtime,'user-like',dict(interval_seconds=2,statuses=[200]*3,
                                real_user_aggregate_traffic_known=False))
    finally:
        evidence.close()


def test_three_live_switches_keep_paced_inflight_ordinary_requests_healthy(runtime):
    candidate=dict(runtime,backend=port())
    candidate['command']=runtime['command'][:-1]+[str(candidate['backend'])]
    evidence=Evidence(runtime['temporary']/'switch-traffic','switch-overlap')
    errors=[]
    with running(runtime), running(candidate), Ingress(runtime,runtime['backend'],generation='old') as ingress:
        session=Session(ingress.origin,evidence)
        def traffic():
            try:
                for iteration in range(7):session.probe('ordinary_challenge')
            except BaseException as error:errors.append(type(error).__name__)
        worker=threading.Thread(target=traffic)
        worker.start()
        try:
            for generation,backend in [('candidate1',candidate['backend']),('old',runtime['backend']),('candidate2',candidate['backend'])]:
                time.sleep(1.5)
                assert request(backend,'/friends/challenge')[0]==400
                ingress.reload(backend,True,generation)
            worker.join(timeout=10)
            assert not worker.is_alive() and not errors
            records=evidence_records(evidence)
            assert len(records)==7 and all(record['status']==400 for record in records)
            record_measurement(runtime,'switch-overlap',dict(switches=3,requests=7,statuses=[400]*7,
                                generations=sorted({record['active_generation'] for record in records})))
        finally:
            worker.join(timeout=10)
            evidence.close()


def test_failed_real_switch_restores_routing_before_candidate_stop(runtime):
    candidate=dict(runtime,backend=port())
    candidate['command']=runtime['command'][:-1]+[str(candidate['backend'])]
    manager=running(candidate)
    evidence=Evidence(runtime['temporary']/'failed-real-switch','rollback')
    with running(runtime), Ingress(runtime,runtime['backend'],generation='old') as ingress:
        def stop():
            assert request(ingress.port,'/friends/challenge')[0]==400
            manager.__exit__(None,None,None)
        try:
            with pytest.raises(ProbeFailed):
                transaction(evidence,prepare=manager.__enter__,ready=lambda:request(candidate['backend'],'/friends/challenge')[0]==400,
                            switch=lambda:ingress.reload(candidate['backend'],True,'candidate'),accept=lambda:False,
                            commit=lambda:None,restore=lambda:ingress.reload(runtime['backend'],True,'old'),
                            restored=lambda:request(ingress.port,'/friends/challenge')[0]==400,drain=lambda:True,stop_candidate=stop)
            assert request(ingress.port,'/friends/challenge')[0]==400
            with pytest.raises(ConnectionRefusedError):request(candidate['backend'],'/friends/challenge')
        finally:
            manager.__exit__(None,None,None)
            evidence.close()


def test_storage_failure_after_switch_still_restores_before_stop():
    calls=[]
    class BrokenEvidence:
        def persist(self,record):
            if record['event'] in ('switched','failure','routing_restored_and_drained'):
                raise OSError('full')
    with pytest.raises(ProbeFailed):
        transaction(BrokenEvidence(),prepare=lambda:None,ready=lambda:True,switch=lambda:None,
                    accept=lambda:True,commit=lambda:None,restore=lambda:calls.append('restore'),
                    restored=lambda:True,drain=lambda:True,stop_candidate=lambda:calls.append('stop'))
    assert calls==['restore','stop']


def test_correlated_proxy_failure_not_confused_with_upstream_502():
    probe_id='b'*32
    headers={'X-FC-Ingress':'nginx','X-FC-Probe-ID':probe_id,'X-FC-Upstream-Status':'502',
             'X-FC-Upstream-Connect':'-','X-FC-Upstream-Header':'-'}
    result=response_metadata(headers,probe_id)
    assert result['response_origin']=='ingress' and result['upstream_error']=='upstream_connect_not_established'
    headers.update({'X-FC-Upstream-Connect':'0.001','X-FC-Upstream-Header':'0.002'})
    result=response_metadata(headers,probe_id)
    assert result['response_origin']=='upstream' and result['upstream_error']=='upstream_http_error'


@pytest.mark.parametrize('status',[429,502])
def test_new_session_failure_is_durable_and_never_retried(tmp_path,status):
    evidence=Evidence(tmp_path/'evidence','no-retry')
    try:
        with responder(status,payload=b'{"proof":"synthetic-sensitive-value"}') as origin:
            session=Session(origin,evidence)
            with pytest.raises(ProbeFailed):session.probe('ordinary_challenge')
        records=evidence_records(evidence)
        assert len(records)==1 and records[0]['status']==status and not records[0]['valid']
        assert 'synthetic-sensitive-value' not in json.dumps(records)
        assert records[0]['response_origin']=='unknown'
    finally:
        evidence.close()


def test_invalid_readiness_body_fails_after_durable_redacted_receipt(tmp_path):
    evidence=Evidence(tmp_path/'evidence','invalid-readiness')
    try:
        with responder(200,payload=b'{"credential":"synthetic-sensitive-value"}') as origin:
            session=Session(origin,evidence)
            with pytest.raises(ProbeFailed):
                session.probe('restricted_readiness',{'proof':'never-record-proof'},validate=lambda value:False)
        record,=evidence_records(evidence)
        assert record['label']=='restricted_readiness' and record['status']==200 and not record['valid']
        assert 'sensitive-value' not in json.dumps(record) and 'never-record-proof' not in json.dumps(record)
    finally:
        evidence.close()


def test_matrix_cannot_skip_real_proof_or_readiness_validation(tmp_path):
    evidence=Evidence(tmp_path/'evidence','mandatory-g')
    try:
        session=Session('http://127.0.0.1:1',evidence)
        for proof,validator in [(None,lambda value:True),(lambda value:{},None)]:
            with pytest.raises(ValueError):session.matrix({'non_canary':[{}]},proof,validator)
        assert not evidence_records(evidence)
    finally:
        evidence.close()


@pytest.mark.parametrize('lane', ['matrix','observer'])
def test_attempt9_exact_millisecond_schedule_crosses_only_per_ip_bound(lane):
    records=json.loads((ROOT/'tests/fixtures/http_attempt9_transition.json').read_text())[lane]
    records=[record for record in records if record['transport_error']!='interrupted']
    def rejected(rate,burst):
        last=int(datetime.fromisoformat(records[0]['timestamp']).timestamp()*1000)
        excess=0
        results=[False]
        for record in records[1:]:
            now=int(datetime.fromisoformat(record['timestamp']).timestamp()*1000)
            candidate=max(0,excess-rate*(now-last)+1000)
            limited=candidate>burst*1000
            results.append(limited)
            if not limited:excess,last=candidate,now
        return results
    predicted=rejected(2,8)
    historical=[record['status']==429 for record in records]
    if lane=='matrix':
        assert predicted==historical
    else:
        assert sum(predicted)==sum(historical)==7
        assert [index for index,pair in enumerate(zip(predicted,historical)) if pair[0]!=pair[1]]==[19,20]
    assert not any(rejected(10,20))


def test_transition_helper_loads_isolated_outside_repository(tmp_path):
    for name in ('friends_http_transition.py','friends_http_acceptance.py'):
        shutil.copyfile(ROOT/'scripts'/name,tmp_path/name)
    result=subprocess.run([sys.executable,'-I','-c',
        'import runpy,sys; value=runpy.run_path(sys.argv[1]); assert all(name in value for name in ("Session","Evidence","transaction"))',
        str(tmp_path/'friends_http_transition.py')],cwd=tmp_path,env={'PATH':os.defpath},capture_output=True,timeout=5)
    assert result.returncode==0
