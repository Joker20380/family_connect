from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

from fleet.contracts import canonical, load
from apps.fleet.workflow import record_completion


class Command(BaseCommand):
    help = 'Принять локальный synthetic receipt; никаких production операций'

    def add_arguments(self, parser):
        parser.add_argument('operation_id')
        parser.add_argument('--operator',required=True)
        parser.add_argument('--receipt',required=True)
        parser.add_argument('--health')

    def handle(self, *args, **options):
        try:
            actor=get_user_model().objects.get(username=options['operator'])
            raw=Path(options['receipt']).read_bytes()
            if len(raw)>65536:raise ValueError('receipt_bound')
            health=load(Path(options['health']).read_bytes()) if options['health'] else None
            result=record_completion(actor,options['operation_id'],load(raw),health)
            self.stdout.write(canonical(dict(operation_id=str(result.pk),state=result.state)).decode())
        except (OSError,ValueError,ValidationError) as error:
            raise CommandError('Локальный receipt отклонён; значения скрыты.') from error
