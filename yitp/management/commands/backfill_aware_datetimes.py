from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction


class Command(BaseCommand):
    help = "Convert naive datetime fields to timezone-aware values for users and payments."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Fixing naive datetime fields..."))
        tz = timezone.get_default_timezone()
        users_updated = self._fix_users(tz)
        payments_updated = self._fix_payments(tz)
        self.stdout.write(
            self.style.SUCCESS(
                f"Completed. Users updated: {users_updated}, Payments updated: {payments_updated}"
            )
        )

    def _make_aware(self, dt, tz):
        if dt and timezone.is_naive(dt):
            return timezone.make_aware(dt, tz)
        return dt

    def _fix_users(self, tz):
        User = get_user_model()
        updated = 0
        with transaction.atomic():
            for user in User.objects.all():
                fields_changed = []
                last_login = self._make_aware(user.last_login, tz)
                date_joined = self._make_aware(user.date_joined, tz)
                if last_login != user.last_login:
                    user.last_login = last_login
                    fields_changed.append('last_login')
                if date_joined != user.date_joined:
                    user.date_joined = date_joined
                    fields_changed.append('date_joined')
                if fields_changed:
                    user.save(update_fields=fields_changed)
                    updated += 1
        return updated

    def _fix_payments(self, tz):
        try:
            from payments.models import Payment
        except Exception:
            return 0

        updated = 0
        with transaction.atomic():
            for payment in Payment.objects.all():
                fields_changed = []
                created_at = self._make_aware(getattr(payment, 'created_at', None), tz)
                if created_at is not None and created_at != getattr(payment, 'created_at', None):
                    payment.created_at = created_at
                    fields_changed.append('created_at')
                if fields_changed:
                    payment.save(update_fields=fields_changed)
                    updated += 1
        return updated
