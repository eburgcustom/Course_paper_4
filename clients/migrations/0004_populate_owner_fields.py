from django.db import migrations, models
from django.conf import settings


def populate_owner_fields(apps, schema_editor):
    """Заполняем поля owner для существующих записей."""
    Mailing = apps.get_model('clients', 'Mailing')
    Message = apps.get_model('clients', 'Message')
    Recipient = apps.get_model('clients', 'Recipient')
    CustomUser = apps.get_model('users', 'CustomUser')
    
    # Находим первого пользователя (обычно суперпользователь)
    first_user = CustomUser.objects.first()
    
    if first_user:
        # Обновляем все существующие записи
        Mailing.objects.filter(owner__isnull=True).update(owner=first_user)
        Message.objects.filter(owner__isnull=True).update(owner=first_user)
        Recipient.objects.filter(owner__isnull=True).update(owner=first_user)


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0003_mailing_owner_message_owner_recipient_owner'),
        ('users', '0002_customuser_role_alter_customuser_is_active'),
    ]

    operations = [
        migrations.RunPython(populate_owner_fields),
        migrations.AlterField(
            model_name='mailing',
            name='owner',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name='mailings',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Владелец'
            ),
        ),
        migrations.AlterField(
            model_name='message',
            name='owner',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name='messages',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Владелец'
            ),
        ),
        migrations.AlterField(
            model_name='recipient',
            name='owner',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name='recipients',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Владелец'
            ),
        ),
    ]
