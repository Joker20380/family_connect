import sys

from django.core.management.base import BaseCommand, CommandError

from apps.console.inventory import SnapshotError, strict_load
from apps.console.subscriptions import ingest


class Command(BaseCommand):
    help = 'Read-only production subscription observation from operator stdin only'

    def handle(self, **options):
        try:
            snapshot = ingest(strict_load(sys.stdin.buffer.read(4 * 1024 * 1024 + 1)))
        except SnapshotError as error:
            raise CommandError(str(error)) from None
        self.stdout.write(f'Subscription observation imported: {snapshot.status}; production writes: 0')
