from django import forms
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import SponsorshipRequest, Profile, InstructorProfile
import re
import secrets
import string


class SponsorshipRequestForm(forms.ModelForm):
    """Form for submitting sponsorship requests"""
    
    class Meta:
        model = SponsorshipRequest
        fields = [
            'program', 'program_other', 'amount_needed', 
            'financial_situation', 'financial_situation_other',
            'reason', 'supporting_document',
            'emergency_contact_name', 'emergency_contact_phone', 
            'emergency_contact_email', 'emergency_contact_relationship'
        ]
        
        widgets = {
            'program': forms.Select(attrs={
                'class': 'form-select sponsorship-select yitp-form-field',
                'id': 'id_program'
            }),
            'program_other': forms.TextInput(attrs={
                'class': 'form-control yitp-form-field',
                'placeholder': 'Please specify the program',
                'style': 'display: none;'
            }),
            'amount_needed': forms.NumberInput(attrs={
                'class': 'form-control yitp-form-field',
                'placeholder': '0.00',
                'min': '1',
                'step': '0.01'
            }),
            'financial_situation': forms.Select(attrs={
                'class': 'form-select sponsorship-select yitp-form-field',
                'id': 'id_financial_situation'
            }),
            'financial_situation_other': forms.TextInput(attrs={
                'class': 'form-control yitp-form-field',
                'placeholder': 'Please specify your situation',
                'style': 'display: none;'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control sponsorship-reason-field',
                'rows': 6,
                'placeholder': 'Please provide a detailed explanation of why you need sponsorship (minimum 100 characters)',
                'maxlength': '2000',
                'id': 'id_reason',
                'data-min-chars': '100',
                'data-max-chars': '2000'
            }),
            'supporting_document': forms.FileInput(attrs={
                'class': 'form-control yitp-form-field',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control yitp-form-field',
                'placeholder': 'Full name of emergency contact'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control yitp-form-field',
                'placeholder': '+1234567890'
            }),
            'emergency_contact_email': forms.EmailInput(attrs={
                'class': 'form-control yitp-form-field',
                'placeholder': 'emergency@example.com'
            }),
            'emergency_contact_relationship': forms.TextInput(attrs={
                'class': 'form-control yitp-form-field',
                'placeholder': 'e.g., Parent, Sibling, Friend'
            }),
        }
        
        labels = {
            'program': 'Program/Course Requesting Sponsorship For',
            'program_other': 'Specify Other Program',
            'amount_needed': 'Amount Needed (USD)',
            'financial_situation': 'Current Financial Situation',
            'financial_situation_other': 'Specify Other Situation',
            'reason': 'Detailed Explanation',
            'supporting_document': 'Supporting Documents (Optional)',
            'emergency_contact_name': 'Emergency Contact Name',
            'emergency_contact_phone': 'Emergency Contact Phone',
            'emergency_contact_email': 'Emergency Contact Email',
            'emergency_contact_relationship': 'Relationship to You',
        }
        
        help_texts = {
            'amount_needed': 'Enter the total amount you need in USD',
            'reason': 'Explain your current situation, why you need sponsorship, and how this program will help you (minimum 100 characters)',
            'supporting_document': 'Upload any supporting documents such as financial statements, medical records, etc. (PDF, DOC, DOCX, JPG, PNG)',
            'emergency_contact_phone': 'Include country code if international',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make all fields required except optional ones
        for field_name, field in self.fields.items():
            if field_name not in ['program_other', 'financial_situation_other', 'supporting_document']:
                field.required = True
            
            # Add Bootstrap classes and styling
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': field.widget.attrs.get('class', '') + ' form-control'})

    def clean_program_other(self):
        """Validate program_other field when 'other' is selected"""
        program = self.cleaned_data.get('program')
        program_other = self.cleaned_data.get('program_other')
        
        if program == 'other' and not program_other:
            raise ValidationError('Please specify the program when "Other" is selected.')
        
        return program_other

    def clean_financial_situation_other(self):
        """Validate financial_situation_other field when 'other' is selected"""
        financial_situation = self.cleaned_data.get('financial_situation')
        financial_situation_other = self.cleaned_data.get('financial_situation_other')
        
        if financial_situation == 'other' and not financial_situation_other:
            raise ValidationError('Please specify your financial situation when "Other" is selected.')
        
        return financial_situation_other

    def clean_amount_needed(self):
        """Validate amount_needed field"""
        amount = self.cleaned_data.get('amount_needed')
        
        if amount is not None:
            if amount <= 0:
                raise ValidationError('Amount must be greater than 0.')
            if amount > 100000:  # Set a reasonable maximum
                raise ValidationError('Amount cannot exceed $100,000.')
        
        return amount

    def clean_reason(self):
        """Validate reason field"""
        reason = self.cleaned_data.get('reason')
        
        if reason:
            if len(reason.strip()) < 100:
                raise ValidationError('Please provide at least 100 characters explaining your situation.')
            if len(reason.strip()) > 2000:
                raise ValidationError('Please keep your explanation under 2000 characters.')
        
        return reason.strip() if reason else reason

    def clean_emergency_contact_phone(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('emergency_contact_phone')

        if phone:
            # Remove all non-digit characters except +, spaces, hyphens, and parentheses
            # Place hyphen at the end of character class to avoid range interpretation
            cleaned_phone = re.sub(r'[^\d+\s()-]', '', phone)

            # Basic phone number validation - allow international and domestic formats
            # Supports: +1234567890, (123) 456-7890, 123-456-7890, 123 456 7890
            if not re.match(r'^[\+]?[\d\s\-\(\)]{7,20}$', cleaned_phone):
                raise ValidationError('Please enter a valid phone number.')

            # Additional validation: ensure there are enough digits
            digits_only = re.sub(r'[^\d]', '', cleaned_phone)
            if len(digits_only) < 7:
                raise ValidationError('Phone number must contain at least 7 digits.')
            if len(digits_only) > 15:
                raise ValidationError('Phone number cannot exceed 15 digits.')

        return phone

    def clean_supporting_document(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('supporting_document')
        
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size cannot exceed 10MB.')
            
            # Check file extension
            allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
            file_extension = file.name.split('.')[-1].lower()
            
            if file_extension not in allowed_extensions:
                raise ValidationError(
                    f'File type not allowed. Please upload: {", ".join(allowed_extensions).upper()}'
                )
        
        return file

    def clean(self):
        """Additional form-wide validation"""
        cleaned_data = super().clean()
        
        # Ensure emergency contact email is different from user's email
        emergency_email = cleaned_data.get('emergency_contact_email')
        if hasattr(self, 'user') and emergency_email:
            if emergency_email.lower() == self.user.email.lower():
                raise ValidationError({
                    'emergency_contact_email': 'Emergency contact email must be different from your own email.'
                })
        
        return cleaned_data

    def save(self, commit=True):
        """Save the form with additional processing"""
        instance = super().save(commit=False)
        
        # Set user if provided
        if hasattr(self, 'user'):
            instance.user = self.user
        
        if commit:
            instance.save()
        
        return instance


class UserProfileForm(forms.ModelForm):
    """Form for updating Django auth user fields"""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'Email address',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Amina'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Ndlovu'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'you@example.com'
            }),
        }


