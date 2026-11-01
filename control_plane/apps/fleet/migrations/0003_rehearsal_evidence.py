import django.core.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('fleet_console','0002_immutable_audit')]
    operations = [migrations.CreateModel(
        name='RehearsalEvidence',
        fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('instance_id',models.CharField(max_length=96,validators=[django.core.validators.RegexValidator('^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$')])),
            ('operation_id',models.CharField(max_length=96,validators=[django.core.validators.RegexValidator('^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$')])),
            ('kind',models.CharField(max_length=32)),
            ('receipt_sha256',models.CharField(max_length=64,validators=[django.core.validators.RegexValidator('^[0-9a-f]{64}$')])),
            ('receipt',models.JSONField()),
            ('imported_at',models.DateTimeField(default=django.utils.timezone.now)),
        ], options=dict(ordering=['id'],constraints=[models.UniqueConstraint(fields=('instance_id','kind','operation_id'),name='fleet_rehearsal_event_unique')]),
    ), migrations.RunSQL(
        'CREATE TRIGGER fleet_rehearsal_evidence_immutable BEFORE UPDATE OR DELETE ON fleet_console_rehearsalevidence '
        'FOR EACH ROW EXECUTE FUNCTION cp0_immutable_record();',
        'DROP TRIGGER fleet_rehearsal_evidence_immutable ON fleet_console_rehearsalevidence;')]
