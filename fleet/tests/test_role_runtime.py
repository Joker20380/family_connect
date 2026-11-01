import base64
import copy
import datetime
import os
from pathlib import Path
from types import SimpleNamespace
import uuid

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.x509.oid import NameOID

from fleet.contracts import FleetError, canonical, digest, load
from fleet.private_files import read_private, write_private
from fleet.rehearsal_templates import SYSCTL, UNIT_NAMES, nftables, units
from fleet.role_config import SNI, awg_config, mesh_config, tcp_config
from fleet.role_runtime import Runtime
from fleet.tests.test_permit import authority


def synthetic_slots(instance_id, now=1000, expiry=15400):
    private = X25519PrivateKey.generate()
    peer = X25519PrivateKey.generate()
    private_bytes = private.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption())
    raw_public = private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    peer_public = peer.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    signer = Ed25519PrivateKey.generate()
    leaf_key = Ed25519PrivateKey.generate()
    identity = peer_public+leaf_key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    gateway = digest(identity)[:32]
    family = 'f'*32
    begin = datetime.datetime.fromtimestamp(now,datetime.timezone.utc)
    end = datetime.datetime.fromtimestamp(expiry,datetime.timezone.utc)
    issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Disposable test authority')])
    authority = x509.CertificateBuilder().subject_name(issuer).issuer_name(issuer).public_key(signer.public_key()).serial_number(1).not_valid_before(begin).not_valid_after(end).add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True).sign(signer,None)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Disposable test gateway'),
        x509.NameAttribute(NameOID.SERIAL_NUMBER,gateway),
        *[x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME,claim) for claim in
          ('protocol=family-connect-5n3-test-v1','family='+family,'role=gateway','revision=1')]])
    leaf = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(leaf_key.public_key()).serial_number(2).not_valid_before(begin).not_valid_after(end).add_extension(x509.SubjectAlternativeName([x509.UniformResourceIdentifier('urn:family-connect:identity:'+identity.hex()),x509.DNSName('gateway.family-connect.test')]),critical=False).sign(signer,None)
    revocations = x509.CertificateRevocationListBuilder().issuer_name(issuer).last_update(begin).next_update(end).add_extension(x509.CRLNumber(1),critical=False).sign(signer,None)
    credentials = dict(certificate=leaf.public_bytes(serialization.Encoding.PEM).decode(),
        private_key=leaf_key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).decode(),
        authority=authority.public_bytes(serialization.Encoding.PEM).decode(),revocations=revocations.public_bytes(serialization.Encoding.PEM).decode(),
        family=family,gateway=gateway,minimum_revision=1,minimum_crl=1)
    return {
        'awg-material':canonical(dict(scope='DISPOSABLE_FLEET_REHEARSAL',server_private_key=base64.b64encode(private_bytes).decode(),peer_public_key=base64.b64encode(peer_public).decode())),
        'tcp-material':canonical(dict(scope='DISPOSABLE_FLEET_REHEARSAL',private_key=base64.urlsafe_b64encode(private_bytes).decode().rstrip('='),public_key=base64.urlsafe_b64encode(raw_public).decode().rstrip('='),uuid=str(uuid.uuid4()),short_id='0123456789abcdef',sni=SNI,destination=SNI+':443')),
        'mesh-material':canonical(dict(scope='DISPOSABLE_FLEET_REHEARSAL',instance_id=instance_id,credentials=credentials)),
        'publisher-material':canonical(dict(scope='DISPOSABLE_FLEET_REHEARSAL',token='synthetic-offline-token-only')),
    }


