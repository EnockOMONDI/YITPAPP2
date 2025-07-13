#!/usr/bin/env python
"""
Migration script to export development data and import to production database
"""
import os
import sys
import django
import json
from datetime import datetime

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from users.models import InstructorProfile, Profile
from courses.models import Course
from progress.models import Enrollment

def export_development_data():
    """Export development database data to JSON fixtures"""
    print("🔄 Exporting development database data...")
    
    # Create exports directory
    exports_dir = 'data_exports'
    os.makedirs(exports_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Export core data
    fixtures = [
        ('auth.User', 'users'),
        ('users.Profile', 'profiles'),
        ('users.InstructorProfile', 'instructor_profiles'),
        ('courses.Course', 'courses'),
        ('progress.Enrollment', 'enrollments'),
        ('contenttypes.ContentType', 'contenttypes'),
        ('auth.Permission', 'permissions'),
    ]
    
    exported_files = []
    
    for model, filename in fixtures:
        try:
            output_file = f'{exports_dir}/{filename}_{timestamp}.json'
            call_command('dumpdata', model, '--output', output_file, '--indent', 2)
            exported_files.append(output_file)
            print(f"✅ Exported {model} to {output_file}")
        except Exception as e:
            print(f"❌ Error exporting {model}: {e}")
    
    return exported_files

def verify_test_instructor():
    """Verify test instructor exists in current database"""
    try:
        test_instructor = User.objects.get(email='yayek37675@simerm.com')
        instructor_profile = test_instructor.instructor_profile
        
        print(f"✅ Test Instructor Verified:")
        print(f"   Username: {test_instructor.username}")
        print(f"   Email: {test_instructor.email}")
        print(f"   Full Name: {test_instructor.get_full_name()}")
        print(f"   Role: {instructor_profile.instructor_role}")
        print(f"   Verification: {instructor_profile.verification_status}")
        print(f"   Active: {instructor_profile.is_active}")
        
        return True
    except User.DoesNotExist:
        print("❌ Test instructor not found in current database")
        return False
    except Exception as e:
        print(f"❌ Error verifying test instructor: {e}")
        return False

def switch_to_production():
    """Switch to production environment"""
    print("🔄 Switching to production environment...")
    os.environ['DJANGO_ENV'] = 'production'
    
    # Reload Django settings
    from django.conf import settings
    settings._wrapped = None
    django.setup()
    
    print("✅ Switched to production environment")

def migrate_production_database():
    """Run migrations on production database"""
    print("🔄 Running migrations on production database...")
    try:
        call_command('migrate', '--verbosity=2')
        print("✅ Production database migrations completed")
        return True
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def import_data_to_production(exported_files):
    """Import data to production database"""
    print("🔄 Importing data to production database...")
    
    # Import in correct order to handle dependencies
    import_order = [
        'contenttypes',
        'permissions', 
        'users',
        'profiles',
        'instructor_profiles',
        'courses',
        'enrollments',
    ]
    
    for prefix in import_order:
        matching_files = [f for f in exported_files if prefix in f]
        for file_path in matching_files:
            try:
                call_command('loaddata', file_path, '--verbosity=2')
                print(f"✅ Imported {file_path}")
            except Exception as e:
                print(f"❌ Error importing {file_path}: {e}")

def verify_production_data():
    """Verify data was imported correctly to production"""
    print("🔄 Verifying production database data...")
    
    try:
        user_count = User.objects.count()
        instructor_count = InstructorProfile.objects.count()
        
        print(f"✅ Production Database Stats:")
        print(f"   Total Users: {user_count}")
        print(f"   Total Instructor Profiles: {instructor_count}")
        
        # Verify test instructor
        test_instructor = User.objects.get(email='yayek37675@simerm.com')
        instructor_profile = test_instructor.instructor_profile
        
        print(f"✅ Test Instructor in Production:")
        print(f"   Username: {test_instructor.username}")
        print(f"   Email: {test_instructor.email}")
        print(f"   Role: {instructor_profile.instructor_role}")
        print(f"   Verification: {instructor_profile.verification_status}")
        
        return True
    except Exception as e:
        print(f"❌ Error verifying production data: {e}")
        return False

def main():
    """Main migration process"""
    print("=" * 60)
    print("🚀 YITP LMS DATABASE MIGRATION TO PRODUCTION")
    print("=" * 60)
    
    # Step 1: Verify test instructor in development
    if not verify_test_instructor():
        print("❌ Migration aborted: Test instructor not found")
        return False
    
    # Step 2: Export development data
    exported_files = export_development_data()
    if not exported_files:
        print("❌ Migration aborted: No data exported")
        return False
    
    # Step 3: Switch to production environment
    switch_to_production()
    
    # Step 4: Run migrations on production
    if not migrate_production_database():
        print("❌ Migration aborted: Production migrations failed")
        return False
    
    # Step 5: Import data to production
    import_data_to_production(exported_files)
    
    # Step 6: Verify production data
    if verify_production_data():
        print("✅ Migration completed successfully!")
        return True
    else:
        print("❌ Migration completed with errors")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
