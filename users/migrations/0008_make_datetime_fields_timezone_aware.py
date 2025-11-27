from django.db import migrations
from django.utils import timezone


def make_datetimes_aware(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Payment = apps.get_model('payments', 'Payment')
    tz = timezone.get_default_timezone()

    def to_aware(value):
        if value and timezone.is_naive(value):
            return timezone.make_aware(value, tz)
        return value

    batch_size = 1000
    for user in User.objects.all().only('id', 'last_login', 'date_joined').iterator(chunk_size=batch_size):
        update_fields = []
        new_last_login = to_aware(user.last_login)
        if new_last_login != user.last_login:
            user.last_login = new_last_login
            update_fields.append('last_login')
        new_date_joined = to_aware(user.date_joined)
        if new_date_joined != user.date_joined:
            user.date_joined = new_date_joined
            update_fields.append('date_joined')
        if update_fields:
            user.save(update_fields=update_fields)

    for payment in Payment.objects.all().only('id', 'created_at', 'confirmed_at', 'expires_at').iterator(chunk_size=batch_size):
        updates = {}
        new_created_at = to_aware(payment.created_at)
        if new_created_at != payment.created_at:
            updates['created_at'] = new_created_at
        new_confirmed_at = to_aware(payment.confirmed_at)
        if new_confirmed_at != payment.confirmed_at:
            updates['confirmed_at'] = new_confirmed_at
        new_expires_at = to_aware(payment.expires_at)
        if new_expires_at != payment.expires_at:
            updates['expires_at'] = new_expires_at
        if updates:
            Payment.objects.filter(pk=payment.pk).update(**updates)


def noop_reverse(apps, schema_editor):
    # The conversion is idempotent and should not be reversed.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_update_instructor_roles'),
        ('payments', '0003_convert_kes_to_usd'),
    ]

    operations = [
        migrations.RunPython(make_datetimes_aware, noop_reverse),
    ]
