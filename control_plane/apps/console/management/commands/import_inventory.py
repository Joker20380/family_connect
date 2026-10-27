import sys
from django.core.management.base import BaseCommand, CommandError
from apps.console.inventory import ingest, strict_load, SnapshotError


class Command(BaseCommand):
    help = 'Импорт проверенного production-readonly снимка из stdin; нет подключения к production'

    def handle(self, **options):
        try:
            snapshot = ingest(strict_load(sys.stdin.buffer.read(4 * 1024 * 1024 + 1)))
        except SnapshotError as error:
            raise CommandError(str(error)) from None
        self.stdout.write(f'Импортирован снимок {snapshot.pk}; устройств: {snapshot.devices.count()}; production writes: 0')
