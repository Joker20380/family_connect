from concurrent.futures import ThreadPoolExecutor
import sqlite3

import pytest

from control.fleet_access import AUDIENCE, FleetAccess, Reservation
from control.fleet_scheduler import FleetScheduler
from control.fleet_store import FleetStore, LeaseRejected
from device_identity.device import DeviceIdentity
from test_fleet import inventory, observations
from test_fleet_store import state, reserve, grant
from test_fleet_gateway import system


def request(**changes):
    args=dict(request_id='proof-1',registry_revision=7,country='nl',transport='amneziawg',version='3.1',lifetime=100)
    args.update(changes)
    return args


def proof(store, device, **changes):
    c=FleetAccess(store).challenge(public=device.public_identity,wg=device.wireguard_public_key,request=request(**changes))
    assert c['audience']==AUDIENCE and c['request']['request_id']==request(**changes)['request_id']
    return device.prove_transport_key(c['challenge'],c['audience'])


def test_proof_consumption_and_lost_result_retry_survive_restart(state):
    store,device,clock=state
    p=proof(store,device)
    reopened=FleetStore(store.files.path,clock=lambda:clock[0])
    lease=FleetAccess(reopened).complete(p,observations=observations())
    with pytest.raises(LeaseRejected):FleetAccess(store).complete(p,observations=observations())
    new=proof(store,device)
    assert FleetAccess(store).complete(new,observations=[])==lease
    assert lease.expires_at==1100 and lease.state=='reserved'


def test_same_proof_concurrent_completion_reserves_once(state):
    store,device,_=state;p=proof(store,device)
    def attempt(_):
        try:return FleetAccess(store).complete(p,observations=observations()).lease_id
        except LeaseRejected:return None
    with ThreadPoolExecutor(2) as pool:result=list(pool.map(attempt,range(2)))
    assert sum(x is not None for x in result)==1
    assert len(store.pending())==1


@pytest.mark.parametrize('change',['revoke','revision','expiry'])
def test_access_rechecked_after_challenge(state,change):
    store,device,clock=state;p=proof(store,device)
    if change=='revoke':grant(store,device,revision=2,revoked=True)
    elif change=='revision':grant(store,device,revision=2)
    else:clock[0]+=120
    with pytest.raises(LeaseRejected):FleetAccess(store).complete(p,observations=observations())
    assert store.pending()==[]


def test_wrong_identity_binding_domain_signature_and_ungranted_device(state):
    store,device,_=state;service=FleetAccess(store);other=DeviceIdentity.generate()
    with pytest.raises(LeaseRejected):proof(store,other)
    with pytest.raises(LeaseRejected):service.challenge(public=device.public_identity,wg=other.wireguard_public_key,request=request())
    p=proof(store,device)
    bad=[other.prove_transport_key(p['challenge'],AUDIENCE),device.prove_transport_key(p['challenge']),
         dict(p,wireguard_public_key=other.wireguard_public_key),dict(p,signature='A'*88),None]
    for value in bad:
        with pytest.raises(ValueError):service.complete(value,observations=observations())
    assert service.complete(p,observations=observations()).state=='reserved'


def test_challenge_limit_and_expired_challenge_cleanup(state):
    store,device,clock=state
    for _ in range(8):proof(store,device)
    with pytest.raises(LeaseRejected,match='challenge-limit'):proof(store,device)
    clock[0]+=120
    proof(store,device)


def test_failed_reservation_rolls_back_challenge_consumption(state):
    store,device,_=state;p=proof(store,device)
    with pytest.raises(LeaseRejected,match='no-capacity'):FleetAccess(store).complete(p,observations=[])
    assert FleetAccess(store).complete(p,observations=observations()).state=='reserved'


def test_request_is_immutable_and_model_copy_cannot_bypass_validation(state):
    store,device,_=state
    value=Reservation(**request()).model_copy(update={'lifetime':True})
    with pytest.raises(ValueError):FleetAccess(store).challenge(public=device.public_identity,wg=device.wireguard_public_key,request=value)
    for change in (dict(transport='vless-reality',version='1'),dict(version='1'),dict(address_families=[5]),dict(device=device.reference)):
        with pytest.raises(ValueError):
            FleetAccess(store).challenge(public=device.public_identity,wg=device.wireguard_public_key,request=request(**change))


def test_scheduler_ready_revoke_release(system):
    store,agent,backend,command,clock=system
    scheduler=FleetScheduler(store,{command.gateway_id:agent})
    assert scheduler.tick()==[(command.lease_id,'ready')]
    store.retire(command.lease_id)
    assert scheduler.tick()==[(command.lease_id,'released')]
    assert backend.peers=={} and scheduler.tick()==[]


def test_retry_backoff_persists_and_release_bypasses_install_delay(system):
    store,agent,_,command,clock=system
    assert FleetScheduler(store,{}).tick()==[(command.lease_id,'retry')]
    reopened=FleetStore(store.files.path,clock=lambda:clock[0])
    scheduler=FleetScheduler(reopened,{command.gateway_id:agent})
    assert scheduler.tick()==[]
    clock[0]+=4;assert scheduler.tick()==[]
    clock[0]+=1;assert FleetScheduler(reopened,{}).tick()==[(command.lease_id,'retry')]
    clock[0]+=9;assert scheduler.tick()==[]
    store.retire(command.lease_id)
    assert scheduler.tick()==[(command.lease_id,'released')]