class ProfileDetailsForm(forms.ModelForm):
    """Form for updating extended YITP profile attributes"""

    class Meta:
        model = Profile
        fields = ['bio', 'phone_number', 'country', 'city', 'timezone_name', 'image']
        labels = {
            'bio': 'About you',
            'phone_number': 'Phone number',
            'country': 'Country',
            'city': 'City',
            'timezone_name': 'Timezone',
            'image': 'Profile photo',
        }
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about your goals inside YITP...'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254700000000'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country of residence'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City or region'
            }),
            'timezone_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Africa/Nairobi'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }

    def clean_phone_number(self):
        """Basic normalization + validation for phone numbers"""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            cleaned_phone = re.sub(r'[^\d+\s()-]', '', phone)
            digits_only = re.sub(r'\D', '', cleaned_phone)
            if digits_only and (len(digits_only) < 7 or len(digits_only) > 15):
                raise ValidationError('Phone number must be between 7 and 15 digits.')
            return cleaned_phone
        return phone


class AdminUserCreationForm(forms.Form):
    """Superuser-facing form to quickly create learners and staff accounts."""

    ROLE_CHOICES = [
        ('learner', 'Learner'),
        ('course_instructor', 'Course Instructor'),
        ('content_manager', 'Content Manager'),
        ('accountant', 'Accountant'),
        ('teaching_assistant', 'Teaching Assistant'),
        ('grader', 'Grader'),
        ('system_admin', 'System Administrator'),
    ]

    first_name = forms.CharField(label='First name', max_length=150)
    last_name = forms.CharField(label='Last name', max_length=150, required=False)
    email = forms.EmailField(label='Email')
    username = forms.CharField(label='Username', max_length=150)
    role = forms.ChoiceField(label='Assign role', choices=ROLE_CHOICES)
    password = forms.CharField(
        label='Temporary password',
        max_length=128,
        required=False,
        help_text='Leave blank to auto-generate a secure password.',
        widget=forms.PasswordInput(render_value=True)
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username

    def _generate_password(self):
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
        return ''.join(secrets.choice(alphabet) for _ in range(12))

    def save(self):
        cleaned = self.cleaned_data
        password = cleaned['password'] or self._generate_password()
        user = User.objects.create_user(
            username=cleaned['username'],
            email=cleaned['email'],
            password=password,
            first_name=cleaned['first_name'],
            last_name=cleaned['last_name'],
        )

        role = cleaned['role']
        if role == 'system_admin':
            user.is_staff = True
            user.is_superuser = True
        elif role != 'learner':
            user.is_staff = True
        user.save()

        if role != 'learner':
            profile, _ = InstructorProfile.objects.get_or_create(user=user)
            profile.instructor_role = role
            profile.is_active = True
            if role == 'system_admin':
                profile.verification_status = 'verified'
            profile.save()

        return user, password
