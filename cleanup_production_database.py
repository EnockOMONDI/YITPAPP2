#!/usr/bin/env python
"""
Production Database Cleanup
Removes all courses except "Introduction to YITP" from production database
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode
django.setup()

def create_production_backup():
    """Create a backup of production data"""
    print("📦 CREATING PRODUCTION BACKUP")
    print("=" * 50)
    
    try:
        from django.core.management import call_command
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"production_backup_before_cleanup_{timestamp}.json"
        
        print("⏳ Creating full production backup (this may take a while)...")
        
        with open(backup_file, 'w') as f:
            call_command('dumpdata', 
                        'courses', 'assessments', 'progress', 'users',
                        '--natural-foreign', 
                        '--indent', '2',
                        stdout=f)
        
        print(f"✅ Production backup created: {backup_file}")
        
        # Get file size for verification
        file_size = os.path.getsize(backup_file)
        print(f"   Backup size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        
        return backup_file
        
    except Exception as e:
        print(f"❌ Production backup failed: {str(e)}")
        return None

def verify_production_connection():
    """Verify we're connected to production database"""
    print("🔍 VERIFYING PRODUCTION CONNECTION")
    print("=" * 50)
    
    try:
        from django.conf import settings
        from django.db import connection
        
        # Check database configuration
        db_config = settings.DATABASES['default']
        
        print(f"Database Engine: {db_config['ENGINE']}")
        print(f"Database Name: {db_config.get('NAME', 'Not specified')}")
        print(f"Database Host: {db_config.get('HOST', 'Not specified')}")
        
        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        if result:
            print("✅ Production database connection verified")
            return True
        else:
            print("❌ Production database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection verification failed: {str(e)}")
        return False

def ensure_intro_course_exists():
    """Ensure Introduction course exists in production"""
    print("\n🔍 ENSURING INTRODUCTION COURSE EXISTS")
    print("=" * 50)
    
    try:
        from courses.models import Course
        from django.core.management import call_command
        
        # Check if intro course exists
        intro_course = Course.objects.filter(
            title__icontains="Introduction to YITP"
        ).first()
        
        if intro_course:
            print(f"✅ Introduction course found:")
            print(f"   ID: {intro_course.id}")
            print(f"   Title: {intro_course.title}")
            print(f"   Instructor: {intro_course.instructor.username}")
            return intro_course
        else:
            print("⚠️ Introduction course not found in production!")
            print("Creating Introduction course...")
            
            # Create the intro course
            call_command('create_intro_course')
            
            # Verify creation
            intro_course = Course.objects.filter(
                title__icontains="Introduction to YITP"
            ).first()
            
            if intro_course:
                print(f"✅ Introduction course created successfully")
                return intro_course
            else:
                print("❌ Failed to create Introduction course")
                return None
                
    except Exception as e:
        print(f"❌ Error ensuring Introduction course: {str(e)}")
        return None

def analyze_production_courses():
    """Analyze courses in production database"""
    print("\n📊 ANALYZING PRODUCTION COURSES")
    print("=" * 50)
    
    try:
        from courses.models import Course
        
        all_courses = Course.objects.all()
        print(f"Total courses in production: {all_courses.count()}")
        
        if all_courses.exists():
            print(f"\nCourse details:")
            for course in all_courses:
                print(f"   ID: {course.id} | Title: {course.title}")
                print(f"      Instructor: {course.instructor.username}")
                print(f"      Status: {course.status}")
                print(f"      Modules: {course.modules.count()}")
                
                # Count lessons and enrollments
                lesson_count = sum(module.lessons.count() for module in course.modules.all())
                enrollment_count = course.enrollments.count()
                
                print(f"      Lessons: {lesson_count}")
                print(f"      Enrollments: {enrollment_count}")
                print()
        
        return all_courses
        
    except Exception as e:
        print(f"❌ Error analyzing courses: {str(e)}")
        return Course.objects.none()

