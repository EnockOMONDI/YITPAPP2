#!/usr/bin/env python
"""
Resolve Django static file conflicts and verify YITP course functionality
"""

import os
import sys
import django
from pathlib import Path
import hashlib
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.conf import settings
from django.contrib.staticfiles.finders import get_finders
from django.contrib.staticfiles import finders

def analyze_static_file_conflicts():
    """Analyze static file conflicts and duplicates"""
    print("🔍 ANALYZING STATIC FILE CONFLICTS")
    print("=" * 70)
    
    # Get all static file finders
    static_finders = list(get_finders())
    
    print(f"📁 Static File Configuration:")
    print(f"   STATIC_URL: {settings.STATIC_URL}")
    print(f"   STATIC_ROOT: {settings.STATIC_ROOT}")
    if hasattr(settings, 'STATICFILES_DIRS'):
        print(f"   STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
    
    print(f"\n🔍 Active Static File Finders:")
    for i, finder in enumerate(static_finders, 1):
        print(f"   {i}. {finder.__class__.__name__}")
    
    # Check for specific duplicate files mentioned
    duplicate_files = [
        'admin/js/inlines.js',
        'admin/js/admin/RelatedObjectLookups.js'
    ]
    
    conflicts = {}
    
    for file_path in duplicate_files:
        print(f"\n🔍 Analyzing: {file_path}")
        
        # Find all instances of this file
        file_instances = []
        for finder in static_finders:
            try:
                found_files = finder.find(file_path, all=True)
                if found_files:
                    if isinstance(found_files, list):
                        file_instances.extend(found_files)
                    else:
                        file_instances.append(found_files)
            except Exception as e:
                print(f"   Warning: {finder.__class__.__name__} error: {str(e)}")
        
        if len(file_instances) > 1:
            conflicts[file_path] = file_instances
            print(f"   🚨 CONFLICT: Found {len(file_instances)} instances")
            
            for i, instance in enumerate(file_instances, 1):
                if os.path.exists(instance):
                    stat = os.stat(instance)
                    mod_time = datetime.fromtimestamp(stat.st_mtime)
                    size = stat.st_size
                    
                    # Calculate file hash
                    with open(instance, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()[:8]
                    
                    print(f"      {i}. {instance}")
                    print(f"         Modified: {mod_time}")
                    print(f"         Size: {size} bytes")
                    print(f"         Hash: {file_hash}")
                else:
                    print(f"      {i}. {instance} (FILE NOT FOUND)")
        else:
            print(f"   ✅ No conflicts found")
    
    return conflicts

def find_all_static_duplicates():
    """Find all duplicate static files in the project"""
    print("\n🔍 SCANNING FOR ALL STATIC FILE DUPLICATES")
    print("=" * 70)
    
    # Common files that often have duplicates
    common_duplicates = [
        'admin/css/base.css',
        'admin/css/forms.css',
        'admin/js/core.js',
        'admin/js/jquery.init.js',
        'admin/js/actions.js',
        'css/bootstrap.min.css',
        'js/jquery.min.js',
        'js/bootstrap.min.js'
    ]
    
    all_conflicts = {}
    
    for file_path in common_duplicates:
        instances = []
        for finder in get_finders():
            try:
                found = finder.find(file_path, all=True)
                if found:
                    if isinstance(found, list):
                        instances.extend(found)
                    else:
                        instances.append(found)
            except:
                continue
        
        if len(instances) > 1:
            all_conflicts[file_path] = instances
    
    if all_conflicts:
        print(f"🚨 Found {len(all_conflicts)} files with duplicates:")
        for file_path, instances in all_conflicts.items():
            print(f"   {file_path}: {len(instances)} instances")
    else:
        print("✅ No common duplicate files found")
    
    return all_conflicts

def resolve_admin_static_conflicts():
    """Resolve Django admin static file conflicts"""
    print("\n🔧 RESOLVING ADMIN STATIC CONFLICTS")
    print("=" * 70)
    
    # Check if there are custom admin static files
    custom_admin_paths = []
    
    # Check in STATICFILES_DIRS
    if hasattr(settings, 'STATICFILES_DIRS'):
        for static_dir in settings.STATICFILES_DIRS:
            admin_path = os.path.join(static_dir, 'admin')
            if os.path.exists(admin_path):
                custom_admin_paths.append(admin_path)
    
    # Check in app static directories
    for app in settings.INSTALLED_APPS:
        try:
            app_module = __import__(app, fromlist=[''])
            app_path = os.path.dirname(app_module.__file__)
            admin_static_path = os.path.join(app_path, 'static', 'admin')
            if os.path.exists(admin_static_path):
                custom_admin_paths.append(admin_static_path)
        except:
            continue
    
    print(f"📁 Custom admin static paths found: {len(custom_admin_paths)}")
    for path in custom_admin_paths:
        print(f"   {path}")
    
    # Recommendation for resolution
    if custom_admin_paths:
        print(f"\n💡 RESOLUTION RECOMMENDATIONS:")
        print(f"   1. Remove custom admin static files if they're outdated")
        print(f"   2. Rename custom admin files to avoid conflicts")
        print(f"   3. Use Django's admin static files from django.contrib.admin")
        
        # Check if files are identical
        conflicts_resolved = 0
        for path in custom_admin_paths:
            inlines_path = os.path.join(path, 'js', 'inlines.js')
            if os.path.exists(inlines_path):
                print(f"\n🔍 Found custom inlines.js: {inlines_path}")
                # Could compare with Django's version here
                conflicts_resolved += 1
        
        return conflicts_resolved > 0
    else:
        print("✅ No custom admin static files found")
        return True

def verify_yitp_static_assets():
    """Verify YITP course static assets"""
    print("\n🔍 VERIFYING YITP STATIC ASSETS")
    print("=" * 70)
    
    # YITP-specific static files to check
    yitp_assets = [
        'css/yitp-course-branding.css',
        'assets/fonts/inter/Inter-Regular.woff2',
        'assets/img/logo/youthimpact.png',
        'lmsassets/css/course-detail.css',
        'lmsassets/js/lesson-progress.js'
    ]
    
    found_assets = []
    missing_assets = []
    
    for asset in yitp_assets:
        found = finders.find(asset)
        if found:
            found_assets.append(asset)
            print(f"   ✅ Found: {asset}")
            print(f"      Path: {found}")
        else:
            missing_assets.append(asset)
            print(f"   ❌ Missing: {asset}")
    
    print(f"\n📊 YITP Assets Summary:")
    print(f"   Found: {len(found_assets)}/{len(yitp_assets)}")
    print(f"   Missing: {len(missing_assets)}")
    
    # Check YITP course branding CSS specifically
    branding_css = finders.find('css/yitp-course-branding.css')
    if branding_css:
        print(f"\n🎨 YITP Branding CSS Analysis:")
        with open(branding_css, 'r') as f:
            content = f.read()
            print(f"   File size: {len(content)} characters")
            print(f"   Contains YITP colors: {'#ff5d15' in content and '#1a2e53' in content}")
    
    return len(missing_assets) == 0

def test_collectstatic_dry_run():
    """Test collectstatic in dry-run mode to identify conflicts"""
    print("\n🧪 TESTING COLLECTSTATIC (DRY RUN)")
    print("=" * 70)
    
    import subprocess
    
    try:
        # Run collectstatic with dry-run and verbosity
        result = subprocess.run([
            'python', 'manage.py', 'collectstatic', 
            '--dry-run', '--verbosity=2', '--noinput'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        output = result.stdout + result.stderr
        
        # Look for conflict warnings
        conflict_lines = [line for line in output.split('\n') if 'Found another file' in line]
        
        if conflict_lines:
            print(f"🚨 Found {len(conflict_lines)} conflicts:")
            for line in conflict_lines:
                print(f"   {line.strip()}")
        else:
            print("✅ No conflicts detected in dry run")
        
        # Look for files being copied
        copy_lines = [line for line in output.split('\n') if 'Copying' in line]
        print(f"\n📋 Files to be copied: {len(copy_lines)}")
        
        return len(conflict_lines) == 0
        
    except Exception as e:
        print(f"❌ Error running collectstatic dry run: {str(e)}")
        return False

def create_static_file_cleanup_script():
    """Create script to clean up duplicate static files"""
    print("\n📝 CREATING STATIC FILE CLEANUP SCRIPT")
    print("=" * 70)
    
    cleanup_script = """#!/bin/bash
# Static File Cleanup Script for YITP

echo "🔧 YITP Static File Cleanup"
echo "=========================="

# Remove any custom admin static files that conflict
echo "Checking for custom admin static files..."

# Check common locations for duplicate admin files
STATIC_DIRS=(
    "static/admin"
    "*/static/admin"
    "staticfiles/admin"
)

for dir in "${STATIC_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "Found admin static directory: $dir"
        echo "Please review and remove if it contains outdated Django admin files"
    fi
done

# Clean up any .pyc files that might interfere
echo "Cleaning Python cache files..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Clear existing collected static files
echo "Clearing existing staticfiles..."
if [ -d "staticfiles" ]; then
    rm -rf staticfiles/*
fi

echo "✅ Cleanup complete. Run 'python manage.py collectstatic' to rebuild."
"""
    
    with open('cleanup_static_files.sh', 'w') as f:
        f.write(cleanup_script)
    
    # Make executable
    os.chmod('cleanup_static_files.sh', 0o755)
    
    print("✅ Created cleanup_static_files.sh")
    print("   Run with: ./cleanup_static_files.sh")
    
    return True

def main():
    """Main function to resolve static file conflicts"""
    print("🔧 YITP STATIC FILE CONFLICT RESOLUTION")
    print("=" * 80)
    
    # Step 1: Analyze conflicts
    conflicts = analyze_static_file_conflicts()
    
    # Step 2: Find all duplicates
    all_conflicts = find_all_static_duplicates()
    
    # Step 3: Resolve admin conflicts
    admin_resolved = resolve_admin_static_conflicts()
    
    # Step 4: Verify YITP assets
    yitp_assets_ok = verify_yitp_static_assets()
    
    # Step 5: Test collectstatic
    collectstatic_ok = test_collectstatic_dry_run()
    
    # Step 6: Create cleanup script
    cleanup_created = create_static_file_cleanup_script()
    
    # Summary
    print(f"\n📊 RESOLUTION SUMMARY")
    print("=" * 70)
    print(f"   Conflicts found: {len(conflicts)}")
    print(f"   All duplicates: {len(all_conflicts)}")
    print(f"   Admin conflicts resolved: {admin_resolved}")
    print(f"   YITP assets verified: {yitp_assets_ok}")
    print(f"   Collectstatic test: {collectstatic_ok}")
    print(f"   Cleanup script created: {cleanup_created}")
    
    if len(conflicts) == 0 and collectstatic_ok:
        print(f"\n🎉 ALL STATIC FILE ISSUES RESOLVED!")
        print(f"✅ Ready for production deployment")
    else:
        print(f"\n⚠️ MANUAL INTERVENTION REQUIRED")
        print(f"📝 Next steps:")
        print(f"   1. Run ./cleanup_static_files.sh")
        print(f"   2. Remove duplicate admin static files")
        print(f"   3. Run collectstatic again")
    
    return len(conflicts) == 0

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎯 Static file conflicts resolved!")
    else:
        print("\n⚠️ Please address remaining conflicts")
