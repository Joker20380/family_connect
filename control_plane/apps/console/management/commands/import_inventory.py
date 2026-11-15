import sys
from control.friends.pseudonyms import unseal
from django.core.management.base import BaseCommand, CommandError
from apps.console.inventory import ingest, strict_load, SnapshotError
from apps.console.subscriptions import record_attempt


class Command(BaseCommand):
    help = 'Импорт проверенного production-readonly снимка из stdin; нет подключения к production'

    def add_arguments(self, parser):
        parser.add_argument('--subscription-attempt', action='store_true')

    def handle(self, **options):
        try:
            snapshot = ingest(unseal(strict_load(sys.stdin.buffer.read(4 * 1024 * 1024 + 1)), 'inventory'),
                              subscription_attempt=options['subscription_attempt'])
        except (SnapshotError, ValueError, OSError, KeyError, TypeError):
            if options['subscription_attempt']:
                record_attempt('import_failed')
            raise CommandError('Inventory import rejected; no payload logged') from None
        self.stdout.write(f'Импортирован снимок {snapshot.pk}; устройств: {snapshot.devices.count()}; production writes: 0')
