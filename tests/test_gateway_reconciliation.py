import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from control.product.gateways import GatewayReconciler
from control.product.provisioning import ProvisioningService
from control.product.store import ProductStore
from device_identity.device import DeviceIdentity
from provisioning.envelope import ProvisioningRejected
from test_product_provisioning import setup, proof


class Gateway:
    def __init__(self):
        self.peers={};self.fail=False;self.calls=[]
    def apply(self, identity, key, addresses, *, present, gateway):
        self.calls.append(present)
        if self.fail:raise RuntimeError('secret subprocess output')
        if present:self.peers[key]=addresses
        else:self.peers.pop(key,None)


def worker(setup):
    gateway=Gateway()
    return GatewayReconciler(setup[0],{'g1':gateway}),gateway


def test_pending_and_failed_gateway_block_publication(setup):
    store, clock, device, signer, network, service, _=setup
    reconcile,gateway=worker(setup)
    reconcile.stage(device.reference,network,lease_seconds=9000)
    with pytest.raises(ProvisioningRejected):service.publish(device.reference,network,signing_identity=signer)
    gateway.fail=True
    assert reconcile.run_once()[0]['status']=='retry'
    row=reconcile.status()[0]
    assert row['error']=='GATEWAY_UNAVAILABLE' and 'secret' not in json.dumps(row)
    assert reconcile.run_once()==[]
    clock[0]=row['retry_at'];gateway.fail=False
    assert reconcile.run_once()[0]['status']=='present'
    assert service.publish(device.reference,network,signing_identity=signer)['revision']==2


@pytest.mark.parametrize('reason',['device','entitlement','key','expiry'])
def test_revoke_and_expiry_remove_peer_durably(setup,reason):
    store,clock,device,*_=setup
    reconcile,gateway=worker(setup)
    reconcile.run_once()
    if reason=='device':store.revoke_device(device.reference)
    elif reason=='entitlement':store.revoke_entitlement(store.authorization(device.reference)['entitlement_id'])
    elif reason=='key':
        with store._transaction() as db:db.execute('UPDATE transport_keys SET revoked_at=1000')
    else:clock[0]=10000
    if reason in ('device','entitlement'):
        assert reconcile.status()[0]['desired']=='absent'  # queued in revoke transaction
    restarted=GatewayReconciler(ProductStore(store.path,clock=lambda:clock[0]),{'g1':gateway})
    assert restarted.run_once()[0]['status']=='absent'
    assert not gateway.peers
    assert restarted.run_once()[0]['status']=='absent'


def test_failed_remove_retries_and_does_not_report_success(setup):
    reconcile,gateway=worker(setup);reconcile.run_once()
    setup[0].revoke_device(setup[2].reference);gateway.fail=True
    assert reconcile.run_once()[0]['status']=='retry'
    assert gateway.peers and reconcile.status()[0]['applied'] is None
    setup[1][0]=1002;gateway.fail=False;reconcile.run_once()
    assert not gateway.peers


def test_no_stale_install_after_concurrent_revoke(setup):
    reconcile,gateway=worker(setup)
    entered,release=Event(),Event()
    original=gateway.apply
    def paused(*args,**kwargs):
        entered.set();assert release.wait(2);original(*args,**kwargs)
    gateway.apply=paused
    with ThreadPoolExecutor(max_workers=2) as pool:
        install=pool.submit(reconcile.run_once)
        assert entered.wait(2)
        revoke=pool.submit(setup[0].revoke_device,setup[2].reference)
        release.set();install.result();revoke.result()
    gateway.apply=original
    assert reconcile.status()[0]['desired']=='absent'
    reconcile.run_once()
    assert gateway.calls==[True,False] and not gateway.peers


def test_crash_after_external_install_is_recovered(setup):
    reconcile,gateway=worker(setup)
    original=gateway.apply
    def crash(*args,**kwargs):original(*args,**kwargs);raise SystemExit()
    gateway.apply=crash
    with pytest.raises(SystemExit):reconcile.run_once()
    assert gateway.peers
    setup[0].revoke_device(setup[2].reference)
    gateway.apply=original;reconcile.run_once()
    assert not gateway.peers


def test_external_drift_is_repaired(setup):
    reconcile,gateway=worker(setup);reconcile.run_once()
    gateway.peers.clear();reconcile.run_once()
    assert setup[2].wireguard_public_key in gateway.peers


