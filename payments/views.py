"""
Payment Processing Views for YITP
Handles M-Pesa, PayPal, and Bank Transfer payments with installment support
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from decimal import Decimal
import json
import logging
import re

from courses.models import Course
from .models import Payment
from .payment_service import PaymentService

logger = logging.getLogger(__name__)


def _validate_paypal_payment_id(payment_id):
    """
    Validate PayPal payment ID format and length

    Args:
        payment_id: PayPal transaction ID to validate

    Returns:
        dict: {'valid': bool, 'message': str}
    """
    if not payment_id:
        return {
            'valid': False,
            'message': 'PayPal transaction ID is required.'
        }

    # Remove whitespace
    payment_id = payment_id.strip()

    # Check minimum length
    if len(payment_id) < 10:
        return {
            'valid': False,
            'message': 'Please provide a valid PayPal transaction ID (minimum 10 characters).'
        }

    # Check maximum length
    if len(payment_id) > 50:
        return {
            'valid': False,
            'message': 'PayPal transaction ID is too long (maximum 50 characters).'
        }

    # Check for valid characters (alphanumeric, hyphens, underscores)
    if not re.match(r'^[A-Za-z0-9\-_]+$', payment_id):
        return {
            'valid': False,
            'message': 'PayPal transaction ID contains invalid characters. Only letters, numbers, hyphens, and underscores are allowed.'
        }

    # Check for duplicate PayPal payment ID across all payments
    if Payment.objects.filter(paypal_payment_id=payment_id).exists():
        return {
            'valid': False,
            'message': 'This PayPal transaction ID has already been used. Please check your transaction history or contact support.'
        }

    return {
        'valid': True,
        'message': 'Valid PayPal transaction ID.'
    }


def _validate_paypal_payer_id(payer_id):
    """
    Validate PayPal payer ID format

    Args:
        payer_id: PayPal payer ID to validate

    Returns:
        dict: {'valid': bool, 'message': str}
    """
    if not payer_id:
        return {'valid': True, 'message': 'Payer ID is optional.'}

    # Remove whitespace
    payer_id = payer_id.strip()

    # Check length (PayPal payer IDs are typically 13 characters)
    if len(payer_id) < 10 or len(payer_id) > 20:
        return {
            'valid': False,
            'message': 'PayPal payer ID should be between 10-20 characters.'
        }

    # Check for valid characters
    if not re.match(r'^[A-Za-z0-9]+$', payer_id):
        return {
            'valid': False,
            'message': 'PayPal payer ID should contain only letters and numbers.'
        }

    return {
        'valid': True,
        'message': 'Valid PayPal payer ID.'
    }


def _check_duplicate_paypal_payment(user, course, paypal_payment_id):
    """
    Check for duplicate PayPal payments

    Args:
        user: User making the payment
        course: Course being paid for
        paypal_payment_id: PayPal transaction ID

    Returns:
        dict: {'exists': bool, 'message': str, 'payment': Payment or None}
    """
    # Check for existing payment by user and course
    existing_payment = Payment.objects.filter(
        user=user,
        course=course,
        payment_method='paypal',
        status__in=['pending', 'confirmed']
    ).first()

    if existing_payment:
        return {
            'exists': True,
            'message': f'You already have a {existing_payment.status} PayPal payment for this course.',
            'payment': existing_payment
        }

    # Check for duplicate PayPal transaction ID
    duplicate_transaction = Payment.objects.filter(
        paypal_payment_id=paypal_payment_id
    ).first()

    if duplicate_transaction:
        return {
            'exists': True,
            'message': 'This PayPal transaction ID has already been used. Please check your payment history.',
            'payment': duplicate_transaction
        }

    return {
        'exists': False,
        'message': 'No duplicate payment found.',
        'payment': None
    }


def _validate_bank_transaction_id(transaction_id):
    """
    Validate bank transfer transaction ID format and length

    Args:
        transaction_id: Bank transaction ID to validate

    Returns:
        dict: {'valid': bool, 'message': str}
    """
    if not transaction_id:
        return {
            'valid': False,
            'message': 'Bank transaction ID is required.'
        }

    # Remove whitespace
    transaction_id = transaction_id.strip()

    # Check minimum length
    if len(transaction_id) < 8:
        return {
            'valid': False,
            'message': 'Please provide a valid bank transaction ID (minimum 8 characters).'
        }

    # Check maximum length
    if len(transaction_id) > 50:
        return {
            'valid': False,
            'message': 'Bank transaction ID is too long (maximum 50 characters).'
        }

    # Check for valid characters (alphanumeric, hyphens, underscores, dots)
    if not re.match(r'^[A-Za-z0-9\-_.]+$', transaction_id):
        return {
            'valid': False,
            'message': 'Bank transaction ID contains invalid characters. Only letters, numbers, hyphens, underscores, and dots are allowed.'
        }

    # Check for duplicate transaction ID across all payments
    if Payment.objects.filter(transaction_id=transaction_id).exists():
        return {
            'valid': False,
            'message': 'This bank transaction ID has already been used. Please check your transaction history or contact support.'
        }

    return {
        'valid': True,
        'message': 'Valid bank transaction ID.'
    }


def _check_duplicate_bank_payment(user, course, transaction_id):
    """
    Check for duplicate bank transfer payments

    Args:
        user: User making the payment
        course: Course being paid for
        transaction_id: Bank transaction ID

    Returns:
        dict: {'exists': bool, 'message': str, 'payment': Payment or None}
    """
    # Check for existing payment by user and course
    existing_payment = Payment.objects.filter(
        user=user,
        course=course,
        payment_method='bank_transfer',
        status__in=['pending', 'confirmed']
    ).first()

    if existing_payment:
        return {
            'exists': True,
            'message': f'You already have a {existing_payment.status} bank transfer payment for this course.',
            'payment': existing_payment
        }

    # Check for duplicate transaction ID
    duplicate_transaction = Payment.objects.filter(
        transaction_id=transaction_id
    ).first()

    if duplicate_transaction:
        return {
            'exists': True,
            'message': 'This bank transaction ID has already been used. Please check your payment history.',
            'payment': duplicate_transaction
        }

    return {
        'exists': False,
        'message': 'No duplicate payment found.',
        'payment': None
    }


@login_required
def payment_methods(request, course_id):
    """
    Display payment methods for course enrollment
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is already enrolled
    from progress.models import Enrollment
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('courses:course_detail', course_id=course.id)
    
    context = {
        'course': course,
        'payment_methods': PaymentService.get_payment_methods(),
    }
    
    return render(request, 'payments/payment_methods.html', context)


