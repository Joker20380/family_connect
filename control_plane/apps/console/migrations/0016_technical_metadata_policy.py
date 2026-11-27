from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('console', '0015_technical_metadata_geoip')]
    operations = [
        migrations.AddField(model_name='technicalmetadata', name='processing_mode',
            field=models.CharField(max_length=32, default='consented_extended')),
        migrations.AddField(model_name='technicalmetadata', name='policy_version',
            field=models.CharField(max_length=32, default='legacy-v1')),
    ]
