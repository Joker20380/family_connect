"""Permit-bound operator workflow, separate from the synthetic fleetctl boundary."""

import argparse
import base64
import os
from pathlib import Path
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .contracts import FleetError, canonical, digest, fail, load
from .enrollment import EnrollmentStore
from .materials import public_hex
from .permit import ACTIONS, SCOPE
from .private_files import checked, read_private, write_private
from .rehearsal_materials import bind_enrollment
from .remote import RemoteInstaller
from .role_config import PORTS

COMMANDS=('prepare','plan','preflight','enroll','deliver-materials','stage','start-verification',
          'run-acceptance','complete-verification','activate-local','status','upgrade','rollback','reboot-verify','drain','retire')


def parser():
    root=argparse.ArgumentParser(prog='fleet-rehearsal',allow_abbrev=False)
    commands=root.add_subparsers(dest='action',required=True)
    prepare=commands.add_parser('prepare',allow_abbrev=False)
    for name in ('source-commit','artifact-root','private-key','output'):
        prepare.add_argument('--'+name,required=True)
    for action in COMMANDS[1:]:
        command=commands.add_parser(action,allow_abbrev=False)
        for name in ('permit','permit-key','bundle','bundle-key','known-hosts','fingerprint','host','user','instance','operation-id'):
            command.add_argument('--'+name,required=True)
        command.add_argument('--ssh-key')
        command.add_argument('--ipv6')
        command.add_argument('--output')
        if action in ('enroll','run-acceptance'):
            command.add_argument('--authority-key',required=True)
        if action=='enroll':
            command.add_argument('--operator-state',required=True)
        if action=='deliver-materials':
            command.add_argument('--create-materials',action='store_true')
            command.add_argument('--authority-key')
            command.add_argument('--operator-state')
        if action in ('deliver-materials','complete-verification','run-acceptance'):
            command.add_argument('--input',required=True)
        if action=='drain':
            command.add_argument('--recover-operation-id')
        if action=='reboot-verify':
            command.add_argument('--request-reboot',action='store_true')
    return root


def private_authority(path, expected):
    key=Ed25519PrivateKey.from_private_bytes(read_private(path,owner=os.geteuid(),limit=32))
    if public_hex(key.public_key())!=public_hex(expected):
        fail('operator_authority_binding')
    return key


def execute_known(remote, action, operation_id, parameters=None):
    parameters={} if parameters is None else parameters
    try:
        return remote.execute(action,operation_id,parameters)
    except FleetError as error:
        if str(error)!='remote_transport_failure':
            raise
        if action!='status':
            try:
                status=remote.execute('status',operation_id+'-reconcile')
                completed=[entry for entry in status['operations'] if entry['operation_id']==operation_id]
                if completed and completed[0]['result']!='RUNNING':
                    from .permit import replay_binding
                    replay_binding(completed[0]['binding'],remote.permit,dict(operation_id=operation_id,
                        action=action,bundle_id=remote.manifest['bundle_id'],parameters=parameters))
                    return completed[0]
            except Exception:
                pass
        return dict(scope=SCOPE,operation_id=operation_id,result='UNKNOWN',recovery='READ_JOURNAL_DO_NOT_RETRY')


def remote_for(args):
    permit=load(Path(args.permit).read_bytes())
    public=Ed25519PublicKey.from_public_bytes(Path(args.permit_key).read_bytes())
    bundle_key=Ed25519PublicKey.from_public_bytes(Path(args.bundle_key).read_bytes())
    if args.instance!=permit['body']['instance_id']:
        fail('operator_instance_binding')
    remote=RemoteInstaller(host=args.host,user=args.user,known_hosts=args.known_hosts,fingerprint=args.fingerprint,
        authorization=permit,permit_key=public,bundle=args.bundle,bundle_key=bundle_key)
    if args.ssh_key:
        path=checked(Path(args.ssh_key).absolute(),owner=os.geteuid())
        if path.stat().st_mode & 0o077:
            fail('ssh_private_key_permissions')
        remote.ssh.argv[-1:-1]=['-i',str(path),'-o','IdentitiesOnly=yes']
    return remote


