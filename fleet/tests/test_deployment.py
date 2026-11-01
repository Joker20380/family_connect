import copy
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from fleet import health, preflight
from fleet.bundle import build
from fleet.contracts import FleetError, canonical, digest, load
from fleet.enrollment import EnrollmentStore, generate_node_key, proof_payload
from fleet.installer import SandboxInstaller
from fleet.tests.test_bundle import bundle
from fleet.tests.test_contracts import instance


def host_report():
    return dict(os='ubuntu', version='24.04', architecture='x86_64', kernel='6.8.0-generic', cpu=2,
        ram_mb=2048, disk_mb=4096, time_sync=True, tun=True, ipv4='192.0.2.10', ipv6=None,
        resolver=True, https=True, systemd=True, firewall='nftables', security='apparmor-enforcing',
        ports_available=True, pending_reboot=False, existing_instance=None)


@pytest.fixture
def installer(bundle,tmp_path):
    root,spec,key,directory,manifest=bundle
    node=instance();node.update(desired_bundle=manifest['bundle_id'],enrollment_state='ENROLLED',deployment_identity='b'*64)
    return SandboxInstaller(tmp_path/'host',node,directory,key.public_key())


def checks(installer):
    names=health.required(installer.manifest['roles'])
    return health.run_hooks(installer.instance['instance_id'],installer.manifest['bundle_id'],installer.manifest['roles'],
                            {name:lambda:True for name in names})


def stage(installer):
    installer.execute('preflight','preflight',report=host_report())
    installer.execute('stage','stage')
    path=installer.configuration/'awg-material.slot'
    path.write_bytes(b'synthetic secret stays outside immutable release')
    path.chmod(0o600)


def activate(installer):
    stage(installer)
    installer.execute('verify','verify',health_report=checks(installer))
    installer.execute('activate','activate')


@pytest.mark.parametrize('field,value',[('os','debian'),('version','26.04'),('architecture','aarch64'),('tun',False),
    ('time_sync',False),('pending_reboot',True),('ports_available',False),('existing_instance','another-instance'),('ram_mb',True)])
def test_preflight_before_writes(installer,field,value):
    report=host_report();report[field]=value
    with pytest.raises(FleetError):installer.execute('preflight','reject',report=report)
    assert not installer.root.exists()


def test_dry_run(installer):
    for action in ('preflight','stage','verify','activate','rollback'):
        assert installer.execute(action,'dry',dry_run=True)['dry_run']
    assert not installer.root.exists()


def test_stage_idempotency_and_no_secrets(installer):
    stage(installer)
    retained=installer.execute('stage','stage')
    assert retained['state']=='SUCCEEDED'
    assert installer.execute('stage','stage')==retained
    assert not installer.current.exists()
    assert not any(path.suffix=='.slot' for path in installer.releases.rglob('*'))
    with pytest.raises(FleetError):installer.execute('activate','stage')


def test_verified_required(installer):
    stage(installer)
    with pytest.raises(FleetError):installer.execute('activate','blocked')
    assert not installer.current.exists()
    report=checks(installer);report['checks']['host.time_sync']=False
    with pytest.raises(FleetError):installer.execute('verify','unhealthy',health_report=report)


def test_activate_and_empty_rollback(installer):
    activate(installer)
    assert installer.status()['state']=='ACTIVE'
    assert installer.current.resolve().name==installer.manifest['bundle_id']
    installer.execute('rollback','rollback')
    assert not installer.current.exists()
    assert installer.status()['state']=='DISCOVERED'


def test_failed_activation_retains_evidence(installer):
    stage(installer);installer.execute('verify','verify',health_report=checks(installer))
    def failure():raise RuntimeError('private token must never be logged')
    with pytest.raises(RuntimeError):installer.execute('activate','failed',activation_hook=failure)
    evidence=load((installer.operations/'failed.json').read_bytes())
    assert evidence['state']=='FAILED' and evidence['first_failure']=='operation_failed'
    assert 'private token' not in canonical(evidence).decode()
    assert not installer.current.exists()


def test_upgrade_rollback_previous(installer,bundle,tmp_path):
    activate(installer)
    original=installer.manifest['bundle_id']
    installer.execute('drain','drain')
    root,spec,key,directory,manifest=bundle
    (root/'runtime').write_bytes(b'new synthetic runtime fixture for an upgrade only\n')
    spec['members'][0]['sha256']=digest((root/'runtime').read_bytes())
    new=build(root,spec,key,tmp_path/'upgrade')
    node=dict(installer.instance,desired_bundle=new['bundle_id'])
    upgraded=SandboxInstaller(installer.root,node,tmp_path/'upgrade',key.public_key())
    upgraded.execute('preflight','upgrade-preflight',report=host_report())
    upgraded.execute('stage','upgrade-stage')
    assert upgraded.current.resolve().name==original
    upgraded.execute('verify','upgrade-verify',health_report=checks(upgraded))
    upgraded.execute('activate','upgrade-activate')
    assert upgraded.current.resolve().name==new['bundle_id']
    upgraded.execute('rollback','upgrade-rollback')
    assert upgraded.current.resolve().name==original
    assert (upgraded.configuration/(original+'.json')).is_file()
    assert (upgraded.releases/new['bundle_id']).is_dir()


