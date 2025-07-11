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
        ('partially_paid', 'Partially Paid (Installment)'),
        ('sponsorship', 'Sponsored Access'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
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

    # Installment payment tracking
    partial_payment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when partial payment (50%) was made"
    )
    payment_expiration_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when partial payment access expires (30 days from partial payment)"
    )
    installment_amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount paid in first installment (50% of course price)"
    )
    total_course_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total course price for installment tracking"
    )

    # Sponsorship tracking
    sponsorship_request = models.ForeignKey(
        'SponsorshipRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sponsored_profile',
        help_text="Linked sponsorship request if payment status is 'sponsorship'"
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

    # Gamification Fields
    total_points = models.IntegerField(
        default=0,
        help_text="Total points earned by the user"
    )
    current_streak = models.IntegerField(
        default=0,
        help_text="Current consecutive days of learning activity"
    )
    longest_streak = models.IntegerField(
        default=0,
        help_text="Longest consecutive days of learning activity achieved"
    )
    last_activity_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last learning activity for streak calculation"
    )

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
    def has_partial_payment(self):
        """Check if user has partial payment status"""
        return self.payment_status == 'partially_paid'

    @property
    def has_sponsorship_access(self):
        """Check if user has sponsorship access"""
        return self.payment_status == 'sponsorship'

    @property
    def has_any_payment_access(self):
        """Check if user has any form of payment access (confirmed, partial, or sponsorship)"""
        return self.payment_status in ['confirmed', 'partially_paid', 'sponsorship']

    @property
    def is_partial_payment_expired(self):
        """Check if partial payment has expired"""
        if self.payment_status == 'partially_paid' and self.payment_expiration_date:
            return timezone.now() > self.payment_expiration_date
        return False

    @property
    def days_until_expiration(self):
        """Get days remaining until partial payment expires"""
        if self.payment_status == 'partially_paid' and self.payment_expiration_date:
            remaining = self.payment_expiration_date - timezone.now()
            return max(0, remaining.days)
        return 0

    @property
    def remaining_installment_amount(self):
        """Get remaining amount for second installment"""
        if self.payment_status == 'partially_paid' and self.total_course_price and self.installment_amount_paid:
            return self.total_course_price - self.installment_amount_paid
        return 0

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

    def confirm_partial_payment(self, amount, course_price, method, reference=None, notes=None):
        """Confirm partial payment (50% installment) for the user"""
        from datetime import timedelta

        self.payment_status = 'partially_paid'
        self.partial_payment_date = timezone.now()
        self.payment_expiration_date = timezone.now() + timedelta(days=30)
        self.installment_amount_paid = amount
        self.total_course_price = course_price
        self.payment_amount = amount
        self.payment_method = method
        self.payment_confirmed_at = timezone.now()

        if reference:
            self.payment_reference = reference
        if notes:
            self.payment_notes = notes

        self.save(update_fields=[
            'payment_status', 'partial_payment_date', 'payment_expiration_date',
            'installment_amount_paid', 'total_course_price', 'payment_amount',
            'payment_method', 'payment_confirmed_at', 'payment_reference', 'payment_notes'
        ])

    def complete_installment_payment(self, remaining_amount, reference=None, notes=None):
        """Complete the second installment payment"""
        total_paid = self.installment_amount_paid + remaining_amount

        self.payment_status = 'confirmed'
        self.payment_amount = total_paid
        self.payment_confirmed_at = timezone.now()

        # Clear installment tracking fields
        self.partial_payment_date = None
        self.payment_expiration_date = None

        if reference:
            self.payment_reference = reference
        if notes:
            self.payment_notes = notes

        self.save(update_fields=[
            'payment_status', 'payment_amount', 'payment_confirmed_at',
            'partial_payment_date', 'payment_expiration_date',
            'payment_reference', 'payment_notes'
        ])

    def expire_partial_payment(self):
        """Expire partial payment and revoke access"""
        self.payment_status = 'unpaid'
        self.partial_payment_date = None
        self.payment_expiration_date = None
        self.installment_amount_paid = None
        self.total_course_price = None

        self.save(update_fields=[
            'payment_status', 'partial_payment_date', 'payment_expiration_date',
            'installment_amount_paid', 'total_course_price'
        ])

    def confirm_sponsorship_access(self, sponsorship_request):
        """Grant access through approved sponsorship"""
        self.payment_status = 'sponsorship'
        self.sponsorship_request = sponsorship_request
        self.payment_confirmed_at = timezone.now()
        self.payment_method = 'scholarship'

        self.save(update_fields=[
            'payment_status', 'sponsorship_request', 'payment_confirmed_at', 'payment_method'
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

    def update_learning_streak(self):
        """Update learning streak based on daily activity"""
        from django.utils import timezone
        today = timezone.now().date()

        if self.last_activity_date:
            if self.last_activity_date == today:
                return  # Already updated today
            elif self.last_activity_date == today - timezone.timedelta(days=1):
                # Consecutive day - increment streak
                self.current_streak += 1
            else:
                # Gap in activity - reset streak
                self.current_streak = 1
        else:
            # First activity
            self.current_streak = 1

        # Update longest streak if current is higher
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        self.last_activity_date = today
        self.save(update_fields=['current_streak', 'longest_streak', 'last_activity_date'])

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

    # Course Selection
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='sponsorship_requests',
        null=True,
        blank=True,
        help_text="Course for which sponsorship is requested"
    )

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

    # Approval workflow fields
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_sponsorships',
        help_text="Admin user who approved this request"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when sponsorship was approved"
    )

    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (if applicable)"
    )

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

    def approve_sponsorship(self, approved_by_user, notes=""):
        """Approve the sponsorship request and grant course access"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.reviewed_by = approved_by_user
        self.reviewed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()

        # Grant course access through sponsorship
        profile = self.user.profile
        profile.confirm_sponsorship_access(self)

        return True

    def reject_sponsorship(self, rejected_by_user, reason="", notes=""):
        """Reject the sponsorship request"""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.reviewed_by = rejected_by_user
        self.reviewed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()

        return True

    @property
    def is_approved(self):
        """Check if sponsorship is approved"""
        return self.status == 'approved'

    @property
    def is_pending(self):
        """Check if sponsorship is pending"""
        return self.status == 'pending'


# ============================================================================
# INSTRUCTOR ROLE SYSTEM MODELS
# ============================================================================

class Specialization(models.Model):
    """
    Instructor specialization areas
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS icon class")
    color = models.CharField(max_length=7, default='#ff5d15', help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Specialization"
        verbose_name_plural = "Specializations"
        ordering = ['name']


class InstructorProfile(models.Model):
    """
    Enhanced instructor profile with role differentiation and professional information
    """
    INSTRUCTOR_ROLES = [
        ('system_admin', 'System Administrator'),
        ('course_instructor', 'Course Instructor'),
        ('teaching_assistant', 'Teaching Assistant'),
        ('content_creator', 'Content Creator'),
        ('grader', 'Grader'),
    ]

    VERIFICATION_STATUS = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    instructor_role = models.CharField(
        max_length=30,
        choices=INSTRUCTOR_ROLES,
        default='course_instructor',
        help_text="Primary instructor role in the system"
    )

    # Professional Information
    bio = models.TextField(
        blank=True,
        help_text="Professional biography and teaching philosophy"
    )
    qualifications = models.TextField(
        blank=True,
        help_text="Educational background and certifications"
    )
    specializations = models.ManyToManyField(
        Specialization,
        blank=True,
        help_text="Areas of expertise and specialization"
    )
    years_experience = models.IntegerField(
        default=0,
        help_text="Years of teaching/training experience"
    )

    # Contact & Social
    linkedin_url = models.URLField(blank=True, help_text="LinkedIn profile URL")
    website_url = models.URLField(blank=True, help_text="Personal or professional website")
    office_hours = models.TextField(
        blank=True,
        help_text="Available office hours for student consultations"
    )

    # Verification & Status
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending',
        help_text="Instructor verification status"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether instructor is currently active"
    )
    can_create_courses = models.BooleanField(
        default=True,
        help_text="Permission to create new courses"
    )
    can_manage_assessments = models.BooleanField(
        default=True,
        help_text="Permission to create and manage quizzes/assessments"
    )
    can_view_analytics = models.BooleanField(
        default=True,
        help_text="Permission to view student analytics and progress"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_instructors'
    )

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_instructor_role_display()})"

    def save(self, *args, **kwargs):
        # Auto-verify system admins
        if self.instructor_role == 'system_admin' and self.verification_status == 'pending':
            self.verification_status = 'verified'
            self.verified_at = timezone.now()

        super().save(*args, **kwargs)

        # Update user staff status and permissions based on role
        if self.instructor_role in ['system_admin', 'course_instructor', 'content_creator', 'teaching_assistant']:
            self.user.is_staff = True

            # Grant necessary permissions for admin access
            from django.contrib.auth.models import Permission
            from django.contrib.contenttypes.models import ContentType

            # Get content types for models instructors need to access
            course_ct = ContentType.objects.get_for_model('courses.Course')
            module_ct = ContentType.objects.get_for_model('courses.Module')
            lesson_ct = ContentType.objects.get_for_model('courses.Lesson')
            quiz_ct = ContentType.objects.get_for_model('assessments.Quiz')
            question_ct = ContentType.objects.get_for_model('assessments.Question')
            message_ct = ContentType.objects.get_for_model('communication.Message')

            # Define permissions based on role
            if self.instructor_role == 'system_admin':
                # System admins get all permissions
                self.user.is_superuser = True
            else:
                # Other instructors get specific permissions
                permissions_to_add = []

                # Course permissions
                permissions_to_add.extend([
                    Permission.objects.get(content_type=course_ct, codename='view_course'),
                    Permission.objects.get(content_type=course_ct, codename='add_course'),
                    Permission.objects.get(content_type=course_ct, codename='change_course'),
                ])

                # Module and lesson permissions
                permissions_to_add.extend([
                    Permission.objects.get(content_type=module_ct, codename='view_module'),
                    Permission.objects.get(content_type=module_ct, codename='add_module'),
                    Permission.objects.get(content_type=module_ct, codename='change_module'),
                    Permission.objects.get(content_type=lesson_ct, codename='view_lesson'),
                    Permission.objects.get(content_type=lesson_ct, codename='add_lesson'),
                    Permission.objects.get(content_type=lesson_ct, codename='change_lesson'),
                ])

                # Assessment permissions
                if self.can_manage_assessments:
                    permissions_to_add.extend([
                        Permission.objects.get(content_type=quiz_ct, codename='view_quiz'),
                        Permission.objects.get(content_type=quiz_ct, codename='add_quiz'),
                        Permission.objects.get(content_type=quiz_ct, codename='change_quiz'),
                        Permission.objects.get(content_type=question_ct, codename='view_question'),
                        Permission.objects.get(content_type=question_ct, codename='add_question'),
                        Permission.objects.get(content_type=question_ct, codename='change_question'),
                    ])

                # Message permissions
                permissions_to_add.extend([
                    Permission.objects.get(content_type=message_ct, codename='view_message'),
                    Permission.objects.get(content_type=message_ct, codename='change_message'),
                ])

                # Add permissions to user
                self.user.user_permissions.add(*permissions_to_add)

            self.user.save()

    @property
    def is_verified(self):
        """Check if instructor is verified"""
        return self.verification_status == 'verified'

    @property
    def can_access_admin(self):
        """Check if instructor can access admin interface"""
        return self.is_verified and self.instructor_role in [
            'system_admin', 'course_instructor', 'content_creator'
        ]

    def get_assigned_courses(self):
        """Get courses assigned to this instructor"""
        from courses.models import Course
        if self.instructor_role == 'system_admin':
            return Course.objects.all()
        else:
            return Course.objects.filter(instructor=self.user)

    def get_permissions_summary(self):
        """Get summary of instructor permissions"""
        return {
            'create_courses': self.can_create_courses,
            'manage_assessments': self.can_manage_assessments,
            'view_analytics': self.can_view_analytics,
            'access_admin': self.can_access_admin,
            'role': self.get_instructor_role_display(),
            'verification_status': self.get_verification_status_display(),
        }

    class Meta:
        verbose_name = "Instructor Profile"
        verbose_name_plural = "Instructor Profiles"
        ordering = ['-created_at']


