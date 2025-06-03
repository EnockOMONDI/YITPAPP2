#!/usr/bin/env python
"""
YITP Deployment Diagnostic Script
Run this script to diagnose potential deployment issues before deploying to Render.

Usage:
    python diagnose_deployment.py
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python Version...")
    print("=" * 50)
    
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python version may not be compatible (requires 3.8+)")
        return False

def check_requirements():
    """Check if all requirements can be installed."""
    print("\n📦 Checking Requirements...")
    print("=" * 50)
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')
        
        print(f"Found {len(requirements)} requirements:")
        for req in requirements:
            if req.strip() and not req.startswith('#'):
                print(f"  - {req.strip()}")
        
        print("\n🔍 Testing critical imports...")
        critical_packages = [
            ('django', 'Django'),
            ('psycopg2', 'PostgreSQL adapter'),
            ('shortuuid', 'ShortUUID'),
            ('pyuploadcare', 'Uploadcare'),
            ('ckeditor', 'CKEditor'),
        ]
        
        success_count = 0
        for package, description in critical_packages:
            try:
                importlib.import_module(package)
                print(f"  ✅ {package} ({description})")
                success_count += 1
            except ImportError:
                print(f"  ❌ {package} ({description}) - Not installed")
        
        print(f"\n📊 Import Success: {success_count}/{len(critical_packages)}")
        return success_count == len(critical_packages)
        
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False

def check_django_apps():
    """Check Django app configuration."""
    print("\n🔧 Checking Django Apps...")
    print("=" * 50)
    
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    
    try:
        import django
        django.setup()
        
        from django.conf import settings
        
        print("📋 Installed Apps:")
        for app in settings.INSTALLED_APPS:
            print(f"  - {app}")
        
        # Check if apps exist
        print("\n🔍 Verifying App Directories:")
        app_issues = []
        
        for app in settings.INSTALLED_APPS:
            if '.' in app and not app.startswith('django.'):
                app_name = app.split('.')[0]
                if os.path.exists(app_name):
                    print(f"  ✅ {app_name} directory exists")
                    
                    # Check for __init__.py
                    init_file = os.path.join(app_name, '__init__.py')
                    if os.path.exists(init_file):
                        print(f"    ✅ {app_name}/__init__.py exists")
                    else:
                        print(f"    ❌ {app_name}/__init__.py missing")
                        app_issues.append(f"{app_name}/__init__.py missing")
                        
                    # Check for apps.py
                    apps_file = os.path.join(app_name, 'apps.py')
                    if os.path.exists(apps_file):
                        print(f"    ✅ {app_name}/apps.py exists")
                    else:
                        print(f"    ❌ {app_name}/apps.py missing")
                        app_issues.append(f"{app_name}/apps.py missing")
                        
                else:
                    print(f"  ❌ {app_name} directory missing")
                    app_issues.append(f"{app_name} directory missing")
        
        if app_issues:
            print(f"\n🚨 App Issues Found:")
            for issue in app_issues:
                print(f"  - {issue}")
            return False
        else:
            print(f"\n✅ All apps configured correctly")
            return True
            
    except Exception as e:
        print(f"❌ Django setup failed: {str(e)}")
        return False

def check_database_config():
    """Check database configuration."""
    print("\n🗄️  Checking Database Configuration...")
    print("=" * 50)
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
        import django
        django.setup()
        
        from django.conf import settings
        
        db_config = settings.DATABASES['default']
        print(f"Database Engine: {db_config['ENGINE']}")
        print(f"Database Name: {db_config['NAME']}")
        print(f"Database Host: {db_config['HOST']}")
        print(f"Database Port: {db_config['PORT']}")
        print(f"Database User: {db_config['USER']}")
        
        # Check environment variables
        env_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DATABASE_URL']
        print(f"\n🔍 Environment Variables:")
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                display_value = value if var not in ['DB_PASSWORD', 'DATABASE_URL'] else f"{'*' * 10}..."
                print(f"  ✅ {var}: {display_value}")
            else:
                print(f"  ⚪ {var}: Not set (using defaults)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database config check failed: {str(e)}")
        return False

def check_static_files():
    """Check static files configuration."""
    print("\n📁 Checking Static Files Configuration...")
    print("=" * 50)
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
        import django
        django.setup()
        
        from django.conf import settings
        
        print(f"STATIC_URL: {settings.STATIC_URL}")
        print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
        print(f"STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
        
        # Check if static directory exists
        if os.path.exists('static'):
            print("✅ static/ directory exists")
            
            # Check for key static files
            key_files = [
                'static/assets/css/style.css',
                'static/assets/css/messages.css',
                'static/assets/js/main.js',
            ]
            
            for file_path in key_files:
                if os.path.exists(file_path):
                    print(f"  ✅ {file_path} exists")
                else:
                    print(f"  ⚠️  {file_path} missing")
        else:
            print("❌ static/ directory missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Static files check failed: {str(e)}")
        return False

def check_build_script():
    """Check build script."""
    print("\n🔨 Checking Build Script...")
    print("=" * 50)
    
    if os.path.exists('build.sh'):
        print("✅ build.sh exists")
        
        # Check if executable
        if os.access('build.sh', os.X_OK):
            print("✅ build.sh is executable")
        else:
            print("⚠️  build.sh is not executable (may need chmod +x)")
        
        return True
    else:
        print("❌ build.sh missing")
        return False

def main():
    """Main diagnostic function."""
    print("🔍 YITP Deployment Diagnostic")
    print("=" * 50)
    print("This script will check for common deployment issues.\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Requirements", check_requirements),
        ("Django Apps", check_django_apps),
        ("Database Config", check_database_config),
        ("Static Files", check_static_files),
        ("Build Script", check_build_script),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"🚨 Error in {check_name}: {str(e)}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    passed = 0
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if result:
            passed += 1
    
    success_rate = passed / len(results)
    print(f"\n🎯 Overall Success Rate: {success_rate:.1%} ({passed}/{len(results)})")
    
    if success_rate >= 0.8:
        print("🎉 Deployment diagnostic SUCCESSFUL!")
        print("🚀 Ready for deployment to Render!")
    else:
        print("⚠️  Deployment diagnostic found issues!")
        print("🔧 Please fix the failed checks before deploying.")
    
    return success_rate >= 0.8

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
