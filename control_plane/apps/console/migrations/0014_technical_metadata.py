from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('console', '0013_system_messages')]
    operations = [
        migrations.CreateModel(name='TechnicalMetadata', fields=[
            ('pseudonym', models.CharField(max_length=64, primary_key=True, serialize=False)),
            ('consent_epoch', models.BigIntegerField()),
            ('sequence', models.BigIntegerField()),
            ('consent', models.CharField(max_length=16)),
            ('received_at', models.BigIntegerField()),
            ('observations', models.JSONField(default=dict)),
        ]),
        migrations.CreateModel(name='TechnicalMetadataSource', fields=[
            ('source', models.CharField(max_length=32, primary_key=True, serialize=False)),
            ('observed_at', models.BigIntegerField(default=0)),
            ('status', models.CharField(default='unavailable', max_length=16)),
        ]),
    ]
