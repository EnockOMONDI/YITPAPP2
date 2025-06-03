#!/usr/bin/env python
"""
Script to check what tables exist in the database
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.db import connection

def check_database_tables():
    """Check what tables exist in the database."""
    print("🔍 Checking Database Tables")
    print("=" * 50)
    
    with connection.cursor() as cursor:
        # Get all table names
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        all_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Total tables in database: {len(all_tables)}")
        print("\n🔍 All tables:")
        for table in all_tables:
            print(f"  - {table}")
        
        # Check specifically for users app tables
        users_tables = [table for table in all_tables if table.startswith('users_')]
        print(f"\n👥 Users app tables ({len(users_tables)}):")
        for table in users_tables:
            print(f"  - {table}")
        
        # Check migration table
        cursor.execute("""
            SELECT app, name, applied 
            FROM django_migrations 
            WHERE app = 'users'
            ORDER BY applied;
        """)
        
        migrations = cursor.fetchall()
        print(f"\n📊 Users app migrations in django_migrations table:")
        if migrations:
            for app, name, applied in migrations:
                print(f"  - {app}.{name} (applied: {applied})")
        else:
            print("  - No users app migrations found in django_migrations table")
        
        return users_tables, migrations

if __name__ == "__main__":
    check_database_tables()
