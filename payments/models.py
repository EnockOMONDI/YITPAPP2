"""
Payment Models for YITP Enhanced Payment System
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class PaymentMethod(models.Model):
    """Available payment methods"""
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=100, blank=True)
    
    # Configuration fields
    requires_phone = models.BooleanField(default=False)
    requires_account_number = models.BooleanField(default=False)
    processing_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Payment(models.Model):
    """Payment records for course enrollments"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('card', 'Credit/Debit Card'),
        ('cash', 'Cash Payment'),
        ('other', 'Other'),
    ]
    
    # Core payment information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    
    # Payment method and reference
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, unique=True)
    transaction_id = models.CharField(max_length=200, blank=True, null=True)
    
    # Status and timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    # Additional payment details
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    processing_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Installment payment tracking
    is_installment = models.BooleanField(default=False, help_text="Whether this is an installment payment")
    installment_sequence = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Installment sequence (1 for first, 2 for second)"
    )
    related_payment = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Link to related installment payment"
    )

    # PayPal specific fields
    paypal_payment_id = models.CharField(max_length=200, blank=True, null=True)
    paypal_payer_id = models.CharField(max_length=200, blank=True, null=True)

    # Admin and tracking fields
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments'
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.reference_number} - {self.user.email} - {self.course.title}"
    
    @property
    def total_amount(self):
        """Total amount including processing fees"""
        return self.amount + self.processing_fee
    
    @property
    def is_expired(self):
        """Check if payment has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        # Default expiry: 24 hours from creation
        return (timezone.now() - self.created_at).total_seconds() > 86400
    
    @property
    def is_pending(self):
        """Check if payment is still pending"""
        return self.status == 'pending' and not self.is_expired
    
    @property
    def is_confirmed(self):
        """Check if payment is confirmed"""
        return self.status == 'confirmed'

    def confirm_payment(self, verified_by=None, notes=""):
        """Mark payment as confirmed"""
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        if verified_by:
            self.verified_by = verified_by
        if notes:
            self.notes = notes
        self.save()

        # Update user's profile payment status based on payment type
        profile = self.user.profile

        if self.is_installment and self.installment_sequence == 1:
            # First installment - grant partial access
            profile.confirm_partial_payment(
                amount=self.amount,
                course_price=self.course.price,
                method=self.payment_method,
                reference=self.reference_number,
                notes=notes
            )
        elif self.is_installment and self.installment_sequence == 2:
            # Second installment - complete payment
            profile.complete_installment_payment(
                remaining_amount=self.amount,
                reference=self.reference_number,
                notes=notes
            )
        else:
            # Full payment
            profile.confirm_payment(
                amount=self.amount,
                method=self.payment_method,
                reference=self.reference_number,
                notes=notes
            )

        return True

    @classmethod
    def create_installment_payment(cls, user, course, installment_sequence=1):
        """Create an installment payment record"""
        from decimal import Decimal

        if installment_sequence == 1:
            # First installment is 50% of course price
            amount = course.price * Decimal('0.5')
        else:
            # Second installment is remaining 50%
            amount = course.price * Decimal('0.5')

        payment = cls.objects.create(
            user=user,
            course=course,
            amount=amount,
            payment_method='mpesa',  # Default, will be updated
            reference_number=cls._generate_reference(),
            is_installment=True,
            installment_sequence=installment_sequence
        )

        return payment

    @staticmethod
    def _generate_reference():
        """Generate unique payment reference"""
        import uuid
        return f"YITP-{uuid.uuid4().hex[:8].upper()}"

    @property
    def is_first_installment(self):
        """Check if this is the first installment"""
        return self.is_installment and self.installment_sequence == 1

    @property
    def is_second_installment(self):
        """Check if this is the second installment"""
        return self.is_installment and self.installment_sequence == 2

    def save(self, *args, **kwargs):
        # Save first to get created_at if this is a new object
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Set expiry time if not set (only for new objects)
        if is_new and not self.expires_at and self.status == 'pending':
            self.expires_at = self.created_at + timezone.timedelta(hours=24)
            # Save again to update expires_at
            super().save(update_fields=['expires_at'])

        # Auto-expire if past expiry time
        elif self.expires_at and timezone.now() > self.expires_at and self.status == 'pending':
            self.status = 'expired'
            super().save(update_fields=['status'])


class PaymentCallback(models.Model):
    """Store payment gateway callbacks for debugging and reconciliation"""
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='callbacks')
    gateway = models.CharField(max_length=50)  # 'mpesa', 'stripe', etc.
    callback_data = models.JSONField()
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.gateway} callback for {self.payment.reference_number}"


class PaymentNotification(models.Model):
    """Track payment-related notifications sent to users"""
    
    NOTIFICATION_TYPES = [
        ('payment_pending', 'Payment Pending'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('payment_failed', 'Payment Failed'),
        ('payment_expired', 'Payment Expired'),
        ('payment_reminder', 'Payment Reminder'),
        ('installment_confirmed', 'First Installment Confirmed'),
        ('installment_reminder', 'Second Installment Reminder'),
        ('installment_expiring', 'Installment Access Expiring'),
        ('installment_expired', 'Installment Access Expired'),
        ('sponsorship_approved', 'Sponsorship Approved'),
        ('sponsorship_rejected', 'Sponsorship Rejected'),
    ]
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=25, choices=NOTIFICATION_TYPES)
    sent_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-sent_at']
        unique_together = ['payment', 'notification_type']
    
    def __str__(self):
        return f"{self.notification_type} for {self.payment.reference_number}"


# SponsorshipRequest model removed to avoid conflicts with users.models.SponsorshipRequest
# Use the one in users app instead
