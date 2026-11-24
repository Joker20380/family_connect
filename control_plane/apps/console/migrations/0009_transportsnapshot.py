from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('console', '0008_subscriptionsnapshot')]
    operations = [migrations.CreateModel(
        name='TransportSnapshot',
        fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(max_length=32)),
                ('observed_at', models.DateTimeField()), ('imported_at', models.DateTimeField(auto_now_add=True)),
                ('digest', models.CharField(max_length=64, unique=True)), ('status', models.CharField(max_length=16)),
                ('runtime_sha256', models.CharField(max_length=64, null=True)), ('devices', models.JSONField(default=list))],
        options={'ordering': ['-pk'], 'default_permissions': ('view',)}),
        migrations.RunSQL(
            'CREATE TRIGGER transports_immutable BEFORE UPDATE OR DELETE ON console_transportsnapshot '
            'FOR EACH ROW EXECUTE FUNCTION cp0_immutable_record();',
            'DROP TRIGGER transports_immutable ON console_transportsnapshot;')]
