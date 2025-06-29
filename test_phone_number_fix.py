#!/usr/bin/env python3
"""
Test script to verify phone number storage fix in YITP registration system.
This script tests the specific phone number storage issue that was identified.
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Profile
from django.test import Client
from django.urls import reverse
from django.utils import timezone

def test_phone_number_storage():
    """Test that phone numbers are properly stored during registration"""
    print("🔧 Testing Phone Number Storage Fix")
    print("=" * 50)
    
    # Test 1: Direct Profile Creation
    print("\n📱 Test 1: Direct Profile Creation with Phone Number")
    print("-" * 40)
    try:
        # Create test user
        test_username = f"phonetest_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        user = User.objects.create_user(
            username=test_username,
            email="phonetest@example.com",
            first_name="Phone",
            last_name="Test",
            password="testpass123",
            is_active=False
        )
        
        # Create profile with phone number
        profile, created = Profile.objects.get_or_create(user=user)
        test_phone = "+1234567890"
        profile.phone_number = test_phone
        profile.save()
        
        # Verify phone number is stored
        profile.refresh_from_db()
        if profile.phone_number == test_phone:
            print(f"✅ Phone number correctly stored: {profile.phone_number}")
        else:
            print(f"❌ Phone number not stored correctly. Expected: {test_phone}, Got: {profile.phone_number}")
            return False
            
    except Exception as e:
        print(f"❌ Direct profile creation failed: {e}")
        return False
    
    # Test 2: Registration Form Simulation
    print("\n📝 Test 2: Registration Form Simulation")
    print("-" * 40)
    try:
        client = Client()
        
        # Simulate registration form submission
        test_username2 = f"formtest_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        test_phone2 = "+9876543210"
        
        registration_data = {
            'first_name': 'Form',
            'last_name': 'Test',
            'username': test_username2,
            'email': 'formtest@example.com',
            'phone_number': test_phone2,
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'terms': 'on'
        }
        
        # Submit registration form
        response = client.post('/register/', registration_data)
        
        # Check if user was created
        try:
            user2 = User.objects.get(username=test_username2)
            print(f"✅ User created via form: {user2.username}")
            
            # Check if profile exists and has phone number
            try:
                profile2 = Profile.objects.get(user=user2)
                if profile2.phone_number == test_phone2:
                    print(f"✅ Phone number stored via form: {profile2.phone_number}")
                else:
                    print(f"❌ Phone number not stored via form. Expected: {test_phone2}, Got: {profile2.phone_number}")
                    return False
            except Profile.DoesNotExist:
                print("❌ Profile not created for form user")
                return False
                
        except User.DoesNotExist:
            print("❌ User not created via form submission")
            return False
            
    except Exception as e:
        print(f"❌ Form submission test failed: {e}")
        return False
    
    # Test 3: Signal Interference Check
    print("\n🔄 Test 3: Signal Interference Check")
    print("-" * 40)
    try:
        # Create user and immediately check if signals interfere
        test_username3 = f"signaltest_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        user3 = User.objects.create_user(
            username=test_username3,
            email="signaltest@example.com",
            password="testpass123"
        )
        
        # Profile should be auto-created by signals
        try:
            profile3 = Profile.objects.get(user=user3)
            print("✅ Profile auto-created by signals")
            
            # Now set phone number
            test_phone3 = "+5555555555"
            profile3.phone_number = test_phone3
            profile3.save()
            
            # Trigger user save to see if signals interfere
            user3.first_name = "Signal"
            user3.last_name = "Test"
            user3.save()
            
            # Check if phone number is still there
            profile3.refresh_from_db()
            if profile3.phone_number == test_phone3:
                print(f"✅ Phone number survived signal interference: {profile3.phone_number}")
            else:
                print(f"❌ Phone number lost due to signal interference. Expected: {test_phone3}, Got: {profile3.phone_number}")
                return False
                
        except Profile.DoesNotExist:
            print("❌ Profile not auto-created by signals")
            return False
            
    except Exception as e:
        print(f"❌ Signal interference test failed: {e}")
        return False
    
    # Test 4: Phone Number Validation
    print("\n✅ Test 4: Phone Number Validation")
    print("-" * 40)
    try:
        client = Client()
        
        # Test with invalid phone number (too short)
        test_username4 = f"validtest_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        invalid_data = {
            'first_name': 'Valid',
            'last_name': 'Test',
            'username': test_username4,
            'email': 'validtest@example.com',
            'phone_number': '123',  # Too short
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'terms': 'on'
        }
        
        response = client.post('/register/', invalid_data)
        
        # User should not be created due to validation error
        if not User.objects.filter(username=test_username4).exists():
            print("✅ Invalid phone number correctly rejected")
        else:
            print("❌ Invalid phone number was accepted")
            return False
            
    except Exception as e:
        print(f"❌ Phone validation test failed: {e}")
        return False
    
    print("\n🎉 All Phone Number Storage Tests Passed!")
    print("=" * 50)
    return True

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    try:
        # Delete test users (profiles will be deleted via cascade)
        test_users = User.objects.filter(username__startswith='phonetest_')
        test_users.delete()
        
        test_users = User.objects.filter(username__startswith='formtest_')
        test_users.delete()
        
        test_users = User.objects.filter(username__startswith='signaltest_')
        test_users.delete()
        
        test_users = User.objects.filter(username__startswith='validtest_')
        test_users.delete()
        
        print("✅ Test data cleaned up successfully")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

if __name__ == "__main__":
    try:
        success = test_phone_number_storage()
        cleanup_test_data()
        
        if success:
            print("\n✅ PHONE NUMBER STORAGE FIX VERIFIED SUCCESSFULLY!")
            sys.exit(0)
        else:
            print("\n❌ PHONE NUMBER STORAGE ISSUES DETECTED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test script error: {e}")
        cleanup_test_data()
        sys.exit(1)
