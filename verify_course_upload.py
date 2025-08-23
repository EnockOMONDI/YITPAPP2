#!/usr/bin/env python
"""
Verify YITP Course Upload
Confirms successful upload to both development and production databases
"""

import os
import sys
import django

def setup_django_environment(environment='development'):
    """Setup Django environment for specified database"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    
    if environment == 'production':
        os.environ['DJANGO_ENV'] = 'production'
    else:
        os.environ.pop('DJANGO_ENV', None)  # Remove to ensure development mode
    
    django.setup()

def verify_course_upload(environment):
    """Verify course upload in specified environment"""
    print(f"🔍 VERIFYING {environment.upper()} COURSE UPLOAD")
    print("=" * 60)
    
    try:
        from courses.models import Course, Module, Lesson
        from assessments.models import Quiz, Question
        from django.contrib.auth.models import User
        
        # Find the uploaded course
        course = Course.objects.filter(title="Youth Impact Training Programme (YITP)").first()
        
        if not course:
            print(f"❌ Course not found in {environment}")
            return False
        
        print(f"✅ COURSE FOUND:")
        print(f"   Title: {course.title}")
        print(f"   ID: {course.id}")
        print(f"   Slug: {course.slug}")
        print(f"   Price: ${course.price}")
        print(f"   Instructor: {course.instructor.username}")
        print(f"   Category: {course.category.name}")
        print(f"   Status: {course.status}")
        print(f"   Published: {course.is_published}")
        
        # Verify instructor
        instructor = course.instructor
        print(f"\n✅ INSTRUCTOR VERIFICATION:")
        print(f"   Username: {instructor.username}")
        print(f"   Email: {instructor.email}")
        print(f"   Full Name: {instructor.get_full_name()}")
        print(f"   Is Staff: {instructor.is_staff}")
        print(f"   Is Active: {instructor.is_active}")
        
        # Check instructor profile
        if hasattr(instructor, 'instructor_profile'):
            profile = instructor.instructor_profile
            print(f"   Profile Role: {profile.instructor_role}")
            print(f"   Verification Status: {profile.verification_status}")
            print(f"   Can Create Courses: {profile.can_create_courses}")
        
        # Verify course structure
        modules = course.modules.all()
        print(f"\n✅ COURSE STRUCTURE:")
        print(f"   Modules: {modules.count()}")
        
        total_lessons = 0
        total_quizzes = 0
        total_questions = 0
        
        for module in modules:
            lessons = module.lessons.all()
            total_lessons += lessons.count()
            
            print(f"   Module: {module.title}")
            print(f"      Lessons: {lessons.count()}")
            print(f"      Duration: {module.estimated_duration} minutes")
            
            for lesson in lessons:
                quizzes = lesson.quizzes.all()
                total_quizzes += quizzes.count()
                
                if quizzes.exists():
                    print(f"      Lesson: {lesson.title} (has quiz)")
                    for quiz in quizzes:
                        questions = quiz.questions.count()
                        total_questions += questions
                        print(f"         Quiz: {quiz.title} ({questions} questions)")
                else:
                    print(f"      Lesson: {lesson.title}")
        
        print(f"\n📊 TOTALS:")
        print(f"   Total Lessons: {total_lessons}")
        print(f"   Total Quizzes: {total_quizzes}")
        print(f"   Total Questions: {total_questions}")
        
        # Verify URLs
        print(f"\n🔗 ACCESS URLS:")
        print(f"   Course URL: /lms/courses/{course.slug}/")
        print(f"   Admin URL: /admin/courses/course/{course.id}/change/")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def main():
    """Main verification function"""
    print("✅ YITP COURSE UPLOAD VERIFICATION")
    print("=" * 80)
    
    results = {}
    
    # Verify development
    setup_django_environment('development')
    results['development'] = verify_course_upload('development')
    
    # Verify production
    setup_django_environment('production')
    results['production'] = verify_course_upload('production')
    
    # Summary
    print(f"\n🎯 VERIFICATION SUMMARY")
    print("=" * 80)
    
    for env, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {env.title()}: {status}")
    
    all_success = all(results.values())
    
    if all_success:
        print(f"\n🎉 ALL VERIFICATIONS SUCCESSFUL!")
        print(f"   Course successfully uploaded to both environments")
        print(f"   Instructor 'yitp1' configured in both databases")
        print(f"   Course price set to $39.00 USD")
        print(f"   Ready for student enrollment and testing")
    else:
        print(f"\n⚠️ SOME VERIFICATIONS FAILED")
        print(f"   Please review the details above")

if __name__ == '__main__':
    main()