class CourseInstructor(models.Model):
    """
    Course-specific instructor assignments with granular permissions
    """
    ASSIGNMENT_ROLES = [
        ('primary_instructor', 'Primary Instructor'),
        ('co_instructor', 'Co-Instructor'),
        ('teaching_assistant', 'Teaching Assistant'),
        ('grader', 'Grader'),
        ('guest_lecturer', 'Guest Lecturer'),
    ]

    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='instructor_assignments'
    )
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='course_assignments'
    )
    assignment_role = models.CharField(
        max_length=30,
        choices=ASSIGNMENT_ROLES,
        default='teaching_assistant'
    )

    # Granular Permissions
    can_edit_content = models.BooleanField(default=True)
    can_manage_enrollments = models.BooleanField(default=True)
    can_grade_assessments = models.BooleanField(default=True)
    can_view_analytics = models.BooleanField(default=True)
    can_communicate_students = models.BooleanField(default=True)
    can_publish_course = models.BooleanField(default=False)

    # Assignment Details
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='instructor_assignments_made'
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, help_text="Assignment notes or special instructions")

    def __str__(self):
        return f"{self.instructor.get_full_name()} - {self.course.title} ({self.get_assignment_role_display()})"

    class Meta:
        verbose_name = "Course Instructor Assignment"
        verbose_name_plural = "Course Instructor Assignments"
        unique_together = ['course', 'instructor']
        ordering = ['-assigned_at']