@login_required
@require_POST
def process_mpesa(request):
    """
    Process M-Pesa payment
    """
    try:
        course_id = request.POST.get('course_id')
        amount = Decimal(request.POST.get('amount'))
        phone_number = request.POST.get('phone_number')
        is_installment = request.POST.get('is_installment', 'false').lower() == 'true'
        installment_sequence = int(request.POST.get('installment_sequence', 1))
        
        course = get_object_or_404(Course, id=course_id)
        
        # Create payment record
        payment = PaymentService.create_payment_record(
            user=request.user,
            course=course,
            amount=amount,
            payment_method='mpesa',
            is_installment=is_installment,
            installment_sequence=installment_sequence
        )
        
        # Process M-Pesa payment
        result = PaymentService.process_mpesa_payment(payment, phone_number)
        
        if result['success']:
            messages.success(request, result['message'])
            return redirect('payments:payment_status', payment_id=payment.id)
        else:
            messages.error(request, result['message'])
            return redirect('payments:payment_methods', course_id=course.id)
            
    except Exception as e:
        logger.error(f"M-Pesa payment processing error: {str(e)}")
        messages.error(request, 'Payment processing failed. Please try again.')
        return redirect('payments:payment_methods', course_id=course_id)


@login_required
@require_POST
def process_paypal(request):
    """
    Process PayPal payment verification with enhanced validation and email notifications
    """
    try:
        course_id = request.POST.get('course_id')
        amount = Decimal(request.POST.get('amount'))
        paypal_payment_id = request.POST.get('paypal_payment_id', '').strip()
        paypal_payer_id = request.POST.get('paypal_payer_id', '').strip()
        is_installment = request.POST.get('is_installment', 'false').lower() == 'true'
        installment_sequence = int(request.POST.get('installment_sequence', 1))

        course = get_object_or_404(Course, id=course_id)

        # Enhanced PayPal transaction ID validation
        validation_result = _validate_paypal_payment_id(paypal_payment_id)
        if not validation_result['valid']:
            messages.error(request, validation_result['message'])
            return redirect('payments:payment_methods', course_id=course.id)

        # Validate PayPal payer ID if provided
        if paypal_payer_id:
            payer_validation = _validate_paypal_payer_id(paypal_payer_id)
            if not payer_validation['valid']:
                messages.error(request, payer_validation['message'])
                return redirect('payments:payment_methods', course_id=course.id)

        # Check for existing enrollment
        from progress.models import Enrollment
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            messages.info(request, 'You are already enrolled in this course.')
            return redirect('courses:course_detail', course_id=course.id)

        # Enhanced duplicate payment prevention
        duplicate_check = _check_duplicate_paypal_payment(request.user, course, paypal_payment_id)
        if duplicate_check['exists']:
            messages.info(request, duplicate_check['message'])
            return redirect('payments:payment_status', payment_id=duplicate_check['payment'].id)

        # Create payment record
        payment = PaymentService.create_payment_record(
            user=request.user,
            course=course,
            amount=amount,
            payment_method='paypal',
            is_installment=is_installment,
            installment_sequence=installment_sequence
        )

        # Store PayPal details
        payment.paypal_payment_id = paypal_payment_id
        if paypal_payer_id:
            payment.paypal_payer_id = paypal_payer_id
        payment.save()

        # Send email notifications
        from .email_service import PaymentEmailService

        # Send user confirmation
        user_email_sent = PaymentEmailService.send_user_payment_submitted_notification(payment)
        if not user_email_sent:
            logger.warning(f"Failed to send user confirmation email for payment {payment.reference_number}")

        # Send admin notification
        admin_email_sent = PaymentEmailService.send_admin_verification_notification(payment)
        if not admin_email_sent:
            logger.warning(f"Failed to send admin notification email for payment {payment.reference_number}")

        # Set payment to pending status for manual verification
        payment.status = 'pending'
        payment.save()

        messages.success(request, 'PayPal payment submitted successfully! Your transaction ID has been sent to our team and will be verified within 24 hours.')
        return redirect('payments:payment_status', payment_id=payment.id)

    except Exception as e:
        logger.error(f"PayPal payment processing error: {str(e)}")
        messages.error(request, 'PayPal payment processing failed. Please try again.')
        return redirect('payments:payment_methods', course_id=course_id)


