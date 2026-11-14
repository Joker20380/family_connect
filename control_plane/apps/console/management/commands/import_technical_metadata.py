import sys
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.console.inventory import strict_load, SnapshotError
from apps.console.technical_metadata import ingest, prune


class Command(BaseCommand):
    help = 'Replace latest technical metadata from stdin; never save an append-only snapshot'

    def add_arguments(self, parser):
        parser.add_argument('--unavailable', action='store_true')

    def handle(self, **options):
        prune()
        try:
            data = dict(schema=1, source='gateway-ru', observed_at=int(timezone.now().timestamp()),
                        status='unavailable', devices=[]) if options['unavailable'] else strict_load(
                            sys.stdin.buffer.read(4 * 1024 * 1024 + 1))
            count = ingest(data)
        except (SnapshotError, ValueError, TypeError, KeyError):
            raise CommandError('Technical metadata import rejected; no payload logged') from None
        self.stdout.write(f'Technical metadata: {count} latest records; no history; production writes: 0')
