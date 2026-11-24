from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('console', '0011_inventorydevice_console_inv_pseudon_72959a_idx_and_more')]
    operations = [migrations.AlterModelOptions(name='auditrecord', options={
        'verbose_name': 'событие аудита', 'verbose_name_plural': 'события аудита', 'ordering': ['-occurred_at'],
        'permissions': [('view_support_messages', 'Просматривать переписку поддержки'),
                        ('send_support_message', 'Отправлять личные сообщения от поддержки')],
    })]
