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


def _validate_mpesa_reference(mpesa_reference):
    """
    Validate M-Pesa reference code format and length

    Args:
        mpesa_reference: M-Pesa reference code to validate

    Returns:
        dict: {'valid': bool, 'message': str}
    """
    if not mpesa_reference:
        return {
            'valid': False,
            'message': 'M-Pesa reference code is required.'
        }

    # Remove whitespace and convert to uppercase
    mpesa_reference = mpesa_reference.strip().upper()

    # Check exact length (M-Pesa references are typically 10 characters)
    if len(mpesa_reference) != 10:
        return {
            'valid': False,
            'message': 'M-Pesa reference code must be exactly 10 characters long.'
        }

    # Check for valid characters (alphanumeric only)
    if not re.match(r'^[A-Z0-9]+$', mpesa_reference):
        return {
            'valid': False,
            'message': 'M-Pesa reference code contains invalid characters. Only letters and numbers are allowed.'
        }

    # Check for duplicate reference across all payments
    if Payment.objects.filter(transaction_id=mpesa_reference).exists():
        return {
            'valid': False,
            'message': 'This M-Pesa reference code has already been used. Please check your transaction history or contact support.'
        }

    return {
        'valid': True,
        'message': 'Valid M-Pesa reference code.'
    }


def _check_duplicate_mpesa_payment(user, course, mpesa_reference):
    """
    Check for duplicate M-Pesa payments

    Args:
        user: User making the payment
        course: Course being paid for
        mpesa_reference: M-Pesa reference code

    Returns:
        dict: {'exists': bool, 'message': str, 'payment': Payment or None}
    """
    # Check for duplicate reference
    duplicate_transaction = Payment.objects.filter(
        transaction_id=mpesa_reference
    ).first()

    if duplicate_transaction:
        return {
            'exists': True,
            'message': 'This M-Pesa reference code has already been used. Please check your payment history.',
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
        return redirect('courses:course_detail', slug=course.slug)
    
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
    Process fully automated PayPal payment order creation and redirect to PayPal
    """
    try:
        course_id = request.POST.get('course_id')
        amount = Decimal(request.POST.get('amount'))
        is_installment = request.POST.get('is_installment', 'false').lower() == 'true'
        installment_sequence = int(request.POST.get('installment_sequence', 1))

        course = get_object_or_404(Course, id=course_id)

        # Check for existing enrollment
        from progress.models import Enrollment
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            messages.info(request, 'You are already enrolled in this course.')
            return redirect('courses:course_detail', slug=course.slug)

        # Create payment record
        payment = PaymentService.create_payment_record(
            user=request.user,
            course=course,
            amount=amount,
            payment_method='paypal',
            is_installment=is_installment,
            installment_sequence=installment_sequence
        )

        # Send payment initiation email to user
        from .email_service import PaymentEmailService
        PaymentEmailService.send_paypal_payment_initiated_notification(payment)

        # Process PayPal payment using automated service
        result = PaymentService.process_paypal_payment(payment)

        if result['success']:
            # Redirect user to PayPal for payment
            return redirect(result['paypal_url'])
        else:
            # Send failure notification
            PaymentEmailService.send_paypal_payment_failed_notification(payment, result['message'])
            messages.error(request, f"PayPal payment setup failed: {result['message']}")
            return redirect('payments:payment_methods', course_id=course.id)

    except Exception as e:
        logger.error(f"PayPal payment processing error: {str(e)}")
        messages.error(request, 'Payment processing failed. Please try again.')
        return redirect('payments:payment_methods', course_id=course_id)


# Removed manual verification functions - PayPal is now fully automated


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
            return redirect('courses:course_detail', slug=course.slug)

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
@require_POST
def process_mpesa_paybill(request):
    """
    Process M-Pesa Paybill payment verification with enhanced validation and email notifications
    """
    try:
        course_id = request.POST.get('course_id')
        amount = Decimal(request.POST.get('amount'))
        mpesa_reference = request.POST.get('mpesa_reference', '').strip().upper()
        is_installment = request.POST.get('is_installment', 'false').lower() == 'true'
        installment_sequence = int(request.POST.get('installment_sequence', 1))

        course = get_object_or_404(Course, id=course_id)

        # Enhanced M-Pesa reference validation
        validation_result = _validate_mpesa_reference(mpesa_reference)
        if not validation_result['valid']:
            messages.error(request, validation_result['message'])
            return redirect('payments:payment_methods', course_id=course.id)

        # Check for existing enrollment
        from progress.models import Enrollment
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            messages.info(request, 'You are already enrolled in this course.')
            return redirect('courses:course_detail', slug=course.slug)

        # Enhanced duplicate payment prevention
        duplicate_check = _check_duplicate_mpesa_payment(request.user, course, mpesa_reference)
        if duplicate_check['exists']:
            messages.info(request, duplicate_check['message'])
            return redirect('payments:payment_status', payment_id=duplicate_check['payment'].id)

        # Create payment record
        payment = PaymentService.create_payment_record(
            user=request.user,
            course=course,
            amount=amount,
            payment_method='mpesa_paybill',
            is_installment=is_installment,
            installment_sequence=installment_sequence
        )

        # Store M-Pesa reference
        payment.transaction_id = mpesa_reference
        payment.status = 'pending'
        payment.save()

        # Send email notifications
        from .email_service import PaymentEmailService

        # Send user confirmation
        user_email_sent = PaymentEmailService.send_user_mpesa_submitted_notification(payment)
        if not user_email_sent:
            logger.warning(f"Failed to send user confirmation email for payment {payment.reference_number}")

        # Send admin notification
        admin_email_sent = PaymentEmailService.send_admin_mpesa_verification_notification(payment)
        if not admin_email_sent:
            logger.warning(f"Failed to send admin notification email for payment {payment.reference_number}")

        messages.success(request, 'M-Pesa payment submitted successfully! Your M-Pesa reference has been sent to our team and will be verified within 1 hour.')
        return redirect('payments:payment_status', payment_id=payment.id)

    except Exception as e:
        logger.error(f"M-Pesa payment processing error: {str(e)}")
        messages.error(request, 'M-Pesa payment processing failed. Please try again.')
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
    Handle PayPal webhook notifications for automated payment verification with idempotency
    """
    try:
        from .paypal_service import PayPalService
        from .email_service import PaymentEmailService
        from django.db import transaction

        # Verify webhook signature
        if not PayPalService.verify_webhook_signature(request.body, request.headers):
            logger.warning("PayPal webhook signature verification failed")
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

        webhook_data = json.loads(request.body)
        event_type = webhook_data.get('event_type', 'unknown')
        logger.info(f"PayPal webhook received: {event_type}")

        # Extract relevant IDs based on event type
        if event_type == 'CHECKOUT.ORDER.APPROVED':
            order_id = webhook_data['resource']['id']
            return handle_order_approved(order_id)

        elif event_type == 'PAYMENT.CAPTURE.COMPLETED':
            capture_data = webhook_data['resource']
            capture_id = capture_data['id']
            # Get order ID from capture data
            order_id = capture_data.get('supplementary_data', {}).get('related_ids', {}).get('order_id')
            if not order_id:
                # Try alternative path for order ID
                order_id = capture_data.get('invoice_id') or capture_data.get('custom_id')

            return handle_capture_completed(order_id, capture_id, capture_data)

        return JsonResponse({'status': 'success', 'message': f'Event {event_type} acknowledged'})

    except Exception as e:
        logger.error(f"PayPal webhook processing error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def handle_order_approved(order_id):
    """
    Handle CHECKOUT.ORDER.APPROVED webhook with idempotency checks
    """
    try:
        from .paypal_service import PayPalService
        from .email_service import PaymentEmailService
        from django.db import transaction

        # Find payment by PayPal order ID
        try:
            payment = Payment.objects.get(paypal_payment_id=order_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for PayPal order: {order_id}")
            return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=404)

        # Idempotency check: If payment is already confirmed, don't process again
        if payment.status == 'confirmed':
            logger.info(f"Payment {payment.reference_number} already confirmed, skipping duplicate webhook")
            return JsonResponse({'status': 'success', 'message': 'Payment already processed'})

        # Check if payment is in a state that can be captured
        if payment.status not in ['pending']:
            logger.warning(f"Payment {payment.reference_number} status is {payment.status}, cannot capture")
            return JsonResponse({'status': 'success', 'message': f'Payment status is {payment.status}'})

        # Attempt to capture the payment
        capture_result = PayPalService.capture_payment_order(order_id)

        if capture_result['success']:
            # Use database transaction to ensure atomicity
            with transaction.atomic():
                # Refresh payment object to avoid race conditions
                payment.refresh_from_db()

                # Double-check status after refresh
                if payment.status == 'confirmed':
                    logger.info(f"Payment {payment.reference_number} was confirmed by another process")
                    return JsonResponse({'status': 'success', 'message': 'Payment already confirmed'})

                # Confirm payment using existing service
                confirmation_result = PaymentService.confirm_payment(
                    payment.reference_number,
                    transaction_id=capture_result['capture_id']
                )

                if confirmation_result['success']:
                    logger.info(f"PayPal payment auto-confirmed: {payment.reference_number}")

                    # Send success email notifications (outside transaction to avoid blocking)
                    try:
                        PaymentEmailService.send_paypal_payment_success_notification(
                            payment,
                            capture_result['capture_id']
                        )
                    except Exception as e:
                        logger.error(f"Failed to send success notification: {str(e)}")

                    return JsonResponse({'status': 'success', 'message': 'Payment confirmed and notifications sent'})
                else:
                    logger.error(f"Failed to confirm PayPal payment: {payment.reference_number}")

                    # Send failure notification
                    try:
                        PaymentEmailService.send_paypal_payment_failed_notification(
                            payment,
                            f"Payment confirmation failed: {confirmation_result.get('message', 'Unknown error')}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send failure notification: {str(e)}")

                    return JsonResponse({'status': 'error', 'message': 'Payment confirmation failed'}, status=500)
        else:
            # Handle capture failure (including ORDER_ALREADY_CAPTURED)
            error_message = capture_result.get('message', 'Unknown error')

            # Check if this is an "already captured" error (which is actually success)
            if 'ORDER_ALREADY_CAPTURED' in error_message or 'already captured' in error_message.lower():
                logger.info(f"PayPal order {order_id} already captured, treating as success")

                # Try to find the capture ID from the error or use a placeholder
                capture_id = capture_result.get('capture_id') or f"CAPTURED_{order_id}"

                # Confirm payment if not already confirmed
                if payment.status != 'confirmed':
                    with transaction.atomic():
                        payment.refresh_from_db()
                        if payment.status != 'confirmed':
                            confirmation_result = PaymentService.confirm_payment(
                                payment.reference_number,
                                transaction_id=capture_id
                            )

                            if confirmation_result['success']:
                                logger.info(f"PayPal payment confirmed after already-captured: {payment.reference_number}")

                                # Send success notification
                                try:
                                    PaymentEmailService.send_paypal_payment_success_notification(
                                        payment,
                                        capture_id
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to send success notification: {str(e)}")

                return JsonResponse({'status': 'success', 'message': 'Payment already captured and confirmed'})
            else:
                logger.error(f"PayPal capture failed for order {order_id}: {error_message}")

                # Send failure notification
                try:
                    PaymentEmailService.send_paypal_payment_failed_notification(
                        payment,
                        f"PayPal capture failed: {error_message}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send failure notification: {str(e)}")

                return JsonResponse({'status': 'error', 'message': f'Capture failed: {error_message}'}, status=500)

    except Exception as e:
        logger.error(f"Error handling order approved webhook: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def handle_capture_completed(order_id, capture_id, capture_data):
    """
    Handle PAYMENT.CAPTURE.COMPLETED webhook
    """
    try:
        from .email_service import PaymentEmailService

        logger.info(f"PayPal payment captured: {capture_id} for order: {order_id}")

        # If we have order_id, try to find and confirm payment
        if order_id:
            try:
                payment = Payment.objects.get(paypal_payment_id=order_id)

                # If payment is not yet confirmed, confirm it now
                if payment.status != 'confirmed':
                    confirmation_result = PaymentService.confirm_payment(
                        payment.reference_number,
                        transaction_id=capture_id
                    )

                    if confirmation_result['success']:
                        logger.info(f"PayPal payment confirmed via capture webhook: {payment.reference_number}")

                        # Send success notification if not already sent
                        try:
                            PaymentEmailService.send_paypal_payment_success_notification(
                                payment,
                                capture_id
                            )
                        except Exception as e:
                            logger.error(f"Failed to send success notification: {str(e)}")
                else:
                    logger.info(f"Payment {payment.reference_number} already confirmed")

            except Payment.DoesNotExist:
                logger.warning(f"Payment not found for PayPal order: {order_id} (capture: {capture_id})")

        return JsonResponse({'status': 'success', 'message': 'Capture completed processed'})

    except Exception as e:
        logger.error(f"Error handling capture completed webhook: {str(e)}")
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
