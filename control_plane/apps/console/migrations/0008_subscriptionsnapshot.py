from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('console', '0007_networkprobe')]
    operations = [migrations.CreateModel(
        name='SubscriptionSnapshot',
        fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('observed_at', models.DateTimeField()), ('imported_at', models.DateTimeField(auto_now_add=True)),
                ('digest', models.CharField(max_length=64, unique=True)), ('status', models.CharField(max_length=16)),
                ('runtime_sha256', models.CharField(max_length=64, null=True)), ('devices', models.JSONField(default=list))],
        options={'ordering': ['-observed_at', '-pk'], 'default_permissions': ('view',)}),
        migrations.RunSQL(
            'CREATE TRIGGER subscriptions_immutable BEFORE UPDATE OR DELETE ON console_subscriptionsnapshot '
            'FOR EACH ROW EXECUTE FUNCTION cp0_immutable_record();',
            'DROP TRIGGER subscriptions_immutable ON console_subscriptionsnapshot;')]
