#!/usr/bin/env python
"""
YITP Repository Verification Script
This script verifies the repository structure and helps identify discrepancies
between local and remote repository content.

Usage:
    python verify_repository.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(command, capture_output=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=capture_output, 
            text=True,
            cwd=os.getcwd()
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_git_status():
    """Check git repository status."""
    print("🔍 Git Repository Status")
    print("=" * 50)
    
    # Check if we're in a git repository
    success, output, error = run_command("git rev-parse --is-inside-work-tree")
    if not success:
        print("❌ Not in a git repository")
        return False
    
    print("✅ In a git repository")
    
    # Get current branch
    success, branch, error = run_command("git branch --show-current")
    if success:
        print(f"📍 Current branch: {branch}")
    else:
        print(f"❌ Could not determine current branch: {error}")
    
    # Check git status
    success, status, error = run_command("git status --porcelain")
    if success:
        if status:
            print("⚠️  Uncommitted changes:")
            for line in status.split('\n'):
                print(f"  {line}")
        else:
            print("✅ No uncommitted changes")
    
    # Check remote URL
    success, remote, error = run_command("git remote get-url origin")
    if success:
        print(f"🌐 Remote URL: {remote}")
    
    # Get last commit
    success, commit, error = run_command("git log -1 --oneline")
    if success:
        print(f"📝 Last commit: {commit}")
    
    return True

def check_directory_structure():
    """Check the current directory structure."""
    print("\n📁 Directory Structure Analysis")
    print("=" * 50)
    
    current_dir = os.getcwd()
    print(f"📍 Current directory: {current_dir}")
    
    # Check for Django project files
    django_files = ['manage.py', 'requirements.txt', 'render.yaml']
    print("\n🔍 Django project files:")
    for file in django_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file}")
    
    # Check for Django apps
    potential_apps = []
    for item in os.listdir('.'):
        if os.path.isdir(item) and not item.startswith('.'):
            # Check if it's a Django app (has __init__.py)
            if os.path.exists(os.path.join(item, '__init__.py')):
                potential_apps.append(item)
    
    print(f"\n🔍 Potential Django apps found: {len(potential_apps)}")
    for app in sorted(potential_apps):
        print(f"  📁 {app}/")
        
        # Check for Django app files
        app_files = ['__init__.py', 'apps.py', 'models.py', 'views.py', 'urls.py', 'admin.py']
        for file in app_files:
            file_path = os.path.join(app, file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"    ✅ {file} ({size} bytes)")
            else:
                print(f"    ❌ {file}")
    
    return potential_apps

def check_blogapp_specifically():
    """Detailed check of the blogapp directory."""
    print("\n🔍 Detailed blogapp Analysis")
    print("=" * 50)
    
    if not os.path.exists('blogapp'):
        print("❌ blogapp directory does not exist")
        return False
    
    print("✅ blogapp directory exists")
    
    # Check directory permissions
    blogapp_path = Path('blogapp')
    print(f"📍 blogapp path: {blogapp_path.absolute()}")
    print(f"🔐 Directory permissions: {oct(blogapp_path.stat().st_mode)[-3:]}")
    
    # List all files in blogapp
    print("\n📋 blogapp directory contents:")
    for item in sorted(os.listdir('blogapp')):
        item_path = os.path.join('blogapp', item)
        if os.path.isfile(item_path):
            size = os.path.getsize(item_path)
            print(f"  📄 {item} ({size} bytes)")
        else:
            print(f"  📁 {item}/")
    
    # Check critical files
    critical_files = {
        '__init__.py': 'Python package marker',
        'apps.py': 'Django app configuration',
        'models.py': 'Database models',
        'views.py': 'View functions',
        'urls.py': 'URL patterns',
        'admin.py': 'Admin configuration'
    }
    
    print("\n🔍 Critical file analysis:")
    for file, description in critical_files.items():
        file_path = os.path.join('blogapp', file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✅ {file} ({description}) - {size} bytes")
            
            # Check if file is readable
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    lines = len(content.split('\n'))
                    print(f"    📊 {lines} lines, readable")
                    
                    # Check for syntax errors in Python files
                    if file.endswith('.py'):
                        try:
                            compile(content, file_path, 'exec')
                            print(f"    ✅ Valid Python syntax")
                        except SyntaxError as e:
                            print(f"    ❌ Syntax error: {e}")
                            
            except Exception as e:
                print(f"    ❌ Cannot read file: {e}")
        else:
            print(f"  ❌ {file} ({description}) - MISSING")
    
    return True

def check_python_import():
    """Test Python import of blogapp."""
    print("\n🐍 Python Import Test")
    print("=" * 50)
    
    # Add current directory to Python path
    sys.path.insert(0, os.getcwd())
    
    print(f"📍 Current working directory: {os.getcwd()}")
    print(f"🛤️  Python path (first 3): {sys.path[:3]}")
    
    try:
        print("🔍 Attempting to import blogapp...")
        import blogapp
        print(f"✅ blogapp imported successfully")
        print(f"📍 Module location: {blogapp.__file__}")
        
        # Check module attributes
        attrs = dir(blogapp)
        print(f"📋 Module attributes: {len(attrs)} items")
        
        # Try importing apps.py
        try:
            print("🔍 Attempting to import blogapp.apps...")
            import blogapp.apps
            print("✅ blogapp.apps imported successfully")
            
            # Try importing BlogappConfig
            try:
                from blogapp.apps import BlogappConfig
                print("✅ BlogappConfig imported successfully")
                print(f"📍 BlogappConfig: {BlogappConfig}")
                print(f"📍 App name: {BlogappConfig.name}")
                print(f"📍 Verbose name: {BlogappConfig.verbose_name}")
            except ImportError as e:
                print(f"❌ Cannot import BlogappConfig: {e}")
                
        except ImportError as e:
            print(f"❌ Cannot import blogapp.apps: {e}")
            
    except ImportError as e:
        print(f"❌ Cannot import blogapp: {e}")
        
        # Additional debugging
        print("\n🔍 Import debugging:")
        print(f"📁 Current directory contents: {os.listdir('.')}")
        
        if os.path.exists('blogapp'):
            print(f"📁 blogapp directory contents: {os.listdir('blogapp')}")
        
        return False
    
    return True

def check_django_settings():
    """Check Django settings configuration."""
    print("\n⚙️  Django Settings Check")
    print("=" * 50)
    
    try:
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
        
        import django
        print(f"✅ Django version: {django.get_version()}")
        
        django.setup()
        
        from django.conf import settings
        
        print("📋 INSTALLED_APPS:")
        for i, app in enumerate(settings.INSTALLED_APPS, 1):
            print(f"  {i:2d}. {app}")
        
        # Check if blogapp is in INSTALLED_APPS
        if 'blogapp' in settings.INSTALLED_APPS:
            print("✅ blogapp found in INSTALLED_APPS")
        elif 'blogapp.apps.BlogappConfig' in settings.INSTALLED_APPS:
            print("✅ blogapp.apps.BlogappConfig found in INSTALLED_APPS")
        else:
            print("❌ blogapp not found in INSTALLED_APPS")
        
        return True
        
    except Exception as e:
        print(f"❌ Django settings error: {e}")
        return False

def main():
    """Main verification function."""
    print("🔍 YITP Repository Verification")
    print("=" * 50)
    print("This script will analyze the repository structure and identify potential issues.\n")
    
    checks = [
        ("Git Repository Status", check_git_status),
        ("Directory Structure", check_directory_structure),
        ("blogapp Analysis", check_blogapp_specifically),
        ("Python Import Test", check_python_import),
        ("Django Settings", check_django_settings),
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
    print("📊 VERIFICATION SUMMARY")
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
        print("🎉 Repository verification SUCCESSFUL!")
        print("🚀 Repository structure appears correct for deployment!")
    else:
        print("⚠️  Repository verification found issues!")
        print("🔧 Please review the failed checks above.")
    
    return success_rate >= 0.8

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
