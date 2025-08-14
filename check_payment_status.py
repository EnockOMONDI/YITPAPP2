#!/usr/bin/env python
"""
Check payment status for specific user
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from payments.models import Payment
from django.contrib.auth.models import User

def check_user_payments():
    try:
        user = User.objects.get(email='direso3598@jobzyy.com')
        payments = Payment.objects.filter(user=user).order_by('-created_at')
        
        print(f'User: {user.email}')
        print(f'Total payments: {payments.count()}')
        
        for payment in payments:
            print(f'\nPayment ID: {payment.id}')
            print(f'Reference: {payment.reference_number}')
            print(f'Status: {payment.status}')
            print(f'Amount: ${payment.amount} {payment.currency}')
            print(f'Method: {payment.payment_method}')
            print(f'PayPal Order ID: {payment.paypal_payment_id}')
            print(f'Transaction ID: {payment.transaction_id}')
            print(f'Created: {payment.created_at}')
            print(f'Confirmed: {payment.confirmed_at}')
            print(f'Is Installment: {payment.is_installment}')
            
    except User.DoesNotExist:
        print('User not found')
    except Exception as e:
        print(f'Error: {str(e)}')

if __name__ == '__main__':
    check_user_payments()
