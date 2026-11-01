from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from fleet.contracts import canonical, load
from fleet.evidence import KINDS
from apps.fleet.rehearsal import import_receipt


class Command(BaseCommand):
    help = 'Append-only импорт подписанного безопасного rehearsal receipt; без SSH и private keys'

    def add_arguments(self, parser):
        parser.add_argument('--kind', required=True, choices=KINDS)
        parser.add_argument('--receipt', required=True)
        parser.add_argument('--public-key', required=True)

    def handle(self, *args, **options):
        try:
            raw = Path(options['receipt']).read_bytes()
            if len(raw)>16384:
                raise ValueError('bound')
            receipt = load(raw)
            if receipt['body']['kind']!=options['kind']:
                raise ValueError('kind')
            public = Ed25519PublicKey.from_public_bytes(Path(options['public_key']).read_bytes())
            record, created = import_receipt(receipt, public)
            self.stdout.write(canonical(dict(result='IMPORTED' if created else 'IDENTICAL',
                operation_id=record.operation_id, kind=record.kind, receipt_sha256=record.receipt_sha256)).decode())
        except (OSError, ValueError, TypeError, KeyError, ValidationError):
            raise CommandError('Rehearsal receipt отклонён; содержимое скрыто.') from None
