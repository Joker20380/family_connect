from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('console', '0010_devicelabel_subscriptioneventobservation_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='inventorydevice',
            index=models.Index(fields=['pseudonym', 'snapshot'], name='console_inv_pseudon_72959a_idx'),
        ),
        migrations.AddIndex(
            model_name='inventorysnapshot',
            index=models.Index(fields=['scope', 'source', 'imported_at'], name='console_inv_scope_ca70bb_idx'),
        ),
    ]
