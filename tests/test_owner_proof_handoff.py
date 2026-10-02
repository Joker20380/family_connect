import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from scripts import friends_http_transition as transition
from test_friends_http_runtime import runtime, running
from test_http_transition import evidence_records
from test_restricted_runtime import bundle, material_fixture, snapshot


def product_observation(product):
    app=dict(receipt_class='real_owner_product',challenge_id='a'*32,fetch_id='b'*32,
             challenge_result='issued',fetch_result='authorized',import_result='accepted',
             revision=2,expires_at=int(time.time())+600,observed_at=int(time.time()))
    server=[dict(probe_id=app[key],generation=product.generation,timestamp=time.time(),
                 status=200,upstream_status='200',product_step=step)
            for key,step in [('challenge_id','challenge'),('fetch_id','readiness')]]
    return app,server


@pytest.fixture
def evidence(tmp_path):
    value=transition.Evidence(tmp_path/'receipts','handoff-local-test')
    yield value
    value.close()


def test_product_receipts_require_both_server_requests_and_validated_app_import(evidence):
    product=transition.OwnerProduct(evidence,'candidate')
    app,server=product_observation(product)
    assert product.observe(app,server) and product.passed
    assert evidence_records(evidence)[-1]['state']=='OWNER_PRODUCT_READY'
    with pytest.raises(transition.ProbeFailed):product.observe(app,server)


@pytest.mark.parametrize('mutation',[
    'absent','cannot_sign','bad_proof','non_canary','revoked','import_failed','expired',
    'fixture_class','secret','wrong_generation','stale','duplicate','wrong_route','missing_trace',
    'boolean_revision','zero_revision','deadline','future',
])
def test_product_failures_are_redacted_and_cannot_commit(evidence,mutation):
    product=transition.OwnerProduct(evidence,'candidate')
    app,server=product_observation(product)
    if mutation=='absent':app=None
    elif mutation=='cannot_sign':app['fetch_result']='failed'
    elif mutation in ('bad_proof','non_canary','revoked'):server[1]['status']=403
    elif mutation=='import_failed':app['import_result']='failed'
    elif mutation=='expired':app['expires_at']=1
    elif mutation=='fixture_class':app['receipt_class']='server_contract_fixture'
    elif mutation=='secret':app['raw_proof']='secret-sentinel'
    elif mutation=='wrong_generation':server[1]['generation']='old'
    elif mutation=='stale':server[1]['timestamp']=product.opened-10
    elif mutation=='duplicate':server[1]=server[0]
    elif mutation=='wrong_route':server[1]['product_step']='challenge'
    elif mutation=='missing_trace':server=[]
    elif mutation=='boolean_revision':app['revision']=True
    elif mutation=='zero_revision':app['revision']=0
    elif mutation=='deadline':product.deadline=time.monotonic()-1
    elif mutation=='future':app['observed_at']+=10
    assert not product.observe(app,server) and not product.passed
    record,=evidence_records(evidence)
    assert record['state']=='OWNER_PREWARM_FAILED'
    assert 'secret-sentinel' not in json.dumps(record) and 'raw_proof' not in record


def test_product_persistence_failure_forbids_pass(evidence,monkeypatch):
    product=transition.OwnerProduct(evidence,'candidate')
    monkeypatch.setattr(evidence,'persist',lambda record:(_ for _ in ()).throw(OSError()))
    with pytest.raises(OSError):product.observe(*product_observation(product))
    assert not product.passed


@pytest.mark.parametrize('layer', ['direct_candidate','ingress_external'])
def test_operator_cannot_send_owner_fg(evidence,layer):
    class Candidate:
        port=18086
        generation='candidate'
    session=transition.Session('http://127.0.0.1:18086',evidence,layer=layer,
                               candidate=Candidate(),generation='candidate')
    for label in ('restricted_canary','restricted_readiness'):
        with pytest.raises(ValueError):session.probe(label)
    assert not evidence_records(evidence)


