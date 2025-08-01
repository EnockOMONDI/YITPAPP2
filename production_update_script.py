#!/usr/bin/env python
"""
YITP Production Database Update Script
Handles post-deployment database synchronization and admin account setup
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    django.setup()

def update_admin_password():
    """Update the yiptadmin00 password to admin123"""
    from django.contrib.auth.models import User
    
    try:
        user = User.objects.get(username='yiptadmin00')
        user.set_password('admin123')
        user.save()
        print("✅ SUCCESS: yiptadmin00 password updated to 'admin123'")
        return True
    except User.DoesNotExist:
        print("❌ ERROR: User 'yiptadmin00' not found")
        return False
    except Exception as e:
        print(f"❌ ERROR updating password: {e}")
        return False

def verify_admin_access():
    """Verify admin user can authenticate"""
    from django.contrib.auth import authenticate
    
    try:
        user = authenticate(username='yiptadmin00', password='admin123')
        if user:
            print("✅ SUCCESS: Admin authentication verified")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Is Staff: {user.is_staff}")
            print(f"   Is Superuser: {user.is_superuser}")
            return True
        else:
            print("❌ ERROR: Admin authentication failed")
            return False
    except Exception as e:
        print(f"❌ ERROR during authentication: {e}")
        return False

def verify_dashboard_callback():
    """Verify dashboard callback function is available"""
    try:
        from yitp.admin import dashboard_callback
        print("✅ SUCCESS: dashboard_callback function imported successfully")
        
        # Test the function
        from django.http import HttpRequest
        request = HttpRequest()
        context = {}
        result = dashboard_callback(request, context)
        
        print(f"✅ SUCCESS: Dashboard callback executed successfully")
        print(f"   Context keys: {list(result.keys())}")
        return True
    except ImportError as e:
        print(f"❌ IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def check_database_connection():
    """Check database connection and basic queries"""
    from django.db import connection
    from django.contrib.auth.models import User
    
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Test user count
        user_count = User.objects.count()
        admin_count = User.objects.filter(is_superuser=True).count()
        
        print("✅ SUCCESS: Database connection verified")
        print(f"   Total users: {user_count}")
        print(f"   Admin users: {admin_count}")
        return True
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
        return False

def run_migrations():
    """Run Django migrations"""
    try:
        print("🔄 Running Django migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ SUCCESS: Migrations completed")
        return True
    except Exception as e:
        print(f"❌ MIGRATION ERROR: {e}")
        return False

def collect_static_files():
    """Collect static files"""
    try:
        print("🔄 Collecting static files...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✅ SUCCESS: Static files collected")
        return True
    except Exception as e:
        print(f"❌ STATIC FILES ERROR: {e}")
        return False

def main():
    """Main execution function"""
    print("=" * 60)
    print("🚀 YITP PRODUCTION DATABASE UPDATE SCRIPT")
    print("=" * 60)
    
    # Setup Django
    setup_django()
    
    # Track success/failure
    results = []
    
    # 1. Check database connection
    print("\n1️⃣ CHECKING DATABASE CONNECTION...")
    results.append(("Database Connection", check_database_connection()))
    
    # 2. Run migrations
    print("\n2️⃣ RUNNING MIGRATIONS...")
    results.append(("Migrations", run_migrations()))
    
    # 3. Update admin password
    print("\n3️⃣ UPDATING ADMIN PASSWORD...")
    results.append(("Admin Password Update", update_admin_password()))
    
    # 4. Verify admin access
    print("\n4️⃣ VERIFYING ADMIN ACCESS...")
    results.append(("Admin Authentication", verify_admin_access()))
    
    # 5. Verify dashboard callback
    print("\n5️⃣ VERIFYING DASHBOARD CALLBACK...")
    results.append(("Dashboard Callback", verify_dashboard_callback()))
    
    # 6. Collect static files
    print("\n6️⃣ COLLECTING STATIC FILES...")
    results.append(("Static Files", collect_static_files()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    success_count = 0
    for task, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {task}")
        if success:
            success_count += 1
    
    print(f"\n🎯 OVERALL RESULT: {success_count}/{len(results)} tasks completed successfully")
    
    if success_count == len(results):
        print("\n🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
        print("🌐 Admin URL: https://www.youthimpactglobal.com/admin/")
        print("👤 Username: yiptadmin00")
        print("🔑 Password: admin123")
    else:
        print("\n⚠️  DEPLOYMENT COMPLETED WITH ISSUES")
        print("Please review the failed tasks above and resolve manually.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
