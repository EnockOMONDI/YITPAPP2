#!/usr/bin/env python
"""
YITP Database Cleanup Script
Removes all courses except "Introduction to YITP: Your Learning Journey Begins"
from both development and production databases
"""

import os
import sys
import django
import json
from datetime import datetime
from django.core.management import call_command
from io import StringIO

def setup_django_environment(environment='development'):
    """Setup Django environment for specified database"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    
    if environment == 'production':
        os.environ['DJANGO_ENV'] = 'production'
    else:
        os.environ.pop('DJANGO_ENV', None)  # Remove to ensure development mode
    
    django.setup()

def create_database_backup(environment):
    """Create database backup before cleanup"""
    print(f"📦 CREATING {environment.upper()} DATABASE BACKUP")
    print("=" * 60)
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"yitp_backup_{environment}_{timestamp}.json"
        
        # Create full database backup
        with open(backup_filename, 'w') as backup_file:
            call_command('dumpdata', 
                        '--natural-foreign', 
                        '--natural-primary',
                        '--indent', '2',
                        stdout=backup_file)
        
        print(f"✅ Database backup created: {backup_filename}")
        return backup_filename
        
    except Exception as e:
        print(f"❌ Backup creation failed: {str(e)}")
        return None

def identify_target_course():
    """Identify the course to preserve"""
    print(f"🔍 IDENTIFYING TARGET COURSE TO PRESERVE")
    print("=" * 60)
    
    try:
        from courses.models import Course
        
        # Look for the Introduction course
        target_course = Course.objects.filter(
            title__icontains="Introduction to YITP"
        ).first()
        
        if target_course:
            print(f"✅ Found target course to preserve:")
            print(f"   ID: {target_course.id}")
            print(f"   Title: {target_course.title}")
            print(f"   Slug: {target_course.slug}")
            print(f"   Instructor: {target_course.instructor.username}")
            print(f"   Status: {target_course.status}")
            print(f"   Published: {target_course.is_published}")
            return target_course
        else:
            print("❌ Target course 'Introduction to YITP' not found!")
            return None
            
    except Exception as e:
        print(f"❌ Error identifying target course: {str(e)}")
        return None

def list_courses_to_delete(target_course):
    """List all courses that will be deleted"""
    print(f"📋 COURSES SCHEDULED FOR DELETION")
    print("=" * 60)
    
    try:
        from courses.models import Course
        
        # Get all courses except the target
        courses_to_delete = Course.objects.exclude(id=target_course.id)
        
        if courses_to_delete.exists():
            print(f"Found {courses_to_delete.count()} courses to delete:")
            
            for i, course in enumerate(courses_to_delete, 1):
                print(f"   {i}. ID: {course.id} | Title: {course.title}")
                print(f"      Slug: {course.slug}")
                print(f"      Instructor: {course.instructor.username}")
                print(f"      Modules: {course.modules.count()}")
                
                # Count lessons
                lesson_count = sum(module.lessons.count() for module in course.modules.all())
                print(f"      Lessons: {lesson_count}")
                
                # Count enrollments
                enrollment_count = course.enrollments.count()
                print(f"      Enrollments: {enrollment_count}")
                print()
            
            return courses_to_delete
        else:
            print("✅ No courses found for deletion (only target course exists)")
            return Course.objects.none()
            
    except Exception as e:
        print(f"❌ Error listing courses: {str(e)}")
        return Course.objects.none()

def analyze_related_data(courses_to_delete):
    """Analyze related data that will be affected"""
    print(f"🔗 ANALYZING RELATED DATA IMPACT")
    print("=" * 60)
    
    try:
        from courses.models import Module, Lesson
        from assessments.models import Quiz, Question, Assignment
        from progress.models import Enrollment, LessonProgress
        
        total_modules = 0
        total_lessons = 0
        total_quizzes = 0
        total_questions = 0
        total_assignments = 0
        total_enrollments = 0
        total_progress = 0
        
        for course in courses_to_delete:
            modules = course.modules.all()
            total_modules += modules.count()
            
            for module in modules:
                lessons = module.lessons.all()
                total_lessons += lessons.count()
                
                for lesson in lessons:
                    total_quizzes += lesson.quizzes.count()
                    total_assignments += lesson.assignments.count()
                    total_progress += lesson.lesson_progress.count()
                    
                    for quiz in lesson.quizzes.all():
                        total_questions += quiz.questions.count()
            
            total_enrollments += course.enrollments.count()
        
        print(f"📊 DELETION IMPACT SUMMARY:")
        print(f"   Courses: {courses_to_delete.count()}")
        print(f"   Modules: {total_modules}")
        print(f"   Lessons: {total_lessons}")
        print(f"   Quizzes: {total_quizzes}")
        print(f"   Questions: {total_questions}")
        print(f"   Assignments: {total_assignments}")
        print(f"   Enrollments: {total_enrollments}")
        print(f"   Progress Records: {total_progress}")
        
        return {
            'courses': courses_to_delete.count(),
            'modules': total_modules,
            'lessons': total_lessons,
            'quizzes': total_quizzes,
            'questions': total_questions,
            'assignments': total_assignments,
            'enrollments': total_enrollments,
            'progress': total_progress
        }
        
    except Exception as e:
        print(f"❌ Error analyzing related data: {str(e)}")
        return {}

def perform_cleanup(courses_to_delete, environment):
    """Perform the actual course deletion"""
    print(f"🗑️ PERFORMING {environment.upper()} DATABASE CLEANUP")
    print("=" * 60)
    
    try:
        deleted_courses = []
        
        for course in courses_to_delete:
            course_info = {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'instructor': course.instructor.username
            }
            
            print(f"   Deleting: {course.title} (ID: {course.id})")
            
            # Django's CASCADE will handle related objects
            course.delete()
            
            deleted_courses.append(course_info)
            print(f"   ✅ Deleted successfully")
        
        print(f"\n✅ CLEANUP COMPLETED")
        print(f"   Total courses deleted: {len(deleted_courses)}")
        
        return deleted_courses
        
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")
        return []

def verify_cleanup(target_course):
    """Verify cleanup was successful"""
    print(f"✅ VERIFYING CLEANUP RESULTS")
    print("=" * 60)
    
    try:
        from courses.models import Course
        
        # Check remaining courses
        remaining_courses = Course.objects.all()
        
        print(f"📊 CLEANUP VERIFICATION:")
        print(f"   Remaining courses: {remaining_courses.count()}")
        
        if remaining_courses.count() == 1:
            remaining_course = remaining_courses.first()
            if remaining_course.id == target_course.id:
                print(f"   ✅ Only target course remains: {remaining_course.title}")
                
                # Verify course integrity
                modules = remaining_course.modules.count()
                lessons = sum(module.lessons.count() for module in remaining_course.modules.all())
                
                print(f"   📚 Target course integrity:")
                print(f"      Modules: {modules}")
                print(f"      Lessons: {lessons}")
                print(f"      Status: {remaining_course.status}")
                print(f"      Published: {remaining_course.is_published}")
                
                return True
            else:
                print(f"   ❌ Wrong course remaining: {remaining_course.title}")
                return False
        elif remaining_courses.count() == 0:
            print(f"   ❌ No courses remaining - target course was deleted!")
            return False
        else:
            print(f"   ❌ Multiple courses remaining:")
            for course in remaining_courses:
                print(f"      - {course.title} (ID: {course.id})")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def cleanup_database(environment):
    """Main cleanup function for a specific environment"""
    print(f"\n🚀 STARTING {environment.upper()} DATABASE CLEANUP")
    print("=" * 80)
    
    # Setup Django environment
    setup_django_environment(environment)
    
    # Step 1: Create backup
    backup_file = create_database_backup(environment)
    if not backup_file:
        print(f"❌ Cannot proceed without backup for {environment}")
        return False
    
    # Step 2: Identify target course
    target_course = identify_target_course()
    if not target_course:
        print(f"❌ Cannot proceed without target course in {environment}")
        return False
    
    # Step 3: List courses to delete
    courses_to_delete = list_courses_to_delete(target_course)
    if not courses_to_delete.exists():
        print(f"✅ No cleanup needed for {environment} - only target course exists")
        return True
    
    # Step 4: Analyze impact
    impact_data = analyze_related_data(courses_to_delete)
    
    # Step 5: Confirm deletion
    print(f"\n⚠️ CONFIRMATION REQUIRED FOR {environment.upper()}")
    print("=" * 60)
    print(f"This will permanently delete {courses_to_delete.count()} courses and all related data.")
    print(f"Backup created: {backup_file}")
    
    # For safety, require manual confirmation
    if environment == 'production':
        confirmation = input("Type 'DELETE PRODUCTION' to confirm: ")
        if confirmation != 'DELETE PRODUCTION':
            print("❌ Production cleanup cancelled")
            return False
    else:
        confirmation = input("Type 'DELETE DEVELOPMENT' to confirm: ")
        if confirmation != 'DELETE DEVELOPMENT':
            print("❌ Development cleanup cancelled")
            return False
    
    # Step 6: Perform cleanup
    deleted_courses = perform_cleanup(courses_to_delete, environment)
    
    # Step 7: Verify results
    success = verify_cleanup(target_course)
    
    # Step 8: Generate report
    print(f"\n📋 {environment.upper()} CLEANUP REPORT")
    print("=" * 60)
    print(f"   Environment: {environment}")
    print(f"   Backup File: {backup_file}")
    print(f"   Courses Deleted: {len(deleted_courses)}")
    print(f"   Target Preserved: {target_course.title}")
    print(f"   Success: {'✅ Yes' if success else '❌ No'}")
    
    if deleted_courses:
        print(f"\n   Deleted Courses:")
        for course in deleted_courses:
            print(f"      - {course['title']} (ID: {course['id']})")
    
    return success

def create_superuser_if_needed():
    """Create superuser for admin access if needed"""
    print(f"\n👤 CHECKING SUPERUSER ACCESS")
    print("=" * 60)
    
    try:
        from django.contrib.auth.models import User
        
        superusers = User.objects.filter(is_superuser=True)
        
        if superusers.exists():
            print(f"✅ Found {superusers.count()} superuser(s):")
            for user in superusers:
                print(f"   - {user.username} ({user.email})")
        else:
            print("⚠️ No superusers found. Creating admin user...")
            
            admin_user = User.objects.create_superuser(
                username='yitpadmin',
                email='admin@youthimpactglobal.com',
                password='YITPAdmin2025!'
            )
            
            print(f"✅ Created superuser: {admin_user.username}")
            print(f"   Email: {admin_user.email}")
            print(f"   Password: YITPAdmin2025!")
            
    except Exception as e:
        print(f"❌ Error checking/creating superuser: {str(e)}")

def ensure_intro_course_exists(environment):
    """Ensure the Introduction course exists before cleanup"""
    print(f"🔍 ENSURING INTRODUCTION COURSE EXISTS IN {environment.upper()}")
    print("=" * 60)

    try:
        from courses.models import Course
        from django.core.management import call_command

        # Check if intro course exists
        intro_course = Course.objects.filter(
            title__icontains="Introduction to YITP"
        ).first()

        if intro_course:
            print(f"✅ Introduction course found: {intro_course.title}")
            return intro_course
        else:
            print("⚠️ Introduction course not found. Creating it...")

            # Create the intro course using management command
            call_command('create_intro_course')

            # Verify creation
            intro_course = Course.objects.filter(
                title__icontains="Introduction to YITP"
            ).first()

            if intro_course:
                print(f"✅ Introduction course created: {intro_course.title}")
                return intro_course
            else:
                print("❌ Failed to create Introduction course")
                return None

    except Exception as e:
        print(f"❌ Error ensuring Introduction course: {str(e)}")
        return None

def main():
    """Main execution function"""
    print("🧹 YITP DATABASE CLEANUP UTILITY")
    print("=" * 80)
    print("This script will remove all courses except 'Introduction to YITP'")
    print("from both development and production databases.")
    print()
    print("⚠️ IMPORTANT SAFETY NOTES:")
    print("   • Database backups will be created before any deletions")
    print("   • The 'Introduction to YITP' course will be preserved")
    print("   • All other courses and related data will be permanently deleted")
    print("   • This action cannot be undone without restoring from backup")
    print()

    # Check which environments to clean
    environments = []

    print("📋 SELECT ENVIRONMENTS TO CLEAN:")
    dev_cleanup = input("   Clean development database? (y/n): ").lower().strip()
    if dev_cleanup == 'y':
        environments.append('development')

    prod_cleanup = input("   Clean production database? (y/n): ").lower().strip()
    if prod_cleanup == 'y':
        environments.append('production')

    if not environments:
        print("❌ No environments selected for cleanup")
        return

    print(f"\n📋 SELECTED ENVIRONMENTS: {', '.join(environments)}")

    # Final confirmation
    print(f"\n⚠️ FINAL CONFIRMATION")
    print("=" * 60)
    print("This will permanently delete all courses except 'Introduction to YITP'")
    print("from the selected database(s).")

    final_confirm = input("Type 'CONFIRM CLEANUP' to proceed: ").strip()
    if final_confirm != 'CONFIRM CLEANUP':
        print("❌ Cleanup cancelled by user")
        return

    results = {}

    # Process each environment
    for environment in environments:
        try:
            print(f"\n{'='*80}")
            print(f"🚀 PROCESSING {environment.upper()} DATABASE")
            print(f"{'='*80}")

            # Setup environment
            setup_django_environment(environment)

            # Ensure intro course exists
            intro_course = ensure_intro_course_exists(environment)
            if not intro_course:
                print(f"❌ Cannot proceed without Introduction course in {environment}")
                results[environment] = False
                continue

            # Perform cleanup
            results[environment] = cleanup_database(environment)

            # Create superuser for admin access
            if results[environment]:
                create_superuser_if_needed()

        except Exception as e:
            print(f"❌ Fatal error in {environment} cleanup: {str(e)}")
            results[environment] = False

    # Final summary
    print(f"\n🎯 FINAL CLEANUP SUMMARY")
    print("=" * 80)

    for environment, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {environment.title()}: {status}")

    all_success = all(results.values())

    if all_success:
        print(f"\n🎉 ALL CLEANUP OPERATIONS COMPLETED SUCCESSFULLY!")
        print(f"   Only 'Introduction to YITP' course remains in selected databases")
        print(f"   Database backups created for safety")
        print(f"   Admin access verified/created")
        print(f"\n📋 NEXT STEPS:")
        print(f"   • Verify course access through admin panel")
        print(f"   • Test course functionality")
        print(f"   • Keep backup files for emergency recovery")
    else:
        print(f"\n⚠️ SOME CLEANUP OPERATIONS FAILED")
        print(f"   Please review the logs above for details")
        print(f"   Database backups are available for recovery if needed")
        print(f"\n🔧 TROUBLESHOOTING:")
        print(f"   • Check database connections")
        print(f"   • Verify Django settings")
        print(f"   • Review error messages above")
        print(f"   • Restore from backup if necessary")

if __name__ == '__main__':
    main()