class IsolatedExecutor:
    def __init__(self):
        self.calls=[]
        self.table=None
        self.forward=b'0\n'
        self.fail_start=False

    def run(self, argv, *, input=None, check=True):
        self.calls.append((argv,input))
        output=b''
        code=0
        if argv==['ip','-j','route','show','default']:
            output=b'[{"dev":"eth0"}]'
        elif argv==['ip','link','show','dev','fcrh0']:
            code=1
        elif argv[:3]==['nft','-s','list']:
            output=self.table or b''
            code=0 if self.table else 1
        elif argv==['nft','-f','-']:
            self.table=input if b'table inet family_connect_rehearsal {' in input else None
        elif argv==['sysctl','-n','net.ipv4.ip_forward']:
            output=self.forward
        elif argv[:2]==['sysctl','-p']:
            self.forward=b'1\n'
        elif argv[:2]==['sysctl','-w']:
            self.forward=argv[2].split('=')[1].encode()+b'\n'
        elif argv[:2]==['systemctl','start'] and self.fail_start:
            raise FleetError('injected_start_failure')
        return SimpleNamespace(stdout=output,stderr=b'',returncode=code)


@pytest.fixture
def runtime(authority,tmp_path):
    key,permit,arguments=authority
    root=tmp_path/'root'
    for name in ('opt','etc','etc/sysctl.d','etc/systemd/system','var/lib','run'):
        (root/name).mkdir(parents=True,exist_ok=True)
    directory=root/'var/lib'/permit['body']['instance_id']
    directory.mkdir(mode=0o700)
    slots=synthetic_slots(permit['body']['instance_id'])
    (directory/'slots').mkdir(mode=0o700)
    for name,value in slots.items():
        write_private(directory/'slots'/name,value)
    write_private(directory/'slots/receipt.json',canonical(dict(slots={name:digest(value) for name,value in slots.items()},expires_at=15400)))
    contents={'bin/'+name:('synthetic executable '+name).encode() for name in ('amneziawg-go','awg','xray','gateway')}
    contents['metadata/revision.json']=canonical(dict(revision='A'))
    contents['runtime/roles.py']=b'from fleet.role_runtime import Runtime\n'
    members=[dict(path=name,sha256=digest(value),size=len(value),mode=0o555 if name.startswith('bin/') else 0o444) for name,value in sorted(contents.items())]
    manifest=dict(bundle_id=permit['body']['bundle_a'],members=members)
    result=Runtime(manifest=manifest,contents=contents,authorization=permit,authority=key.public_key(),directory=directory,
                   root=root,executor=IsolatedExecutor(),clock=lambda:1001)
    result.enrolled_identity=lambda:'a'*64
    result.material_store=lambda:SimpleNamespace(retire=lambda:None)
    result.test_signer=key
    return result


def test_interface_and_immutable_stage(runtime):
    for method in ('enrolled_identity','stage','configure','switch','start','accept','stop','reboot_check','drain','retire'):
        assert callable(getattr(runtime,method))
    target=runtime.manifest['bundle_id']
    runtime.stage(target)
    before={str(path):path.stat().st_ino for path in (runtime.releases/target).rglob('*')}
    runtime.stage(target)
    assert before=={str(path):path.stat().st_ino for path in (runtime.releases/target).rglob('*')}
    assert (runtime.releases/target).stat().st_mode & 0o777==0o555


def test_configure_paths_modes_and_fixed_argv(runtime):
    target=runtime.manifest['bundle_id']
    runtime.stage(target)
    runtime.configure(target)
    metadata=runtime.verify_configuration(target)
    assert metadata['bundle_id']==target
    assert (runtime.configuration/target/'profile/gateway.json').stat().st_mode & 0o777==0o640
    assert (runtime.configuration/target/'publisher.env').stat().st_mode & 0o777==0o600
    assert any(argv[1:]==['run','-test','-config',str(runtime.configuration/target/'tcp.json')] for argv,data in runtime.executor.calls)
    for argv,data in runtime.executor.calls:
        assert not any('synthetic-offline-token' in value or 'PrivateKey =' in value for value in argv)
    runtime.configure(target)


