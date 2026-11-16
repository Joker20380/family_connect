from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('console', '0014_technical_metadata')]
    operations = [migrations.AddField(model_name='technicalmetadata', name='geoip',
                                     field=models.JSONField(default=None, null=True))]
