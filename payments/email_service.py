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
            protocol = 'https' if getattr(settings, 'USE_HTTPS', False) else 'http'
            return f"{protocol}://{current_site.domain}"
        except:
            return 'https://yitp.org'  # Fallback URL
    
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
            
            # Generate admin URLs
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
            course_url = f"{base_url}{reverse('courses:course_detail', args=[payment.course.id])}"
            
            # Email subject and content
            subject = f"🎉 YITP: Payment Verified - Welcome to {payment.course.title}!"
            
            # Simple text message for now (can be enhanced with template later)
            message = f"""
Dear {payment.user.get_full_name() or payment.user.username},

Great news! Your {payment.get_payment_method_display()} payment has been verified and approved.

Payment Details:
- Reference: {payment.reference_number}
- Course: {payment.course.title}
- Amount: KES {payment.amount:,.0f}

You now have access to your course. Start learning today!

Access your course: {course_url}

Best regards,
YITP Team
            """.strip()
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=PaymentEmailService.FROM_EMAIL,
                recipient_list=[payment.user.email],
                fail_silently=False
            )
            
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
            payment_methods_url = f"{base_url}{reverse('payments:payment_methods', args=[payment.course.id])}"
            
            # Email subject and content
            subject = f"❌ YITP: Payment Verification Failed - {payment.reference_number}"
            
            reason_text = f"\n\nReason: {reason}" if reason else ""
            
            message = f"""
Dear {payment.user.get_full_name() or payment.user.username},

We were unable to verify your {payment.get_payment_method_display()} payment for {payment.course.title}.

Payment Details:
- Reference: {payment.reference_number}
- Amount: KES {payment.amount:,.0f}
{reason_text}

Please try submitting your payment again or contact our support team for assistance.

Try again: {payment_methods_url}
Support: support@yitp.org

Best regards,
YITP Team
            """.strip()
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=PaymentEmailService.FROM_EMAIL,
                recipient_list=[payment.user.email],
                fail_silently=False
            )
            
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
            payment_methods_url = f"{base_url}/payments/methods/"

            remaining_amount = profile.remaining_installment_amount
            days_until_expiry = profile.days_until_expiration

            # Email subject and content
            subject = f"⏰ YITP: Second Installment Reminder - KES {remaining_amount:,.0f} Due"

            message = f"""
Dear {profile.user.get_full_name() or profile.user.username},

This is a friendly reminder about your second installment payment for the Youth Impact Training Programme.

PAYMENT DETAILS:
- First installment paid: {days_since_payment} days ago
- Remaining amount: KES {remaining_amount:,.0f}
- Days until access expires: {days_until_expiry}
- Payment due date: {profile.payment_expiration_date.strftime('%B %d, %Y')}

To complete your second installment payment, please visit:
{payment_methods_url}

PAYMENT METHODS AVAILABLE:
• M-Pesa: Quick mobile payment
• Bank Transfer: Direct bank transfer
• PayPal: Secure online payment

Don't lose access to your course! Complete your payment before {profile.payment_expiration_date.strftime('%B %d, %Y')}.

Need help? Contact our support team at support@yitp.org

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
            payment_methods_url = f"{base_url}/payments/methods/"

            remaining_amount = profile.remaining_installment_amount

            # Email subject and content
            urgency = "🚨 URGENT" if days_remaining == 1 else "⚠️ WARNING"
            subject = f"{urgency}: YITP Course Access Expires in {days_remaining} Day{'s' if days_remaining > 1 else ''}"

            message = f"""
Dear {profile.user.get_full_name() or profile.user.username},

{urgency}: Your YITP course access will expire in {days_remaining} day{'s' if days_remaining > 1 else ''}!

PAYMENT DETAILS:
- Remaining amount: KES {remaining_amount:,.0f}
- Expiry date: {profile.payment_expiration_date.strftime('%B %d, %Y at %I:%M %p')}
- Time remaining: {days_remaining} day{'s' if days_remaining > 1 else ''}

IMMEDIATE ACTION REQUIRED:
Complete your second installment payment now to maintain course access.

Pay now: {payment_methods_url}

PAYMENT METHODS AVAILABLE:
• M-Pesa: Quick mobile payment
• Bank Transfer: Direct bank transfer
• PayPal: Secure online payment

Don't lose your progress! Complete your payment immediately.

Need urgent help? Contact support@yitp.org or call +254722646958

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
