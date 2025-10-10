#!/usr/bin/env python
"""
YITP Instructor Creation Fix Script
Fixes email configuration and tests instructor account creation
"""

import os
import sys
import django

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    django.setup()

def test_email_configuration():
    """Test email configuration"""
    from users.email_utils import test_email_configuration
    
    print("🔍 Testing email configuration...")
    result = test_email_configuration()
    
    if result['success']:
        print("✅ Email configuration test PASSED")
        print("Configuration details:")
        for key, value in result['config'].items():
            print(f"  {key}: {value}")
        return True
    else:
        print("❌ Email configuration test FAILED")
        print(f"Error: {result['message']}")
        return False

def test_instructor_creation():
    """Test instructor account creation"""
    from users.email_utils import create_instructor_account
    
    print("\n🧪 Testing instructor account creation...")
    
    # Test data
    test_email = "test.instructor@example.com"
    test_first_name = "Test"
    test_last_name = "Instructor"
    
    try:
        # Check if test user already exists
        from django.contrib.auth.models import User
        if User.objects.filter(email=test_email).exists():
            print(f"⚠️  Test user {test_email} already exists, deleting...")
            User.objects.filter(email=test_email).delete()
        
        # Create instructor account
        result = create_instructor_account(
            email=test_email,
            first_name=test_first_name,
            last_name=test_last_name,
            created_by_admin=True
        )
        
        if result['success']:
            print("✅ Instructor account creation test PASSED")
            print(f"  User: {result['user'].username}")
            print(f"  Email sent: {result['email_sent']}")
            print(f"  Temporary password: {result['temporary_password']}")
            
            # Clean up test user
            if result['user']:
                result['user'].delete()
                print("🧹 Test user cleaned up")
            
            return True
        else:
            print("❌ Instructor account creation test FAILED")
            print(f"Error: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during instructor creation test: {str(e)}")
        return False

def fix_existing_instructor(email):
    """Fix an existing instructor account"""
    from django.contrib.auth.models import User
    from users.email_utils import send_instructor_welcome_email
    
    try:
        user = User.objects.get(email=email)
        print(f"👤 Found user: {user.username} ({user.email})")
        
        # Check if user has instructor profile
        if hasattr(user, 'instructor_profile'):
            print("✅ User has instructor profile")
            
            # Try to resend welcome email
            print("📧 Attempting to resend welcome email...")
            success = send_instructor_welcome_email(
                user=user,
                temporary_password="Please contact admin for password reset"
            )
            
            if success:
                print("✅ Welcome email sent successfully")
            else:
                print("❌ Failed to send welcome email")
                
        else:
            print("⚠️  User does not have instructor profile")
            
    except User.DoesNotExist:
        print(f"❌ User with email {email} not found")
    except Exception as e:
        print(f"❌ Error fixing instructor: {str(e)}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("🔧 YITP INSTRUCTOR CREATION FIX SCRIPT")
    print("=" * 60)
    
    # Setup Django
    setup_django()
    
    # Test email configuration
    email_ok = test_email_configuration()
    
    # Test instructor creation
    instructor_ok = test_instructor_creation()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FIX SCRIPT SUMMARY")
    print("=" * 60)
    
    if email_ok and instructor_ok:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Email configuration is working")
        print("✅ Instructor creation is working")
        print("\n🚀 The instructor creation system should now work correctly in production.")
    else:
        print("⚠️  ISSUES DETECTED:")
        if not email_ok:
            print("❌ Email configuration needs attention")
        if not instructor_ok:
            print("❌ Instructor creation needs attention")
        
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("1. Deploy the updated code with fixed email settings")
        print("2. Verify EMAIL_HOST is set to smtp.gmail.com in production")
        print("3. Check that Gmail app password is correctly configured")
        print("4. Test with: python manage.py test_email_config --send-test-email test@example.com")
    
    # Offer to fix specific instructor
    if len(sys.argv) > 1:
        instructor_email = sys.argv[1]
        print(f"\n🔧 Attempting to fix instructor: {instructor_email}")
        fix_existing_instructor(instructor_email)
    
    print("=" * 60)

if __name__ == "__main__":
    main()
