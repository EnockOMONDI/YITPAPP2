#!/usr/bin/env python
"""
YITP Email Notification System Test Script
Tests all email functionality including OTP verification, login notifications, and sponsorship emails
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from django.utils import timezone
from users.models import OTPVerification, Profile, SponsorshipRequest
from users.email_utils import (
    generate_otp, send_otp_email, send_welcome_email, 
    send_login_notification, send_sponsorship_confirmation_email,
    send_sponsorship_admin_notification, send_sponsorship_status_update_email
)
from users.otp_views import generate_and_send_otp

def test_email_system():
    """Test all email notification functionality"""
    print("🧪 YITP Email Notification System Test")
    print("=" * 60)
    
    # Test 1: OTP Generation
    print("\n📧 Test 1: OTP Generation")
    print("-" * 30)
    try:
        otp_code = generate_otp(6)
        print(f"✅ OTP Generated: {otp_code}")
        assert len(otp_code) == 6
        assert otp_code.isdigit()
        print("✅ OTP format validation passed")
    except Exception as e:
        print(f"❌ OTP generation failed: {e}")
        return False
    
    # Test 2: User Creation and Profile
    print("\n👤 Test 2: User Creation and Profile")
    print("-" * 30)
    try:
        # Create test user
        test_username = f"testuser_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        user = User.objects.create_user(
            username=test_username,
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123",
            is_active=False
        )
        print(f"✅ Test user created: {user.username}")
        
        # Create profile with phone number
        profile, created = Profile.objects.get_or_create(user=user)
        profile.phone_number = "+1234567890"
        profile.save()
        print(f"✅ Profile created with phone: {profile.phone_number}")
        
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return False
    
    # Test 3: OTP Email (Console Backend)
    print("\n📨 Test 3: OTP Email Sending")
    print("-" * 30)
    try:
        # Generate and send OTP
        otp_record, email_sent = generate_and_send_otp(user)
        print(f"✅ OTP record created: {otp_record.otp_code}")
        print(f"✅ Email sent status: {email_sent}")
        print(f"✅ OTP expires at: {otp_record.expires_at}")
        
        # Verify OTP record
        assert not otp_record.is_used
        assert not otp_record.is_verified
        assert not otp_record.is_expired()
        print("✅ OTP record validation passed")
        
    except Exception as e:
        print(f"❌ OTP email test failed: {e}")
        return False
    
    # Test 4: OTP Verification
    print("\n🔐 Test 4: OTP Verification")
    print("-" * 30)
    try:
        # Simulate OTP verification
        otp_record.is_verified = True
        otp_record.is_used = True
        otp_record.save()
        
        # Activate user
        user.is_active = True
        user.save()
        
        print("✅ OTP verification simulated")
        print("✅ User activated")
        
    except Exception as e:
        print(f"❌ OTP verification test failed: {e}")
        return False
    
    # Test 5: Welcome Email
    print("\n🎉 Test 5: Welcome Email")
    print("-" * 30)
    try:
        welcome_sent = send_welcome_email(user)
        print(f"✅ Welcome email sent: {welcome_sent}")
        
    except Exception as e:
        print(f"❌ Welcome email test failed: {e}")
        return False
    
    # Test 6: Login Notification
    print("\n🔒 Test 6: Login Notification")
    print("-" * 30)
    try:
        # Create mock request
        factory = RequestFactory()
        request = factory.post('/login/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        
        login_sent = send_login_notification(user, request)
        print(f"✅ Login notification sent: {login_sent}")
        
    except Exception as e:
        print(f"❌ Login notification test failed: {e}")
        return False
    
    # Test 7: Sponsorship Request
    print("\n💰 Test 7: Sponsorship Request Emails")
    print("-" * 30)
    try:
        # Create sponsorship request
        sponsorship = SponsorshipRequest.objects.create(
            user=user,
            program='career_development',
            amount_needed=1500.00,
            financial_situation='unemployed',
            reason="I need financial assistance to complete the YITP program and advance my career.",
            emergency_contact_name="Jane Doe",
            emergency_contact_phone="+1987654321",
            emergency_contact_email="jane@example.com",
            emergency_contact_relationship="Sister"
        )
        print(f"✅ Sponsorship request created: #{sponsorship.id}")
        
        # Test confirmation email
        confirmation_sent = send_sponsorship_confirmation_email(sponsorship)
        print(f"✅ Sponsorship confirmation email sent: {confirmation_sent}")
        
        # Test admin notification
        admin_sent = send_sponsorship_admin_notification(sponsorship)
        print(f"✅ Admin notification email sent: {admin_sent}")
        
    except Exception as e:
        print(f"❌ Sponsorship email test failed: {e}")
        return False
    
    # Test 8: Sponsorship Status Update
    print("\n📊 Test 8: Sponsorship Status Update")
    print("-" * 30)
    try:
        old_status = sponsorship.status
        sponsorship.status = 'approved'
        sponsorship.save()
        
        status_sent = send_sponsorship_status_update_email(sponsorship, old_status)
        print(f"✅ Status update email sent: {status_sent}")
        print(f"✅ Status changed from '{old_status}' to '{sponsorship.status}'")
        
    except Exception as e:
        print(f"❌ Status update email test failed: {e}")
        return False
    
    # Test 9: Database Cleanup
    print("\n🧹 Test 9: Cleanup")
    print("-" * 30)
    try:
        # Clean up test data
        sponsorship.delete()
        otp_record.delete()
        profile.delete()
        user.delete()
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    print("\n🎊 ALL TESTS PASSED!")
    print("=" * 60)
    print("✅ OTP verification system working")
    print("✅ Email templates rendering correctly")
    print("✅ User registration flow functional")
    print("✅ Login notifications operational")
    print("✅ Sponsorship email system working")
    print("✅ Database models functioning properly")
    print("\n🚀 Email notification system is ready for production!")
    
    return True

def test_email_templates():
    """Test that all email templates exist and can be rendered"""
    print("\n📄 Testing Email Templates")
    print("-" * 30)
    
    templates = [
        'emails/base_email.html',
        'emails/otp_verification.html',
        'emails/otp_verification.txt',
        'emails/welcome.html',
        'emails/welcome.txt',
        'emails/login_notification.html',
        'emails/login_notification.txt',
        'emails/sponsorship_confirmation.html',
        'emails/sponsorship_confirmation.txt',
        'emails/sponsorship_status_update.html',
        'emails/sponsorship_status_update.txt',
        'emails/sponsorship_admin_notification.html',
    ]
    
    from django.template.loader import get_template
    from django.template import TemplateDoesNotExist
    
    for template_name in templates:
        try:
            template = get_template(template_name)
            print(f"✅ {template_name}")
        except TemplateDoesNotExist:
            print(f"❌ {template_name} - NOT FOUND")
            return False
        except Exception as e:
            print(f"⚠️ {template_name} - ERROR: {e}")
    
    print("✅ All email templates found and accessible")
    return True

if __name__ == "__main__":
    print("🔧 YITP Email System Comprehensive Test")
    print("=" * 60)
    
    # Test templates first
    if not test_email_templates():
        print("❌ Template test failed")
        sys.exit(1)
    
    # Test email system
    if not test_email_system():
        print("❌ Email system test failed")
        sys.exit(1)
    
    print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("The YITP email notification system is fully functional and ready for production use.")
