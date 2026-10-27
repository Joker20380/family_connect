from django.db import migrations

TABLES = ('inventorysnapshot', 'inventorydevice', 'serverobservation', 'technicalsample')


class Migration(migrations.Migration):
    dependencies = [('console', '0004_inventorysnapshot_alter_auditrecord_options_and_more')]
    operations = [migrations.RunSQL(
        '\n'.join(f'CREATE TRIGGER cp1_{table}_immutable BEFORE UPDATE OR DELETE ON console_{table} '
            'FOR EACH ROW EXECUTE FUNCTION cp0_immutable_record();' for table in TABLES),
        '\n'.join(f'DROP TRIGGER cp1_{table}_immutable ON console_{table};' for table in TABLES))]
