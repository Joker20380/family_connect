import base64
from concurrent.futures import ThreadPoolExecutor
import json
import sqlite3
import threading
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from control.fleet_publish import FleetPublisher
from control.fleet_store import LeaseRejected, FleetStore
from provisioning.configuration import ConfigVerifier, ConfigError, LOCAL_KEY
from provisioning.fleet import ProfileBinding
from device_identity.device import DeviceIdentity
from test_fleet import inventory as original_inventory
from test_fleet_store import state, grant, reserve


@pytest.fixture
def inventory():
    value=original_inventory.__wrapped__()
    for gateway in value['gateways']:gateway['endpoints'][0]['version']='2.0'
    return value


def profile(version='2.0'):
    parameters=dict(Jc='4',Jmin='40',Jmax='100',S1='32',S2='32',S3='32',S4='32',H1='100',H2='200',H3='300',H4='400')
    if version=='3.1':parameters.update(H1='1',H2='2',H3='3',H4='4',HeaderProtectionKey=base64.b64encode(bytes([42])*32).decode(),ContentPaddingAddition='0-64',RandomTrailers='true',DisableCookies='false')
    if version=='1':parameters={}
    return ProfileBinding(transport='wireguard' if version=='1' else 'amneziawg',version=version,
        server_public=base64.b64encode(bytes([43])*32).decode(),dns=('1.1.1.1',),parameters=parameters)


@pytest.fixture
def publishing(state):
    store,device,clock=state
    lease=reserve(store,device,version='2.0')
    signer=Ed25519PrivateKey.generate()
    store.pin_publication_authority(base64.b64encode(signer.public_key().public_bytes_raw()).decode())
    pins={(lease.gateway_id,lease.transport,lease.version):profile()}
    publisher=FleetPublisher(store,signer=signer,bindings=pins)
    verifier=ConfigVerifier(anchor=signer.public_key().public_bytes_raw(),device=device,client_version='0.2.13')
    return SimpleNamespace(store=store,device=device,clock=clock,lease=lease,signer=signer,pins=pins,publisher=publisher,verifier=verifier)


def emit(p,publisher=None):
    return (publisher or p.publisher).publish(p.lease.lease_id,device=p.device.reference,previous_config_hash=None,min_client_version='0.2.10')
def ready(p):p.store.mark_ready(p.lease.lease_id,generation=1)
def make(p,signer=None,pins=None):return FleetPublisher(p.store,signer=signer or p.signer,bindings=pins or p.pins)


def test_ready_required_and_existing_verifier_accepts_exact_retry(publishing):
    p=publishing
    with pytest.raises(LeaseRejected):emit(p)
    ready(p);raw=emit(p);state=p.verifier.verify(raw,now=1000).state
    assert state.schema_version==2 and state.revision==1 and state.config_id==p.lease.lease_id
    parsed=state.transport_profiles[0].parsed()
    assert parsed['Interface']['Address']==p.lease.address and LOCAL_KEY in state.transport_profiles[0].config
    assert p.lease.address.encode() not in raw
    reopened=FleetStore(p.store.files.path,clock=lambda:p.clock[0])
    pub=FleetPublisher(reopened,signer=p.signer,bindings=p.pins)
    assert emit(p,pub)==raw and state.expires_at==p.lease.expires_at


@pytest.mark.parametrize('kind',['revoke','retire','expiry','other-device'])
def test_cached_publication_denied_after_access_loss(publishing,kind):
    p=publishing;ready(p);emit(p)
    if kind=='revoke':grant(p.store,p.device,revision=2,revoked=True)
    elif kind=='retire':p.store.retire(p.lease.lease_id)
    elif kind=='expiry':p.clock[0]=p.lease.expires_at
    else:
        other=DeviceIdentity.generate();grant(p.store,other)
        with pytest.raises(LeaseRejected):p.publisher.publish(p.lease.lease_id,device=other.reference,previous_config_hash=None,min_client_version='0.2.10')
        return
    with pytest.raises(LeaseRejected):emit(p)


def test_access_revision_new_counter_no_lease_extension(publishing):
    p=publishing;ready(p);first=emit(p)
    grant(p.store,p.device,revision=2,expires_at=3000)
    value=p.verifier.verify(emit(p),now=1000).state
    assert value.revision==2 and value.expires_at==p.lease.expires_at


def test_competing_publishers_only_one_artifact(publishing):
    p=publishing;ready(p)
    with ThreadPoolExecutor(4) as pool:results=list(pool.map(lambda _:emit(p),range(4)))
    assert len(set(results))==1
    with p.store._transaction() as (db,_):assert db.execute('SELECT COUNT(*) FROM publications').fetchone()[0]==1


def test_authority_and_profile_changes_need_migration(publishing):
    p=publishing;ready(p);raw=emit(p);other=Ed25519PrivateKey.generate()
    with pytest.raises(LeaseRejected):p.store.pin_publication_authority(base64.b64encode(other.public_key().public_bytes_raw()).decode())
    with pytest.raises(LeaseRejected):emit(p,make(p,signer=other))
    changed=profile().model_copy(update={'mtu':1400})
    with pytest.raises(LeaseRejected):emit(p,make(p,pins={next(iter(p.pins)):changed}))
    reversed_profile=ProfileBinding(**{**profile().model_dump(),'parameters':dict(reversed(list(profile().parameters.items())))})
    assert emit(p,make(p,pins={next(iter(p.pins)):reversed_profile}))==raw