def perform_production_cleanup(intro_course):
    """Perform the production cleanup"""
    print("🗑️ PERFORMING PRODUCTION CLEANUP")
    print("=" * 50)
    
    try:
        from courses.models import Course
        
        # Get courses to delete (all except intro)
        courses_to_delete = Course.objects.exclude(id=intro_course.id)
        
        if not courses_to_delete.exists():
            print("✅ No courses to delete - only intro course exists")
            return True
        
        print(f"Courses to delete: {courses_to_delete.count()}")
        
        # Show what will be deleted
        total_modules = 0
        total_lessons = 0
        total_enrollments = 0
        
        for course in courses_to_delete:
            modules = course.modules.count()
            lessons = sum(module.lessons.count() for module in course.modules.all())
            enrollments = course.enrollments.count()
            
            total_modules += modules
            total_lessons += lessons
            total_enrollments += enrollments
            
            print(f"   Will delete: {course.title}")
            print(f"      Modules: {modules}, Lessons: {lessons}, Enrollments: {enrollments}")
        
        print(f"\nTotal impact:")
        print(f"   Courses: {courses_to_delete.count()}")
        print(f"   Modules: {total_modules}")
        print(f"   Lessons: {total_lessons}")
        print(f"   Enrollments: {total_enrollments}")
        
        # Final confirmation
        print(f"\n⚠️ CRITICAL PRODUCTION OPERATION")
        print("This will permanently delete the above data from PRODUCTION!")
        confirmation = input("Type 'DELETE PRODUCTION DATA' to confirm: ").strip()
        
        if confirmation != 'DELETE PRODUCTION DATA':
            print("❌ Production cleanup cancelled")
            return False
        
        # Perform deletion
        deleted_courses = []
        for course in courses_to_delete:
            course_info = {
                'id': course.id,
                'title': course.title,
                'instructor': course.instructor.username
            }
            
            print(f"   Deleting: {course.title} (ID: {course.id})")
            course.delete()
            
            deleted_courses.append(course_info)
            print(f"   ✅ Deleted successfully")
        
        print(f"\n✅ PRODUCTION CLEANUP COMPLETED")
        print(f"   Courses deleted: {len(deleted_courses)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Production cleanup failed: {str(e)}")
        return False

def verify_production_cleanup(intro_course):
    """Verify production cleanup results"""
    print("\n✅ VERIFYING PRODUCTION CLEANUP")
    print("=" * 50)
    
    try:
        from courses.models import Course
        
        remaining_courses = Course.objects.all()
        
        print(f"Remaining courses: {remaining_courses.count()}")
        
        if remaining_courses.count() == 1:
            remaining_course = remaining_courses.first()
            if remaining_course.id == intro_course.id:
                print(f"✅ SUCCESS: Only Introduction course remains")
                print(f"   Title: {remaining_course.title}")
                print(f"   ID: {remaining_course.id}")
                print(f"   Status: {remaining_course.status}")
                print(f"   Published: {remaining_course.is_published}")
                
                # Verify course integrity
                modules = remaining_course.modules.count()
                lessons = sum(module.lessons.count() for module in remaining_course.modules.all())
                
                print(f"   Modules: {modules}")
                print(f"   Lessons: {lessons}")
                
                return True
            else:
                print(f"❌ Wrong course remaining: {remaining_course.title}")
                return False
        elif remaining_courses.count() == 0:
            print(f"❌ No courses remaining - Introduction course was deleted!")
            return False
        else:
            print(f"❌ Multiple courses remaining:")
            for course in remaining_courses:
                print(f"   - {course.title} (ID: {course.id})")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def main():
    """Main production cleanup function"""
    print("🚨 YITP PRODUCTION DATABASE CLEANUP")
    print("=" * 60)
    print("⚠️ WARNING: This will modify the PRODUCTION database!")
    print("This will remove all courses except 'Introduction to YITP'")
    print("from the production database.")
    print()
    
    # Initial confirmation
    print("🔒 PRODUCTION SAFETY CHECK")
    initial_confirm = input("Are you sure you want to modify PRODUCTION? (yes/no): ").lower().strip()
    if initial_confirm != 'yes':
        print("❌ Production cleanup cancelled")
        return
    
    # Verify production connection
    if not verify_production_connection():
        print("❌ Cannot proceed without verified production connection")
        return
    
    # Create backup
    backup_file = create_production_backup()
    if not backup_file:
        print("❌ Cannot proceed without production backup")
        return
    
    # Ensure intro course exists
    intro_course = ensure_intro_course_exists()
    if not intro_course:
        print("❌ Cannot proceed without Introduction course")
        return
    
    # Analyze current state
    all_courses = analyze_production_courses()
    
    # Perform cleanup
    success = perform_production_cleanup(intro_course)
    if not success:
        print("❌ Production cleanup failed")
        return
    
    # Verify results
    verified = verify_production_cleanup(intro_course)
    if not verified:
        print("❌ Production verification failed")
        return
    
    # Final report
    print(f"\n🎉 PRODUCTION CLEANUP COMPLETED!")
    print("=" * 60)
    print(f"✅ Only 'Introduction to YITP' course remains in production")
    print(f"✅ Production backup: {backup_file}")
    print(f"✅ Database integrity verified")
    print()
    print("📋 IMPORTANT NOTES:")
    print("   • Production database has been modified")
    print("   • Backup file contains all deleted data")
    print("   • Test the remaining course thoroughly")
    print("   • Monitor for any issues")
    print()
    print("🔗 PRODUCTION ACCESS:")
    print("   URL: https://www.youthimpactglobal.com/admin/")
    print("   Use existing admin credentials")

if __name__ == '__main__':
    main()
