from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MinValueValidator
from django.utils import timezone
from datetime import timedelta
from PIL import Image
from django.conf import settings
from taggit.managers import TaggableManager
from html import unescape
from django.utils.html import strip_tags
from shortuuid.django_fields import ShortUUIDField
from pyuploadcare.dj.models import ImageField
from ckeditor.fields import RichTextField


# Create your models here.
class Profile(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('pending', 'Pending Verification'),
        ('confirmed', 'Payment Confirmed'),
        ('expired', 'Payment Expired'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash Payment'),
        ('installment', 'Installment Plan'),
        ('scholarship', 'Scholarship'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    bio = models.TextField(default='Edit your Bio!')
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Contact phone number")

    # Payment Status Fields
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid',
        help_text="Current payment status for YITP courses"
    )
    payment_confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when payment was confirmed"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        null=True,
        help_text="Method used for payment"
    )
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount paid (in KES)"
    )
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Payment reference number or transaction ID"
    )
    payment_notes = models.TextField(
        blank=True,
        help_text="Additional notes about payment (admin use)"
    )

    # Profile completion tracking
    profile_completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Percentage of profile completion based on filled fields"
    )
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email has been verified via OTP"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_username()

    def save(self, *args, **kwargs):
        """Override save to automatically update profile completion percentage"""
        # Calculate completion percentage before saving
        self.profile_completion_percentage = self.calculate_profile_completion()
        super().save(*args, **kwargs)

    @property
    def has_confirmed_payment(self):
        """Check if user has confirmed payment status"""
        return self.payment_status == 'confirmed'

    @property
    def payment_status_display(self):
        """Get human-readable payment status with emoji"""
        status_icons = {
            'unpaid': '❌ Unpaid',
            'pending': '⏳ Pending Verification',
            'confirmed': '✅ Payment Confirmed',
            'expired': '⚠️ Payment Expired',
        }
        return status_icons.get(self.payment_status, self.get_payment_status_display())

    def confirm_payment(self, amount, method, reference=None, notes=None):
        """Confirm payment for the user"""
        self.payment_status = 'confirmed'
        self.payment_confirmed_at = timezone.now()
        self.payment_amount = amount
        self.payment_method = method
        if reference:
            self.payment_reference = reference
        if notes:
            self.payment_notes = notes
        self.save(update_fields=[
            'payment_status', 'payment_confirmed_at', 'payment_amount',
            'payment_method', 'payment_reference', 'payment_notes'
        ])

    def has_admin_privileges(self):
        """Check if user has admin privileges for monitoring"""
        return self.user.is_staff or self.user.is_superuser

    def can_access_analytics(self):
        """Check if user can access detailed analytics"""
        return self.has_admin_privileges() or self.user.groups.filter(name='Analytics_Viewers').exists()

    def can_monitor_progress(self):
        """Check if user can monitor other users' progress"""
        return self.has_admin_privileges() or self.user.groups.filter(name='Progress_Monitors').exists()

    def calculate_profile_completion(self):
        """Calculate profile completion percentage based on filled fields"""
        total_fields = 0
        completed_fields = 0

        # Core profile fields to check
        profile_fields = [
            ('bio', self.bio != 'Edit your Bio!' and self.bio.strip()),
            ('phone_number', bool(self.phone_number and self.phone_number.strip())),
            ('image', self.image.name != 'default.jpg'),
        ]

        # User fields to check
        user_fields = [
            ('first_name', bool(self.user.first_name and self.user.first_name.strip())),
            ('last_name', bool(self.user.last_name and self.user.last_name.strip())),
            ('email', bool(self.user.email and self.user.email.strip())),
        ]

        # Count all fields
        all_fields = profile_fields + user_fields
        total_fields = len(all_fields)

        # Count completed fields
        for field_name, is_completed in all_fields:
            if is_completed:
                completed_fields += 1

        # Calculate percentage
        if total_fields == 0:
            percentage = 0.00
        else:
            percentage = (completed_fields / total_fields) * 100

        return round(percentage, 2)

    def update_profile_completion(self):
        """Update the profile completion percentage"""
        self.profile_completion_percentage = self.calculate_profile_completion()
        self.save(update_fields=['profile_completion_percentage', 'updated_at'])
        return self.profile_completion_percentage

    def get_completion_status(self):
        """Get profile completion status with recommendations"""
        percentage = float(self.profile_completion_percentage)

        if percentage >= 90:
            return {
                'status': 'excellent',
                'message': '🎉 Your profile is excellent!',
                'color': 'success',
                'recommendations': []
            }
        elif percentage >= 70:
            return {
                'status': 'good',
                'message': '👍 Your profile looks good!',
                'color': 'info',
                'recommendations': self._get_missing_fields()
            }
        elif percentage >= 50:
            return {
                'status': 'fair',
                'message': '📝 Your profile needs some work',
                'color': 'warning',
                'recommendations': self._get_missing_fields()
            }
        else:
            return {
                'status': 'poor',
                'message': '⚠️ Please complete your profile',
                'color': 'danger',
                'recommendations': self._get_missing_fields()
            }

    def _get_missing_fields(self):
        """Get list of missing profile fields with user-friendly names"""
        missing = []

        if self.bio == 'Edit your Bio!' or not self.bio.strip():
            missing.append('Add a personal bio')
        if not self.phone_number or not self.phone_number.strip():
            missing.append('Add your phone number')
        if self.image.name == 'default.jpg':
            missing.append('Upload a profile picture')
        if not self.user.first_name or not self.user.first_name.strip():
            missing.append('Add your first name')
        if not self.user.last_name or not self.user.last_name.strip():
            missing.append('Add your last name')

        return missing

class OTPVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "OTP Verification"
        verbose_name_plural = "OTP Verifications"

    def __str__(self):
        return f"OTP for {self.user.username} - {self.otp_code}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired() and not self.is_verified
    
class Editpage(models.Model):
    SECTION_CHOICES = [
        ('hnew', 'Home | heading 1'),
        ('hneww', 'Home | Heading 2'),
        ('hnewww', 'Home | Heading 3'),
        ('Programme1', 'Home | Programme1'),
        ('Programme2', 'Home | Programme2'),
        ('Programme3', 'Home | Programme3'),

        ('about_us', 'Home | About Us'),
        ('mission', 'Home | Our Mission'),
        ('vision', 'Home | Our Vision'),
        ('Volunteer', 'Home | Volunteer'),
        ('footer', 'Home | Footer'),
        ('aboutUs', 'About Us | About Us'),
        ('our_Programs', 'Programs | Goddess Care Initiative'),
        ('reach', 'Programs | Our Reach '),
        ('team1', 'Our Team | Kelly'),
        ('team2', 'Our Team | Elsie'),
        ('team3', 'Our Team | Loise'),

    ]

    section_name = models.CharField(max_length=100, choices=SECTION_CHOICES, unique=True, blank=True)
    heading = RichTextField(blank=True) 
    content = RichTextField(blank=True)  
    slider_image = ImageField(blank=True, manual_crop="") 
    

    def __str__(self):
        return self.get_section_name_display()
    

class MainProgrames(models.Model):
    SECTION_CHOICES = [
        ('Programme1', 'Programe | Programme1'),
        ('Programme2', 'Programe | Programme2'),
        ('Programme3', 'Programe | Programme3'),
        ('Programme4', 'Programe | Programme4'),

    ]

    programe_name = models.CharField(max_length=100, choices=SECTION_CHOICES, unique=True)
    programe_description = RichTextField()
    programe_objective1 = RichTextField() 
    programe_objective2 = RichTextField()
    programe_objective3 = RichTextField()
    programe_objective4 = RichTextField()
    

    def __str__(self):
        return self.get_section_name_display()
    
    from ckeditor.fields import RichTextField  # Make sure this import is at the top

class SecondSection(models.Model):
    subtitle = RichTextField()  # Changed to RichTextField
    title = RichTextField()     # Changed to RichTextField
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return strip_tags(self.subtitle)  # Using strip_tags for clean string representation

    class Meta:
        verbose_name = "Second Section"
        verbose_name_plural = "Second Sections"

class SecondSectionIcon(models.Model):
    ICON_CHOICES = [
        ('icon-vegetable', 'Food Icon'),
        ('icon-water-1', 'Water Icon'),
        ('icon-stethoscope', 'Medical Icon'),
        # Add more icon choices as needed
    ]

    icon_class = models.CharField(max_length=50, choices=ICON_CHOICES)
    text = RichTextField()      # Changed to RichTextField
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{strip_tags(self.text)} - {self.icon_class}"

    class Meta:
        ordering = ['order']
        verbose_name = "Second Section Icon"
        verbose_name_plural = "Second Section Icons"

class SecondSectionBox(models.Model):
    text = RichTextField()      # Changed to RichTextField
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return strip_tags(self.text)

    class Meta:
        verbose_name = "Second Section Box"
        verbose_name_plural = "Second Section Boxes"


class SponsorshipRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ]

    PROGRAM_CHOICES = [
        ('youth_impact_training empowerment', 'youth impact training'),
    ]

    FINANCIAL_SITUATION_CHOICES = [
        ('unemployed', 'Unemployed'),
        ('student', 'Student'),
        ('low_income', 'Low Income'),
        ('single_parent', 'Single Parent'),
        ('disabled', 'Person with Disability'),
        ('refugee', 'Refugee/Asylum Seeker'),
        ('other', 'Other (Please specify)'),
    ]

    # Basic Information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sponsorship_requests')

    # Program and Financial Details
    program = models.CharField(max_length=50, choices=PROGRAM_CHOICES)
    program_other = models.CharField(max_length=200, blank=True, help_text="Specify if 'Other' is selected")
    amount_needed = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(1.00)],
        help_text="Amount in USD"
    )

    # Financial Situation
    financial_situation = models.CharField(max_length=50, choices=FINANCIAL_SITUATION_CHOICES)
    financial_situation_other = models.CharField(max_length=200, blank=True, help_text="Specify if 'Other' is selected")

    # Detailed Request
    reason = models.TextField(
        validators=[MinLengthValidator(100)],
        help_text="Please provide a detailed explanation (minimum 100 characters)"
    )

    # Supporting Documentation
    supporting_document = models.FileField(
        upload_to='sponsorship_documents/',
        blank=True,
        null=True,
        help_text="Optional: Upload supporting documents (PDF, DOC, DOCX, JPG, PNG)"
    )

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)
    emergency_contact_email = models.EmailField()
    emergency_contact_relationship = models.CharField(max_length=50, help_text="Relationship to you")

    # Status and Timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, help_text="Internal notes for administrators")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_sponsorship_requests'
    )

    class Meta:
        verbose_name = "Sponsorship Request"
        verbose_name_plural = "Sponsorship Requests"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_program_display()} - ${self.amount_needed}"

    def get_program_name(self):
        """Return the program name, including custom program if 'other' is selected"""
        if self.program == 'other' and self.program_other:
            return self.program_other
        return self.get_program_display()

    def get_financial_situation_name(self):
        """Return the financial situation, including custom situation if 'other' is selected"""
        if self.financial_situation == 'other' and self.financial_situation_other:
            return self.financial_situation_other
        return self.get_financial_situation_display()

    def mark_as_reviewed(self, reviewer, status, notes=""):
        """Mark the request as reviewed"""
        self.status = status
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()
