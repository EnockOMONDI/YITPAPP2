#!/usr/bin/env python
"""
YITP Production Deployment Script for Introductory Course
Deploys the comprehensive introductory course to production using multiple methods
"""

import os
import sys
import django
from django.core.management import call_command

def setup_django():
    """Setup Django environment for production"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    django.setup()

def method_1_migration_deployment():
    """Method 1: Deploy using Django migrations"""
    print("🔄 METHOD 1: DJANGO MIGRATION DEPLOYMENT")
    print("-" * 50)
    
    try:
        print("📦 Running database migrations...")
        call_command('migrate', verbosity=2)
        print("✅ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"❌ Migration deployment failed: {str(e)}")
        return False

def method_2_management_command():
    """Method 2: Deploy using management command"""
    print("\n🔄 METHOD 2: MANAGEMENT COMMAND DEPLOYMENT")
    print("-" * 50)
    
    try:
        print("🎓 Running create_intro_course command...")
        call_command('create_intro_course', verbosity=2)
        print("✅ Management command completed successfully")
        return True
    except Exception as e:
        print(f"❌ Management command deployment failed: {str(e)}")
        return False

def method_3_fixture_import():
    """Method 3: Deploy using fixture import"""
    print("\n🔄 METHOD 3: FIXTURE IMPORT DEPLOYMENT")
    print("-" * 50)
    
    try:
        # Check if fixture file exists
        fixture_file = 'intro_course_complete.json'
        if not os.path.exists(fixture_file):
            print(f"❌ Fixture file {fixture_file} not found")
            print("   Please upload the fixture file to the production server")
            return False
        
        print(f"📦 Loading fixture: {fixture_file}")
        call_command('loaddata', fixture_file, verbosity=2)
        print("✅ Fixture import completed successfully")
        return True
    except Exception as e:
        print(f"❌ Fixture import failed: {str(e)}")
        return False

def verify_deployment():
    """Verify the course deployment"""
    print("\n🔍 VERIFYING DEPLOYMENT")
    print("=" * 60)
    
    try:
        from django.contrib.auth.models import User
        from users.models import InstructorProfile
        from courses.models import Course, Module, Lesson
        from assessments.models import Quiz, Question
        
        verification_results = []
        
        # Check instructor
        print("👤 Checking instructor account...")
        try:
            instructor = User.objects.get(username='yitpteam')
            print(f"   ✅ Instructor: {instructor.username} ({instructor.email})")
            print(f"   🔑 Staff: {instructor.is_staff}, Active: {instructor.is_active}")
            
            if hasattr(instructor, 'instructor_profile'):
                profile = instructor.instructor_profile
                print(f"   👨‍🏫 Role: {profile.instructor_role}")
                print(f"   ✅ Verified: {profile.verification_status}")
                verification_results.append(("Instructor", True))
            else:
                print("   ❌ No instructor profile")
                verification_results.append(("Instructor", False))
        except User.DoesNotExist:
            print("   ❌ Instructor not found")
            verification_results.append(("Instructor", False))
        
        # Check course
        print("\n📚 Checking course...")
        try:
            course = Course.objects.get(title__icontains="Introduction to YITP")
            print(f"   ✅ Course: {course.title}")
            print(f"   💰 Price: ${course.price} (Free: {course.price == 0})")
            print(f"   📊 Status: {course.status}")
            print(f"   ⭐ Featured: {course.is_featured}")
            verification_results.append(("Course", True))
        except Course.DoesNotExist:
            print("   ❌ Course not found")
            verification_results.append(("Course", False))
            return False
        
        # Check module and lesson
        print("\n📖 Checking module and lesson...")
        try:
            module = course.modules.first()
            lesson = module.lessons.first() if module else None
            
            if module and lesson:
                print(f"   ✅ Module: {module.title}")
                print(f"   ✅ Lesson: {lesson.title}")
                print(f"   ⏱️ Duration: {lesson.estimated_duration} minutes")
                verification_results.append(("Module/Lesson", True))
            else:
                print("   ❌ Module or lesson missing")
                verification_results.append(("Module/Lesson", False))
        except Exception as e:
            print(f"   ❌ Module/lesson check failed: {e}")
            verification_results.append(("Module/Lesson", False))
        
        # Check quiz and questions
        print("\n🧠 Checking quiz and questions...")
        try:
            quiz = lesson.quizzes.first() if lesson else None
            questions = quiz.questions.all() if quiz else []
            
            if quiz and questions.count() >= 8:
                print(f"   ✅ Quiz: {quiz.title}")
                print(f"   🎯 Passing Score: {quiz.passing_score}%")
                print(f"   ❓ Questions: {questions.count()}")
                print(f"   ⏱️ Time Limit: {quiz.time_limit} minutes")
                verification_results.append(("Quiz/Questions", True))
            else:
                print(f"   ❌ Quiz missing or insufficient questions: {questions.count() if quiz else 0}")
                verification_results.append(("Quiz/Questions", False))
        except Exception as e:
            print(f"   ❌ Quiz/questions check failed: {e}")
            verification_results.append(("Quiz/Questions", False))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 60)
        
        success_count = sum(1 for _, success in verification_results if success)
        total_count = len(verification_results)
        
        for component, success in verification_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status}: {component}")
        
        success_rate = (success_count / total_count) * 100
        print(f"\n🎯 Success Rate: {success_count}/{total_count} ({success_rate:.0f}%)")
        
        return success_rate >= 100
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def print_access_info():
    """Print production access information"""
    print("\n🌐 PRODUCTION ACCESS INFORMATION")
    print("=" * 60)
    
    print("🎓 Course Details:")
    print("   • Title: Introduction to YITP: Your Learning Journey Begins")
    print("   • Type: Mandatory first course for all new students")
    print("   • Duration: 25 minutes")
    print("   • Price: Free ($0.00)")
    print("   • Quiz: 8 questions, 70% passing score")
    
    print("\n👨‍🏫 Instructor Login:")
    print("   • Username: yitpteam")
    print("   • Password: sLXSxmMg3tVeV64")
    print("   • Email: enockomondike@gmail.com")
    
    print("\n🌐 Production URLs:")
    print("   • Admin: https://www.youthimpactglobal.com/admin/")
    print("   • Course Catalog: https://www.youthimpactglobal.com/courses/")
    print("   • Student Dashboard: https://www.youthimpactglobal.com/dashboard/")
    
    print("\n✅ Verification Steps:")
    print("   1. Login to admin interface")
    print("   2. Navigate to Courses → Courses")
    print("   3. Verify 'Introduction to YITP' course exists")
    print("   4. Check course is published and featured")
    print("   5. Test student enrollment and quiz completion")

def main():
    """Main deployment execution"""
    print("🚀 YITP INTRODUCTORY COURSE - PRODUCTION DEPLOYMENT")
    print("=" * 70)
    print("🌐 Target: www.youthimpactglobal.com")
    print("📅 Deployment:", __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)
    
    # Setup Django
    setup_django()
    
    # Try deployment methods in order of preference
    deployment_success = False
    
    # Method 1: Migration (if migration file exists)
    if os.path.exists('courses/migrations/0002_create_intro_course.py'):
        if method_1_migration_deployment():
            deployment_success = True
    
    # Method 2: Management command (fallback)
    if not deployment_success:
        if method_2_management_command():
            deployment_success = True
    
    # Method 3: Fixture import (alternative)
    if not deployment_success:
        if method_3_fixture_import():
            deployment_success = True
    
    if not deployment_success:
        print("\n❌ ALL DEPLOYMENT METHODS FAILED")
        print("Please check the errors above and try manual deployment")
        sys.exit(1)
    
    # Verify deployment
    print("\n" + "=" * 70)
    if verify_deployment():
        print("\n🎉 DEPLOYMENT SUCCESSFUL!")
        print("The YITP introductory course is now live in production!")
    else:
        print("\n⚠️ DEPLOYMENT COMPLETED WITH ISSUES")
        print("Please review the verification results above")
    
    # Print access information
    print_access_info()
    
    print("\n" + "=" * 70)
    print("🎓 YITP INTRODUCTORY COURSE DEPLOYMENT COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
