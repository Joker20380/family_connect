from datetime import datetime, timezone
from django.core.validators import RegexValidator
from django.db import migrations, models


def preserve_events(apps, schema_editor):
    snapshot_model = apps.get_model('console', 'SubscriptionSnapshot')
    event_model = apps.get_model('console', 'SubscriptionEventObservation')
    for snapshot in snapshot_model.objects.filter(status='ok').order_by('pk').iterator(chunk_size=100):
        for row in snapshot.devices:
            event = row.get('event')
            if event is None:
                continue
            existing, created = event_model.objects.get_or_create(event_id=event['event_id'], defaults=dict(
                pseudonym=row['pseudonym'], occurred_at=datetime.fromtimestamp(event['occurred_at'], timezone.utc), details=event))
            if not created and (existing.pseudonym != row['pseudonym'] or existing.details != event):
                raise ValueError('Conflicting historical event; preserve observations for review')


class Migration(migrations.Migration):

    dependencies = [
        ('console', '0009_transportsnapshot'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceLabel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pseudonym', models.CharField(max_length=64, unique=True, validators=[RegexValidator(r'^[a-f0-9]{64}$')])),
                ('label', models.CharField(max_length=120, verbose_name='Локальное название')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'локальная метка рабочего устройства',
                'verbose_name_plural': 'локальные метки рабочих устройств',
            },
        ),
        migrations.CreateModel(
            name='SubscriptionEventObservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_id', models.CharField(max_length=64, unique=True)),
                ('pseudonym', models.CharField(db_index=True, max_length=64)),
                ('occurred_at', models.DateTimeField(db_index=True)),
                ('details', models.JSONField()),
                ('imported_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'default_permissions': ('view',),
            },
        ),
        migrations.AddField(
            model_name='inventorydevice',
            name='metadata',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='subscriptionsnapshot',
            name='history',
            field=models.JSONField(null=True),
        ),
        migrations.CreateModel(
            name='MeasurementSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(max_length=32)),
                ('observed_at', models.DateTimeField()),
                ('imported_at', models.DateTimeField(auto_now_add=True)),
                ('digest', models.CharField(max_length=64, unique=True)),
                ('node', models.JSONField(null=True)),
                ('devices', models.JSONField(default=list)),
                ('awg_status', models.CharField(max_length=16)),
                ('unknown_peers', models.PositiveIntegerField(null=True)),
                ('tcp_status', models.CharField(max_length=20)),
                ('mesh_status', models.CharField(max_length=20)),
            ],
            options={
                'default_permissions': ('view',),
                'indexes': [models.Index(fields=['source', 'observed_at'], name='console_mea_source_5d20a3_idx')],
            },
        ),
        migrations.RunPython(preserve_events, migrations.RunPython.noop),
        migrations.RunSQL(
            'CREATE TRIGGER measurements_immutable BEFORE UPDATE OR DELETE ON console_measurementsnapshot '
            'FOR EACH ROW EXECUTE FUNCTION cp0_immutable_record(); '
            'CREATE TRIGGER canonical_events_immutable BEFORE UPDATE OR DELETE ON console_subscriptioneventobservation '
            'FOR EACH ROW EXECUTE FUNCTION cp0_immutable_record();',
            'DROP TRIGGER measurements_immutable ON console_measurementsnapshot; '
            'DROP TRIGGER canonical_events_immutable ON console_subscriptioneventobservation;'),
    ]
