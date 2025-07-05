"""
Enhanced Payment Processing Service for YITP
Replaces manual WhatsApp verification with automated payment processing
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
import logging
import uuid
import requests
from decimal import Decimal

from users.models import Profile
from .models import Payment, PaymentMethod

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Unified payment processing service supporting multiple payment methods
    """
    
    # Payment status choices
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    FAILED = 'failed'
    EXPIRED = 'expired'
    REFUNDED = 'refunded'
    
    @staticmethod
    def create_payment_record(user, course, amount, payment_method='mpesa'):
        """
        Create a payment record for course enrollment
        
        Args:
            user: User object
            course: Course object
            amount: Payment amount (Decimal)
            payment_method: Payment method ('mpesa', 'bank_transfer', 'card')
            
        Returns:
            Payment object
        """
        try:
            payment = Payment.objects.create(
                user=user,
                course=course,
                amount=amount,
                payment_method=payment_method,
                reference_number=PaymentService._generate_reference(),
                status=PaymentService.PENDING,
                created_at=timezone.now()
            )
            
            logger.info(f"Payment record created: {payment.reference_number} for {user.email}")
            return payment
            
        except Exception as e:
            logger.error(f"Failed to create payment record: {str(e)}")
            raise ValidationError(f"Failed to create payment record: {str(e)}")

    @staticmethod
    def _generate_reference():
        """Generate unique payment reference number"""
        return f"YITP-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    @staticmethod
    def process_mpesa_payment(payment, phone_number):
        """
        Process M-Pesa payment using Safaricom Daraja API
        
        Args:
            payment: Payment object
            phone_number: M-Pesa phone number (254XXXXXXXXX format)
            
        Returns:
            dict: {'success': bool, 'message': str, 'transaction_id': str or None}
        """
        try:
            # Validate phone number format
            if not phone_number.startswith('254') or len(phone_number) != 12:
                return {
                    'success': False,
                    'message': 'Invalid phone number format. Use 254XXXXXXXXX format.',
                    'transaction_id': None
                }

            # M-Pesa STK Push implementation
            mpesa_config = {
                'consumer_key': settings.MPESA_CONSUMER_KEY,
                'consumer_secret': settings.MPESA_CONSUMER_SECRET,
                'business_shortcode': settings.MPESA_SHORTCODE,
                'passkey': settings.MPESA_PASSKEY,
                'callback_url': settings.MPESA_CALLBACK_URL
            }
            
            # Generate access token
            auth_response = PaymentService._get_mpesa_access_token(mpesa_config)
            if not auth_response['success']:
                return auth_response

            # Initiate STK Push
            stk_response = PaymentService._initiate_stk_push(
                mpesa_config, 
                auth_response['access_token'],
                payment,
                phone_number
            )
            
            if stk_response['success']:
                # Update payment with transaction details
                payment.transaction_id = stk_response['checkout_request_id']
                payment.phone_number = phone_number
                payment.status = PaymentService.PENDING
                payment.save()
                
                return {
                    'success': True,
                    'message': 'Payment request sent to your phone. Please complete the transaction.',
                    'transaction_id': stk_response['checkout_request_id']
                }
            else:
                return stk_response
                
        except Exception as e:
            logger.error(f"M-Pesa payment processing failed: {str(e)}")
            return {
                'success': False,
                'message': f'Payment processing failed: {str(e)}',
                'transaction_id': None
            }

    @staticmethod
    def _get_mpesa_access_token(config):
        """Get M-Pesa access token"""
        try:
            import base64
            
            # Create credentials
            credentials = base64.b64encode(
                f"{config['consumer_key']}:{config['consumer_secret']}".encode()
            ).decode()
            
            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'access_token': response.json()['access_token']
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to get M-Pesa access token'
                }
                
        except Exception as e:
            logger.error(f"M-Pesa token generation failed: {str(e)}")
            return {
                'success': False,
                'message': f'Token generation failed: {str(e)}'
            }

    @staticmethod
    def _initiate_stk_push(config, access_token, payment, phone_number):
        """Initiate M-Pesa STK Push"""
        try:
            import base64
            from datetime import datetime
            
            # Generate timestamp and password
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(
                f"{config['business_shortcode']}{config['passkey']}{timestamp}".encode()
            ).decode()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': config['business_shortcode'],
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(payment.amount),
                'PartyA': phone_number,
                'PartyB': config['business_shortcode'],
                'PhoneNumber': phone_number,
                'CallBackURL': config['callback_url'],
                'AccountReference': payment.reference_number,
                'TransactionDesc': f'YITP Course Payment - {payment.course.title}'
            }
            
            response = requests.post(
                'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['ResponseCode'] == '0':
                    return {
                        'success': True,
                        'checkout_request_id': result['CheckoutRequestID']
                    }
                else:
                    return {
                        'success': False,
                        'message': result.get('ResponseDescription', 'STK Push failed')
                    }
            else:
                return {
                    'success': False,
                    'message': 'Failed to initiate payment request'
                }
                
        except Exception as e:
            logger.error(f"STK Push initiation failed: {str(e)}")
            return {
                'success': False,
                'message': f'Payment initiation failed: {str(e)}'
            }

    @staticmethod
    @transaction.atomic
    def confirm_payment(payment_reference, transaction_id=None):
        """
        Confirm payment and update user profile
        
        Args:
            payment_reference: Payment reference number
            transaction_id: Optional transaction ID from payment provider
            
        Returns:
            dict: {'success': bool, 'message': str, 'payment': Payment or None}
        """
        try:
            payment = Payment.objects.get(reference_number=payment_reference)
            
            # Update payment status
            payment.status = PaymentService.CONFIRMED
            payment.confirmed_at = timezone.now()
            if transaction_id:
                payment.transaction_id = transaction_id
            payment.save()
            
            # Update user profile
            profile = payment.user.profile
            profile.payment_status = 'confirmed'
            profile.payment_confirmed_at = timezone.now()
            profile.payment_amount = payment.amount
            profile.payment_reference = payment_reference
            profile.save()
            
            logger.info(f"Payment confirmed: {payment_reference} for {payment.user.email}")
            
            return {
                'success': True,
                'message': 'Payment confirmed successfully',
                'payment': payment
            }
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found: {payment_reference}")
            return {
                'success': False,
                'message': 'Payment record not found',
                'payment': None
            }
        except Exception as e:
            logger.error(f"Payment confirmation failed: {str(e)}")
            return {
                'success': False,
                'message': f'Payment confirmation failed: {str(e)}',
                'payment': None
            }

    @staticmethod
    def get_payment_methods():
        """Get available payment methods"""
        return [
            {
                'code': 'mpesa',
                'name': 'M-Pesa',
                'description': 'Pay using M-Pesa mobile money',
                'icon': 'mpesa-icon.png',
                'enabled': True
            },
            {
                'code': 'bank_transfer',
                'name': 'Bank Transfer',
                'description': 'Direct bank transfer to YITP account',
                'icon': 'bank-icon.png',
                'enabled': True
            },
            {
                'code': 'card',
                'name': 'Credit/Debit Card',
                'description': 'Pay using Visa, Mastercard, or other cards',
                'icon': 'card-icon.png',
                'enabled': False  # To be implemented later
            }
        ]

    @staticmethod
    def check_payment_status(payment_reference):
        """
        Check current payment status
        
        Returns:
            dict: {'status': str, 'payment': Payment or None, 'message': str}
        """
        try:
            payment = Payment.objects.get(reference_number=payment_reference)
            
            # Check if payment has expired (24 hours)
            if payment.status == PaymentService.PENDING:
                hours_since_creation = (timezone.now() - payment.created_at).total_seconds() / 3600
                if hours_since_creation > 24:
                    payment.status = PaymentService.EXPIRED
                    payment.save()
            
            return {
                'status': payment.status,
                'payment': payment,
                'message': f'Payment status: {payment.get_status_display()}'
            }
            
        except Payment.DoesNotExist:
            return {
                'status': 'not_found',
                'payment': None,
                'message': 'Payment record not found'
            }
