#!/usr/bin/env python
"""
YITP Case Sensitivity Test Script
This script tests the blogapp directory and import consistency.

Usage:
    python test_case_sensitivity.py
"""

import os
import sys
import django

def test_directory_existence():
    """Test which directory actually exists."""
    print("🔍 Testing Directory Existence")
    print("=" * 50)
    
    directories_to_check = ['blogapp']
    
    for directory in directories_to_check:
        if os.path.exists(directory):
            print(f"✅ {directory} directory exists")
            
            # Check contents
            try:
                contents = os.listdir(directory)
                print(f"   📋 Contents: {contents}")
                
                # Check for key files
                key_files = ['__init__.py', 'apps.py', 'models.py', 'views.py', 'urls.py']
                for file in key_files:
                    file_path = os.path.join(directory, file)
                    if os.path.exists(file_path):
                        print(f"   ✅ {file}")
                    else:
                        print(f"   ❌ {file}")
                        
            except Exception as e:
                print(f"   ❌ Error reading directory: {e}")
        else:
            print(f"❌ {directory} directory does not exist")
    
    return True

def test_python_imports():
    """Test Python imports for different case variations."""
    print("\n🐍 Testing Python Imports")
    print("=" * 50)
    
    # Add current directory to Python path
    sys.path.insert(0, os.getcwd())
    
    import_tests = [
        ('blogapp', 'import blogapp'),
    ]

    for app_name, import_statement in import_tests:
        print(f"\n🔍 Testing: {import_statement}")
        try:
            if app_name == 'blogapp':
                import blogapp
                print(f"   ✅ {app_name} imported successfully")
                print(f"   📍 Location: {blogapp.__file__}")

        except ImportError as e:
            print(f"   ❌ {app_name} import failed: {e}")
        except Exception as e:
            print(f"   ❌ {app_name} import error: {e}")

def test_django_configuration():
    """Test Django configuration with different app names."""
    print("\n⚙️  Testing Django Configuration")
    print("=" * 50)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    
    try:
        django.setup()
        print("✅ Django setup successful")
        
        from django.conf import settings
        
        print("\n📋 Current INSTALLED_APPS:")
        for i, app in enumerate(settings.INSTALLED_APPS, 1):
            print(f"  {i:2d}. {app}")
        
        # Check for blog app variations
        blog_apps_found = []
        for app in settings.INSTALLED_APPS:
            if 'blog' in app.lower():
                blog_apps_found.append(app)
        
        print(f"\n🔍 Blog apps found in INSTALLED_APPS: {blog_apps_found}")
        
        # Test Django's app registry
        from django.apps import apps
        
        print("\n🔍 Testing Django app registry:")
        try:
            if 'blogapp' in [app.lower() for app in settings.INSTALLED_APPS]:
                app_config = apps.get_app_config('blogapp')
                print(f"   ✅ blogapp found in app registry")
                print(f"   📍 App config: {app_config}")
                print(f"   📍 App name: {app_config.name}")
                print(f"   📍 App label: {app_config.label}")
        except Exception as e:
            print(f"   ❌ blogapp not found in app registry: {e}")
            
        # Only test blogapp since we've standardized on lowercase
        
        return True
        
    except Exception as e:
        print(f"❌ Django configuration error: {e}")
        return False

def test_model_imports():
    """Test model imports from the blog app."""
    print("\n📊 Testing Model Imports")
    print("=" * 50)
    
    model_import_tests = [
        ('from blogapp.models import Post, Category, Comment', 'blogapp'),
    ]

    for import_statement, app_name in model_import_tests:
        print(f"\n🔍 Testing: {import_statement}")
        try:
            if app_name == 'blogapp':
                from blogapp.models import Post, Category, Comment
                print(f"   ✅ Models imported from {app_name}")
                print(f"   📍 Post model: {Post}")
                print(f"   📍 Category model: {Category}")
                print(f"   📍 Comment model: {Comment}")

        except ImportError as e:
            print(f"   ❌ Model import from {app_name} failed: {e}")
        except Exception as e:
            print(f"   ❌ Model import error from {app_name}: {e}")

def main():
    """Main test function."""
    print("🔍 YITP Case Sensitivity Test")
    print("=" * 50)
    print("Testing blogapp directory and import consistency.\n")
    
    tests = [
        ("Directory Existence", test_directory_existence),
        ("Python Imports", test_python_imports),
        ("Django Configuration", test_django_configuration),
        ("Model Imports", test_model_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"🚨 Error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 CASE SENSITIVITY TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        if result is not None:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        else:
            print(f"ℹ️  INFO {test_name}")
    
    print(f"\n🎯 Tests Passed: {passed}/{len([r for r in results if r[1] is not None])}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("=" * 50)
    
    if os.path.exists('blogapp'):
        print("📁 Local directory is 'blogapp' (lowercase)")
        print("✅ Configuration uses consistent lowercase naming")
        print("✅ All imports and references use 'blogapp'")
    else:
        print("❌ No blogapp directory found!")
        print("🔧 Expected directory: blogapp (lowercase)")
    
    return True

if __name__ == "__main__":
    main()
