import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('console', '0012_support_permissions'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AlterModelOptions(name='auditrecord', options={
            'verbose_name': 'событие аудита', 'verbose_name_plural': 'события аудита', 'ordering': ['-occurred_at'],
            'permissions': [('view_support_messages', 'Просматривать переписку поддержки'),
                            ('send_support_message', 'Отправлять личные сообщения от поддержки'),
                            ('view_system_messages', 'Просматривать системные объявления'),
                            ('send_system_message', 'Публиковать системные объявления')],
        }),
        migrations.CreateModel(name='SystemMessage', fields=[
            ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ('title', models.CharField(max_length=160)),
            ('body', models.TextField(max_length=4000)),
            ('kind', models.CharField(max_length=20)),
            ('platforms', models.JSONField()),
            ('days', models.PositiveIntegerField()),
            ('status', models.CharField(choices=[('draft', 'Предпросмотр — не отправлено'),
                ('queued', 'В очереди публикации'), ('unknown', 'Результат неизвестен — повтор только с прежним ID'),
                ('refused', 'Отказ в публикации'), ('published', 'Опубликовано в системной ленте')], default='draft', max_length=16)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
        ], options={'default_permissions': ()}),
    ]
