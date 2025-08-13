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
    def create_payment_record(user, course, amount, payment_method='mpesa', is_installment=False, installment_sequence=None):
        """
        Create a payment record for course enrollment

        Args:
            user: User object
            course: Course object
            amount: Payment amount (Decimal)
            payment_method: Payment method ('mpesa', 'bank_transfer', 'paypal', 'card')
            is_installment: Boolean indicating if this is an installment payment
            installment_sequence: Integer (1 or 2) for installment sequence

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
                is_installment=is_installment,
                installment_sequence=installment_sequence,
                created_at=timezone.now()
            )

            logger.info(f"Payment record created: {payment.reference_number} for {user.email} - Method: {payment_method}")
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
    def process_paypal_payment(payment, paypal_payment_id=None, paypal_payer_id=None):
        """
        Process PayPal payment using existing PayPal infrastructure

        Args:
            payment: Payment object
            paypal_payment_id: PayPal transaction ID (optional for manual verification)
            paypal_payer_id: PayPal payer ID (optional for manual verification)

        Returns:
            dict: {'success': bool, 'message': str, 'paypal_url': str or None}
        """
        try:
            from .paypal_service import PayPalService

            # Create PayPal payment order using SDK
            order_result = PayPalService.create_payment_order(payment)

            if order_result['success']:
                # Update payment with PayPal details
                payment.paypal_payment_id = order_result['order_id']
                if paypal_payer_id:
                    payment.paypal_payer_id = paypal_payer_id

                payment.status = PaymentService.PENDING
                payment.save()

                logger.info(f"PayPal payment order created: {payment.reference_number} -> {order_result['order_id']}")

                return {
                    'success': True,
                    'message': 'PayPal payment order created. Please complete payment on PayPal.',
                    'paypal_url': order_result['approval_url'],
                    'order_id': order_result['order_id'],
                    'payment_id': payment.reference_number
                }
            else:
                logger.error(f"PayPal order creation failed for payment {payment.reference_number}: {order_result['message']}")
                return {
                    'success': False,
                    'message': f"PayPal payment failed: {order_result['message']}",
                    'paypal_url': None,
                    'payment_id': payment.reference_number
                }

        except Exception as e:
            logger.error(f"PayPal payment processing failed: {str(e)}")
            return {
                'success': False,
                'message': f'PayPal payment processing failed: {str(e)}',
                'paypal_url': None
            }

    @staticmethod
    def _generate_paypal_url(payment):
        """
        Generate PayPal payment URL with enhanced error handling
        Uses the existing PayPal link structure with proper validation
        """
        try:
            # Validate payment object
            if not payment or not payment.reference_number:
                raise ValueError("Invalid payment object or missing reference number")

            # Validate amount
            if not payment.amount or payment.amount <= 0:
                raise ValueError("Invalid payment amount")

            # Use existing PayPal payment link structure
            base_url = "https://www.paypal.com/ncp/payment/FUAJVJ66L978C"

            # Validate base URL format
            if not base_url.startswith('https://'):
                raise ValueError("Invalid PayPal base URL - must use HTTPS")

            # Add payment reference and amount as parameters for tracking
            # URL encode parameters to handle special characters
            from urllib.parse import urlencode
            params = {
                'reference': payment.reference_number,
                'amount': str(payment.amount),
                'currency': payment.currency or 'KES'
            }

            paypal_url = f"{base_url}?{urlencode(params)}"

            # Validate final URL length (PayPal has URL length limits)
            if len(paypal_url) > 2048:
                logger.warning(f"PayPal URL length exceeds recommended limit: {len(paypal_url)} characters")

            logger.info(f"Generated PayPal URL for payment {payment.reference_number}")
            return paypal_url

        except Exception as e:
            logger.error(f"Failed to generate PayPal URL for payment {payment.reference_number if payment else 'unknown'}: {str(e)}")
            # Return fallback URL without parameters
            return "https://www.paypal.com/ncp/payment/FUAJVJ66L978C"

    @staticmethod
    def process_bank_transfer_payment(payment, transaction_id=None):
        """
        Process bank transfer payment with manual verification

        Args:
            payment: Payment object
            transaction_id: Bank transaction ID for verification

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # Update payment with transaction details
            if transaction_id:
                payment.reference_number = transaction_id

            payment.status = PaymentService.PENDING
            payment.save()

            logger.info(f"Bank transfer payment initiated: {payment.reference_number}")

            return {
                'success': True,
                'message': 'Bank transfer payment recorded. Please wait for manual verification.',
                'payment_id': payment.reference_number
            }

        except Exception as e:
            logger.error(f"Bank transfer payment processing failed: {str(e)}")
            return {
                'success': False,
                'message': f'Bank transfer payment processing failed: {str(e)}'
            }

    @staticmethod
    def verify_manual_payment(payment, transaction_id, verified_by=None, notes=""):
        """
        Manually verify PayPal or bank transfer payment

        Args:
            payment: Payment object
            transaction_id: Transaction ID from PayPal or bank
            verified_by: User who verified the payment (admin)
            notes: Additional verification notes

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # Update payment with verification details
            if payment.payment_method == 'paypal':
                payment.paypal_payment_id = transaction_id
            else:
                payment.reference_number = transaction_id

            # Confirm the payment using enhanced method from Phase 1
            payment.confirm_payment(verified_by=verified_by, notes=notes)

            logger.info(f"Manual payment verification completed: {payment.reference_number}")

            return {
                'success': True,
                'message': 'Payment verified and confirmed successfully.',
                'payment_status': payment.status
            }

        except Exception as e:
            logger.error(f"Manual payment verification failed: {str(e)}")
            return {
                'success': False,
                'message': f'Payment verification failed: {str(e)}'
            }

    @staticmethod
    def confirm_payment_and_enroll(payment, verified_by=None):
        """
        Confirm payment and automatically enroll user in course

        Args:
            payment: Payment object to confirm
            verified_by: User who verified the payment (for manual payments)

        Returns:
            dict: {'success': bool, 'message': str, 'enrollment': Enrollment or None}
        """
        try:
            # Confirm the payment using enhanced method from Phase 1
            confirmation_result = payment.confirm_payment(verified_by=verified_by)

            # confirm_payment returns True/False, not a dictionary
            if not confirmation_result:
                return {
                    'success': False,
                    'message': 'Payment confirmation failed.',
                    'enrollment': None
                }

            # Create course enrollment
            from progress.models import Enrollment
            enrollment, created = Enrollment.objects.get_or_create(
                student=payment.user,
                course=payment.course,
                defaults={
                    'enrollment_date': timezone.now(),
                    'status': 'active'
                }
            )

            if created:
                logger.info(f"User {payment.user.username} enrolled in course {payment.course.title}")

                # Update user profile payment status
                profile = payment.user.profile
                if payment.is_installment and payment.installment_sequence == 1:
                    profile.payment_status = 'partially_paid'
                    profile.payment_expiration_date = timezone.now() + timezone.timedelta(days=30)
                else:
                    profile.payment_status = 'confirmed'
                    profile.payment_expiration_date = None
                profile.save()

                return {
                    'success': True,
                    'message': 'Payment confirmed and course enrollment completed.',
                    'enrollment': enrollment
                }
            else:
                return {
                    'success': True,
                    'message': 'Payment confirmed. User was already enrolled in course.',
                    'enrollment': enrollment
                }

        except Exception as e:
            logger.error(f"Payment confirmation and enrollment failed: {str(e)}")
            return {
                'success': False,
                'message': f'Payment confirmation failed: {str(e)}',
                'enrollment': None
            }

    @staticmethod
    def create_installment_payment(user, course, installment_sequence=1, payment_method='mpesa'):
        """
        Create an installment payment (50% of course price)

        Args:
            user: User object
            course: Course object
            installment_sequence: 1 for first installment, 2 for second
            payment_method: Payment method ('mpesa', 'paypal', 'bank_transfer')

        Returns:
            Payment object
        """
        from decimal import Decimal

        # Calculate installment amount (50% of course price)
        installment_amount = course.price * Decimal('0.5')

        # Create installment payment record
        payment = PaymentService.create_payment_record(
            user=user,
            course=course,
            amount=installment_amount,
            payment_method=payment_method,
            is_installment=True,
            installment_sequence=installment_sequence
        )

        logger.info(f"Installment payment created: {payment.reference_number} - Sequence: {installment_sequence}")
        return payment

    @staticmethod
    def process_installment_payment(payment, **kwargs):
        """
        Process installment payment based on payment method

        Args:
            payment: Payment object (must be installment payment)
            **kwargs: Additional arguments based on payment method

        Returns:
            dict: Payment processing result
        """
        if not payment.is_installment:
            return {
                'success': False,
                'message': 'Payment is not an installment payment'
            }

        if payment.payment_method == 'mpesa':
            phone_number = kwargs.get('phone_number')
            if not phone_number:
                return {
                    'success': False,
                    'message': 'Phone number required for M-Pesa payment'
                }
            return PaymentService.process_mpesa_payment(payment, phone_number)

        elif payment.payment_method == 'paypal':
            return PaymentService.process_paypal_payment(
                payment,
                kwargs.get('paypal_payment_id'),
                kwargs.get('paypal_payer_id')
            )

        elif payment.payment_method == 'bank_transfer':
            return PaymentService.process_bank_transfer_payment(
                payment,
                kwargs.get('transaction_id')
            )

        else:
            return {
                'success': False,
                'message': f'Unsupported payment method: {payment.payment_method}'
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
                'enabled': True,
                'supports_installments': True
            },
            {
                'code': 'bank_transfer',
                'name': 'Bank Transfer',
                'description': 'Direct bank transfer to YITP account',
                'icon': 'bank-icon.png',
                'enabled': True,
                'supports_installments': True
            },
            {
                'code': 'paypal',
                'name': 'PayPal',
                'description': 'Pay securely with PayPal',
                'icon': 'paypal-icon.png',
                'enabled': True,
                'supports_installments': True
            },
            {
                'code': 'card',
                'name': 'Credit/Debit Card',
                'description': 'Pay using Visa, Mastercard, or other cards',
                'icon': 'card-icon.png',
                'enabled': False,  # To be implemented later
                'supports_installments': False
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
