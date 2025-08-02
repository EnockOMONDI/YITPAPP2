#!/usr/bin/env python
"""
Test YITP Introductory Course Fixes
Verify the three fixes: Quiz URL, Default Thumbnail, and Completion Email
"""

import os
import sys
import django

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    django.setup()

def test_quiz_url_fix():
    """Test that the quiz URL is correctly generated"""
    print("🔍 TESTING QUIZ URL FIX")
    print("=" * 60)
    
    try:
        from django.template.loader import render_to_string
        from courses.models import Course, Lesson
        from assessments.models import Quiz
        
        # Find the Introduction to YITP course
        course = Course.objects.filter(title__icontains="Introduction to YITP").first()
        if not course:
            print("❌ Introduction to YITP course not found")
            return False
        
        lesson = Lesson.objects.filter(module__course=course).first()
        if not lesson:
            print("❌ No lesson found for the course")
            return False
        
        quiz = Quiz.objects.filter(lesson=lesson).first()
        if not quiz:
            print("❌ No quiz found for the lesson")
            return False
        
        print(f"✅ Found course: {course.title}")
        print(f"✅ Found lesson: {lesson.title}")
        print(f"✅ Found quiz: {quiz.title}")
        print(f"📋 Quiz ID: {quiz.id}")
        
        # Check the lesson detail template for correct URL generation
        with open('templates/lms/courses/lesson_detail.html', 'r') as f:
            template_content = f.read()
        
        # Check for the correct URL pattern
        if "{% url 'assessments:take_quiz' quiz.id %}" in template_content:
            print("✅ Template uses correct take_quiz URL")
        else:
            print("❌ Template missing correct take_quiz URL")
            return False
        
        # Check that old incorrect URL is not present
        if "{% url 'assessments:quiz_detail' quiz_id=quiz.id %}" in template_content:
            print("❌ Template still contains old incorrect URL")
            return False
        else:
            print("✅ Old incorrect URL removed from template")
        
        # Generate expected URLs
        from django.urls import reverse
        correct_url = reverse('assessments:take_quiz', args=[quiz.id])
        print(f"✅ Expected quiz URL: {correct_url}")
        
        # Verify URL doesn't have trailing space
        if correct_url.endswith(' '):
            print("❌ URL has trailing space")
            return False
        else:
            print("✅ URL has no trailing space")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing quiz URL fix: {str(e)}")
        return False

