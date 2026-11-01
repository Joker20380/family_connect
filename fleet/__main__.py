import argparse
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .bundle import verify
from .contracts import FleetError, canonical, digest, fail, inventory, load
from .installer import SandboxInstaller
from .preflight import SSH, accept


def main():
    parser = argparse.ArgumentParser(prog='fleetctl', description='SOURCE/SYNTHETIC ONLY; no live activation or catalog publication')
    parser.add_argument('action', choices=['plan','preflight','stage','verify','activate','rollback','status','drain','quarantine'])
    parser.add_argument('--inventory', required=True)
    parser.add_argument('--instance', required=True)
    parser.add_argument('--host')
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--public-key', required=True)
    parser.add_argument('--sandbox-root')
    parser.add_argument('--operation-id')
    parser.add_argument('--host-report')
    parser.add_argument('--health-report')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--known-hosts')
    parser.add_argument('--fingerprint')
    parser.add_argument('--ssh-user', default='root')
    parser.add_argument('--ports', type=int, nargs='+')
    arguments = parser.parse_args()
    try:
        data = inventory(load(Path(arguments.inventory).read_bytes()))
        matches = [item for item in data['instances'] if item['instance_id']==arguments.instance]
        if len(matches)!=1:
            fail('instance_not_found')
        instance = matches[0]
        if arguments.host is not None and arguments.host != instance['ipv4']:
            fail('host_binding')
        key = Ed25519PublicKey.from_public_bytes(Path(arguments.public_key).read_bytes())
        manifest, contents = verify(arguments.bundle,key,instance['desired_bundle'])
        artifact = next(item for item in data['artifacts'] if item['bundle_id']==manifest['bundle_id'])
        if (artifact['manifest_sha256'] != digest(canonical(manifest)) or artifact['archive_sha256'] != manifest['archive_sha256']
                or artifact['source_commit'] != manifest['source_commit'] or artifact['roles'] != manifest['roles']
                or artifact['supported_os'] != manifest['supported_os'] or artifact['architectures'] != [manifest['architecture']]
                or artifact['signature'] != (Path(arguments.bundle)/'manifest.sig').read_text()):
            fail('artifact_binding')
        if arguments.action=='plan' or arguments.dry_run:
            result=dict(scope='synthetic',instance_id=instance['instance_id'],bundle_id=manifest['bundle_id'],remote_writes=0,dry_run=arguments.dry_run)
        elif arguments.action=='preflight' and not arguments.sandbox_root:
            remote=SSH(instance['ipv4'],arguments.ssh_user,arguments.known_hosts,arguments.fingerprint)
            report=accept(remote.probe(instance,arguments.ports),instance)
            result=dict(result='PASS',scope='READONLY_REMOTE_PREFLIGHT',report=report,remote_writes=0)
        else:
            if not arguments.sandbox_root:
                fail('live_rehearsal_required')
            installer=SandboxInstaller(arguments.sandbox_root,instance,arguments.bundle,key)
            if arguments.action=='status':
                result=installer.status()
            else:
                report=load(Path(arguments.host_report).read_bytes()) if arguments.host_report else None
                checks=load(Path(arguments.health_report).read_bytes()) if arguments.health_report else None
                result=installer.execute(arguments.action,arguments.operation_id,report=report,health_report=checks)
        print(canonical(result).decode())
    except (FleetError,OSError,ValueError,TypeError,KeyError,StopIteration) as error:
        print(canonical(dict(result='FAIL',code=str(error) if isinstance(error,FleetError) else 'invalid_input')).decode())
        raise SystemExit(1)


if __name__=='__main__':
    main()
