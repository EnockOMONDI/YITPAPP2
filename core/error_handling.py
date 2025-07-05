"""
Enhanced Error Handling and User Experience for YITP
Provides comprehensive error handling, logging, and user feedback
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
import logging
import traceback
from functools import wraps

logger = logging.getLogger(__name__)


class YITPError(Exception):
    """Base exception for YITP-specific errors"""
    def __init__(self, message, error_code=None, user_message=None):
        self.message = message
        self.error_code = error_code
        self.user_message = user_message or message
        super().__init__(self.message)


class EnrollmentError(YITPError):
    """Enrollment-specific errors"""
    pass


class PaymentError(YITPError):
    """Payment-specific errors"""
    pass


class CertificateError(YITPError):
    """Certificate-specific errors"""
    pass


class ErrorHandler:
    """
    Centralized error handling for YITP application
    """
    
    # Error codes for different types of errors
    ERROR_CODES = {
        'ENROLLMENT_LIMIT_REACHED': 'E001',
        'PAYMENT_REQUIRED': 'E002',
        'ALREADY_ENROLLED': 'E003',
        'COURSE_NOT_FOUND': 'E004',
        'PAYMENT_FAILED': 'P001',
        'PAYMENT_EXPIRED': 'P002',
        'CERTIFICATE_GENERATION_FAILED': 'C001',
        'EMAIL_DELIVERY_FAILED': 'N001',
        'DATABASE_ERROR': 'D001',
        'VALIDATION_ERROR': 'V001',
        'PERMISSION_DENIED': 'A001',
    }
    
    @staticmethod
    def handle_enrollment_error(error, request, course=None):
        """
        Handle enrollment-specific errors with appropriate user feedback
        
        Args:
            error: Exception object
            request: Django request object
            course: Course object (optional)
            
        Returns:
            HttpResponse: Redirect response with appropriate message
        """
        error_info = ErrorHandler._analyze_error(error)
        
        # Log the error
        logger.error(f"Enrollment error: {error_info['message']}", extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous',
            'course': course.title if course else 'Unknown',
            'error_code': error_info['code'],
            'traceback': traceback.format_exc()
        })
        
        # Provide user feedback
        if error_info['code'] == 'E001':  # Enrollment limit reached
            messages.error(
                request,
                f"Sorry, this course has reached its enrollment limit. "
                f"Please check back later or contact support for waitlist options."
            )
        elif error_info['code'] == 'E002':  # Payment required
            messages.error(
                request,
                f"Payment verification is required for this course. "
                f"Please complete your payment and wait for confirmation before enrolling."
            )
        elif error_info['code'] == 'E003':  # Already enrolled
            messages.info(
                request,
                "You are already enrolled in this course. Check your dashboard to continue learning."
            )
        else:
            # Generic enrollment error
            messages.error(
                request,
                "We encountered an issue processing your enrollment. "
                "Please try again or contact support if the problem persists."
            )
        
        # Redirect to appropriate page
        if course:
            return redirect('courses:course_detail', slug=course.slug)
        else:
            return redirect('courses:course_list')

    @staticmethod
    def handle_payment_error(error, request, payment=None):
        """Handle payment-specific errors"""
        error_info = ErrorHandler._analyze_error(error)
        
        logger.error(f"Payment error: {error_info['message']}", extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous',
            'payment_ref': payment.reference_number if payment else 'Unknown',
            'error_code': error_info['code'],
            'traceback': traceback.format_exc()
        })
        
        if error_info['code'] == 'P001':  # Payment failed
            messages.error(
                request,
                "Payment processing failed. Please check your payment details and try again. "
                "Contact support if you continue to experience issues."
            )
        elif error_info['code'] == 'P002':  # Payment expired
            messages.warning(
                request,
                "Your payment session has expired. Please initiate a new payment to continue."
            )
        else:
            messages.error(
                request,
                "We encountered an issue processing your payment. "
                "Please try again or contact support."
            )
        
        return redirect('payments:payment_methods')

    @staticmethod
    def handle_certificate_error(error, request, enrollment=None):
        """Handle certificate-specific errors"""
        error_info = ErrorHandler._analyze_error(error)
        
        logger.error(f"Certificate error: {error_info['message']}", extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous',
            'course': enrollment.course.title if enrollment else 'Unknown',
            'error_code': error_info['code'],
            'traceback': traceback.format_exc()
        })
        
        messages.error(
            request,
            "We encountered an issue generating your certificate. "
            "Our team has been notified and will resolve this shortly. "
            "You can also contact support for immediate assistance."
        )
        
        return redirect('progress:dashboard')

    @staticmethod
    def _analyze_error(error):
        """Analyze error and return structured information"""
        if isinstance(error, YITPError):
            return {
                'message': error.message,
                'code': error.error_code or 'UNKNOWN',
                'user_message': error.user_message
            }
        elif isinstance(error, ValidationError):
            return {
                'message': str(error),
                'code': 'V001',
                'user_message': 'Please check your input and try again.'
            }
        elif isinstance(error, IntegrityError):
            return {
                'message': str(error),
                'code': 'D001',
                'user_message': 'A database error occurred. Please try again.'
            }
        else:
            return {
                'message': str(error),
                'code': 'UNKNOWN',
                'user_message': 'An unexpected error occurred. Please try again.'
            }

    @staticmethod
    def log_user_action(user, action, details=None, success=True):
        """Log user actions for audit trail"""
        logger.info(f"User action: {action}", extra={
            'user': user.email if user.is_authenticated else 'Anonymous',
            'action': action,
            'details': details or {},
            'success': success,
            'timestamp': timezone.now().isoformat()
        })


def handle_errors(error_type='general'):
    """
    Decorator for handling errors in views
    
    Usage:
        @handle_errors('enrollment')
        def enroll_view(request, course_slug):
            # view logic here
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except EnrollmentError as e:
                return ErrorHandler.handle_enrollment_error(e, request)
            except PaymentError as e:
                return ErrorHandler.handle_payment_error(e, request)
            except CertificateError as e:
                return ErrorHandler.handle_certificate_error(e, request)
            except Exception as e:
                # Log unexpected errors
                logger.error(f"Unexpected error in {view_func.__name__}: {str(e)}", extra={
                    'view': view_func.__name__,
                    'user': request.user.email if request.user.is_authenticated else 'Anonymous',
                    'traceback': traceback.format_exc()
                })
                
                messages.error(
                    request,
                    "An unexpected error occurred. Our team has been notified. "
                    "Please try again or contact support if the issue persists."
                )
                
                # Redirect to safe page
                if error_type == 'enrollment':
                    return redirect('courses:course_list')
                elif error_type == 'payment':
                    return redirect('payments:payment_methods')
                else:
                    return redirect('dashboard')
        
        return wrapper
    return decorator