def test_claim_exclusion_expiry_and_old_completion_cannot_change_new_claim(state):
    store,device,clock=state;lease=reserve(store,device)
    with ThreadPoolExecutor(2) as pool:claims=list(pool.map(lambda _:store.claim_work(),range(2)))
    old=next(x for x in claims if x is not None)
    assert sum(x is not None for x in claims)==1
    reopened=FleetStore(store.files.path,clock=lambda:clock[0])
    assert reopened.claim_work() is None
    clock[0]+=60
    new=reopened.claim_work();assert new[1]!=old[1]
    assert not store.finish_work(*old,'retry')
    assert reopened.claim_work() is None
    assert store.finish_work(*new,'retry')


def test_scheduler_revoke_during_remote_effect_cannot_mark_ready(system):
    store,agent,backend,command,_=system
    class Racing:
        def execute(self,cmd):
            answer=agent.execute(cmd)
            if cmd.operation=='present':store.retire(cmd.lease_id)
            return answer
    assert FleetScheduler(store,{command.gateway_id:Racing()}).tick()==[
        (command.lease_id,'state-changed'),(command.lease_id,'released')]
    assert backend.peers=={}


def test_deadline_prevents_starting_another_operation(system):
    store,agent,_,command,_=system
    times=iter([0,0,31])
    assert FleetScheduler(store,{command.gateway_id:agent},monotonic=lambda:next(times)).tick()==[(command.lease_id,'ready')]
    assert FleetScheduler(store,{},monotonic=lambda:100).tick(limit=1)==[]
    for options in (dict(limit=True),dict(budget=0),dict(limit=101)):
        with pytest.raises(LeaseRejected):FleetScheduler(store,{}).tick(**options)


def test_expiry_batch_is_bounded_and_claims_prioritize_removal(state):
    store,device,clock=state
    first=reserve(store,device)
    other=DeviceIdentity.generate();grant(store,other)
    second=reserve(store,other)
    clock[0]=1100
    assert len(store.expire(limit=1))==1
    lease,_=store.claim_work();assert lease.state=='retiring'
    assert len(store.expire(limit=1))==1
    assert {store.get(x.lease_id).state for x in (first,second)}=={'retiring'}


def test_explicit_schema_upgrade_preserves_lease_and_is_idempotent(state):
    store,device,_=state;lease=reserve(store,device)
    # Build the original schema shape, containing a real reservation.
    with sqlite3.connect(store.files.path/'fleet.db') as db:
        db.execute('DROP TABLE challenges');db.execute('DROP TABLE jobs')
        for table in ('publications','publication_counters','publication_authority'):
            db.execute('DROP TABLE '+table)
        db.execute('UPDATE metadata SET schema_version=1')
    with pytest.raises(LeaseRejected,match='state-or-clock'):store.get(lease.lease_id)
    store.upgrade_services();store.upgrade_services()
    assert store.get(lease.lease_id)==lease
    assert store.claim_work()[0]==lease
    p=proof(store,device,request_id='request-1')
    assert FleetAccess(store).complete(p,observations=[])==lease


def test_failed_gateway_does_not_starve_other_work_and_backoff_caps(state):
    store,device,clock=state
    one=reserve(store,device)
    other=DeviceIdentity.generate();grant(store,other)
    two=reserve(store,other)
    scheduler=FleetScheduler(store,{})
    assert len(scheduler.tick(limit=1))==1
    assert len(scheduler.tick(limit=1))==1
    assert scheduler.tick()==[]
    delays=[]
    for _ in range(9):
        clock[0]+=300
        # Keep grants/leases live for this retry policy test by testing durable
        # claim completion directly (no remote install of expired grants).
        for _ in range(2):
            claim=store.claim_work();assert claim is not None
            store.finish_work(*claim,'retry')
        with store._transaction() as (db,now):
            delays.append(db.execute('SELECT next_at FROM jobs WHERE lease_id=?',(one.lease_id,)).fetchone()[0]-now)
    assert delays[:3]==[10,20,40] and delays[-1]==300
    assert store.get(two.lease_id).state=='reserved'


def test_proof_to_worker_to_revocation_uses_same_grant(state, inventory, tmp_path):
    from control.fleet_gateway import FencedGateway
    from test_fleet import load
    from test_fleet_gateway import Backend
    store,device,clock=state
    lease=FleetAccess(store).complete(proof(store,device),observations=observations())
    gateway=next(g for g in load(inventory).gateways if g.gateway_id==lease.gateway_id)
    backend=Backend();agent=FencedGateway(tmp_path/'fenced',gateway,backend,clock=lambda:clock[0]);agent.initialize()
    scheduler=FleetScheduler(store,{gateway.gateway_id:agent})
    assert scheduler.tick()==[(lease.lease_id,'ready')]
    assert store.publishable(lease.lease_id).state=='ready'
    grant(store,device,revision=2,revoked=True)
    with pytest.raises(LeaseRejected):store.publishable(lease.lease_id)
    with pytest.raises(LeaseRejected):proof(store,device)
    assert scheduler.tick()==[(lease.lease_id,'released')]
    assert backend.peers=={}
