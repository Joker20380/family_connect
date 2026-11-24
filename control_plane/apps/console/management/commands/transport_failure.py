from django.core.management.base import BaseCommand
from apps.console.transports import NODES, attempt


class Command(BaseCommand):
    help = 'Отдельная локальная отметка неуспешной попытки внешнего наблюдения'

    def add_arguments(self, parser):
        parser.add_argument('--source', required=True, choices=NODES)
        parser.add_argument('--failure', required=True, choices=('collection_failed', 'import_failed'))

    def handle(self, **options):
        attempt(options['source'], options['failure'])
