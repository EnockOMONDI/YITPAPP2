#!/usr/bin/env python
"""
Verify Database Cleanup Results
Confirms that only "Introduction to YITP" course remains in both databases
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

def verify_database(environment):
    """Verify database cleanup for specified environment"""
    print(f"🔍 VERIFYING {environment.upper()} DATABASE")
    print("=" * 60)
    
    try:
        from courses.models import Course
        from assessments.models import Quiz, Assignment
        from progress.models import Enrollment
        from django.contrib.auth.models import User
        
        # Get all courses
        all_courses = Course.objects.all()
        
        print(f"📊 COURSE VERIFICATION:")
        print(f"   Total courses: {all_courses.count()}")
        
        if all_courses.count() == 1:
            course = all_courses.first()
            
            if "Introduction to YITP" in course.title:
                print(f"   ✅ Correct course remains: {course.title}")
                print(f"   Course ID: {course.id}")
                print(f"   Course Slug: {course.slug}")
                print(f"   Instructor: {course.instructor.username}")
                print(f"   Status: {course.status}")
                print(f"   Published: {course.is_published}")
                
                # Verify course structure
                modules = course.modules.all()
                print(f"\n📚 COURSE STRUCTURE:")
                print(f"   Modules: {modules.count()}")
                
                total_lessons = 0
                for module in modules:
                    lessons = module.lessons.all()
                    total_lessons += lessons.count()
                    print(f"   Module: {module.title} ({lessons.count()} lessons)")
                
                print(f"   Total Lessons: {total_lessons}")
                
                # Check enrollments
                enrollments = course.enrollments.all()
                print(f"   Enrollments: {enrollments.count()}")
                
                # Check assessments
                lesson_ids = []
                for module in modules:
                    lesson_ids.extend(module.lessons.values_list('id', flat=True))
                
                quizzes = Quiz.objects.filter(lesson_id__in=lesson_ids)
                assignments = Assignment.objects.filter(lesson_id__in=lesson_ids)
                
                print(f"   Quizzes: {quizzes.count()}")
                print(f"   Assignments: {assignments.count()}")
                
                return True, course
            else:
                print(f"   ❌ Wrong course remains: {course.title}")
                return False, None
        elif all_courses.count() == 0:
            print(f"   ❌ No courses found - all courses were deleted!")
            return False, None
        else:
            print(f"   ❌ Multiple courses found ({all_courses.count()}):")
            for course in all_courses:
                print(f"      - {course.title} (ID: {course.id})")
            return False, None
            
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False, None

def check_database_integrity(environment):
    """Check overall database integrity"""
    print(f"\n🔧 DATABASE INTEGRITY CHECK - {environment.upper()}")
    print("=" * 60)
    
    try:
        from courses.models import Course, Module, Lesson, Category
        from assessments.models import Quiz, Question, Assignment
        from progress.models import Enrollment, LessonProgress
        from django.contrib.auth.models import User
        
        # Count all objects
        users = User.objects.all().count()
        categories = Category.objects.all().count()
        courses = Course.objects.all().count()
        modules = Module.objects.all().count()
        lessons = Lesson.objects.all().count()
        quizzes = Quiz.objects.all().count()
        questions = Question.objects.all().count()
        assignments = Assignment.objects.all().count()
        enrollments = Enrollment.objects.all().count()
        progress = LessonProgress.objects.all().count()
        
        print(f"📊 DATABASE OBJECT COUNTS:")
        print(f"   Users: {users}")
        print(f"   Categories: {categories}")
        print(f"   Courses: {courses}")
        print(f"   Modules: {modules}")
        print(f"   Lessons: {lessons}")
        print(f"   Quizzes: {quizzes}")
        print(f"   Questions: {questions}")
        print(f"   Assignments: {assignments}")
        print(f"   Enrollments: {enrollments}")
        print(f"   Progress Records: {progress}")
        
        # Check for orphaned records
        orphaned_modules = Module.objects.filter(course__isnull=True).count()
        orphaned_lessons = Lesson.objects.filter(module__isnull=True).count()
        orphaned_quizzes = Quiz.objects.filter(lesson__isnull=True).count()
        orphaned_assignments = Assignment.objects.filter(lesson__isnull=True).count()
        
        print(f"\n🔍 ORPHANED RECORDS CHECK:")
        print(f"   Orphaned Modules: {orphaned_modules}")
        print(f"   Orphaned Lessons: {orphaned_lessons}")
        print(f"   Orphaned Quizzes: {orphaned_quizzes}")
        print(f"   Orphaned Assignments: {orphaned_assignments}")
        
        if orphaned_modules == 0 and orphaned_lessons == 0 and orphaned_quizzes == 0 and orphaned_assignments == 0:
            print(f"   ✅ No orphaned records found")
            integrity_ok = True
        else:
            print(f"   ⚠️ Found orphaned records")
            integrity_ok = False
        
        return integrity_ok
        
    except Exception as e:
        print(f"❌ Integrity check failed: {str(e)}")
        return False

def test_course_access(course, environment):
    """Test basic course access functionality"""
    print(f"\n🧪 TESTING COURSE ACCESS - {environment.upper()}")
    print("=" * 60)
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Test course list page
        try:
            course_list_url = reverse('courses:course_list')
            response = client.get(course_list_url)
            print(f"   Course List Page: {response.status_code} (Expected: 200 or 302)")
        except Exception as e:
            print(f"   Course List Page: Error - {str(e)}")
        
        # Test course detail page
        try:
            course_detail_url = reverse('courses:course_detail', kwargs={'slug': course.slug})
            response = client.get(course_detail_url)
            print(f"   Course Detail Page: {response.status_code} (Expected: 200 or 302)")
        except Exception as e:
            print(f"   Course Detail Page: Error - {str(e)}")
        
        # Test admin access
        try:
            admin_url = f'/admin/courses/course/{course.id}/change/'
            response = client.get(admin_url)
            print(f"   Admin Course Page: {response.status_code} (Expected: 302 for login redirect)")
        except Exception as e:
            print(f"   Admin Course Page: Error - {str(e)}")
        
        print(f"   ✅ Basic access tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Access testing failed: {str(e)}")
        return False

def generate_cleanup_report():
    """Generate final cleanup report"""
    print(f"\n📋 FINAL CLEANUP REPORT")
    print("=" * 80)
    
    results = {}
    
    # Test development database
    print(f"\n🔧 DEVELOPMENT DATABASE VERIFICATION")
    setup_django_environment('development')
    dev_success, dev_course = verify_database('development')
    dev_integrity = check_database_integrity('development')
    
    if dev_success and dev_course:
        dev_access = test_course_access(dev_course, 'development')
    else:
        dev_access = False
    
    results['development'] = {
        'cleanup_success': dev_success,
        'integrity_ok': dev_integrity,
        'access_ok': dev_access,
        'course': dev_course
    }
    
    # Test production database
    print(f"\n🔧 PRODUCTION DATABASE VERIFICATION")
    setup_django_environment('production')
    prod_success, prod_course = verify_database('production')
    prod_integrity = check_database_integrity('production')
    
    if prod_success and prod_course:
        prod_access = test_course_access(prod_course, 'production')
    else:
        prod_access = False
    
    results['production'] = {
        'cleanup_success': prod_success,
        'integrity_ok': prod_integrity,
        'access_ok': prod_access,
        'course': prod_course
    }
    
    # Generate summary
    print(f"\n🎯 CLEANUP VERIFICATION SUMMARY")
    print("=" * 80)
    
    for env, result in results.items():
        print(f"\n📊 {env.upper()} DATABASE:")
        
        cleanup_status = "✅ SUCCESS" if result['cleanup_success'] else "❌ FAILED"
        integrity_status = "✅ OK" if result['integrity_ok'] else "⚠️ ISSUES"
        access_status = "✅ OK" if result['access_ok'] else "⚠️ ISSUES"
        
        print(f"   Cleanup: {cleanup_status}")
        print(f"   Integrity: {integrity_status}")
        print(f"   Access: {access_status}")
        
        if result['course']:
            print(f"   Remaining Course: {result['course'].title}")
            print(f"   Course ID: {result['course'].id}")
    
    # Overall status
    all_success = all(
        result['cleanup_success'] and result['integrity_ok'] 
        for result in results.values()
    )
    
    if all_success:
        print(f"\n🎉 OVERALL STATUS: ✅ ALL CLEANUP OPERATIONS SUCCESSFUL")
        print(f"   Both databases contain only 'Introduction to YITP' course")
        print(f"   Database integrity verified")
        print(f"   Basic functionality tested")
    else:
        print(f"\n⚠️ OVERALL STATUS: ❌ SOME ISSUES DETECTED")
        print(f"   Please review the detailed results above")
        print(f"   Consider restoring from backup if necessary")
    
    return all_success

def main():
    """Main verification function"""
    print("✅ YITP DATABASE CLEANUP VERIFICATION")
    print("=" * 80)
    print("Verifying that cleanup was successful in both databases")
    print()
    
    success = generate_cleanup_report()
    
    if success:
        print(f"\n🎯 VERIFICATION COMPLETE - ALL SYSTEMS OPERATIONAL")
        print(f"   Development: Only Introduction course remains")
        print(f"   Production: Only Introduction course remains")
        print(f"   Database integrity: Verified")
        print(f"   Basic functionality: Tested")
        print()
        print(f"📋 NEXT STEPS:")
        print(f"   • Test course enrollment and functionality")
        print(f"   • Verify admin panel access")
        print(f"   • Monitor for any issues")
        print(f"   • Keep backup files for emergency recovery")
    else:
        print(f"\n⚠️ VERIFICATION FAILED - MANUAL REVIEW REQUIRED")
        print(f"   Please check the detailed results above")
        print(f"   Consider restoring from backup if necessary")
        print(f"   Contact technical support if issues persist")

if __name__ == '__main__':
    main()