@login_required
@require_POST
def process_bank_transfer(request):
    """
    Process bank transfer payment verification with enhanced validation and email notifications
    """
    try:
        course_id = request.POST.get('course_id')
        amount = Decimal(request.POST.get('amount'))
        transaction_id = request.POST.get('transaction_id', '').strip()
        is_installment = request.POST.get('is_installment', 'false').lower() == 'true'
        installment_sequence = int(request.POST.get('installment_sequence', 1))

        course = get_object_or_404(Course, id=course_id)

        # Enhanced bank transfer transaction ID validation
        validation_result = _validate_bank_transaction_id(transaction_id)
        if not validation_result['valid']:
            messages.error(request, validation_result['message'])
            return redirect('payments:payment_methods', course_id=course.id)

        # Check for existing enrollment
        from progress.models import Enrollment
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            messages.info(request, 'You are already enrolled in this course.')
            return redirect('courses:course_detail', course_id=course.id)

        # Enhanced duplicate payment prevention
        duplicate_check = _check_duplicate_bank_payment(request.user, course, transaction_id)
        if duplicate_check['exists']:
            messages.info(request, duplicate_check['message'])
            return redirect('payments:payment_status', payment_id=duplicate_check['payment'].id)

        # Create payment record
        payment = PaymentService.create_payment_record(
            user=request.user,
            course=course,
            amount=amount,
            payment_method='bank_transfer',
            is_installment=is_installment,
            installment_sequence=installment_sequence
        )

        # Store transaction ID
        payment.transaction_id = transaction_id
        payment.status = 'pending'
        payment.save()

        # Send email notifications
        from .email_service import PaymentEmailService

        # Send user confirmation
        user_email_sent = PaymentEmailService.send_user_payment_submitted_notification(payment)
        if not user_email_sent:
            logger.warning(f"Failed to send user confirmation email for payment {payment.reference_number}")

        # Send admin notification
        admin_email_sent = PaymentEmailService.send_admin_verification_notification(payment)
        if not admin_email_sent:
            logger.warning(f"Failed to send admin notification email for payment {payment.reference_number}")

        messages.success(request, 'Bank transfer payment submitted successfully! Your transaction ID has been sent to our team and will be verified within 24 hours.')
        return redirect('payments:payment_status', payment_id=payment.id)

    except Exception as e:
        logger.error(f"Bank transfer payment processing error: {str(e)}")
        messages.error(request, 'Bank transfer payment processing failed. Please try again.')
        return redirect('payments:payment_methods', course_id=course_id)


@login_required
def payment_status(request, payment_id):
    """
    Display payment status and next steps
    """
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    context = {
        'payment': payment,
        'course': payment.course,
    }
    
    return render(request, 'payments/payment_status.html', context)


@csrf_exempt
@require_POST
def mpesa_callback(request):
    """
    Handle M-Pesa payment callback from Safaricom
    """
    try:
        callback_data = json.loads(request.body)
        logger.info(f"M-Pesa callback received: {callback_data}")
        
        # Process callback data
        # This would contain the actual M-Pesa callback processing logic
        # For now, return success response
        
        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Success'
        })
        
    except Exception as e:
        logger.error(f"M-Pesa callback processing error: {str(e)}")
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': 'Failed'
        })


