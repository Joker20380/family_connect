from collections import Counter

from django.core.management.base import BaseCommand, CommandError

from apps.console.system_publisher import Publisher, publish_next


class Command(BaseCommand):
    help = 'Publish explicitly confirmed system messages; credentials belong only to this external process.'

    def add_arguments(self, parser):
        parser.add_argument('--origin', required=True)
        parser.add_argument('--token-file', required=True)
        parser.add_argument('--limit', type=int, default=1)

    def handle(self, *args, **options):
        if not 1 <= options['limit'] <= 20:
            raise CommandError('Limit must be between 1 and 20')
        try:
            publisher = Publisher(options['origin'], options['token_file'])
        except (OSError, ValueError, UnicodeError):
            raise CommandError('Publisher configuration unavailable or invalid; credentials are not printed') from None
        results = Counter()
        for _ in range(options['limit']):
            result = publish_next(publisher)
            if result is None:
                break
            results[result] += 1
        self.stdout.write('Publication results: ' + str(dict(results)))
