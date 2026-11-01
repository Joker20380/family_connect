from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

from fleet.contracts import load
from apps.fleet.workflow import accept_enrollment


class Command(BaseCommand):
    help = 'Проверить локальный signed instance receipt; transport issuance отсутствует'

    def add_arguments(self, parser):
        parser.add_argument('instance')
        parser.add_argument('--operator',required=True)
        parser.add_argument('--receipt',required=True)
        parser.add_argument('--authority-key',required=True)

    def handle(self, *args, **options):
        try:
            actor=get_user_model().objects.get(username=options['operator'])
            content=Path(options['receipt']).read_bytes()
            if len(content)>16384:raise ValueError('receipt_bound')
            authority=Ed25519PublicKey.from_public_bytes(Path(options['authority_key']).read_bytes())
            accept_enrollment(actor,options['instance'],load(content),authority)
            self.stdout.write('ENROLLMENT_RECEIPT_VERIFIED_SYNTHETIC')
        except (ValueError,OSError,ValidationError) as error:
            raise CommandError('Регистрация отклонена; значения скрыты.') from error