@csrf_exempt
@require_POST
def mpesa_timeout(request):
    """
    Handle M-Pesa payment timeout
    """
    try:
        timeout_data = json.loads(request.body)
        logger.info(f"M-Pesa timeout received: {timeout_data}")

        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Success'
        })

    except Exception as e:
        logger.error(f"M-Pesa timeout processing error: {str(e)}")
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': 'Failed'
        })


@csrf_exempt
@require_POST
def paypal_webhook(request):
    """
    Handle PayPal webhook notifications for automated payment verification
    """
    try:
        from .paypal_service import PayPalService

        # Verify webhook signature
        if not PayPalService.verify_webhook_signature(request.body, request.headers):
            logger.warning("PayPal webhook signature verification failed")
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

        webhook_data = json.loads(request.body)
        logger.info(f"PayPal webhook received: {webhook_data.get('event_type', 'unknown')}")

        event_type = webhook_data.get('event_type')

        if event_type == 'CHECKOUT.ORDER.APPROVED':
            # Payment approved, capture it
            order_id = webhook_data['resource']['id']
            capture_result = PayPalService.capture_payment_order(order_id)

            if capture_result['success']:
                # Find payment by PayPal order ID
                try:
                    payment = Payment.objects.get(paypal_payment_id=order_id)

                    # Confirm payment using existing service
                    confirmation_result = PaymentService.confirm_payment(
                        payment.reference_number,
                        transaction_id=capture_result['capture_id']
                    )

                    if confirmation_result['success']:
                        logger.info(f"PayPal payment auto-confirmed: {payment.reference_number}")
                    else:
                        logger.error(f"Failed to confirm PayPal payment: {payment.reference_number}")

                except Payment.DoesNotExist:
                    logger.error(f"Payment not found for PayPal order: {order_id}")

        elif event_type == 'PAYMENT.CAPTURE.COMPLETED':
            # Payment captured successfully
            capture_id = webhook_data['resource']['id']
            logger.info(f"PayPal payment captured: {capture_id}")

        return JsonResponse({'status': 'success'})

    except Exception as e:
        logger.error(f"PayPal webhook processing error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def paypal_return(request):
    """
    Handle PayPal payment return (success)
    """
    try:
        payment_id = request.GET.get('payment_id')
        token = request.GET.get('token')  # PayPal order ID
        payer_id = request.GET.get('PayerID')

        if not payment_id or not token:
            messages.error(request, 'Invalid PayPal return parameters.')
            return redirect('courses:course_list')

        # Get payment object
        payment = get_object_or_404(Payment, id=payment_id, user=request.user)

        # Capture the payment
        from .paypal_service import PayPalService
        capture_result = PayPalService.capture_payment_order(token)

        if capture_result['success']:
            # Update payment with payer ID and capture ID
            payment.paypal_payer_id = payer_id
            payment.transaction_id = capture_result['capture_id']
            payment.save()

            # Confirm payment
            confirmation_result = PaymentService.confirm_payment(
                payment.reference_number,
                transaction_id=capture_result['capture_id']
            )

            if confirmation_result['success']:
                messages.success(request, 'PayPal payment completed successfully! Your course access has been activated.')
                return redirect('payments:payment_status', payment_id=payment.id)
            else:
                messages.error(request, 'Payment captured but confirmation failed. Please contact support.')
                return redirect('payments:payment_status', payment_id=payment.id)
        else:
            messages.error(request, f'PayPal payment capture failed: {capture_result["message"]}')
            return redirect('payments:payment_status', payment_id=payment.id)

    except Exception as e:
        logger.error(f"PayPal return processing error: {str(e)}")
        messages.error(request, 'Payment processing error. Please contact support.')
        return redirect('courses:course_list')


@login_required
def paypal_cancel(request):
    """
    Handle PayPal payment cancellation
    """
    try:
        payment_id = request.GET.get('payment_id')

        if payment_id:
            payment = get_object_or_404(Payment, id=payment_id, user=request.user)
            payment.status = 'failed'
            payment.notes = 'Payment cancelled by user on PayPal'
            payment.save()

            messages.warning(request, 'PayPal payment was cancelled. You can try again or use a different payment method.')
            return redirect('payments:payment_methods', course_id=payment.course.id)
        else:
            messages.info(request, 'Payment was cancelled.')
            return redirect('courses:course_list')

    except Exception as e:
        logger.error(f"PayPal cancel processing error: {str(e)}")
        messages.info(request, 'Payment was cancelled.')
        return redirect('courses:course_list')
