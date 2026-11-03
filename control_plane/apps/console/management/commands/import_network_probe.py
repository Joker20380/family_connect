import sys

from django.core.management.base import BaseCommand, CommandError

from apps.console.inventory import strict_load, SnapshotError
from apps.console.probe_inventory import ingest


class Command(BaseCommand):
    help = 'Импорт независимой TCP-пробы из stdin; без доступа к серверам и без восстановления'

    def handle(self, **options):
        try:
            sample = ingest(strict_load(sys.stdin.buffer.read(4097)))
        except SnapshotError as error:
            raise CommandError(str(error)) from None
        self.stdout.write(f'Проба {sample.pk}: {sample.source}; автоматические действия: 0')
