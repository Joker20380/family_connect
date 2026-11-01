"""One-command, disposable filesystem acceptance; explicitly not VPN acceptance."""

import argparse
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

import cryptography
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .bundle import build, verify
from .contracts import ROLES, canonical, digest, fail, load
from .enrollment import EnrollmentStore, generate_node_key, proof_payload
from .health import required, run_hooks


def run(output, source_commit):
    os.umask(0o077)
    root=Path(__file__).resolve().parents[1]
    output=Path(output).resolve()
    output.mkdir(mode=0o700,parents=True,exist_ok=False)
    paths=sorted(list((root/'fleet').glob('*.py'))+list((root/'fleet/templates').glob('*'))+
                 [root/'scripts/fleetctl',root/'fleet/requirements.lock',root/'LICENSE'])
    members=[]
    for path in paths:
        relative=str(path.relative_to(root))
        expected=subprocess.check_output(['git','show',source_commit+':'+relative],cwd=root)
        if expected!=path.read_bytes():
            fail('simulation_source_not_committed')
        members.append(dict(path=relative,source=relative,sha256=digest(expected),mode=0o555 if path.name=='fleetctl' else 0o444,
                            restart_group='monitoring',secret_slots=[]))
    signing=Ed25519PrivateKey.from_private_bytes(bytes([7])*32)
    authority=Ed25519PrivateKey.from_private_bytes(bytes([8])*32)
    slots=['awg-material','tcp-reality-material','mesh-material','monitoring-material']
    spec=dict(source_commit=source_commit,scope='synthetic',roles=list(ROLES),secret_slots=slots,members=members)
    first=build(root,spec,signing,output/'bundle-a')
    second=build(root,spec,signing,output/'bundle-b')
    for path in (output/'bundle-a').iterdir():
        if path.read_bytes()!=(output/'bundle-b'/path.name).read_bytes():
            fail('bundle_not_reproducible')
    verify(output/'bundle-a',signing.public_key(),first['bundle_id'])
    public=signing.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    (output/'bundle-public.key').write_bytes(public)
    (output/'enrollment-public.key').write_bytes(authority.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw))
    private=output/'private';private.mkdir(mode=0o700)
    binding=dict(instance_id='nl-test-001',logical_gateway='nl',bundle_id=first['bundle_id'],provider='synthetic',region='test',ipv4='192.0.2.10',roles=list(ROLES))
    store=EnrollmentStore(private/'enrollment.sqlite3',authority)
    token,challenge=store.issue(binding)
    public_identity=generate_node_key(private/'node.key')
    node_key=Ed25519PrivateKey.from_private_bytes((private/'node.key').read_bytes())
    enrolled=store.enroll(token,binding,public_identity,node_key.sign(proof_payload(binding,challenge['challenge'],public_identity)))
    (private/'enrollment-receipt.json').write_bytes(canonical(enrolled))
    node=dict(instance_id='nl-test-001',logical_gateway='nl',provider='synthetic',region='test',ipv4='192.0.2.10',ipv6=None,
        os_family='ubuntu',os_version='24.04',architecture='x86_64',state='DISCOVERED',desired_bundle=first['bundle_id'],
        actual_bundle=None,enrollment_state='ENROLLED',health_state='UNKNOWN',deployment_identity=digest(bytes.fromhex(public_identity)),roles=list(ROLES),
        created_at='2026-11-01T00:00:00Z',activated_at=None,drained_at=None,quarantined_at=None)
    artifact=dict(bundle_id=first['bundle_id'],source_commit=source_commit,manifest_sha256=digest(canonical(first)),
        archive_sha256=first['archive_sha256'],signature=(output/'bundle-a/manifest.sig').read_text(),supported_os=first['supported_os'],
        architectures=[first['architecture']],roles=list(ROLES),created_at='2026-11-01T00:00:00Z')
    inventory=dict(schema=1,logical_gateways=[dict(id='nl',country='NL',transports=['awg','tcp','mesh'],desired_state='ACTIVE',active_instance=None,
        fallback_instances=[],catalog_generation=4)],instances=[node],artifacts=[artifact])
    (private/'inventory.json').write_bytes(canonical(inventory))
    host=dict(os='ubuntu',version='24.04',architecture='x86_64',kernel='6.8.0-generic',cpu=2,ram_mb=2048,disk_mb=4096,time_sync=True,tun=True,
        ipv4='192.0.2.10',ipv6=None,resolver=True,https=True,systemd=True,firewall='nftables',security='apparmor-supported',ports_available=True,
        pending_reboot=False,existing_instance=None)
    (private/'host.json').write_bytes(canonical(host))
    health=run_hooks(node['instance_id'],first['bundle_id'],list(ROLES),{name:lambda:True for name in required(ROLES)})
    (private/'health.json').write_bytes(canonical(health))
    receipts=[]
    with tempfile.TemporaryDirectory(prefix='fc-fleet-sim-') as temporary:
        sandbox=Path(temporary)/'instance'
        common=['--inventory',str(private/'inventory.json'),'--instance',node['instance_id'],'--bundle',str(output/'bundle-a'),
            '--public-key',str(output/'bundle-public.key'),'--sandbox-root',str(sandbox),
            '--enrollment-receipt',str(private/'enrollment-receipt.json'),'--enrollment-key',str(output/'enrollment-public.key')]
        for action in ('plan','preflight','stage','verify','activate','status','rollback','status'):
            arguments=[sys.executable,'-m','fleet',action]+common
            if action not in ('plan','status'):arguments+=['--operation-id','sim-'+action]
            if action=='preflight':arguments+=['--host-report',str(private/'host.json')]
            if action=='verify':arguments+=['--health-report',str(private/'health.json')]
            result=subprocess.run(arguments,cwd=root,capture_output=True,text=True,timeout=90)
            if result.returncode:
                fail('simulation_cli_'+action)
            receipts.append(load(result.stdout))
            if action=='stage':
                for slot in slots:
                    path=sandbox/'etc/family-connect'/(slot+'.slot')
                    path.write_bytes(b'SYNTHETIC_ONLY_NOT_A_TRANSPORT_CREDENTIAL')
                    path.chmod(0o600)
        if receipts[-1]['state']!='DISCOVERED':
            fail('simulation_rollback')
    (private/'operation-receipts.json').write_bytes(canonical(receipts))
    result=dict(status='SYNTHETIC_FILESYSTEM_ACCEPTANCE_PASS',source_commit=source_commit,bundle_id=first['bundle_id'],
        archive_sha256=first['archive_sha256'],manifest_sha256=digest(canonical(first)),hash_inventory_sha256=digest((output/'bundle-a/sha256.json').read_bytes()),
        signature_sha256=digest((output/'bundle-a/manifest.sig').read_bytes()),member_count=len(members),build_twice_identical=True,
        roles=list(ROLES),health_checks=len(required(ROLES)),enrollment='POSSESSION_AND_SIGNED_RECEIPT_PASS',
        cli=['plan','preflight','stage','verify','activate','status','rollback'],rollback='EMPTY_INACTIVE_BOOTSTRAP',
        ownership='CURRENT_UID_SYNTHETIC_MAPPING',host_report='EXPLICIT_SYNTHETIC_FIXTURE_NOT_OS_ATTESTATION',
        vpn_dataplane='NOT_RUN',production_writes=0,user_invitations=0,paid_events=0,phone_actions=0,
        signing_scope='EXPLICIT_PUBLIC_SYNTHETIC_TEST_KEY',signer_public_sha256=digest(public),
        toolchain=dict(python=platform.python_version(),cryptography=cryptography.__version__,
            zstd=subprocess.check_output(['zstd','--version'],text=True,timeout=5).strip()))
    (output/'receipt.json').write_bytes(canonical(result))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--source-commit',required=True)
    arguments=parser.parse_args()
    print(canonical(run(arguments.output,arguments.source_commit)).decode())


if __name__=='__main__':
    main()
