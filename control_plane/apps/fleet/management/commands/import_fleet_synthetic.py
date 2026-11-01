import ipaddress
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from fleet.bundle import verify
from fleet.contracts import canonical, digest, inventory, load
from apps.fleet.models import GatewayArtifact, LogicalGateway, GatewayInstance


class Command(BaseCommand):
    help = 'Импорт проверенного synthetic inventory; не подключается к серверам'

    def add_arguments(self, parser):
        parser.add_argument('--inventory',required=True)
        parser.add_argument('--bundle',required=True)
        parser.add_argument('--public-key',required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            data=inventory(load(Path(options['inventory']).read_bytes()))
            key=Ed25519PublicKey.from_public_bytes(Path(options['public_key']).read_bytes())
            manifest,contents=verify(options['bundle'],key)
            if manifest['scope']!='synthetic' or len(data['artifacts'])!=1:
                raise ValueError('synthetic_only')
            artifact=data['artifacts'][0]
            expected=dict(bundle_id=manifest['bundle_id'],source_commit=manifest['source_commit'],
                manifest_sha256=digest(canonical(manifest)),archive_sha256=manifest['archive_sha256'],
                signature=(Path(options['bundle'])/'manifest.sig').read_text(),supported_os=manifest['supported_os'],
                architectures=[manifest['architecture']],roles=manifest['roles'])
            if {key:value for key,value in artifact.items() if key!='created_at'}!=expected:
                raise ValueError('artifact_binding')
            stored,created=GatewayArtifact.objects.get_or_create(bundle_id=expected['bundle_id'],defaults={**expected,'signature_verified':True})
            if not stored.signature_verified or any(getattr(stored,key)!=value for key,value in expected.items()):
                raise ValueError('existing_artifact_conflict')
            for gateway in data['logical_gateways']:
                if gateway['active_instance'] is not None or gateway['fallback_instances']:
                    raise ValueError('synthetic_initial_state')
                expected_gateway={key:gateway[key] for key in ('country','transports','desired_state','catalog_generation')}
                stored_gateway,created=LogicalGateway.objects.get_or_create(id=gateway['id'],defaults=expected_gateway)
                if any(getattr(stored_gateway,key)!=value for key,value in expected_gateway.items()):
                    raise ValueError('existing_gateway_conflict')
            networks=[ipaddress.ip_network(value) for value in ('192.0.2.0/24','198.51.100.0/24','203.0.113.0/24')]
            for node in data['instances']:
                if node['state']!='DISCOVERED' or node['actual_bundle'] is not None or node['enrollment_state']!='NEW' or not any(ipaddress.ip_address(node['ipv4']) in network for network in networks):
                    raise ValueError('synthetic_instance_only')
                values=dict(node)
                for field in ('logical_gateway','desired_bundle','actual_bundle'):
                    values[field+'_id']=values.pop(field)
                stored_node,created=GatewayInstance.objects.get_or_create(instance_id=node['instance_id'],defaults=values)
                if any(getattr(stored_node,key)!=value for key,value in values.items() if not key.endswith('_at')):
                    raise ValueError('existing_instance_conflict')
            self.stdout.write(canonical(dict(result='PASS',scope='synthetic',instances=len(data['instances']),remote_writes=0)).decode())
        except (OSError,ValueError) as error:
            raise CommandError('Synthetic inventory отклонён; значения скрыты.') from error
