"""
Payment URLs for YITP
Handles routing for payment processing views
"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment method selection
    path('methods/<int:course_id>/', views.payment_methods, name='payment_methods'),
    
    # Payment processing
    path('process/mpesa/', views.process_mpesa, name='process_mpesa'),
    path('process/paypal/', views.process_paypal, name='process_paypal'),
    path('process/bank-transfer/', views.process_bank_transfer, name='process_bank_transfer'),
    
    # Payment status
    path('status/<int:payment_id>/', views.payment_status, name='payment_status'),
    
    # M-Pesa callbacks
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('mpesa/timeout/', views.mpesa_timeout, name='mpesa_timeout'),

    # PayPal callbacks and webhooks
    path('paypal/webhook/', views.paypal_webhook, name='paypal_webhook'),
    path('paypal/return/', views.paypal_return, name='paypal_return'),
    path('paypal/cancel/', views.paypal_cancel, name='paypal_cancel'),
]