def test_root_symlink_rejected(installer,tmp_path):
    installer.root.symlink_to(tmp_path/'outside')
    with pytest.raises(FleetError):installer.initialize(host_report())


def test_health_binding_and_all_roles():
    roles=list(health.CHECKS)
    report=health.run_hooks('test-001','test-bundle',roles,{name:lambda:True for name in health.required(roles)},now=100)
    assert health.accept(report,'test-001','test-bundle',roles,now=101)
    for field,value in [('instance_id','wrong'),('bundle_id','wrong'),('observed_at',-999),('scope','production')]:
        modified=copy.deepcopy(report);modified[field]=value
        with pytest.raises(FleetError):health.accept(modified,'test-001','test-bundle',roles,now=101)


def test_ssh_fingerprint(tmp_path):
    known=tmp_path/'known_hosts';known.write_text('192.0.2.10 ssh-ed25519 AAAATEST\n');known.chmod(0o600)
    calls=[]
    def runner(argv,**kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0,stdout='256 SHA256:accepted test\n')
    with pytest.raises(FleetError):preflight.SSH('192.0.2.10','root',known,'SHA256:wrong',runner)
    remote=preflight.SSH('192.0.2.10','root',known,'SHA256:accepted',runner)
    assert 'StrictHostKeyChecking=yes' in remote.argv and 'PasswordAuthentication=no' in remote.argv
    with pytest.raises(FleetError):remote.mutate('stage')
    assert all(command[0]=='ssh-keygen' for command in calls)


@pytest.fixture
def enrollment(tmp_path):
    authority=Ed25519PrivateKey.generate()
    store=EnrollmentStore(tmp_path/'enrollment.sqlite3',authority,clock=lambda:100)
    binding=dict(instance_id='nl-test-001',logical_gateway='nl',bundle_id='test-v1',provider='synthetic',region='test',ipv4='192.0.2.10',roles=['awg'])
    token,challenge=store.issue(binding)
    private=tmp_path/'node.key'
    public=generate_node_key(private)
    key=Ed25519PrivateKey.from_private_bytes(private.read_bytes())
    signature=key.sign(proof_payload(binding,challenge['challenge'],public))
    return store,binding,token,challenge,public,signature,authority


def test_enrollment_success_replay_and_hash_only(enrollment):
    store,binding,token,challenge,public,signature,authority=enrollment
    assert token.encode() not in store.path.read_bytes()
    receipt=store.enroll(token,binding,public,signature)
    import base64
    authority.public_key().verify(base64.b64decode(receipt['signature']),canonical(receipt['body']))
    assert receipt['body']['transport_issuance'] is False
    with pytest.raises(FleetError):store.enroll(token,binding,public,signature)
    assert token.encode() not in store.path.read_bytes()


@pytest.mark.parametrize('field,value',[('instance_id','other'),('logical_gateway','ru'),('bundle_id','wrong'),
    ('provider','other'),('region','other'),('ipv4','192.0.2.11'),('roles',['tcp'])])
def test_enrollment_wrong_binding(enrollment,field,value):
    store,binding,token,challenge,public,signature,authority=enrollment
    binding[field]=value
    with pytest.raises(FleetError):store.enroll(token,binding,public,signature)


@pytest.mark.parametrize('reason',['expiry','cancel','possession','lifetime'])
def test_enrollment_fail_closed(enrollment,reason):
    store,binding,token,challenge,public,signature,authority=enrollment
    if reason=='expiry':store.clock=lambda:700
    if reason=='cancel':store.cancel(token)
    if reason=='possession':signature=bytes(64)
    if reason=='lifetime':
        with pytest.raises(FleetError):store.issue(binding,601)
        return
    with pytest.raises(FleetError):store.enroll(token,binding,public,signature)


def test_cli_help_and_live_guard():
    result=subprocess.run(['python3','-m','fleet','--help'],capture_output=True,text=True,timeout=5)
    assert result.returncode==0 and 'no live activation' in result.stdout


def test_templates_do_not_flush_or_inject():
    from fleet.render import templates
    result=templates('awg',dict(interface='fcawg0',uplink='eth0',subnet='10.90.0.0/24'))
    assert b'flush ruleset' not in result['firewall/instance.nft']
    assert b'@' not in result['systemd/family-connect-awg.service']
    with pytest.raises(FleetError):templates('awg',dict(interface='evil;shutdown',uplink='eth0',subnet='10.90.0.0/24'))