def dispatch(args):
    if args.action=='prepare':
        from .package import prepare
        return prepare(args.source_commit,Path(args.artifact_root),Path(args.private_key),Path(args.output))
    remote=remote_for(args)
    if args.action=='plan':
        return dict(scope=SCOPE,action='plan',instance_id=args.instance,bundle_id=remote.manifest['bundle_id'],
                    roles=remote.manifest['roles'],source_commit=remote.manifest['source_commit'],remote_writes=0)
    remote.authorize(args.action)
    if args.action=='status':
        result = execute_known(remote,'status',args.operation_id)
        try:
            result['diagnostics'] = remote.diagnostics(dict(instance_id=args.instance,ipv4=args.host,ipv6=args.ipv6))
        except Exception:
            result['diagnostics'] = dict(result='UNAVAILABLE',remote_writes=0)
        return result
    instance=dict(instance_id=args.instance,ipv4=args.host,ipv6=args.ipv6)
    ports=list(PORTS.values()) if args.action in ('preflight','enroll') else []
    report=remote.preflight(instance,ports)
    if args.action=='preflight':
        return report
    if args.action=='enroll':
        authority=private_authority(args.authority_key,remote.permit_key)
        directory=checked(Path(args.operator_state).absolute(),directory=True,owner=os.geteuid())
        if directory.stat().st_mode & 0o077:
            fail('operator_state_permissions')
        store=EnrollmentStore(directory/'enrollment.sqlite',authority,scope='rehearsal')
        binding={name:remote.permit['body'][name] for name in ('instance_id','logical_gateway','provider','region','ipv4')}
        binding.update(bundle_id=remote.manifest['bundle_id'],roles=remote.manifest['roles'])
        token,challenge=store.issue(binding)
        proof=execute_known(remote,'enroll',args.operation_id+'-prove',dict(phase='prove',challenge=challenge['challenge'],expires_at=challenge['expires_at']))
        if proof['result']=='UNKNOWN':
            return proof
        if proof['result']!='PASS':
            fail('operator_enrollment_proof')
        public=proof['evidence']
        if public['binding']!=binding:
            fail('operator_enrollment_binding')
        receipt=store.enroll(token,binding,public['public_key'],base64.b64decode(public['identity_proof'],validate=True))
        material_receipt=bind_enrollment(public['material_binding'],challenge['challenge'],
            base64.b64decode(public['material_proof'],validate=True),authority,receipt)
        write_private(directory/(args.instance+'-enrollment.json'),canonical(receipt))
        write_private(directory/(args.instance+'-material-enrollment.json'),canonical(material_receipt))
        return execute_known(remote,'enroll',args.operation_id,dict(phase='commit',enrollment=receipt,material_enrollment=material_receipt))
    if args.action=='run-acceptance':
        from .operator_harness import Harness, run
        authority=private_authority(args.authority_key,remote.permit_key)
        observation=execute_known(remote,'status',args.operation_id+'-status')
        if observation.get('result')=='UNKNOWN':
            return observation
        status=observation['state']
        if status['state']!='AWAITING_EXTERNAL_ACCEPTANCE' or status['verification']['bundle_id']!=remote.manifest['bundle_id']:
            fail('operator_verification_challenge_required')
        harness=Harness(load(read_private(args.input,owner=os.geteuid())),remote.contents,remote.manifest,
                        target=args.host,challenge=status['verification'])
        return run(harness,authority)
    parameters={}
    if args.action=='reboot-verify' and args.request_reboot:
        parameters=dict(phase='request')
    if args.action in ('deliver-materials','complete-verification'):
        parameters['envelope' if args.action=='deliver-materials' else 'receipt']=load(read_private(args.input,owner=os.geteuid()))
        if args.action=='deliver-materials' and args.create_materials:
            from .material_factory import prepare
            if not args.authority_key or not args.operator_state:
                fail('operator_material_custody_required')
            authority=private_authority(args.authority_key,remote.permit_key)
            enrollment=load(read_private(Path(args.operator_state)/(args.instance+'-material-enrollment.json'),owner=os.geteuid()))
            parameters['envelope']=prepare(remote.permit,enrollment,authority,parameters['envelope'],args.operator_state)
    if args.action=='drain' and args.recover_operation_id:
        status=execute_known(remote,'status',args.operation_id+'-status')
        if status.get('result')=='UNKNOWN':
            return status
        matches=[entry for entry in status['operations'] if entry['operation_id']==args.recover_operation_id and entry['result']=='RUNNING']
        if len(matches)!=1:
            fail('operator_recovery_journal_required')
        parameters=dict(recover_operation_id=args.recover_operation_id,recover_binding=matches[0]['binding'])
    return execute_known(remote,args.action,args.operation_id,parameters)


def main():
    args=parser().parse_args()
    try:
        receipt=dispatch(args)
        payload=canonical(receipt)
        if args.output and args.action!='prepare':
            write_private(Path(args.output).absolute(),payload)
        print(payload.decode())
    except Exception:
        print(canonical(dict(scope=SCOPE,action=args.action,result='REJECTED',error='operator_contract_or_gate_failed')).decode())
        raise SystemExit(1) from None


if __name__=='__main__':
    main()
