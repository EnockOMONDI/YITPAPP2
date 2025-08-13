"""
Email Service for Payment Notifications
Handles sending email notifications for payment verification and user confirmations
"""

import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class PaymentEmailService:
    """Service for sending payment-related email notifications"""
    
    # Email addresses
    ADMIN_EMAIL = 'youthimpactglobal3@gmail.com'
    FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@yitp.org')
    
    @staticmethod
    def get_base_url():
        """Get the base URL for the application"""
        try:
            current_site = Site.objects.get_current()
            # Check if we're in development
            if settings.DEBUG and 'localhost' in current_site.domain:
                return 'http://127.0.0.1:8001'
            elif settings.DEBUG:
                return 'http://localhost:8001'
            else:
                protocol = 'https' if getattr(settings, 'USE_HTTPS', True) else 'http'
                return f"{protocol}://{current_site.domain}"
        except:
            # Fallback URLs based on environment
            if settings.DEBUG:
                return 'http://127.0.0.1:8001'
            else:
                return 'https://yitp.org'
    
    @staticmethod
    def send_admin_verification_notification(payment):
        """
        Send email notification to admin when payment requires verification
        
        Args:
            payment: Payment object requiring verification
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            base_url = PaymentEmailService.get_base_url()

            # Generate admin URLs using reverse
            try:
                admin_url = f"{base_url}{reverse('admin:payments_payment_change', args=[payment.id])}"
                user_profile_url = f"{base_url}{reverse('admin:auth_user_change', args=[payment.user.id])}"
            except:
                # Fallback to manual URL construction
                admin_url = f"{base_url}/admin/payments/payment/{payment.id}/change/"
                user_profile_url = f"{base_url}/admin/auth/user/{payment.user.id}/change/"
            
            # Email context
            context = {
                'payment': payment,
                'user': payment.user,
                'course': payment.course,
                'admin_url': admin_url,
                'user_profile_url': user_profile_url,
                'base_url': base_url,
            }
            
            # Render email templates
            html_content = render_to_string('emails/admin_payment_verification_needed.html', context)
            text_content = strip_tags(html_content)
            
            # Email subject
            payment_method = payment.get_payment_method_display()
            subject = f"🔔 YITP: {payment_method} Payment Verification Required - {payment.reference_number}"
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=PaymentEmailService.FROM_EMAIL,
                to=[PaymentEmailService.ADMIN_EMAIL],
                reply_to=[PaymentEmailService.FROM_EMAIL]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            logger.info(f"Admin verification notification sent for payment {payment.reference_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send admin verification notification for payment {payment.reference_number}: {str(e)}")
            return False
    
    @staticmethod
    def send_user_payment_submitted_notification(payment):
        """
        Send confirmation email to user when payment is submitted
        
        Args:
            payment: Payment object that was submitted
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            base_url = PaymentEmailService.get_base_url()
            
            # Generate user URLs
            payment_status_url = f"{base_url}{reverse('payments:payment_status', args=[payment.id])}"
            profile_url = f"{base_url}{reverse('profile')}"
            
            # Email context
            context = {
                'payment': payment,
                'user': payment.user,
                'course': payment.course,
                'payment_status_url': payment_status_url,
                'profile_url': profile_url,
                'base_url': base_url,
            }
            
            # Render email templates
            html_content = render_to_string('emails/user_payment_submitted.html', context)
            text_content = strip_tags(html_content)
            
            # Email subject
            payment_method = payment.get_payment_method_display()
            subject = f"✅ YITP: {payment_method} Payment Submitted Successfully - {payment.course.title}"
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=PaymentEmailService.FROM_EMAIL,
                to=[payment.user.email],
                reply_to=[PaymentEmailService.FROM_EMAIL]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            logger.info(f"User payment confirmation sent to {payment.user.email} for payment {payment.reference_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send user payment confirmation for payment {payment.reference_number}: {str(e)}")
            return False
    
    @staticmethod
    def send_payment_verified_notification(payment):
        """
        Send notification to user when payment is verified and approved
        
        Args:
            payment: Payment object that was verified
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            base_url = PaymentEmailService.get_base_url()

            # Generate URLs using reverse
            try:
                course_url = f"{base_url}{reverse('courses:course_detail', args=[payment.course.id])}"
                dashboard_url = f"{base_url}{reverse('users:profile')}"
            except:
                # Fallback URLs
                course_url = f"{base_url}/courses/{payment.course.id}/"
                dashboard_url = f"{base_url}/profile/"

            # Email context
            context = {
                'payment': payment,
                'user': payment.user,
                'course': payment.course,
                'course_url': course_url,
                'dashboard_url': dashboard_url,
                'base_url': base_url,
            }

            # Render email templates
            html_content = render_to_string('emails/payment_verified.html', context)
            text_content = strip_tags(html_content)

            # Email subject
            subject = f"🎉 YITP: Payment Verified - Welcome to {payment.course.title}!"

            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=PaymentEmailService.FROM_EMAIL,
                to=[payment.user.email],
                reply_to=[PaymentEmailService.FROM_EMAIL]
            )
            email.attach_alternative(html_content, "text/html")

            # Send email
            email.send()
            
            logger.info(f"Payment verification notification sent to {payment.user.email} for payment {payment.reference_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send payment verification notification for payment {payment.reference_number}: {str(e)}")
            return False
    
    @staticmethod
    def send_payment_rejected_notification(payment, reason=""):
        """
        Send notification to user when payment is rejected
        
        Args:
            payment: Payment object that was rejected
            reason: Optional reason for rejection
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            base_url = PaymentEmailService.get_base_url()

            # Generate URLs using reverse
            try:
                payment_url = f"{base_url}{reverse('payments:payment_methods', args=[payment.course.id])}"
            except:
                # Fallback URL
                payment_url = f"{base_url}/payments/methods/{payment.course.id}/"

            # Email context
            context = {
                'payment': payment,
                'user': payment.user,
                'course': payment.course,
                'payment_url': payment_url,
                'rejection_reason': reason,
                'base_url': base_url,
            }

            # Render email templates
            html_content = render_to_string('emails/payment_rejected.html', context)
            text_content = strip_tags(html_content)

            # Email subject
            subject = f"❌ YITP: Payment Verification Issue - {payment.reference_number}"

            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=PaymentEmailService.FROM_EMAIL,
                to=[payment.user.email],
                reply_to=[PaymentEmailService.FROM_EMAIL]
            )
            email.attach_alternative(html_content, "text/html")

            # Send email
            email.send()
            
            logger.info(f"Payment rejection notification sent to {payment.user.email} for payment {payment.reference_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send payment rejection notification for payment {payment.reference_number}: {str(e)}")
            return False
    
    @staticmethod
    def send_installment_reminder(payment):
        """
        Send reminder email for second installment payment
        
        Args:
            payment: First installment payment object
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            if not payment.is_installment or payment.installment_sequence != 1:
                return False
            
            base_url = PaymentEmailService.get_base_url()
            payment_methods_url = f"{base_url}{reverse('payments:payment_methods', args=[payment.course.id])}"
            
            # Calculate remaining amount
            remaining_amount = payment.amount  # Second installment is same as first
            
            subject = f"⏰ YITP: Second Installment Due - {payment.course.title}"
            
            message = f"""
