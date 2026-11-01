from django.db import migrations


TABLES = ('gatewayartifact', 'enrollmenttoken', 'deploymentoperation', 'instancehealthcheck')


class Migration(migrations.Migration):
    dependencies = [('fleet_console', '0001_initial')]
    operations = [migrations.RunSQL(
        '\n'.join(f'CREATE TRIGGER fleet_{table}_immutable BEFORE UPDATE OR DELETE ON fleet_console_{table} '
                  'FOR EACH ROW EXECUTE FUNCTION cp0_immutable_record();' for table in TABLES),
        '\n'.join(f'DROP TRIGGER fleet_{table}_immutable ON fleet_console_{table};' for table in TABLES))]
