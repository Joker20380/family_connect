import sys
from control.friends.pseudonyms import unseal

from django.core.management.base import BaseCommand, CommandError

from apps.console.inventory import SnapshotError, strict_load
from apps.console.subscriptions import ingest, record_attempt


class Command(BaseCommand):
    help = 'Read-only production subscription observation from operator stdin only'

    def add_arguments(self, parser):
        parser.add_argument('--failure', choices=('collection_failed', 'import_failed'))

    def handle(self, **options):
        if options['failure']:
            record_attempt(options['failure'])
            self.stdout.write('Subscription attempt failure recorded; production writes: 0')
            return
        try:
            snapshot = ingest(unseal(strict_load(sys.stdin.buffer.read(4 * 1024 * 1024 + 1)), 'subscriptions'), attempt=True)
        except (SnapshotError, ValueError, OSError, KeyError, TypeError):
            record_attempt('import_failed')
            raise CommandError('Subscription import rejected; no payload logged') from None
        self.stdout.write(f'Subscription observation imported: {snapshot.status}; production writes: 0')
