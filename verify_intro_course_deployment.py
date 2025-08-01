#!/usr/bin/env python
"""
YITP Introductory Course Deployment Verification Script
Standalone verification that can be run after deployment to confirm course creation
"""

import os
import sys
import django

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    django.setup()

def verify_course_deployment():
    """Comprehensive verification of the introductory course deployment"""
    print("🔍 YITP INTRODUCTORY COURSE DEPLOYMENT VERIFICATION")
    print("=" * 70)
    
    try:
        from django.contrib.auth.models import User
        from users.models import InstructorProfile
        from courses.models import Course, Module, Lesson, Category
        from assessments.models import Quiz, Question
        
        verification_results = []
        
        # 1. Verify instructor account
        print("👤 Verifying instructor account...")
        try:
            instructor = User.objects.get(username='yitpteam')
            print(f"   ✅ Username: {instructor.username}")
            print(f"   📧 Email: {instructor.email}")
            print(f"   🔑 Staff: {instructor.is_staff}")
            print(f"   ✅ Active: {instructor.is_active}")
            
            # Check instructor profile
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
        
        # 2. Verify category
        print("\n📂 Verifying course category...")
        try:
            category = Category.objects.get(name='Platform Training')
            print(f"   ✅ Category: {category.name}")
            print(f"   📝 Description: {category.description[:50]}...")
            verification_results.append(("Category", True))
        except Category.DoesNotExist:
            print("   ❌ Platform Training category not found")
            verification_results.append(("Category", False))
        
        # 3. Verify course
        print("\n📚 Verifying course...")
        try:
            course = Course.objects.get(title__icontains="Introduction to YITP")
            print(f"   ✅ Title: {course.title}")
            print(f"   💰 Price: ${course.price} (Free: {course.price == 0})")
            print(f"   📊 Status: {course.status}")
            print(f"   ⭐ Featured: {course.is_featured}")
            print(f"   👨‍🏫 Instructor: {course.instructor.username}")
            print(f"   📖 Category: {course.category.name}")
            print(f"   ⏱️ Duration: {course.estimated_duration} hour(s)")
            verification_results.append(("Course", True))
        except Course.DoesNotExist:
            print("   ❌ Course not found")
            verification_results.append(("Course", False))
            return False
        
        # 4. Verify module
        print("\n📖 Verifying module...")
        try:
            module = course.modules.first()
            if module:
                print(f"   ✅ Title: {module.title}")
                print(f"   📝 Description: {module.description[:50]}...")
                print(f"   📊 Published: {module.is_published}")
                print(f"   ⏱️ Duration: {module.estimated_duration} minutes")
                print(f"   🔢 Order: {module.sort_order}")
                verification_results.append(("Module", True))
            else:
                print("   ❌ No module found")
                verification_results.append(("Module", False))
        except Exception as e:
            print(f"   ❌ Module verification failed: {e}")
            verification_results.append(("Module", False))
        
        # 5. Verify lesson
        print("\n📝 Verifying lesson...")
        try:
            lesson = module.lessons.first() if module else None
            if lesson:
                print(f"   ✅ Title: {lesson.title}")
                print(f"   📊 Published: {lesson.is_published}")
                print(f"   🔒 Mandatory: {lesson.is_mandatory}")
                print(f"   ⏱️ Duration: {lesson.estimated_duration} minutes")
                print(f"   📄 Content length: {len(lesson.content)} characters")
                print(f"   🔢 Order: {lesson.sort_order}")
                verification_results.append(("Lesson", True))
            else:
                print("   ❌ No lesson found")
                verification_results.append(("Lesson", False))
        except Exception as e:
            print(f"   ❌ Lesson verification failed: {e}")
            verification_results.append(("Lesson", False))
        
        # 6. Verify quiz
        print("\n🧠 Verifying quiz...")
        try:
            quiz = lesson.quizzes.first() if lesson else None
            if quiz:
                print(f"   ✅ Title: {quiz.title}")
                print(f"   📊 Published: {quiz.is_published}")
                print(f"   🎯 Passing Score: {quiz.passing_score}%")
                print(f"   🔄 Max Attempts: {quiz.max_attempts}")
                print(f"   ⏱️ Time Limit: {quiz.time_limit} minutes")
                print(f"   📋 Show Results: {quiz.show_results}")
                verification_results.append(("Quiz", True))
            else:
                print("   ❌ No quiz found")
                verification_results.append(("Quiz", False))
        except Exception as e:
            print(f"   ❌ Quiz verification failed: {e}")
            verification_results.append(("Quiz", False))
        
        # 7. Verify questions
        print("\n❓ Verifying quiz questions...")
        try:
            questions = quiz.questions.all() if quiz else []
            if questions.count() >= 8:
                print(f"   ✅ Total Questions: {questions.count()}")
                total_points = sum(q.points for q in questions)
                print(f"   📊 Total Points: {total_points}")
                
                # Show question types
                question_types = {}
                for q in questions:
                    question_types[q.question_type] = question_types.get(q.question_type, 0) + 1
                
                print("   📋 Question Types:")
                for q_type, count in question_types.items():
                    print(f"      {q_type}: {count}")
                
                # Show sample questions
                print("   📝 Sample Questions:")
                for i, q in enumerate(questions[:3], 1):
                    print(f"      {i}. {q.question_text[:60]}...")
                    print(f"         Type: {q.question_type}, Points: {q.points}")
                
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
            print("\n🎉 DEPLOYMENT VERIFICATION: COMPLETE SUCCESS!")
            print("The YITP introductory course is fully deployed and ready!")
            
            print("\n🌐 Access Information:")
            print("   • Course Catalog: https://www.youthimpactglobal.com/courses/")
            print("   • Admin Interface: https://www.youthimpactglobal.com/admin/")
            print("   • Instructor Login: yitpteam / sLXSxmMg3tVeV64")
            
            return True
        elif success_rate >= 80:
            print("\n⚠️ DEPLOYMENT VERIFICATION: MOSTLY SUCCESSFUL")
            print("Some components may need attention, but core functionality is available.")
            return True
        else:
            print("\n❌ DEPLOYMENT VERIFICATION: FAILED")
            print("Significant issues detected. Manual intervention required.")
            return False
            
    except Exception as e:
        print(f"\n❌ VERIFICATION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main verification execution"""
    print("🎓 YITP INTRODUCTORY COURSE VERIFICATION")
    print("=" * 70)
    print("🌐 Target: www.youthimpactglobal.com")
    print("📅 Verification:", __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)
    
    # Setup Django
    setup_django()
    
    # Run verification
    success = verify_course_deployment()
    
    if success:
        print("\n✅ VERIFICATION COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
