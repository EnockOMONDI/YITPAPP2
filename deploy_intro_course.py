#!/usr/bin/env python
"""
YITP Introductory Course Production Deployment Script
Deploys the comprehensive introductory course to production
"""

import os
import sys
import django

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    django.setup()

def deploy_intro_course():
    """Deploy the introductory course to production"""
    from django.core.management import call_command
    
    print("🚀 DEPLOYING YITP INTRODUCTORY COURSE TO PRODUCTION")
    print("=" * 60)
    
    try:
        # Run the course creation command
        print("📚 Creating introductory course...")
        call_command('create_intro_course', verbosity=2)
        
        print("\n✅ DEPLOYMENT SUCCESSFUL!")
        print("=" * 60)
        print("🎓 Course Details:")
        print("   • Title: Introduction to YITP: Your Learning Journey Begins")
        print("   • Instructor: yitpteam (enockomondike@gmail.com)")
        print("   • Price: Free")
        print("   • Duration: 25 minutes")
        print("   • Status: Published")
        print("   • Quiz: 8 questions, 70% passing score")
        
        print("\n🌐 Production Access:")
        print("   • Course Catalog: https://www.youthimpactglobal.com/courses/")
        print("   • Admin Interface: https://www.youthimpactglobal.com/admin/")
        print("   • Instructor Login: yitpteam / sLXSxmMg3tVeV64")
        
        print("\n🎯 Verification Steps:")
        print("   1. Check course appears in catalog")
        print("   2. Test student enrollment")
        print("   3. Verify quiz functionality")
        print("   4. Test course completion")
        print("   5. Check certificate generation")
        
        return True
        
    except Exception as e:
        print(f"❌ DEPLOYMENT FAILED: {str(e)}")
        return False

def verify_course_deployment():
    """Verify the course was deployed correctly"""
    from courses.models import Course, Module, Lesson
    from assessments.models import Quiz, Question
    from django.contrib.auth.models import User
    
    print("\n🔍 VERIFYING COURSE DEPLOYMENT")
    print("=" * 60)
    
    try:
        # Check instructor
        instructor = User.objects.get(username='yitpteam')
        print(f"✅ Instructor: {instructor.username} ({instructor.email})")
        
        # Check course
        course = Course.objects.get(title__icontains="Introduction to YITP")
        print(f"✅ Course: {course.title}")
        print(f"   Status: {course.status}")
        print(f"   Price: ${course.price}")
        print(f"   Featured: {course.is_featured}")
        
        # Check module
        module = course.modules.first()
        print(f"✅ Module: {module.title}")
        print(f"   Lessons: {module.total_lessons}")
        
        # Check lesson
        lesson = module.lessons.first()
        print(f"✅ Lesson: {lesson.title}")
        print(f"   Duration: {lesson.estimated_duration} minutes")
        print(f"   Published: {lesson.is_published}")
        
        # Check quiz
        quiz = lesson.quizzes.first()
        print(f"✅ Quiz: {quiz.title}")
        print(f"   Questions: {quiz.total_questions}")
        print(f"   Passing Score: {quiz.passing_score}%")
        print(f"   Max Attempts: {quiz.max_attempts}")
        
        # Check questions
        questions = quiz.questions.all()
        print(f"✅ Questions: {len(questions)} total")
        for i, q in enumerate(questions, 1):
            print(f"   {i}. {q.question_text[:50]}...")
        
        print("\n🎉 VERIFICATION SUCCESSFUL!")
        print("The introductory course is ready for students!")
        
        return True
        
    except Exception as e:
        print(f"❌ VERIFICATION FAILED: {str(e)}")
        return False

def create_test_enrollment():
    """Create a test enrollment to verify the course works"""
    from django.contrib.auth.models import User
    from courses.models import Course
    from progress.models import Enrollment
    
    print("\n🧪 CREATING TEST ENROLLMENT")
    print("=" * 60)
    
    try:
        # Get the course
        course = Course.objects.get(title__icontains="Introduction to YITP")
        
        # Create or get test user
        test_user, created = User.objects.get_or_create(
            username='test_student',
            defaults={
                'email': 'test@yitp.com',
                'first_name': 'Test',
                'last_name': 'Student',
                'is_active': True
            }
        )
        
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            print(f"✅ Created test user: {test_user.username}")
        else:
            print(f"✅ Using existing test user: {test_user.username}")
        
        # Create enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            student=test_user,
            course=course,
            defaults={
                'status': 'active',
                'progress_percentage': 0.0
            }
        )
        
        if created:
            print(f"✅ Created test enrollment")
        else:
            print(f"✅ Test enrollment already exists")
        
        print(f"   Student: {test_user.username}")
        print(f"   Course: {course.title}")
        print(f"   Status: {enrollment.status}")
        print(f"   Progress: {enrollment.progress_percentage}%")
        
        print("\n🎯 Test Login Credentials:")
        print("   Username: test_student")
        print("   Password: testpass123")
        
        return True
        
    except Exception as e:
        print(f"❌ TEST ENROLLMENT FAILED: {str(e)}")
        return False

def main():
    """Main execution function"""
    print("🎓 YITP INTRODUCTORY COURSE DEPLOYMENT")
    print("=" * 60)
    
    # Setup Django
    setup_django()
    
    # Deploy course
    if not deploy_intro_course():
        sys.exit(1)
    
    # Verify deployment
    if not verify_course_deployment():
        sys.exit(1)
    
    # Create test enrollment
    if not create_test_enrollment():
        print("⚠️ Test enrollment failed, but course deployment was successful")
    
    print("\n" + "=" * 60)
    print("🎉 DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print("The YITP introductory course is now live and ready for students!")
    print("Students can enroll for free and begin their learning journey.")
    print("=" * 60)

if __name__ == "__main__":
    main()
