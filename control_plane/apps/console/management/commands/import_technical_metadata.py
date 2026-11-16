import sys
from control.friends.pseudonyms import unseal
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.console.inventory import SnapshotError
from apps.console.technical_metadata import MAX_EXPORT_BYTES, load_export, ingest, prune


class Command(BaseCommand):
    help = 'Replace latest technical metadata from stdin; never save an append-only snapshot'

    def add_arguments(self, parser):
        parser.add_argument('--unavailable', action='store_true')

    def handle(self, **options):
        prune()
        try:
            data = dict(schema=1, source='gateway-ru', observed_at=int(timezone.now().timestamp()),
                        status='unavailable', devices=[]) if options['unavailable'] else load_export(
                            sys.stdin.buffer.read(MAX_EXPORT_BYTES + 1))
            count = ingest(data if options['unavailable'] else unseal(data, 'technical_metadata'))
        except (SnapshotError, ValueError, TypeError, KeyError):
            raise CommandError('Technical metadata import rejected; no payload logged') from None
        self.stdout.write(f'Technical metadata: {count} latest records; no history; production writes: 0')