def test_mesh_interface_discovery_allowed_without_network_admin_capability():
    rendered=units('gw-'+'a'*32,'fleet-rehearsal-test',300)
    mesh=rendered['fc-rehearsal-mesh.service']
    assert b'RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_NETLINK\n' in mesh
    assert b'CapabilityBoundingSet=\n' in mesh
    for name in ('tcp','snapshot','monitoring'):
        assert b'AF_NETLINK' not in rendered['fc-rehearsal-'+name+'.service']


@pytest.fixture
def predecessor(runtime):
    runtime.stage(runtime.manifest['bundle_id'])
    instance='fleet-rehearsal-retired'
    directory=runtime.directory.parent/instance
    directory.mkdir(mode=0o700)
    (directory/'operations').mkdir(mode=0o700)
    node=Ed25519PrivateKey.generate()
    public=node.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    owner=dict(instance_id=instance,identity=digest(public))
    binding={name:runtime.permit[name] for name in ('logical_gateway','ipv4','provider','region')}
    binding.update(instance_id=instance,bundle_id='gw-'+'c'*32,roles=['awg','tcp','mesh'])
    body=dict(schema=1,scope='rehearsal',binding=binding,public_key=public.hex(),enrolled_at=1000,transport_issuance=False)
    enrollment=dict(body=body,signature=base64.b64encode(runtime.test_signer.sign(canonical(body))).decode())
    custody=dict(scope='DISPOSABLE_FLEET_REHEARSAL_FINAL_CUSTODY',instance_id=instance,
                 actual_bundle=None,disposition='SECRET_ERASURE_PENDING')
    records={'enrollment.json':enrollment,
        'final-custody.json':dict(body=custody,signature=base64.b64encode(node.sign(canonical(custody))).decode()),
        'operations/state.json':dict(owner,state='RETIRED',fenced=False,actual_bundle=None),
        'operations/retire.json':dict(instance_id=instance,action='retire',result='PASS',state_after='RETIRED')}
    for name,value in records.items():
        write_private(directory/name,canonical(value))
    write_private(runtime.configuration/'owner.json',canonical(owner),replace=True)
    return runtime,directory,owner


def test_retired_owner_handoff_is_verified_atomic_and_preserves_predecessor(predecessor):
    runtime,directory,previous=predecessor
    before={str(path.relative_to(directory)):path.read_bytes() for path in directory.rglob('*') if path.is_file()}
    runtime.stage(runtime.manifest['bundle_id'])
    evidence=load(read_private(runtime.directory/'predecessor.json'))
    assert evidence['previous']==previous
    assert load(read_private(runtime.configuration/'owner.json'))['instance_id']==runtime.permit['instance_id']
    runtime.stage(runtime.manifest['bundle_id'])
    assert before=={str(path.relative_to(directory)):path.read_bytes() for path in directory.rglob('*') if path.is_file()}


@pytest.mark.parametrize('state,fenced',[('FAILED',False),('DRAINING',False),('QUARANTINED',True),('RETIRED',True)])
def test_nonretired_or_fenced_owner_cannot_be_adopted(predecessor,state,fenced):
    runtime,directory,previous=predecessor
    record=load(read_private(directory/'operations/state.json'))
    record.update(state=state,fenced=fenced)
    write_private(directory/'operations/state.json',canonical(record),replace=True)
    with pytest.raises(FleetError,match='retired_predecessor_state'):
        runtime.stage(runtime.manifest['bundle_id'])
    assert load(read_private(runtime.configuration/'owner.json'))==previous


