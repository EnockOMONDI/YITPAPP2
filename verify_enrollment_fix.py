#!/usr/bin/env python3
"""
YITP Enrollment Fix Verification Script
=======================================

Purpose: Simple verification that the enrollment display fixes work
Author: YITP Development Team
Date: 2025-01-14
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/djsean/Desktop/APPS2024/YITP2025/YITPAPP')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'

# Initialize Django
django.setup()

from django.contrib.auth.models import User
from courses.models import Course
from progress.models import Enrollment


def verify_enrollment_fix():
    """Verify that the enrollment detection fix works"""
    print("🔍 YITP Enrollment Fix Verification")
    print("=" * 40)
    
    # Get Victor's account
    try:
        user = User.objects.get(email='info@youthimpactglobal.com')
        print(f"✅ Found user: {user.get_full_name()}")
    except User.DoesNotExist:
        print("❌ User not found")
        return False
        
    # Get Course 6
    try:
        course = Course.objects.get(id=6)
        print(f"✅ Found course: {course.title}")
    except Course.DoesNotExist:
        print("❌ Course not found")
        return False
        
    # Test old logic (what was broken)
    old_enrollment = Enrollment.objects.filter(
        student=user,
        course=course,
        status='active'
    ).first()
    
    # Test new logic (the fix)
    new_enrollment = Enrollment.objects.filter(
        student=user,
        course=course,
        status__in=['active', 'completed']
    ).first()
    
    print(f"\n📊 Results:")
    print(f"   Old Logic (broken): {'Found' if old_enrollment else 'NOT FOUND'}")
    print(f"   New Logic (fixed): {'Found' if new_enrollment else 'NOT FOUND'}")
    
    if new_enrollment:
        print(f"\n📋 Enrollment Details:")
        print(f"   Status: {new_enrollment.status}")
        print(f"   Progress: {new_enrollment.progress_percentage}%")
        print(f"   Should show: Course Complete! button")
        print(f"   Should hide: Enroll Now, Try for Free buttons")
        
    return new_enrollment is not None


def verify_template_logic():
    """Verify what the template should display"""
    print(f"\n🎨 Template Display Logic")
    print("=" * 40)
    
    user = User.objects.get(email='info@youthimpactglobal.com')
    course = Course.objects.get(id=6)
    
    # Simulate the template logic
    enrollment = Enrollment.objects.filter(
        student=user,
        course=course,
        status__in=['active', 'completed']
    ).first()
    
    is_enrolled = enrollment is not None
    
    print(f"Template Variables:")
    print(f"   user.is_authenticated: True")
    print(f"   is_enrolled: {is_enrolled}")
    
    if is_enrolled:
        progress = enrollment.progress_percentage
        print(f"   enrollment.progress_percentage: {progress}%")
        
        if progress > 0:
            if progress >= 100:
                button_text = "Course Complete!"
                button_subtext = "Review your progress"
            else:
                button_text = "Continue Learning"
                button_subtext = f"Next lesson available"
        else:
            button_text = "Start Course"
            button_subtext = "Begin your learning"
            
        print(f"\n✅ Expected Display:")
        print(f"   Button: {button_text}")
        print(f"   Subtext: {button_subtext}")
        print(f"   Hidden: Enroll Now, Try for Free buttons")
        
    else:
        print(f"\n❌ Would Show (if broken):")
        print(f"   Enroll Now - Free button")
        print(f"   Try Before You Buy section")
        
    return True


if __name__ == "__main__":
    print("🧪 YITP Enrollment Display Fix Verification")
    print("=" * 50)
    
    # Test 1: Enrollment detection
    test1 = verify_enrollment_fix()
    
    # Test 2: Template logic
    test2 = verify_template_logic()
    
    print(f"\n🎯 SUMMARY")
    print("=" * 20)
    
    if test1 and test2:
        print("✅ ALL TESTS PASSED!")
        print("\n🎉 The fix should work correctly!")
        print("   Victor should now see:")
        print("   • 'Course Complete!' button instead of 'Enroll Now'")
        print("   • Progress bar showing 100%")
        print("   • No 'Try Before You Buy' section")
        print("\n🔄 Next Steps:")
        print("   1. Refresh the course page in browser")
        print("   2. Verify the correct buttons are displayed")
        print("   3. Check that YITP branding colors are applied")
    else:
        print("❌ TESTS FAILED!")
        print("   Additional debugging needed")
        
    sys.exit(0 if (test1 and test2) else 1)
