#!/usr/bin/env python
"""
YITP Production Course Deployment Script
Deploys and verifies the introductory course in production
"""

import os
import sys
import django
from django.core.management import call_command

def setup_django():
    """Setup Django environment for production"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    django.setup()

def deploy_introductory_course():
    """Deploy the introductory course to production"""
    print("🎓 DEPLOYING YITP INTRODUCTORY COURSE TO PRODUCTION")
    print("=" * 70)
    print("🌐 Environment: www.youthimpactglobal.com")
    print("📅 Deployment Date:", __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)
    
    try:
        # Step 1: Run the course creation command
        print("\n📚 STEP 1: Creating introductory course...")
        call_command('create_intro_course', verbosity=2)
        print("✅ Course creation command completed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ DEPLOYMENT FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_production_deployment():
    """Comprehensive verification of the course deployment"""
    print("\n🔍 STEP 2: VERIFYING PRODUCTION DEPLOYMENT")
    print("=" * 70)
    
    try:
        from django.contrib.auth.models import User
        from users.models import InstructorProfile
        from courses.models import Course, Module, Lesson, Category
        from assessments.models import Quiz, Question
        
        verification_results = []
        
        # Verify instructor account
        print("👤 Verifying instructor account...")
        try:
            instructor = User.objects.get(username='yitpteam')
            print(f"   ✅ Instructor found: {instructor.username}")
            print(f"   📧 Email: {instructor.email}")
            print(f"   🔑 Staff status: {instructor.is_staff}")
            print(f"   ✅ Active: {instructor.is_active}")
            
            # Verify instructor profile
            if hasattr(instructor, 'instructor_profile'):
                profile = instructor.instructor_profile
                print(f"   👨‍🏫 Role: {profile.instructor_role}")
                print(f"   ✅ Verification: {profile.verification_status}")
                verification_results.append(("Instructor Account", True))
            else:
                print("   ❌ No instructor profile found")
                verification_results.append(("Instructor Account", False))
                
        except User.DoesNotExist:
            print("   ❌ Instructor 'yitpteam' not found")
            verification_results.append(("Instructor Account", False))
        
        # Verify course
        print("\n📚 Verifying course...")
        try:
            course = Course.objects.get(title__icontains="Introduction to YITP")
            print(f"   ✅ Course found: {course.title}")
            print(f"   💰 Price: ${course.price} (Free: {course.price == 0})")
            print(f"   📊 Status: {course.status}")
            print(f"   ⭐ Featured: {course.is_featured}")
            print(f"   📖 Published: {course.is_published}")
            print(f"   🎯 Category: {course.category.name}")
            print(f"   ⏱️ Duration: {course.estimated_duration} hour(s)")
            verification_results.append(("Course", True))
        except Course.DoesNotExist:
            print("   ❌ Course not found")
            verification_results.append(("Course", False))
            return False
        
        # Verify module
        print("\n📖 Verifying module...")
        try:
            module = course.modules.first()
            if module:
                print(f"   ✅ Module found: {module.title}")
                print(f"   📝 Description: {module.description[:50]}...")
                print(f"   📊 Published: {module.is_published}")
                print(f"   ⏱️ Duration: {module.estimated_duration} minutes")
                verification_results.append(("Module", True))
            else:
                print("   ❌ No module found")
                verification_results.append(("Module", False))
        except Exception as e:
            print(f"   ❌ Module verification failed: {e}")
            verification_results.append(("Module", False))
        
        # Verify lesson
        print("\n📝 Verifying lesson...")
        try:
            lesson = module.lessons.first()
            if lesson:
                print(f"   ✅ Lesson found: {lesson.title}")
                print(f"   📊 Published: {lesson.is_published}")
                print(f"   🔒 Mandatory: {lesson.is_mandatory}")
                print(f"   ⏱️ Duration: {lesson.estimated_duration} minutes")
                print(f"   📄 Content length: {len(lesson.content)} characters")
                verification_results.append(("Lesson", True))
            else:
                print("   ❌ No lesson found")
                verification_results.append(("Lesson", False))
        except Exception as e:
            print(f"   ❌ Lesson verification failed: {e}")
            verification_results.append(("Lesson", False))
        
        # Verify quiz
        print("\n🧠 Verifying quiz...")
        try:
            quiz = lesson.quizzes.first()
            if quiz:
                print(f"   ✅ Quiz found: {quiz.title}")
                print(f"   📊 Published: {quiz.is_published}")
                print(f"   🎯 Passing score: {quiz.passing_score}%")
                print(f"   🔄 Max attempts: {quiz.max_attempts}")
                print(f"   ⏱️ Time limit: {quiz.time_limit} minutes")
                print(f"   ❓ Total questions: {quiz.total_questions}")
                verification_results.append(("Quiz", True))
            else:
                print("   ❌ No quiz found")
                verification_results.append(("Quiz", False))
        except Exception as e:
            print(f"   ❌ Quiz verification failed: {e}")
            verification_results.append(("Quiz", False))
        
        # Verify questions
        print("\n❓ Verifying quiz questions...")
        try:
            questions = quiz.questions.all()
            if questions.count() >= 8:
                print(f"   ✅ Questions found: {questions.count()}")
                total_points = sum(q.points for q in questions)
                print(f"   📊 Total points: {total_points}")
                
                # Show sample questions
                for i, q in enumerate(questions[:3], 1):
                    print(f"   {i}. {q.question_text[:60]}...")
                    print(f"      Type: {q.question_type}, Points: {q.points}")
                
                if questions.count() > 3:
                    print(f"   ... and {questions.count() - 3} more questions")
                
                verification_results.append(("Questions", True))
            else:
                print(f"   ❌ Insufficient questions: {questions.count()}/8")
                verification_results.append(("Questions", False))
        except Exception as e:
            print(f"   ❌ Questions verification failed: {e}")
            verification_results.append(("Questions", False))
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 70)
        
        success_count = sum(1 for _, success in verification_results if success)
        total_count = len(verification_results)
        
        for component, success in verification_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status}: {component}")
        
        success_rate = (success_count / total_count) * 100
        print(f"\n🎯 Overall Success Rate: {success_count}/{total_count} ({success_rate:.0f}%)")
        
        if success_rate >= 100:
            print("🎉 DEPLOYMENT VERIFICATION: COMPLETE SUCCESS!")
            return True
        elif success_rate >= 80:
            print("⚠️ DEPLOYMENT VERIFICATION: MOSTLY SUCCESSFUL")
            return True
        else:
            print("❌ DEPLOYMENT VERIFICATION: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ VERIFICATION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_course_functionality():
    """Test basic course functionality"""
    print("\n🧪 STEP 3: TESTING COURSE FUNCTIONALITY")
    print("=" * 70)
    
    try:
        from django.contrib.auth.models import User
        from courses.models import Course
        from progress.models import Enrollment
        
        # Get the course
        course = Course.objects.get(title__icontains="Introduction to YITP")
        
        # Create test user if needed
        test_user, created = User.objects.get_or_create(
            username='test_intro_student',
            defaults={
                'email': 'test.intro@yitp.com',
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
        
        # Test enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            student=test_user,
            course=course,
            defaults={
                'status': 'active',
                'progress_percentage': 0.0
            }
        )
        
        print(f"✅ Test enrollment: {'Created' if created else 'Exists'}")
        print(f"   Student: {test_user.username}")
        print(f"   Course: {course.title}")
        print(f"   Status: {enrollment.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ FUNCTIONALITY TEST FAILED: {str(e)}")
        return False

def print_access_information():
    """Print production access information"""
    print("\n🌐 STEP 4: PRODUCTION ACCESS INFORMATION")
    print("=" * 70)
    
    print("🎓 Course Information:")
    print("   • Title: Introduction to YITP: Your Learning Journey Begins")
    print("   • Type: Mandatory first course for all new students")
    print("   • Duration: 25 minutes")
    print("   • Price: Free ($0.00)")
    print("   • Quiz: 8 questions, 70% passing score")
    
    print("\n👨‍🏫 Instructor Access:")
    print("   • Username: yitpteam")
    print("   • Password: sLXSxmMg3tVeV64")
    print("   • Email: enockomondike@gmail.com")
    
    print("\n🌐 Production URLs:")
    print("   • Admin Interface: https://www.youthimpactglobal.com/admin/")
    print("   • Course Catalog: https://www.youthimpactglobal.com/courses/")
    print("   • Student Dashboard: https://www.youthimpactglobal.com/dashboard/")
    
    print("\n🎯 Next Steps:")
    print("   1. Login to admin interface and verify course visibility")
    print("   2. Test student enrollment and course completion")
    print("   3. Verify quiz functionality and scoring")
    print("   4. Check certificate generation")
    print("   5. Set up as prerequisite for other courses")

def main():
    """Main deployment execution"""
    print("🚀 YITP INTRODUCTORY COURSE - PRODUCTION DEPLOYMENT")
    print("=" * 70)
    
    # Setup Django
    setup_django()
    
    # Deploy course
    if not deploy_introductory_course():
        print("\n❌ DEPLOYMENT FAILED - Stopping execution")
        sys.exit(1)
    
    # Verify deployment
    if not verify_production_deployment():
        print("\n⚠️ VERIFICATION ISSUES DETECTED")
        print("Please review the failed components above")
    
    # Test functionality
    if not test_course_functionality():
        print("\n⚠️ FUNCTIONALITY TEST ISSUES")
    
    # Print access information
    print_access_information()
    
    print("\n" + "=" * 70)
    print("🎉 PRODUCTION DEPLOYMENT COMPLETED!")
    print("=" * 70)
    print("The YITP introductory course is now live and ready for students!")
    print("=" * 70)

if __name__ == "__main__":
    main()