def test_default_thumbnail():
    """Test that the default thumbnail is properly set up"""
    print(f"\n🔍 TESTING DEFAULT THUMBNAIL")
    print("=" * 60)
    
    try:
        from courses.models import Course
        import os
        from django.conf import settings
        
        # Check if default thumbnail file exists
        default_image_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'courses', 'default-course-thumbnail.jpeg')
        
        if os.path.exists(default_image_path):
            file_size = os.path.getsize(default_image_path)
            print(f"✅ Default thumbnail file exists")
            print(f"📊 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        else:
            print("❌ Default thumbnail file not found")
            return False
        
        # Check Introduction to YITP course thumbnail status
        course = Course.objects.filter(title__icontains="Introduction to YITP").first()
        if course:
            print(f"✅ Found course: {course.title}")
            if course.thumbnail:
                print(f"⚠️ Course has custom thumbnail: {course.thumbnail}")
                print("📋 Note: Remove custom thumbnail via admin panel to use default")
            else:
                print("✅ Course has no custom thumbnail - will use default")
        
        # Check templates use default thumbnail
        templates_to_check = [
            'templates/lms/courses/course_list.html',
            'templates/lms/courses/course_detail.html',
            'templates/lms/courses/home.html',
            'templates/lms/courses/my_courses.html'
        ]
        
        all_updated = True
        for template_path in templates_to_check:
            with open(template_path, 'r') as f:
                content = f.read()
            
            if 'default-course-thumbnail.jpeg' in content:
                print(f"✅ {template_path.split('/')[-1]} - Uses default thumbnail")
            else:
                print(f"❌ {template_path.split('/')[-1]} - Missing default thumbnail")
                all_updated = False
        
        return all_updated
        
    except Exception as e:
        print(f"❌ Error testing default thumbnail: {str(e)}")
        return False

def test_completion_email():
    """Test that the completion email includes 48-hour review message"""
    print(f"\n🔍 TESTING COMPLETION EMAIL")
    print("=" * 60)
    
    try:
        from django.template.loader import render_to_string
        from courses.models import Course
        from progress.models import Enrollment
        from django.contrib.auth.models import User
        
        # Find the Introduction to YITP course
        course = Course.objects.filter(title__icontains="Introduction to YITP").first()
        if not course:
            print("❌ Introduction to YITP course not found")
            return False
        
        print(f"✅ Found course: {course.title}")
        
        # Create test context for email template
        test_user = User.objects.first()
        if not test_user:
            print("❌ No test user found")
            return False
        
        # Create mock enrollment data
        context = {
            'user': test_user,
            'course': course,
            'enrollment': {
                'completion_date': __import__('datetime').datetime.now(),
                'enrollment_date': __import__('datetime').datetime.now(),
                'progress_percentage': 100.0,
                'certificate_issued': False
            },
            'learning_streak': 1,
            'total_study_time': 30,
            'completed_lessons': 1,
            'total_lessons': 1,
            'course_url': f'/lms/courses/courses/{course.slug}/',
            'site_name': 'Youth Impact Training Programme',
            'support_email': 'youthimpactglobal3@gmail.com'
        }
        
        # Test HTML email template
        html_content = render_to_string('emails/course_completion.html', context)
        
        # Check for 48-hour review message in HTML
        review_indicators = [
            '48 hours',
            'Course Access Review Process',
            'Your completion is under review',
            'additional courses are unlocked'
        ]
        
        html_checks_passed = 0
        for indicator in review_indicators:
            if indicator in html_content:
                print(f"✅ HTML email contains: '{indicator}'")
                html_checks_passed += 1
            else:
                print(f"❌ HTML email missing: '{indicator}'")
        
        # Test plain text email template
        plain_content = render_to_string('emails/course_completion.txt', context)
        
        # Check for 48-hour review message in plain text
        plain_checks_passed = 0
        for indicator in review_indicators:
            if indicator in plain_content:
                print(f"✅ Plain text email contains: '{indicator}'")
                plain_checks_passed += 1
            else:
                print(f"❌ Plain text email missing: '{indicator}'")
        
        # Check YITP branding colors in HTML
        if '#ff5d15' in html_content and '#1a2e53' in html_content:
            print("✅ HTML email includes YITP brand colors")
        else:
            print("⚠️ HTML email missing YITP brand colors")
        
        # Test that the email function exists and is callable
        from users.email_utils import send_course_completion_email
        print("✅ Course completion email function is available")
        
        success = (html_checks_passed >= 3 and plain_checks_passed >= 3)
        return success
        
    except Exception as e:
        print(f"❌ Error testing completion email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test execution"""
    print("🧪 YITP INTRODUCTORY COURSE FIXES TEST")
    print("=" * 70)
    print("🎯 Testing Quiz URL, Default Thumbnail, and Completion Email fixes")
    print("📅 Test Date:", __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)
    
    # Setup Django
    setup_django()
    
    # Run tests
    quiz_url_ok = test_quiz_url_fix()
    thumbnail_ok = test_default_thumbnail()
    email_ok = test_completion_email()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    print(f"🔗 Quiz URL Fix: {'✅ PASS' if quiz_url_ok else '❌ FAIL'}")
    print(f"🖼️ Default Thumbnail: {'✅ PASS' if thumbnail_ok else '❌ FAIL'}")
    print(f"📧 Completion Email: {'✅ PASS' if email_ok else '❌ FAIL'}")
    
    overall_success = quiz_url_ok and thumbnail_ok and email_ok
    
    if overall_success:
        print(f"\n🎉 ALL FIXES IMPLEMENTED SUCCESSFULLY!")
        
        print(f"\n🎯 FIXES SUMMARY:")
        print(f"   🔗 Quiz URL: Fixed to use 'take_quiz' endpoint")
        print(f"   🖼️ Default Thumbnail: Templates updated, file ready")
        print(f"   📧 Completion Email: 48-hour review message added")
        
        print(f"\n📋 MANUAL ACTIONS REQUIRED:")
        print(f"   1. Remove custom thumbnail from production admin:")
        print(f"      • Go to: https://www.youthimpactglobal.com/admin/courses/course/")
        print(f"      • Find 'Introduction to YITP' course")
        print(f"      • Edit and remove thumbnail image")
        print(f"      • Save changes")
        
        print(f"\n🌐 TESTING URLS:")
        print(f"   • Course: https://www.youthimpactglobal.com/lms/courses/courses/introduction-to-yitp-your-learning-journey-begins/")
        print(f"   • Lesson: https://www.youthimpactglobal.com/lms/courses/courses/introduction-to-yitp-your-learning-journey-begins/modules/2/")
        
    else:
        print(f"\n⚠️ SOME FIXES FAILED")
        print(f"🔧 Please review the failed tests and fix any issues")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
