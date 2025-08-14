# Generated manually for YITP PayPal audit improvements

from django.db import migrations

def convert_kes_to_usd(apps, schema_editor):
    """Convert existing KES currency records to USD"""
    Payment = apps.get_model('payments', 'Payment')
    
    # Update all payments with KES currency to USD
    kes_payments = Payment.objects.filter(currency='KES')
    for payment in kes_payments:
        payment.currency = 'USD'
        payment.save()
    
    print(f"Converted {kes_payments.count()} payments from KES to USD currency")

def reverse_convert_usd_to_kes(apps, schema_editor):
    """Reverse migration - convert USD back to KES (if needed)"""
    Payment = apps.get_model('payments', 'Payment')
    
    # This is a reverse operation, typically not needed
    # but included for completeness
    usd_payments = Payment.objects.filter(currency='USD')
    for payment in usd_payments:
        payment.currency = 'KES'
        payment.save()
    
    print(f"Reverted {usd_payments.count()} payments from USD to KES currency")

class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_update_currency_to_usd'),
    ]

    operations = [
        migrations.RunPython(
            convert_kes_to_usd,
            reverse_convert_usd_to_kes,
        ),
    ]
