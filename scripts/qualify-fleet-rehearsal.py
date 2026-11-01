#!/usr/bin/env python3
"""Offline Ubuntu container qualification; never physical data-plane acceptance."""

import argparse
import base64
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from fleet.acceptance import SCOPE as ACCEPTANCE_SCOPE, STEPS, sign as sign_acceptance
from fleet.bundle import verify
from fleet.contracts import FleetError, canonical, digest, load
from fleet.enrollment import EnrollmentStore
from fleet.material_factory import generate, raw_public
from fleet.materials import public_hex, seal
from fleet.permit import ACTIONS, SCOPE, sign
from fleet.private_files import write_private
from fleet.rehearsal_materials import bind_enrollment
from fleet.rehearsal_state import RehearsalState
from fleet.rehearsal_templates import TABLE, nftables
from fleet.remote_agent import verified_upload
from fleet.remote_bootstrap import python_dependencies, verify_bundle_payload
from fleet.role_runtime import Runtime
from fleet.tests.test_role_runtime import IsolatedExecutor


def command(argv, *, content=None):
    result=subprocess.run(argv,input=content,capture_output=True,timeout=90)
    if result.returncode:
        raise FleetError('qualification_command_failed:'+Path(argv[0]).name)
    return result.stdout


def qualify(package, output):
    if (not Path('/.dockerenv').exists() or os.geteuid()!=0 or platform.machine()!='x86_64'
            or 'VERSION_ID="24.04"' not in Path('/etc/os-release').read_text()):
        raise FleetError('isolated_ubuntu24_container_required')
    os.umask(0o077)
    key=Ed25519PublicKey.from_public_bytes((package/'bundle.pub').read_bytes())
    bundles={name:verify(package/(name+'-first'),key) for name in ('A','B')}
    receipt=load((package/'receipt.json').read_bytes())
    repository=Path(__file__).resolve().parents[1]
    for name,content in bundles['A'][1].items():
        if name.startswith('runtime/fleet/'):
            assert (repository/name.removeprefix('runtime/')).read_bytes()==content
    assert set(bundles['A'][1])==set(bundles['B'][1])
    changed=[name for name in bundles['A'][1] if bundles['A'][1][name]!=bundles['B'][1][name]]
    assert changed==['metadata/revision.json']
    for revision in bundles:
        folder=package/(revision+'-first')
        files={path.name:base64.b64encode(path.read_bytes()).decode() for path in folder.iterdir()}
        request=dict(bundle=files,bundle_key=public_hex(key),operation=dict(bundle_id=bundles[revision][0]['bundle_id']))
        assert verify_bundle_payload(request)==bundles[revision][1]
        with tempfile.TemporaryDirectory() as temporary:
            assert verified_upload(files,key,bundles[revision][0]['bundle_id'],Path(temporary))==bundles[revision]
    with tempfile.TemporaryDirectory(prefix='fc-qualified-') as temporary:
        workspace=Path(temporary)
        dependencies=python_dependencies(bundles['A'][1],workspace)
        assert python_dependencies(bundles['B'][1],workspace)==dependencies
        damaged=dict(bundles['A'][1])
        wheel=load(damaged['metadata/python-dependencies.json'])['wheels'][0]['path']
        damaged[wheel]=b'damaged-wheel-not-installed'
        try:
            python_dependencies(damaged,workspace)
        except ValueError:
            pass
        else:
            raise AssertionError('damaged wheel admitted')
        observed=command(['/usr/bin/python3','-I','-B','-c',
            "import sys;sys.path.insert(0,sys.argv[1]);import cryptography,cffi,pycparser;print(cryptography.__version__,cffi.__version__,pycparser.__version__)",str(dependencies)])
        assert observed.strip()==b'46.0.7 2.1.1 3.00'
        binary=workspace/'native'
        binary.mkdir()
        for name in ('amneziawg-go','awg','xray','gateway'):
            path=binary/name
            path.write_bytes(bundles['A'][1]['bin/'+name])
            path.chmod(0o500)
            command([str(path),'version' if name=='xray' else '-h' if name=='gateway' else '--version'])
        nft=nftables('eth0')
        command(['nft','-c','-f','-'],content=nft)
        command(['nft','-f','-'],content=b'table inet fc_qualification_neighbor {\n chain sentinel {\n }\n}\n')
        neighbor=command(['nft','-s','list','table','inet','fc_qualification_neighbor'])
        command(['nft','-f','-'],content=nft)
        predecessor=command(['nft','-s','list','table','inet',TABLE])
        command(['nft','-f','-'],content=b'delete table inet family_connect_rehearsal\n'+nftables('eth1'))
        command(['nft','-f','-'],content=b'delete table inet family_connect_rehearsal\n'+predecessor)
        assert command(['nft','-s','list','table','inet',TABLE])==predecessor
        command(['nft','delete','table','inet',TABLE])
        assert command(['nft','-s','list','table','inet','fc_qualification_neighbor'])==neighbor
        command(['nft','delete','table','inet','fc_qualification_neighbor'])
        scenario(workspace,bundles,receipt)
    result=dict(schema=1,scope='ISOLATED_SOURCE_PACKAGE_QUALIFICATION',source_commit=receipt['source_commit'],
        platform='Ubuntu24.04/x86_64',target_reverification='PASS',pinned_python_dependencies='PASS',
        qualification_source_sha256=digest(Path(__file__).read_bytes()),
        native_help_version_config_test='PASS',unit_verification='PASS',nft_syntax_coexistence_rollback='PASS',
        material_delivery_fake_root='PASS',service_account_modes='PASS',two_phase_synthetic_acceptance='PASS',ab_installation='PASS',
        injected_b_failure_rollback_a='PASS',b_upgrade='PASS',explicit_rollback='PASS',retirement='PASS',
        real_systemd_start='NOT_RUN',awg_handshake='NOT_RUN',tcp_tunnel='NOT_RUN',mesh_data_plane='NOT_RUN',
        reboot_persistence='NOT_RUN',production_writes=0,catalog_publications=0,user_invitations=0,paid_events=0,phone_actions=0)
    write_private(output,canonical(result))
    return result


