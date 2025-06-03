#!/usr/bin/env python
"""
Test script to verify database connection using environment variables.
Run this script to test your database configuration before deploying.

Usage:
    python test_db_connection.py
"""

import os
import sys
import django
from django.conf import settings
from django.db import connection
from django.core.management import execute_from_command_line

def test_database_connection():
    """Test the database connection using current Django settings."""
    
    print("🔍 Testing YITP Database Connection...")
    print("=" * 50)
    
    # Display current database configuration
    db_config = settings.DATABASES['default']
    print(f"📊 Database Engine: {db_config['ENGINE']}")
    print(f"🏠 Database Host: {db_config['HOST']}")
    print(f"🔌 Database Port: {db_config['PORT']}")
    print(f"📁 Database Name: {db_config['NAME']}")
    print(f"👤 Database User: {db_config['USER']}")
    print(f"🔐 Password: {'*' * len(db_config['PASSWORD'])}")
    print("=" * 50)
    
    try:
        # Test the connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Database connection successful!")
            print(f"📋 PostgreSQL Version: {version}")
            
            # Test if we can query Django tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'django_%'
                LIMIT 5;
            """)
            tables = cursor.fetchall()
            
            if tables:
                print(f"📊 Found {len(tables)} Django tables:")
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("⚠️  No Django tables found. You may need to run migrations.")
                
    except Exception as e:
        print(f"❌ Database connection failed!")
        print(f"🚨 Error: {str(e)}")
        return False
        
    print("=" * 50)
    print("🎉 Database test completed successfully!")
    return True

def check_environment_variables():
    """Check if required environment variables are set."""
    
    print("🔍 Checking Environment Variables...")
    print("=" * 50)
    
    required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    optional_vars = ['DATABASE_URL', 'DEBUG', 'SECRET_KEY']
    
    print("📋 Required Database Variables:")
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            display_value = value if var != 'DB_PASSWORD' else '*' * len(value)
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")
            all_set = False
    
    print("\n📋 Optional Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            display_value = value if var not in ['SECRET_KEY', 'DATABASE_URL'] else f"{'*' * 10}..."
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ⚪ {var}: Not set (using defaults)")
    
    print("=" * 50)
    return all_set

if __name__ == "__main__":
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    django.setup()
    
    print("🚀 YITP Database Connection Test")
    print("=" * 50)
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    if not env_ok:
        print("⚠️  Some required environment variables are missing.")
        print("💡 Make sure to set all database environment variables before testing.")
        print("📝 Check the .env.example file for reference.")
        sys.exit(1)
    
    # Test database connection
    if test_database_connection():
        print("🎯 Ready for deployment!")
        sys.exit(0)
    else:
        print("🚨 Database connection failed. Please check your configuration.")
        sys.exit(1)