def test_all_candidates_must_confirm(setup):
    store,_,device,signer,network,service,_=setup
    # Build a fresh registered device with two gateways; previous topology is immutable.
    entitlement=store.create_entitlement(expires_at=10000)
    invitation=store.create_invitation(entitlement['entitlement_id'],expires_at=9000)
    second=DeviceIdentity.generate()
    nonce=store.challenge(invitation_token=invitation['invitation_token'],public_identity=second.public_identity,
                          wireguard_public_key=second.wireguard_public_key)['challenge']
    store.enroll(second.prove_transport_key(nonce))
    network={**network,'addresses':['10.77.0.5/32'],'gateways':network['gateways']+[{**network['gateways'][0],'gateway_id':'g2'}]}
    first,other=Gateway(),Gateway();other.fail=True
    reconcile=GatewayReconciler(store,{'g1':first,'g2':other})
    reconcile.stage(second.reference,network);reconcile.run_once()
    with pytest.raises(ProvisioningRejected):service.publish(second.reference,network,signing_identity=signer)
    setup[1][0]=1002;other.fail=False;reconcile.run_once()
    assert service.publish(second.reference,network,signing_identity=signer)['revision']==1
    # Independent revoke preserves the second family/device on both gateways.
    store.revoke_device(device.reference);reconcile.run_once()
    assert second.wireguard_public_key in first.peers and second.wireguard_public_key in other.peers


def test_address_allocation_and_topology_cannot_be_reassigned(setup):
    reconcile,_=worker(setup)
    with pytest.raises(ValueError):reconcile.stage(setup[2].reference,{**setup[4],'addresses':['10.77.0.6/32']})
    with pytest.raises(ValueError):reconcile.stage(setup[2].reference,{**setup[4],'addresses':['10.77.0.4/24']})
    with setup[0]._transaction() as db:
        assert db.execute('SELECT count(*) FROM peer_allocations').fetchone()[0]==1


def test_gateway_loss_blocks_fetch(setup):
    reconcile,gateway=worker(setup);gateway.fail=True;reconcile.run_once()
    with pytest.raises(ProvisioningRejected):setup[5].fetch(proof(setup))


def test_pre_v3_envelopes_are_not_delivered_without_managed_peers(setup):
    store=setup[0]
    with store._transaction() as db:
        db.execute('DELETE FROM peer_outbox');db.execute('DELETE FROM peer_deployments')
    with pytest.raises(ProvisioningRejected):setup[5].fetch(proof(setup))


def test_v2_upgrade_preserves_versions(tmp_path):
    from pathlib import Path
    import os
    store=ProductStore(tmp_path/'product.db')
    fd=os.open(store.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    with sqlite3.connect(store.path) as db:
        for name in ('001_product.sql','002_provisioning.sql'):
            db.executescript((Path(__file__).parents[1]/'control/migrations'/name).read_text())
        db.execute("INSERT INTO families VALUES ('existing',1000)")
    store.migrate();store.check_ready();store.migrate()
    with sqlite3.connect(store.path) as db:
        assert db.execute('SELECT id FROM families').fetchone()[0]=='existing'
        assert db.execute('PRAGMA user_version').fetchone()[0]==3


def test_operator_reports_pending_gateway_as_failure(setup,tmp_path,monkeypatch,capsys):
    from control.product.admin import main
    import control.product.admin as admin
    import control.product.gateway_adapter as adapters
    reconcile,gateway=worker(setup);gateway.fail=True
    monkeypatch.setattr(admin,'ProductStore',lambda _:setup[0])
    monkeypatch.setattr(adapters,'DockerGateway',lambda **_:gateway)
    config=tmp_path/'gateways.json';config.write_text(json.dumps({'g1':{'container':'test','keys':'/unused'}}))
    monkeypatch.setattr('sys.argv',['admin','--database',setup[0].path,'reconcile-peers','--gateways',str(config)])
    with pytest.raises(SystemExit) as error:main()
    assert error.value.code==1
    assert json.loads(capsys.readouterr().out)[0]['status']=='retry'
    setup[1][0]=1002;gateway.fail=False
    main()
    assert json.loads(capsys.readouterr().out)[0]['status']=='present'
