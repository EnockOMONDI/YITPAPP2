#!/usr/bin/env python
"""
Quick Development Database Cleanup
Removes all courses except "Introduction to YITP" from development database
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment for development
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ.pop('DJANGO_ENV', None)  # Ensure development mode
django.setup()

def create_backup():
    """Create a quick backup of current data"""
    print("📦 CREATING DEVELOPMENT BACKUP")
    print("=" * 50)
    
    try:
        from django.core.management import call_command
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"dev_backup_before_cleanup_{timestamp}.json"
        
        with open(backup_file, 'w') as f:
            call_command('dumpdata', 
                        'courses', 'assessments', 'progress',
                        '--natural-foreign', 
                        '--indent', '2',
                        stdout=f)
        
        print(f"✅ Backup created: {backup_file}")
        return backup_file
        
    except Exception as e:
        print(f"❌ Backup failed: {str(e)}")
        return None

def identify_courses():
    """Identify courses in development database"""
    print("\n🔍 IDENTIFYING COURSES")
    print("=" * 50)
    
    try:
        from courses.models import Course
        
        all_courses = Course.objects.all()
        print(f"Total courses found: {all_courses.count()}")
        
        # Find intro course
        intro_course = Course.objects.filter(
            title__icontains="Introduction to YITP"
        ).first()
        
        if intro_course:
            print(f"\n✅ COURSE TO PRESERVE:")
            print(f"   ID: {intro_course.id}")
            print(f"   Title: {intro_course.title}")
            print(f"   Slug: {intro_course.slug}")
        else:
            print(f"\n❌ Introduction course not found!")
            return None, Course.objects.none()
        
        # Find courses to delete
        courses_to_delete = Course.objects.exclude(id=intro_course.id)
        
        if courses_to_delete.exists():
            print(f"\n🗑️ COURSES TO DELETE:")
            for course in courses_to_delete:
                print(f"   ID: {course.id} | Title: {course.title}")
                print(f"      Modules: {course.modules.count()}")
                
                # Count lessons
                lesson_count = sum(module.lessons.count() for module in course.modules.all())
                print(f"      Lessons: {lesson_count}")
                print(f"      Enrollments: {course.enrollments.count()}")
                print()
        else:
            print(f"\n✅ No courses to delete - only intro course exists")
        
        return intro_course, courses_to_delete
        
    except Exception as e:
        print(f"❌ Error identifying courses: {str(e)}")
        return None, Course.objects.none()

def perform_cleanup(courses_to_delete):
    """Delete the specified courses"""
    print("🗑️ PERFORMING CLEANUP")
    print("=" * 50)
    
    if not courses_to_delete.exists():
        print("✅ No courses to delete")
        return True
    
    try:
        deleted_count = 0
        
        for course in courses_to_delete:
            print(f"   Deleting: {course.title} (ID: {course.id})")
            
            # Get counts before deletion for reporting
            module_count = course.modules.count()
            lesson_count = sum(module.lessons.count() for module in course.modules.all())
            enrollment_count = course.enrollments.count()
            
            # Delete course (CASCADE will handle related objects)
            course.delete()
            
            print(f"   ✅ Deleted: {module_count} modules, {lesson_count} lessons, {enrollment_count} enrollments")
            deleted_count += 1
        
        print(f"\n✅ CLEANUP COMPLETED")
        print(f"   Total courses deleted: {deleted_count}")
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")
        return False

def verify_cleanup(intro_course):
    """Verify cleanup was successful"""
    print("\n✅ VERIFYING CLEANUP")
    print("=" * 50)
    
    try:
        from courses.models import Course
        
        remaining_courses = Course.objects.all()
        
        if remaining_courses.count() == 1:
            remaining_course = remaining_courses.first()
            if remaining_course.id == intro_course.id:
                print(f"✅ SUCCESS: Only intro course remains")
                print(f"   Title: {remaining_course.title}")
                print(f"   Modules: {remaining_course.modules.count()}")
                
                lesson_count = sum(module.lessons.count() for module in remaining_course.modules.all())
                print(f"   Lessons: {lesson_count}")
                
                return True
            else:
                print(f"❌ Wrong course remaining: {remaining_course.title}")
                return False
        elif remaining_courses.count() == 0:
            print(f"❌ No courses remaining - intro course was deleted!")
            return False
        else:
            print(f"❌ Multiple courses remaining: {remaining_courses.count()}")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def create_superuser():
    """Create superuser if needed"""
    print("\n👤 CHECKING ADMIN ACCESS")
    print("=" * 50)
    
    try:
        from django.contrib.auth.models import User
        
        superusers = User.objects.filter(is_superuser=True)
        
        if superusers.exists():
            print(f"✅ Found {superusers.count()} superuser(s)")
            for user in superusers:
                print(f"   - {user.username}")
        else:
            print("⚠️ No superusers found. Creating admin user...")
            
            admin_user = User.objects.create_superuser(
                username='yitpadmin',
                email='admin@youthimpactglobal.com',
                password='YITPAdmin2025!'
            )
            
            print(f"✅ Created superuser: {admin_user.username}")
            print(f"   Password: YITPAdmin2025!")
            
    except Exception as e:
        print(f"❌ Error with superuser: {str(e)}")

def main():
    """Main cleanup function"""
    print("🧹 YITP DEVELOPMENT DATABASE CLEANUP")
    print("=" * 60)
    print("This will remove all courses except 'Introduction to YITP'")
    print("from the development database.")
    print()
    
    # Confirmation
    confirm = input("Continue with cleanup? (y/n): ").lower().strip()
    if confirm != 'y':
        print("❌ Cleanup cancelled")
        return
    
    # Step 1: Create backup
    backup_file = create_backup()
    if not backup_file:
        print("❌ Cannot proceed without backup")
        return
    
    # Step 2: Identify courses
    intro_course, courses_to_delete = identify_courses()
    if not intro_course:
        print("❌ Cannot proceed without intro course")
        return
    
    # Step 3: Final confirmation if there are courses to delete
    if courses_to_delete.exists():
        print(f"\n⚠️ FINAL CONFIRMATION")
        print(f"This will delete {courses_to_delete.count()} courses permanently.")
        final_confirm = input("Type 'DELETE' to confirm: ").strip()
        if final_confirm != 'DELETE':
            print("❌ Cleanup cancelled")
            return
    
    # Step 4: Perform cleanup
    success = perform_cleanup(courses_to_delete)
    if not success:
        print("❌ Cleanup failed")
        return
    
    # Step 5: Verify results
    verified = verify_cleanup(intro_course)
    if not verified:
        print("❌ Verification failed")
        return
    
    # Step 6: Ensure admin access
    create_superuser()
    
    # Final report
    print(f"\n🎉 DEVELOPMENT CLEANUP COMPLETED!")
    print("=" * 60)
    print(f"✅ Only 'Introduction to YITP' course remains")
    print(f"✅ Database backup: {backup_file}")
    print(f"✅ Admin access verified")
    print()
    print("📋 NEXT STEPS:")
    print("   • Test the remaining course functionality")
    print("   • Access admin panel to verify data")
    print("   • Keep backup file for emergency recovery")
    print()
    print("🔗 ADMIN ACCESS:")
    print("   URL: http://127.0.0.1:8000/admin/")
    print("   Username: yitpadmin")
    print("   Password: YITPAdmin2025!")

if __name__ == '__main__':
    main()
