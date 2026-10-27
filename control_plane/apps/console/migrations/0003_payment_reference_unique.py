from django.core.validators import RegexValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('console', '0002_immutable_workflow')]
    operations = [migrations.AlterField(model_name='paymentrecord', name='reference_hash',
        field=models.CharField(max_length=64, unique=True, validators=[RegexValidator(r'^[0-9a-f]{64}$')]))]
