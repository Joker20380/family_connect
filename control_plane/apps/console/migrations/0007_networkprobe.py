from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('console', '0006_payment_purpose')]
    operations = [migrations.CreateModel(
        name='NetworkProbe',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('source', models.CharField(max_length=32)),
            ('scope', models.CharField(max_length=12)),
            ('probe', models.CharField(max_length=24)),
            ('vantage', models.CharField(max_length=32)),
            ('address', models.GenericIPAddressField(protocol='IPv4')),
            ('port', models.PositiveIntegerField()),
            ('observed_at', models.DateTimeField()),
            ('imported_at', models.DateTimeField(auto_now_add=True)),
            ('outcome', models.CharField(max_length=16)),
            ('duration_ms', models.FloatField()),
            ('digest', models.CharField(max_length=64, unique=True)),
        ],
        options={'ordering': ['-observed_at'], 'constraints': [
            models.UniqueConstraint(fields=('source', 'observed_at'), name='unique_network_probe_time'),
            models.CheckConstraint(condition=models.Q(scope='production', probe='tcp_connect',
                vantage='operator-workstation', outcome__in=['reachable', 'refused', 'timeout', 'network_error'],
                duration_ms__gte=0, duration_ms__lte=60000), name='network_probe_domain'),
        ]}),
        migrations.RunSQL('CREATE TRIGGER network_probe_immutable BEFORE UPDATE OR DELETE ON console_networkprobe '
            'FOR EACH ROW EXECUTE FUNCTION cp0_immutable_record();',
            'DROP TRIGGER network_probe_immutable ON console_networkprobe;')]