@pytest.mark.parametrize('origin', ['https://example.com','http://127.0.0.1:18086','http://127.0.0.1:18084','http://localhost:49152'])
def test_fixture_session_refuses_production_or_candidate_origin(evidence,origin):
    with pytest.raises(ValueError):transition.Session(origin,evidence,layer='server_contract_fixture')


def test_current_authority_check_is_real_isolated_read_only(bundle,evidence):
    material,_=material_fixture(bundle)
    before=snapshot(bundle.parent)
    archive=bundle/'restricted-sync.pyz'
    assert transition.current_authority_check(evidence,sys.executable,archive,hashlib.sha256(archive.read_bytes()).hexdigest(),
        database=bundle/'access.db',material=material,host='186.246.45.246',ssh_key=material/'sync.key',known_hosts=material/'known_hosts')
    assert snapshot(bundle.parent)==before
    assert evidence_records(evidence)[-1]['passed']


def test_controlled_fg_validated_by_native_without_production_owner_key(runtime,evidence,tmp_path):
    go=os.environ.get('FC_TEST_GO')
    assert go, 'Locked Go toolchain required for accepted handoff gate'
    binary=tmp_path/'delivery-check'
    subprocess.run([go,'build','-trimpath','-buildvcs=false','-o',str(binary),'./wholedevice/testdata/delivery-check.go'],
                   cwd=Path(__file__).resolve().parents[1]/'carrier',check=True,capture_output=True,timeout=120)
    observed=[]
    def validate(value):
        payload=dict(response=value,public=runtime['canary'].public_identity,
                     anchor=(runtime['state']/'anchor.pub').read_text(),now=int(time.time()))
        result=subprocess.run([str(binary)],input=json.dumps(payload).encode(),capture_output=True,timeout=5)
        observed.append(result.returncode)
        return result.returncode==0 and result.stdout==b'compatible\n'
    with running(runtime):
        fixture=transition.Session('http://127.0.0.1:'+str(runtime['backend']),evidence,layer='server_contract_fixture')
        result=fixture.fixture_matrix(runtime['artifact']/'friends-http.pyz',runtime['identities'],
            lambda challenge:runtime['canary'].prove_transport_key(challenge['challenge']),validate)
    assert result.passed and observed==[0]
    records=evidence_records(evidence)
    assert all(record['receipt_class']=='server_contract_fixture' for record in records)
    assert records[-1]['classification']=='CONTROLLED SERVER CONTRACT FIXTURE'
    assert 'real_owner_product' not in json.dumps(records)


def test_android_protocol_observation_not_a_signing_api():
    root=Path(__file__).resolve().parents[1]
    android=root/'clients/android/app/src/main'
    access=(android/'java/com/familyconnect/app/FriendsAccessAndroid.java').read_text()
    assert 'FriendsReadinessProtocol.fetch(this::post,identity,receipt)' in access
    protocol=(android/'java/com/familyconnect/app/FriendsReadinessProtocol.java').read_text()
    assert protocol.index('/challenge')<protocol.index('identity.proveTransportKey(nonce)')<protocol.index('receipt.fetchAuthorized()')
    prewarm=(android/'java/com/familyconnect/app/FriendsRestricted.java').read_text()
    assert prewarm.index('cache.accept(response)')<prewarm.index('receipt.imported(response)')
    assert 'Arrays.fill(response,(byte)0)' in prewarm
    hook=(android/'java/com/familyconnect/app/OwnerPrewarmReceipt.java').read_text()
    for forbidden in ('ControlIdentity','proveTransportKey','material()','private_key','public_identity','join_url'):
        assert forbidden not in hook
    manifest=(android/'AndroidManifest.xml').read_text()
    assert 'OwnerPrewarm' not in manifest
    operator=(root/'scripts/friends_http_transition.py').read_text()
    for forbidden in ('adb','get_private_key','prove_transport_key','FriendsIdentityVault'):
        assert forbidden not in operator