def scenario(workspace,bundles,package_receipt):
    now=int(time.time())
    authority=Ed25519PrivateKey.generate()
    body=dict(schema=1,scope=SCOPE,permit_id='offline-qualification',instance_id='fleet-rehearsal-offline',
        logical_gateway='fleet-rehearsal',ipv4='8.8.8.8',ssh_fingerprint='SHA256:'+'A'*43,
        provider='offline-container',region='isolated',bundle_a=bundles['A'][0]['bundle_id'],bundle_b=bundles['B'][0]['bundle_id'],
        allowed_actions=list(ACTIONS),issued_at=now,expires_at=now+3600,catalog_publication=False,
        production_identity_import=False,user_operations=False,paid_operations=False,
        agent_sha256=package_receipt['agent_sha256'],bundle_signer_sha256=package_receipt['bundle_signer_sha256'])
    permit=sign(body,authority,now=now)
    root=workspace/'root'
    for name in ('opt','etc/sysctl.d','etc/systemd/system','var/lib/family-connect-rehearsal','run','proc/sys/kernel/random'):
        (root/name).mkdir(parents=True,exist_ok=True)
    (root/'proc/sys/kernel/random/boot_id').write_text('offline-boot-not-reboot-evidence')
    directory=root/'var/lib/family-connect-rehearsal'/body['instance_id']
    directory.mkdir(mode=0o700)
    runtime=Runtime(manifest=bundles['A'][0],contents=bundles['A'][1],authorization=permit,authority=authority.public_key(),
        directory=directory,root=root,executor=IsolatedExecutor(),clock=lambda:now+1)
    account=Runtime.service_account(SimpleNamespace(root=Path('/'),command=lambda *argv:command(list(argv))))
    assert account[0]>0 and account[1]>0
    runtime.service_account=lambda:account
    binding={name:body[name] for name in ('instance_id','logical_gateway','provider','region','ipv4')}
    binding.update(bundle_id=body['bundle_a'],roles=bundles['A'][0]['roles'])
    store=EnrollmentStore(workspace/'operator.sqlite',authority,scope='rehearsal',clock=lambda:now)
    token,challenge=store.issue(binding)
    proof=runtime.enroll(dict(phase='prove',challenge=challenge['challenge'],expires_at=challenge['expires_at']))
    enrollment=store.enroll(token,binding,proof['public_key'],base64.b64decode(proof['identity_proof']))
    material_enrollment=bind_enrollment(proof['material_binding'],challenge['challenge'],base64.b64decode(proof['material_proof']),authority,enrollment)
    runtime.enroll(dict(phase='commit',enrollment=enrollment,material_enrollment=material_enrollment))
    identity=Ed25519PrivateKey.generate()
    public=raw_public(X25519PrivateKey.generate())+raw_public(identity)
    slots,unused=generate(body['instance_id'],public,identity,canonical(dict(scope=SCOPE,token='synthetic-offline-only')),
                          issued_at=now,expires_at=now+3600)
    envelope=seal(proof['material_binding'],slots,authority,issued_at=now,expires_at=now+3600)
    runtime.material_store().deliver(envelope,permit_expires_at=body['expires_at'],now=now+1)
    state=RehearsalState(directory/'operations',permit,runtime,clock=lambda:now+1)
    runtime.accept=lambda target,fresh:dict(scope='ISOLATED_EXECUTOR_NOT_DATA_PLANE',bundle_id=target,
                                          configuration=digest(canonical(runtime.verify_configuration(target))))
    counter=0
    def operate(action,revision='A',parameters=None):
        nonlocal counter
        counter+=1
        return state.execute(dict(operation_id='offline-'+str(counter),action=action,bundle_id=body['bundle_'+revision.lower()],parameters=parameters or {}))
    def complete(revision):
        challenge=state.status()['verification']
        data={name:challenge[name] for name in ('instance_id','bundle_id','operation_id','verification_nonce','ipv4','local_health_sha256')}
        data.update(schema=1,scope=ACCEPTANCE_SCOPE,roles={role:{step:'PASS' for step in steps} for role,steps in STEPS.items()},
                    issued_at=now+1,expires_at=now+200,external_evidence_sha256=digest(b'OFFLINE_SYNTHETIC_ONLY'),cleanup='PASS',
                    signer=digest(bytes.fromhex(public_hex(authority.public_key()))))
        signed=sign_acceptance(data,authority,now=now+1)
        assert operate('complete-verification',revision,dict(receipt=signed))['result']=='PASS'
        assert operate('activate-local',revision)['result']=='PASS'
    runtime.stage(body['bundle_a'])
    assert operate('stage')['result']=='PASS'
    assert operate('start-verification')['result']=='AWAITING_EXTERNAL_ACCEPTANCE'
    assert operate('complete-verification')['result']=='AWAITING_EXTERNAL_ACCEPTANCE'
    config=runtime.configuration/body['bundle_a']
    assert (config/'profile/gateway.json').stat().st_gid==account[1]
    assert (config/'profile/gateway.json').stat().st_mode & 0o777==0o640
    assert (config/'publisher.env').stat().st_mode & 0o777==0o600
    command([str(runtime.releases/body['bundle_a']/'bin/xray'),'run','-test','-config',str(config/'tcp.json')])
    with tempfile.TemporaryDirectory() as temporary:
        files=[]
        for source in (config/'units').iterdir():
            preview=Path(temporary)/source.name
            preview.write_bytes(source.read_bytes().replace(b'/opt/family-connect/current',str(runtime.releases/body['bundle_a']).encode()))
            files.append(str(preview))
        command(['systemd-analyze','verify',*files])
    complete('A')
    runtime.manifest,runtime.contents=bundles['B']
    assert operate('stage','B')['result']=='PASS'
    start=runtime.start
    def fail_b(target):
        if target==body['bundle_b']:
            raise FleetError('offline_injected_b_failure')
        start(target)
    runtime.start=fail_b
    failure=operate('upgrade','B')
    assert failure['result']=='FAIL' and failure['rollback']=='PASS' and runtime.pointer()==body['bundle_a']
    runtime.start=start
    assert operate('upgrade','B')['result']=='AWAITING_EXTERNAL_ACCEPTANCE'
    complete('B')
    assert runtime.pointer()==body['bundle_b']
    assert operate('rollback')['result']=='AWAITING_EXTERNAL_ACCEPTANCE'
    complete('A')
    assert runtime.pointer()==body['bundle_a']
    assert operate('drain')['result']=='PASS'
    assert operate('retire')['result']=='PASS'
    assert state.status()['state']=='RETIRED' and runtime.pointer() is None
    assert not (directory/'slots').exists() and not (directory/'material.key').exists() and not (directory/'identity.key').exists()
    assert not runtime.sysctl.exists() and runtime.executor.table is None


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    arguments=parser.parse_args()
    print(canonical(qualify(arguments.package,arguments.output)).decode())
