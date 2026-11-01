from django.core.management.base import BaseCommand

from fleet.contracts import canonical
from apps.fleet.models import DeploymentOperation


class Command(BaseCommand):
    help = 'Экспорт безопасного локального intent; SSH не выполняется'

    def add_arguments(self, parser):
        parser.add_argument('operation_id')

    def handle(self, *args, **options):
        intent=DeploymentOperation.objects.get(pk=options['operation_id'],state='INTENT')
        self.stdout.write(canonical(dict(operation_id=str(intent.pk),instance_id=intent.instance_id,
            action=intent.action,bundle_id=intent.target_bundle_id,scope='synthetic')).decode())