@pytest.mark.parametrize('resource',['identity.key','material.key','slots','slots.pending','config','unit','pointer','sysctl','firewall','interface'])
def test_retired_owner_with_remaining_resources_is_rejected(predecessor,resource):
    runtime,directory,previous=predecessor
    if resource=='config':
        (runtime.configuration/'old-config').mkdir()
    elif resource=='unit':
        (runtime.path('/etc/systemd/system')/'fc-rehearsal-mesh.service').symlink_to('/missing')
    elif resource=='pointer':
        runtime.current.symlink_to('releases/'+runtime.manifest['bundle_id'])
    elif resource=='sysctl':
        runtime.sysctl.write_bytes(SYSCTL)
    elif resource=='firewall':
        runtime.executor.table=b'table inet family_connect_rehearsal {}'
    elif resource=='interface':
        original=runtime.executor.run
        runtime.executor.run=lambda argv,**kwargs: SimpleNamespace(returncode=0,stdout=b'') if argv==['ip','link','show','dev','fcrh0'] else original(argv,**kwargs)
    else:
        write_private(directory/resource,b'synthetic-not-delivered')
    with pytest.raises(FleetError,match='retired_predecessor_resources'):
        runtime.stage(runtime.manifest['bundle_id'])
    assert load(read_private(runtime.configuration/'owner.json'))==previous


@pytest.mark.parametrize('attack',['custody-signature','enrollment-signature','missing-retirement','identity'])
def test_retired_owner_requires_signed_binding_and_final_receipts(predecessor,attack):
    runtime,directory,previous=predecessor
    if attack=='missing-retirement':
        (directory/'operations/retire.json').unlink()
    elif attack=='identity':
        write_private(runtime.configuration/'owner.json',canonical(dict(previous,identity='0'*64)),replace=True)
    else:
        name='final-custody.json' if attack=='custody-signature' else 'enrollment.json'
        record=load(read_private(directory/name));record['signature']=base64.b64encode(bytes(64)).decode()
        write_private(directory/name,canonical(record),replace=True)
    with pytest.raises(FleetError):
        runtime.stage(runtime.manifest['bundle_id'])


@pytest.mark.parametrize('field,value',[('ipv4','9.9.9.9'),('provider','another-provider'),('region','another-region')])
def test_retired_owner_on_another_host_or_provider_cannot_be_adopted(predecessor,field,value):
    runtime,directory,previous=predecessor
    receipt=load(read_private(directory/'enrollment.json'))
    receipt['body']['binding'][field]=value
    receipt['signature']=base64.b64encode(runtime.test_signer.sign(canonical(receipt['body']))).decode()
    write_private(directory/'enrollment.json',canonical(receipt),replace=True)
    with pytest.raises(FleetError,match='retired_predecessor_binding'):
        runtime.stage(runtime.manifest['bundle_id'])


def test_switch_restore_and_owned_retire(runtime):
    target=runtime.manifest['bundle_id']
    unrelated=runtime.root/'etc/unrelated'
    unrelated.write_bytes(b'keep')
    runtime.stage(target)
    runtime.configure(target)
    runtime.switch(target)
    assert runtime.pointer()==target
    assert runtime.sysctl.read_bytes()==SYSCTL
    runtime.start(target)
    runtime.stop()
    runtime.retire()
    assert unrelated.read_bytes()==b'keep'
    assert runtime.executor.table is None
    assert runtime.executor.forward==b'0\n'
    assert not runtime.sysctl.exists()
    assert runtime.pointer() is None
    assert (runtime.releases/target).exists()


@pytest.mark.parametrize('attack',['symlink','hardlink','partial','tamper'])
def test_stage_rejections(runtime,attack,tmp_path):
    target=runtime.manifest['bundle_id']
    runtime.stage(target)
    binary=runtime.releases/target/'bin/awg'
    binary.parent.chmod(0o755)
    if attack=='symlink':
        binary.unlink()
        binary.symlink_to(tmp_path/'outside')
    if attack=='hardlink':
        os.link(binary,tmp_path/'link')
    if attack=='partial':
        binary.unlink()
    if attack=='tamper':
        binary.chmod(0o755)
        binary.write_bytes(b'changed')
    with pytest.raises((FleetError,FileNotFoundError)):
        runtime.stage(target)


def test_interrupted_stage_is_not_retried_blindly(runtime):
    target=runtime.manifest['bundle_id']
    runtime.stage(target)
    os.rename(runtime.releases/target,runtime.releases/(target+'.pending'))
    with pytest.raises(FleetError,match='interrupted_stage'):
        runtime.stage(target)