class UserFeedbackManager:
    """
    Manage user feedback and notifications
    """
    
    @staticmethod
    def success_message(request, message, extra_tags=''):
        """Add success message with consistent styling"""
        messages.success(request, message, extra_tags=f'alert-success {extra_tags}')
    
    @staticmethod
    def error_message(request, message, extra_tags=''):
        """Add error message with consistent styling"""
        messages.error(request, message, extra_tags=f'alert-danger {extra_tags}')
    
    @staticmethod
    def warning_message(request, message, extra_tags=''):
        """Add warning message with consistent styling"""
        messages.warning(request, message, extra_tags=f'alert-warning {extra_tags}')
    
    @staticmethod
    def info_message(request, message, extra_tags=''):
        """Add info message with consistent styling"""
        messages.info(request, message, extra_tags=f'alert-info {extra_tags}')
    
    @staticmethod
    def enrollment_success(request, course, enrollment_created=True):
        """Standardized enrollment success message"""
        if enrollment_created:
            if course.price > 0:
                UserFeedbackManager.success_message(
                    request,
                    f'🎉 Successfully enrolled in "{course.title}"! Your payment has been verified. '
                    f'Check your email for confirmation details and course access instructions.'
                )
            else:
                UserFeedbackManager.success_message(
                    request,
                    f'🎉 Successfully enrolled in "{course.title}"! '
                    f'Check your email for confirmation details and start learning immediately.'
                )
        else:
            UserFeedbackManager.info_message(
                request,
                f'You are already enrolled in "{course.title}". '
                f'Continue your learning journey from your dashboard.'
            )
    
    @staticmethod
    def payment_success(request, payment):
        """Standardized payment success message"""
        UserFeedbackManager.success_message(
            request,
            f'💳 Payment confirmed! Reference: {payment.reference_number}. '
            f'You can now enroll in paid courses. Check your email for payment confirmation.'
        )
    
    @staticmethod
    def certificate_generated(request, certificate):
        """Standardized certificate generation message"""
        UserFeedbackManager.success_message(
            request,
            f'🏆 Congratulations! Your certificate has been generated. '
            f'Certificate ID: {certificate.certificate_id}. '
            f'Download it from your dashboard or check your email.'
        )


def ajax_error_handler(view_func):
    """Decorator for handling AJAX view errors"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"AJAX error in {view_func.__name__}: {str(e)}", extra={
                'view': view_func.__name__,
                'user': request.user.email if request.user.is_authenticated else 'Anonymous',
                'traceback': traceback.format_exc()
            })
            
            return JsonResponse({
                'success': False,
                'error': 'An error occurred processing your request.',
                'message': 'Please try again or contact support if the issue persists.'
            }, status=500)
    
    return wrapper
