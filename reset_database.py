#!/usr/bin/env python
"""
YITP Database Reset Script for Neon PostgreSQL
This script will drop all existing tables and create fresh migrations.

IMPORTANT: This will delete ALL data in the database!
Only use this for deployment troubleshooting.

Usage:
    python reset_database.py [--confirm]
    
Example:
    python reset_database.py --confirm
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import django
from django.core.management import execute_from_command_line

def get_database_config():
    """Get database configuration from environment variables."""
    return {
        'host': os.getenv('DB_HOST', 'ep-cool-term-ab9d4hh0-pooler.eu-west-2.aws.neon.tech'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'YITPDB'),
        'user': os.getenv('DB_USER', 'YITPDB_owner'),
        'password': os.getenv('DB_PASSWORD', 'npg_n0zFeVa6SCxm'),
        'sslmode': 'require'
    }

def connect_to_database():
    """Connect to the Neon PostgreSQL database."""
    config = get_database_config()
    
    try:
        connection = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            sslmode=config['sslmode']
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return connection
    except Exception as e:
        print(f"❌ Failed to connect to database: {str(e)}")
        return None

def get_all_tables(connection):
    """Get all tables in the database."""
    cursor = connection.cursor()
    cursor.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def drop_all_tables(connection):
    """Drop all tables in the database."""
    print("🗑️  Dropping all existing tables...")
    
    tables = get_all_tables(connection)
    
    if not tables:
        print("   ✅ No tables found to drop")
        return True
    
    cursor = connection.cursor()
    
    try:
        # Disable foreign key checks temporarily
        cursor.execute("SET session_replication_role = replica;")
        
        # Drop all tables
        for table in tables:
            print(f"   🗑️  Dropping table: {table}")
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        
        # Re-enable foreign key checks
        cursor.execute("SET session_replication_role = DEFAULT;")
        
        print(f"   ✅ Successfully dropped {len(tables)} tables")
        return True
        
    except Exception as e:
        print(f"   ❌ Error dropping tables: {str(e)}")
        return False
    finally:
        cursor.close()

def reset_django_migrations():
    """Reset Django migrations."""
    print("\n🔄 Resetting Django migrations...")
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    django.setup()
    
    from django.conf import settings
    
    # Get all Django apps
    django_apps = []
    for app in settings.INSTALLED_APPS:
        if not app.startswith('django.') and '.' in app:
            app_name = app.split('.')[0]
            if os.path.exists(app_name):
                django_apps.append(app_name)
        elif not app.startswith('django.') and os.path.exists(app):
            django_apps.append(app)
    
    print(f"   📋 Found Django apps: {', '.join(django_apps)}")
    
    # Remove existing migration files (except __init__.py)
    for app in django_apps:
        migrations_dir = os.path.join(app, 'migrations')
        if os.path.exists(migrations_dir):
            print(f"   🧹 Cleaning migrations for {app}")
            for file in os.listdir(migrations_dir):
                if file.endswith('.py') and file != '__init__.py':
                    file_path = os.path.join(migrations_dir, file)
                    os.remove(file_path)
                    print(f"     - Removed {file}")
    
    return True

def create_fresh_migrations():
    """Create fresh Django migrations."""
    print("\n📝 Creating fresh migrations...")
    
    try:
        # Create new migrations
        print("   📝 Running makemigrations...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        # Apply migrations
        print("   🔧 Running migrate...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("   ✅ Fresh migrations created and applied successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating migrations: {str(e)}")
        return False

def create_superuser():
    """Create a superuser account."""
    print("\n👤 Creating superuser account...")
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(is_superuser=True).exists():
            print("   📝 No superuser found. Creating default superuser...")
            print("   📧 Username: admin")
            print("   📧 Email: admin@youthimpactglobal.com")
            print("   🔐 Password: yitp2024admin")
            
            User.objects.create_superuser(
                username='admin',
                email='admin@youthimpactglobal.com',
                password='yitp2024admin'
            )
            print("   ✅ Superuser created successfully")
        else:
            print("   ✅ Superuser already exists")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating superuser: {str(e)}")
        return False

def main():
    """Main reset function."""
    print("🔄 YITP Database Reset Script")
    print("=" * 50)
    print("⚠️  WARNING: This will delete ALL data in the database!")
    print("=" * 50)
    
    # Check for confirmation
    if '--confirm' not in sys.argv:
        print("❌ This script requires --confirm flag to proceed")
        print("💡 Usage: python reset_database.py --confirm")
        sys.exit(1)
    
    # Display database configuration
    config = get_database_config()
    print(f"🗄️  Database: {config['database']}")
    print(f"🏠 Host: {config['host']}")
    print(f"👤 User: {config['user']}")
    print("=" * 50)
    
    # Connect to database
    print("🔌 Connecting to database...")
    connection = connect_to_database()
    if not connection:
        sys.exit(1)
    
    print("✅ Connected to database successfully")
    
    # Reset process
    steps = [
        ("Drop All Tables", lambda: drop_all_tables(connection)),
        ("Reset Django Migrations", reset_django_migrations),
        ("Create Fresh Migrations", create_fresh_migrations),
        ("Create Superuser", create_superuser),
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        if step_func():
            success_count += 1
        else:
            print(f"❌ {step_name} failed!")
            break
    
    # Close database connection
    connection.close()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DATABASE RESET SUMMARY")
    print("=" * 50)
    
    if success_count == len(steps):
        print("🎉 Database reset completed successfully!")
        print("✅ All tables dropped and recreated")
        print("✅ Fresh migrations applied")
        print("✅ Superuser account created")
        print("\n🚀 Ready for deployment!")
        sys.exit(0)
    else:
        print(f"⚠️  Database reset partially completed ({success_count}/{len(steps)})")
        print("🔧 Please review the errors and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()
