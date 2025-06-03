#!/usr/bin/env python
"""
YITP Final Case Sensitivity Fix Test
This script tests if all import issues are resolved.

Usage:
    python test_final_fix.py
"""

import os
import sys
import django

def test_django_setup():
    """Test Django setup with the fixed configuration."""
    print("🔧 Testing Django Setup with Fixed Configuration")
    print("=" * 60)
    
    try:
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
        
        print("🔍 Setting up Django...")
        django.setup()
        print("✅ Django setup successful")
        
        from django.conf import settings
        
        # Check INSTALLED_APPS
        print("\n📋 Checking INSTALLED_APPS:")
        blog_apps = [app for app in settings.INSTALLED_APPS if 'blog' in app.lower()]
        for app in blog_apps:
            print(f"  ✅ {app}")
        
        # Test app registry
        from django.apps import apps
        
        print("\n🔍 Testing app registry:")
        try:
            app_config = apps.get_app_config('blogapp')
            print(f"  ✅ blogapp found in app registry")
            print(f"  📍 App name: {app_config.name}")
            print(f"  📍 App label: {app_config.label}")
            print(f"  📍 App verbose name: {app_config.verbose_name}")
        except Exception as e:
            print(f"  ❌ blogapp not found in app registry: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_imports():
    """Test model imports from blogapp."""
    print("\n📊 Testing Model Imports from blogapp")
    print("=" * 60)

    try:
        print("🔍 Importing models from blogapp...")
        from blogapp.models import Post, Category, Comment, StaticContent

        print("✅ All models imported successfully:")
        print(f"  📍 Post: {Post}")
        print(f"  📍 Category: {Category}")
        print(f"  📍 Comment: {Comment}")
        print(f"  📍 StaticContent: {StaticContent}")

        return True

    except ImportError as e:
        print(f"❌ Model import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Model import error: {e}")
        return False

def test_admin_imports():
    """Test admin imports (this was the failing point)."""
    print("\n👨‍💼 Testing Admin Imports")
    print("=" * 60)

    try:
        print("🔍 Importing admin from blogapp...")
        import blogapp.admin

        print("✅ Admin module imported successfully")
        print(f"  📍 Admin module: {blogapp.admin}")

        # Check if admin classes are properly defined
        admin_classes = [attr for attr in dir(blogapp.admin) if attr.endswith('Admin')]
        print(f"  📋 Admin classes found: {admin_classes}")

        return True

    except ImportError as e:
        print(f"❌ Admin import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Admin import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_url_imports():
    """Test URL imports from blogapp."""
    print("\n🔗 Testing URL Imports")
    print("=" * 60)

    try:
        print("🔍 Importing URLs from blogapp...")
        import blogapp.urls

        print("✅ URL module imported successfully")
        print(f"  📍 URL module: {blogapp.urls}")
        print(f"  📍 App name: {blogapp.urls.app_name}")
        print(f"  📍 URL patterns: {len(blogapp.urls.urlpatterns)} patterns")

        return True

    except ImportError as e:
        print(f"❌ URL import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ URL import error: {e}")
        return False

def test_views_imports():
    """Test view imports from blogapp."""
    print("\n👁️  Testing View Imports")
    print("=" * 60)

    try:
        print("🔍 Importing views from blogapp...")
        import blogapp.views

        print("✅ Views module imported successfully")
        print(f"  📍 Views module: {blogapp.views}")

        # Check for view functions
        view_functions = [attr for attr in dir(blogapp.views) if not attr.startswith('_') and callable(getattr(blogapp.views, attr))]
        print(f"  📋 View functions found: {view_functions}")

        return True

    except ImportError as e:
        print(f"❌ Views import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Views import error: {e}")
        return False

def test_django_check():
    """Test Django's check command."""
    print("\n🔧 Testing Django Check Command")
    print("=" * 60)
    
    try:
        from django.core.management import execute_from_command_line
        
        print("🔍 Running Django check...")
        # Capture the check command output
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            try:
                execute_from_command_line(['manage.py', 'check'])
                check_output = f.getvalue()
                
                if 'System check identified no issues' in check_output or not check_output.strip():
                    print("✅ Django check passed - no issues found")
                    return True
                else:
                    print(f"⚠️  Django check output: {check_output}")
                    return True  # Still consider it a pass if no errors
                    
            except SystemExit as e:
                if e.code == 0:
                    print("✅ Django check completed successfully")
                    return True
                else:
                    print(f"❌ Django check failed with exit code: {e.code}")
                    print(f"Output: {f.getvalue()}")
                    return False
        
    except Exception as e:
        print(f"❌ Django check error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🔍 YITP Final Case Sensitivity Fix Test")
    print("=" * 60)
    print("Testing all blogApp imports and Django configuration.\n")
    
    tests = [
        ("Django Setup", test_django_setup),
        ("Model Imports", test_model_imports),
        ("Admin Imports", test_admin_imports),
        ("URL Imports", test_url_imports),
        ("View Imports", test_views_imports),
        ("Django Check", test_django_check),
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
    print("\n" + "=" * 60)
    print("📊 FINAL FIX TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    success_rate = passed / len(results)
    print(f"\n🎯 Overall Success Rate: {success_rate:.1%} ({passed}/{len(results)})")
    
    if success_rate == 1.0:
        print("🎉 ALL TESTS PASSED!")
        print("🚀 Ready for deployment to Render!")
        print("\nNext steps:")
        print("1. git add .")
        print("2. git commit -m 'Fix final import issue in blogApp/admin.py'")
        print("3. git push origin deployment")
        print("4. Deploy to Render")
    else:
        print("⚠️  Some tests failed!")
        print("🔧 Please review the failed tests above.")
    
    return success_rate == 1.0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