Dear {payment.user.get_full_name() or payment.user.username},

This is a reminder that your second installment payment is due for {payment.course.title}.

Payment Details:
- Remaining Amount: KES {remaining_amount:,.0f}
- Course: {payment.course.title}
- Due: Within 30 days of first payment

Complete your payment to maintain full course access.

Pay now: {payment_methods_url}

Best regards,
YITP Team
            """.strip()
            
            send_mail(
                subject=subject,
                message=message,
                from_email=PaymentEmailService.FROM_EMAIL,
                recipient_list=[payment.user.email],
                fail_silently=False
            )
            
            logger.info(f"Installment reminder sent to {payment.user.email} for payment {payment.reference_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send installment reminder for payment {payment.reference_number}: {str(e)}")
            return False

    @staticmethod
    def send_enhanced_installment_reminder(profile, days_since_payment):
        """
        Send enhanced installment reminder email to user with partial payment

        Args:
            profile: User profile with partial payment
            days_since_payment: Number of days since first installment payment

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            base_url = PaymentEmailService.get_base_url()

            # Get the course from the user's enrollment
            from progress.models import Enrollment
            enrollment = Enrollment.objects.filter(student=profile.user, status='active').first()
            if not enrollment:
                logger.warning(f"No active enrollment found for user {profile.user.email}")
                return False

            course = enrollment.course
            remaining_amount = profile.remaining_installment_amount
            days_until_expiry = profile.days_until_expiration

            # Generate URLs using reverse
            try:
                payment_url = f"{base_url}{reverse('payments:payment_methods', args=[course.id])}"
                paypal_payment_url = "https://www.paypal.com/ncp/payment/FUAJVJ66L978C"
            except:
                # Fallback URLs
                payment_url = f"{base_url}/payments/methods/{course.id}/"
                paypal_payment_url = "https://www.paypal.com/ncp/payment/FUAJVJ66L978C"

            # Email context
            context = {
                'user': profile.user,
                'course': course,
                'first_payment_amount': profile.installment_amount_paid,
                'remaining_amount': remaining_amount,
                'days_remaining': days_until_expiry,
                'payment_due_date': profile.payment_expiration_date,
                'payment_url': payment_url,
                'paypal_payment_url': paypal_payment_url,
                'base_url': base_url,
            }

            # Render email templates
            html_content = render_to_string('emails/installment_reminder.html', context)
            text_content = strip_tags(html_content)

            # Email subject
            subject = f"⏰ YITP: Second Installment Reminder - KES {remaining_amount:,.0f} Due"

            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=PaymentEmailService.FROM_EMAIL,
                to=[profile.user.email],
                reply_to=[PaymentEmailService.FROM_EMAIL]
            )
            email.attach_alternative(html_content, "text/html")

            # Send email
            email.send()

            logger.info(f"Enhanced installment reminder sent to {profile.user.email} - {days_since_payment} days since payment")
            return True

        except Exception as e:
            logger.error(f"Failed to send enhanced installment reminder to {profile.user.email}: {str(e)}")
            return False

    @staticmethod
    def send_expiry_warning_email(profile, days_remaining):
        """
        Send expiry warning email to user with partial payment

        Args:
            profile: User profile with partial payment
            days_remaining: Number of days until expiry

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            base_url = PaymentEmailService.get_base_url()

            # Get the course from the user's enrollment
            from progress.models import Enrollment
            enrollment = Enrollment.objects.filter(student=profile.user, status='active').first()
            if not enrollment:
                logger.warning(f"No active enrollment found for user {profile.user.email}")
                return False

            course = enrollment.course
            remaining_amount = profile.remaining_installment_amount

            # Generate URLs using reverse
            try:
                payment_url = f"{base_url}{reverse('payments:payment_methods', args=[course.id])}"
                paypal_payment_url = "https://www.paypal.com/ncp/payment/FUAJVJ66L978C"
            except:
                # Fallback URLs
                payment_url = f"{base_url}/payments/methods/{course.id}/"
                paypal_payment_url = "https://www.paypal.com/ncp/payment/FUAJVJ66L978C"

            # Email context
            context = {
                'user': profile.user,
                'course': course,
                'first_payment_amount': profile.installment_amount_paid,
                'remaining_amount': remaining_amount,
                'days_remaining': days_remaining,
                'expiration_date': profile.payment_expiration_date,
                'payment_url': payment_url,
                'paypal_payment_url': paypal_payment_url,
                'base_url': base_url,
            }

            # Render email templates
            html_content = render_to_string('emails/payment_expiration_warning.html', context)
            text_content = strip_tags(html_content)

            # Email subject
            urgency = "🚨 URGENT" if days_remaining == 1 else "⚠️ WARNING"
            subject = f"{urgency}: YITP Course Access Expires in {days_remaining} Day{'s' if days_remaining > 1 else ''}"

            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=PaymentEmailService.FROM_EMAIL,
                to=[profile.user.email],
                reply_to=[PaymentEmailService.FROM_EMAIL]
            )
            email.attach_alternative(html_content, "text/html")

            # Send email
            email.send()

            logger.info(f"Expiry warning sent to {profile.user.email} - {days_remaining} days remaining")
            return True

        except Exception as e:
            logger.error(f"Failed to send expiry warning to {profile.user.email}: {str(e)}")
            return False

    @staticmethod
    def send_renewal_reminder_email(profile, days_since_expiry):
        """
        Send renewal reminder email to user with expired payment

        Args:
            profile: User profile with expired payment
            days_since_expiry: Number of days since payment expired

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            base_url = PaymentEmailService.get_base_url()
            payment_methods_url = f"{base_url}/payments/methods/"

            # Email subject and content
            if days_since_expiry == 1:
                subject = "💔 YITP: Your Course Access Has Expired - Renew Now"
                urgency_message = "Your course access expired yesterday."
            elif days_since_expiry <= 7:
                subject = f"🔄 YITP: Renew Your Course Access - {days_since_expiry} Days Since Expiry"
                urgency_message = f"Your course access expired {days_since_expiry} days ago."
            else:
                subject = f"🎯 YITP: We Miss You! Renew Your Course Access"
                urgency_message = f"Your course access expired {days_since_expiry} days ago."

            message = f"""
Dear {profile.user.get_full_name() or profile.user.username},

{urgency_message} But it's not too late to continue your learning journey with YITP!

RENEWAL DETAILS:
- Account status: Expired
- Days since expiry: {days_since_expiry}
- Renewal required: Full course payment

WHAT YOU'LL GET BACK:
✓ Full access to all course materials
✓ Progress tracking and certificates
✓ Community discussions and support
✓ Updated content and new features

RENEW YOUR ACCESS:
Visit our payment page to restart your YITP journey:
{payment_methods_url}

PAYMENT METHODS AVAILABLE:
• M-Pesa: Quick mobile payment
• Bank Transfer: Direct bank transfer
• PayPal: Secure online payment
• Installment Plan: Pay 50% now, 50% later

Don't let your goals wait! Renew today and continue building your future.

Questions? Contact support@yitp.org or call +254722646958

Best regards,
YITP Team
            """.strip()

            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=PaymentEmailService.FROM_EMAIL,
                recipient_list=[profile.user.email],
                fail_silently=False
            )

            logger.info(f"Renewal reminder sent to {profile.user.email} - {days_since_expiry} days since expiry")
            return True

        except Exception as e:
            logger.error(f"Failed to send renewal reminder to {profile.user.email}: {str(e)}")
            return False

    @staticmethod
    def send_paypal_payment_initiated_notification(payment):
        """
        Send email notification when PayPal payment is initiated

        Args:
            payment: Payment object

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            base_url = PaymentEmailService.get_base_url()

            # Email context
            context = {
                'user': payment.user,
                'course': payment.course,
                'payment': payment,
                'amount': payment.amount,
                'currency': 'USD',
                'is_installment': payment.is_installment,
                'installment_sequence': payment.installment_sequence,
                'base_url': base_url,
                'support_email': PaymentEmailService.ADMIN_EMAIL,
            }

            # Render email template
            html_message = render_to_string('emails/paypal_payment_initiated.html', context)
            plain_message = strip_tags(html_message)

            # Send email
            send_mail(
                subject=f'PayPal Payment Initiated - {payment.course.title}',
                message=plain_message,
                html_message=html_message,
                from_email=PaymentEmailService.FROM_EMAIL,
                recipient_list=[payment.user.email],
                fail_silently=False
            )

            logger.info(f"PayPal payment initiated notification sent to {payment.user.email} for payment {payment.reference_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send PayPal payment initiated notification: {str(e)}")
            return False

    @staticmethod
    def send_paypal_payment_success_notification(payment, transaction_id=None):
        """
        Send email notification when PayPal payment is successful

        Args:
            payment: Payment object
            transaction_id: PayPal transaction ID

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            base_url = PaymentEmailService.get_base_url()

            # Generate course access URL
            try:
                course_url = f"{base_url}{reverse('courses:course_detail', args=[payment.course.id])}"
            except:
                course_url = f"{base_url}/lms/courses/courses/{payment.course.slug}/"

            # Email context
            context = {
                'user': payment.user,
                'course': payment.course,
                'payment': payment,
                'amount': payment.amount,
                'currency': 'USD',
                'transaction_id': transaction_id or payment.transaction_id,
                'is_installment': payment.is_installment,
                'installment_sequence': payment.installment_sequence,
                'course_url': course_url,
                'base_url': base_url,
                'support_email': PaymentEmailService.ADMIN_EMAIL,
            }

            # Render email template
            html_message = render_to_string('emails/paypal_payment_success.html', context)
            plain_message = strip_tags(html_message)

            # Send email to user
            send_mail(
                subject=f'Payment Successful - Course Access Activated: {payment.course.title}',
                message=plain_message,
                html_message=html_message,
                from_email=PaymentEmailService.FROM_EMAIL,
                recipient_list=[payment.user.email],
                fail_silently=False
            )

            # Send admin notification
            PaymentEmailService.send_paypal_admin_success_notification(payment, transaction_id)

            logger.info(f"PayPal payment success notification sent to {payment.user.email} for payment {payment.reference_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send PayPal payment success notification: {str(e)}")
            return False

    @staticmethod
    def send_paypal_payment_failed_notification(payment, error_message=None):
        """
        Send email notification when PayPal payment fails

        Args:
            payment: Payment object
            error_message: Error message from PayPal

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            base_url = PaymentEmailService.get_base_url()

            # Generate retry payment URL
            try:
                retry_url = f"{base_url}{reverse('payments:payment_methods', args=[payment.course.id])}"
            except:
                retry_url = f"{base_url}/payments/methods/{payment.course.id}/"

            # Email context
            context = {
                'user': payment.user,
                'course': payment.course,
                'payment': payment,
                'amount': payment.amount,
                'currency': 'USD',
                'error_message': error_message,
                'retry_url': retry_url,
                'base_url': base_url,
                'support_email': PaymentEmailService.ADMIN_EMAIL,
            }

            # Render email template
            html_message = render_to_string('emails/paypal_payment_failed.html', context)
            plain_message = strip_tags(html_message)

            # Send email
            send_mail(
                subject=f'PayPal Payment Failed - {payment.course.title}',
                message=plain_message,
                html_message=html_message,
                from_email=PaymentEmailService.FROM_EMAIL,
                recipient_list=[payment.user.email],
                fail_silently=False
            )

            # Send admin alert
            PaymentEmailService.send_paypal_admin_failure_notification(payment, error_message)

            logger.info(f"PayPal payment failed notification sent to {payment.user.email} for payment {payment.reference_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send PayPal payment failed notification: {str(e)}")
            return False

    @staticmethod
    def send_paypal_admin_success_notification(payment, transaction_id=None):
        """
        Send admin notification when PayPal payment is successful

        Args:
            payment: Payment object
            transaction_id: PayPal transaction ID

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            base_url = PaymentEmailService.get_base_url()

            # Email context
            context = {
                'payment': payment,
                'user': payment.user,
                'course': payment.course,
                'amount': payment.amount,
                'currency': 'USD',
                'transaction_id': transaction_id or payment.transaction_id,
                'is_installment': payment.is_installment,
                'installment_sequence': payment.installment_sequence,
                'base_url': base_url,
                'admin_url': f"{base_url}/admin/payments/payment/{payment.id}/change/",
            }

            # Render email template
            html_message = render_to_string('emails/paypal_admin_success.html', context)
            plain_message = strip_tags(html_message)

            # Send email to admin
            send_mail(
                subject=f'PayPal Payment Received - ${payment.amount} USD - {payment.user.get_full_name()}',
                message=plain_message,
                html_message=html_message,
                from_email=PaymentEmailService.FROM_EMAIL,
                recipient_list=[PaymentEmailService.ADMIN_EMAIL],
                fail_silently=False
            )

            logger.info(f"PayPal admin success notification sent for payment {payment.reference_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send PayPal admin success notification: {str(e)}")
            return False

    @staticmethod
    def send_paypal_admin_failure_notification(payment, error_message=None):
        """
        Send admin notification when PayPal payment fails

        Args:
            payment: Payment object
            error_message: Error message from PayPal

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            base_url = PaymentEmailService.get_base_url()

            # Email context
            context = {
                'payment': payment,
                'user': payment.user,
                'course': payment.course,
                'amount': payment.amount,
                'currency': 'USD',
                'error_message': error_message,
                'base_url': base_url,
                'admin_url': f"{base_url}/admin/payments/payment/{payment.id}/change/",
            }

            # Render email template
            html_message = render_to_string('emails/paypal_admin_failure.html', context)
            plain_message = strip_tags(html_message)

            # Send email to admin
            send_mail(
                subject=f'PayPal Payment Failed - ${payment.amount} USD - {payment.user.get_full_name()}',
                message=plain_message,
                html_message=html_message,
                from_email=PaymentEmailService.FROM_EMAIL,
                recipient_list=[PaymentEmailService.ADMIN_EMAIL],
                fail_silently=False
            )

            logger.info(f"PayPal admin failure notification sent for payment {payment.reference_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send PayPal admin failure notification: {str(e)}")
            return False
