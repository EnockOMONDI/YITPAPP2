#!/usr/bin/env python
"""
Script to fix Django migration conflict for users app
This script will mark the users.0001_initial migration as applied without running it
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line

def fix_migration_conflict():
    """Fix the migration conflict by marking users.0001_initial as applied."""
    print("🔧 Fixing Django Migration Conflict")
    print("=" * 50)
    
    # Step 1: Verify the tables exist
    print("\n📋 Step 1: Verifying existing tables...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE 'users_%'
            ORDER BY table_name;
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Found {len(existing_tables)} users app tables:")
        for table in existing_tables:
            print(f"  - {table}")
    
    # Step 2: Check current migration status
    print("\n📊 Step 2: Checking current migration status...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT app, name 
            FROM django_migrations 
            WHERE app = 'users'
            ORDER BY applied;
        """)
        
        applied_migrations = cursor.fetchall()
        if applied_migrations:
            print("✅ Found applied users migrations:")
            for app, name in applied_migrations:
                print(f"  - {app}.{name}")
        else:
            print("❌ No users migrations found in django_migrations table")
    
    # Step 3: Mark the migration as fake applied
    print("\n🔧 Step 3: Marking users.0001_initial as applied...")
    try:
        # Use Django's migrate command with --fake flag
        print("Running: python manage.py migrate users 0001 --fake")
        execute_from_command_line(['manage.py', 'migrate', 'users', '0001', '--fake'])
        print("✅ Successfully marked users.0001_initial as applied")
    except Exception as e:
        print(f"❌ Error marking migration as applied: {e}")
        return False
    
    # Step 4: Verify the fix
    print("\n✅ Step 4: Verifying the fix...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT app, name, applied 
            FROM django_migrations 
            WHERE app = 'users'
            ORDER BY applied;
        """)
        
        migrations_after = cursor.fetchall()
        if migrations_after:
            print("✅ Users migrations after fix:")
            for app, name, applied in migrations_after:
                print(f"  - {app}.{name} (applied: {applied})")
        else:
            print("❌ Still no users migrations found")
            return False
    
    print("\n🎉 Migration conflict fixed successfully!")
    print("You can now run 'python manage.py migrate' without errors.")
    return True

if __name__ == "__main__":
    success = fix_migration_conflict()
    if not success:
        sys.exit(1)