def test_templates_owned_policy_and_no_public_monitor():
    firewall=nftables('eth0')
    assert b'flush ruleset' not in firewall and b'masquerade' in firewall
    assert b'tcp dport 19727 drop' in firewall
    with pytest.raises(FleetError):
        nftables('eth0;shutdown')
    rendered=units('gw-'+'a'*32,'fleet-rehearsal-one',300)
    assert len(rendered)==6
    for name,content in rendered.items():
        assert b'User=' in content and b'Group=' in content and b'RestrictAddressFamilies=' in content
        assert b'WorkingDirectory=/opt/family-connect/current' in content
        assert b'StandardError=null' in content
    assert b'IPAddressAllow=localhost' in rendered['fc-rehearsal-monitoring.service']


def test_native_config_contracts_without_live_material():
    slots=synthetic_slots('fleet-rehearsal-one')
    config,binding=awg_config(slots['awg-material'])
    assert config.count(b'[Peer]')==1 and binding['port']==51827
    assert b'4443' in tcp_config(slots['tcp-material'])
    config,binding=mesh_config(slots['mesh-material'],instance_id='fleet-rehearsal-one',now=1001,permit_expires_at=15400)
    assert binding['crl_number']==1
    with pytest.raises(FleetError):
        mesh_config(slots['mesh-material'],instance_id='fleet-rehearsal-other',now=1001,permit_expires_at=15400)
    with pytest.raises(FleetError):
        mesh_config(slots['mesh-material'],instance_id='fleet-rehearsal-one',now=15400,permit_expires_at=15400)


def test_real_layout_two_phase_ab_failure_success_and_retirement(runtime):
    from fleet.rehearsal_state import RehearsalState
    from fleet.tests.test_rehearsal_state import active, complete, request
    authorization=dict(body=runtime.permit,signature='fixture-only')
    state=RehearsalState(runtime.directory/'operations',authorization,runtime,clock=runtime.clock)
    runtime.accept=lambda target,fresh:dict(scope='ISOLATED_EXECUTOR_NOT_DATA_PLANE',
        bundle_id=target,config=digest(canonical(runtime.verify_configuration(target))))
    active(state)
    first=runtime.pointer()
    original_table=runtime.executor.table
    runtime.contents=copy.deepcopy(runtime.contents)
    runtime.contents['metadata/revision.json']=canonical(dict(revision='B'))
    runtime.manifest=copy.deepcopy(runtime.manifest)
    runtime.manifest['bundle_id']=runtime.permit['bundle_b']
    for member in runtime.manifest['members']:
        content=runtime.contents[member['path']]
        member.update(sha256=digest(content),size=len(content))
    state.execute(request(state,'stage','-b',bundle='b'))
    start=runtime.start
    def fail_new(target):
        if target==runtime.permit['bundle_b']:
            raise FleetError('injected_B_failure')
        start(target)
    runtime.start=fail_new
    failure=state.execute(request(state,'upgrade','-bad',bundle='b'))
    assert failure['result']=='FAIL' and failure['rollback']=='PASS'
    assert runtime.pointer()==first
    assert runtime.executor.table.endswith(original_table)
    runtime.start=start
    assert state.execute(request(state,'upgrade','-good',bundle='b'))['result']=='AWAITING_EXTERNAL_ACCEPTANCE'
    complete(state,'-b',bundle='b')
    state.execute(request(state,'activate-local','-b',bundle='b'))
    assert runtime.pointer()==runtime.permit['bundle_b']
    assert state.execute(request(state,'rollback'))['result']=='AWAITING_EXTERNAL_ACCEPTANCE'
    complete(state,'-rollback')
    state.execute(request(state,'activate-local','-rollback'))
    assert runtime.pointer()==first
    assert state.execute(request(state,'drain'))['result']=='PASS'
    assert state.execute(request(state,'retire'))['result']=='PASS'
    assert state.status()['state']=='RETIRED' and runtime.pointer() is None
