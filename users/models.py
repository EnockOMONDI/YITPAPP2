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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    bio = models.TextField(default='Edit your Bio!')
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Contact phone number")

    def __str__(self):
        return self.user.get_username()

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
