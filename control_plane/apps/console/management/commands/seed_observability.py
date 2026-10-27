from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.console.models import DeviceProjection, TechnicalSample


class Command(BaseCommand):
    help = 'Создать 7 дней явно синтетических технических измерений; без подписок и оплат'

    @transaction.atomic
    def handle(self, **options):
        if TechnicalSample.objects.filter(source='demo-v1').exists():
            self.stdout.write('Демо-телеметрия уже создана; повтор не добавляет событий.')
            return
        now = timezone.now().replace(microsecond=0)
        samples = []
        for number, device in enumerate(DeviceProjection.objects.order_by('label')):
            for offset in range(7):
                values = {'activation': int((number + offset) % 19 != 0),
                    'mesh_connect': int((number + offset) % 11 != 0),
                    'crash': int((number + offset) % 43 == 0), 'api_latency_ms': 40 + (number * 13 + offset * 7) % 290}
                for metric, value in values.items():
                    samples.append(TechnicalSample(event_id=f'demo-{number}-{offset}-{metric}', scope='synthetic',
                        source='demo-v1', device=device, metric=metric, value=value, observed_at=now - timedelta(days=offset)))
        TechnicalSample.objects.bulk_create(samples)
        self.stdout.write(f'Создано {len(samples)} синтетических измерений. Production telemetry: не собирается.')