def test_failure_and_expiry_during_sign_roll_back(publishing):
    p=publishing;ready(p)
    class Bad:
        public_key=p.signer.public_key
        def sign(self,data):raise RuntimeError('test signer failure')
    with pytest.raises(RuntimeError):emit(p,make(p,signer=Bad()))
    class Slow:
        public_key=p.signer.public_key
        def sign(self,data):p.clock[0]=p.lease.expires_at;return p.signer.sign(data)
    with pytest.raises(LeaseRejected):emit(p,make(p,signer=Slow()))
    with p.store._transaction() as (db,_):
        assert db.execute('SELECT COUNT(*) FROM publications').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM publication_counters').fetchone()[0]==0


def test_revoke_serializes_with_signing(publishing):
    p=publishing;ready(p);entered=threading.Event();release=threading.Event();revoking=threading.Event()
    class Waiting:
        public_key=p.signer.public_key
        def sign(self,data):entered.set();assert release.wait(3);return p.signer.sign(data)
    def revoke():revoking.set();grant(p.store,p.device,revision=2,revoked=True)
    with ThreadPoolExecutor(2) as pool:
        first=pool.submit(emit,p,make(p,signer=Waiting()));assert entered.wait(3)
        second=pool.submit(revoke);assert revoking.wait(3);assert not second.done()
        release.set();raw=first.result(timeout=3);second.result(timeout=3)
    assert p.verifier.verify(raw,now=1000).state.revision==1
    with pytest.raises(LeaseRejected):emit(p)


def test_schema2_upgrade_preserves_ready_lease(publishing):
    p=publishing;ready(p)
    with sqlite3.connect(p.store.files.path/'fleet.db') as db:
        for table in ('publications','publication_counters','publication_authority'):db.execute('DROP TABLE '+table)
        db.execute('UPDATE metadata SET schema_version=2')
    with pytest.raises(LeaseRejected):p.store.get(p.lease.lease_id)
    p.store.upgrade_services();p.store.upgrade_services()
    assert p.store.get(p.lease.lease_id).state=='ready'
    with pytest.raises(LeaseRejected,match='publication-authority'):emit(p)


def test_previous_hash_and_minimum_version_cannot_change_cached_artifact(publishing):
    p=publishing;ready(p);emit(p)
    with pytest.raises(LeaseRejected):p.publisher.publish(p.lease.lease_id,device=p.device.reference,previous_config_hash='a'*64,min_client_version='0.2.10')
    with pytest.raises(LeaseRejected):p.publisher.publish(p.lease.lease_id,device=p.device.reference,previous_config_hash=None,min_client_version='0.2.13')


@pytest.mark.parametrize('version',['1','2.0','3.1'])
def test_strict_profile_parameters(version):
    value=profile(version).model_dump();value['parameters']['PostUp']='arbitrary'
    with pytest.raises(ValueError):ProfileBinding.model_validate(value)


def test_awg31_invalid_profile_fails_closed():
    from provisioning.configuration import TransportProfile
    with pytest.raises(ValueError):
        TransportProfile(profile_id='a',gateway_id='b',transport='amneziawg',transport_version='3.1',config='not accepted')


def test_delivery_has_no_signer_and_rechecks_current_access(publishing):
    p=publishing;ready(p)
    with pytest.raises(LeaseRejected):p.store.published(p.lease.lease_id,device=p.device.reference)
    raw=emit(p)
    assert p.store.published(p.lease.lease_id,device=p.device.reference)==raw
    grant(p.store,p.device,revision=2)
    with pytest.raises(LeaseRejected):p.store.published(p.lease.lease_id,device=p.device.reference)
    import hashlib
    previous=hashlib.sha256(raw).hexdigest()
    new=p.publisher.publish(p.lease.lease_id,device=p.device.reference,previous_config_hash=previous,min_client_version='0.2.10')
    value=p.verifier.verify(new,now=1000).state
    assert value.revision==2 and value.previous_config_hash==previous
    assert p.store.published(p.lease.lease_id,device=p.device.reference)==new
    grant(p.store,p.device,revision=3,revoked=True)
    with pytest.raises(LeaseRejected):p.store.published(p.lease.lease_id,device=p.device.reference)


def test_wireguard_artifact_uses_existing_client_verifier(tmp_path,inventory):
    from test_fleet import load, observations
    for gateway in inventory['gateways']:
        gateway['endpoints'][0].update(transport='wireguard',version='1')
    store=FleetStore(tmp_path/'wg-store',clock=lambda:1000);store.initialize(load(inventory))
    device=DeviceIdentity.generate();grant(store,device)
    samples=[x.model_copy(update={'ready_transports':('wireguard',)}) for x in observations()]
    lease=reserve(store,device,transport='wireguard',version='1',observations=samples)
    store.mark_ready(lease.lease_id,generation=1)
    signer=Ed25519PrivateKey.generate();store.pin_publication_authority(base64.b64encode(signer.public_key().public_bytes_raw()).decode())
    publisher=FleetPublisher(store,signer=signer,bindings={(lease.gateway_id,'wireguard','1'):profile('1')})
    raw=publisher.publish(lease.lease_id,device=device.reference,previous_config_hash=None,min_client_version='0.2.10')
    value=ConfigVerifier(anchor=signer.public_key().public_bytes_raw(),device=device,client_version='0.2.13').verify(raw,now=1000)
    assert value.state.transport_profiles[0].transport=='wireguard'
