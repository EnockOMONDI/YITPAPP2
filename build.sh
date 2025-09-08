#!/bin/bash

# YITP Django Application Build Script for Render
set -o errexit  # exit on error

echo "🚀 Building YITP Django Application (Deployment Branch)..."
echo "================================================"

# Check Python version
echo "🐍 Python version:"
python --version

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify critical imports
echo "🔍 Verifying critical imports..."
python -c "
import django
print(f'✅ Django version: {django.get_version()}')

import shortuuid
print('✅ shortuuid imported successfully')

import pyuploadcare
print('✅ pyuploadcare imported successfully')

import psycopg2
print('✅ psycopg2 imported successfully')

# Verify crispy forms imports
import crispy_forms
print('✅ crispy_forms imported successfully')

import crispy_bootstrap5
print('✅ crispy_bootstrap5 imported successfully')
"

# Git Repository Setup for Dashboard Integration
echo "🔧 Setting up Git repository for dashboard integration..."
echo "================================================"

# Check if we're in a git repository
if [ -d ".git" ]; then
    echo "✅ Git repository detected"

    # Check current git status
    echo "📊 Current git status:"
    git status --porcelain || echo "Git status check failed"

    # Check current branch
    echo "🌿 Current branch:"
    git branch --show-current || echo "Branch check failed"

    # Check if we have a shallow clone
    if [ -f ".git/shallow" ]; then
        echo "⚠️  Shallow clone detected - fetching full history for dashboard..."
        # Unshallow the repository to get full commit history
        git fetch --unshallow || echo "Failed to unshallow repository"

        # Fetch all branches and tags
        git fetch --all --tags || echo "Failed to fetch all branches"

        echo "✅ Full git history now available"
    else
        echo "✅ Full git repository already available"
    fi

    # Show recent commits for verification
    echo "📝 Recent commits (for dashboard verification):"
    git log --oneline -10 || echo "Git log failed"

else
    echo "❌ No git repository found - dashboard git integration will show defaults"
fi

# Detailed repository and environment diagnostics
echo "🔍 Repository and Environment Diagnostics..."
echo "================================================"

# Show current working directory
echo "📁 Current working directory:"
pwd

# Show directory contents
echo "📋 Root directory contents:"
ls -la

# Show Python path
echo "🐍 Python path:"
python -c "import sys; print('\n'.join(sys.path))"

# Check for blog app directory (handle case sensitivity)
echo "🔍 Checking for blog app directory:"
BLOG_APP_DIR=""
if [ -d "blogapp" ]; then
    BLOG_APP_DIR="blogapp"
    echo "✅ blogapp directory exists (lowercase)"
else
    echo "❌ No blog app directory found!"
    echo "📋 Available directories:"
    find . -maxdepth 1 -type d -name "*app*" -o -name "*blog*" | head -10
fi

if [ -n "$BLOG_APP_DIR" ]; then
    echo "📋 $BLOG_APP_DIR directory contents:"
    ls -la "$BLOG_APP_DIR/"

    # Check specific files
    echo "🔍 Checking critical $BLOG_APP_DIR files:"
    for file in "__init__.py" "apps.py" "models.py" "views.py" "urls.py"; do
        if [ -f "$BLOG_APP_DIR/$file" ]; then
            echo "  ✅ $BLOG_APP_DIR/$file exists"
        else
            echo "  ❌ $BLOG_APP_DIR/$file missing"
        fi
    done
fi

# Check Django apps (including LMS apps)
echo "🔍 Checking Django app directories:"
for app in "users" "yitp" "events" "courses" "progress" "assessments" "communication" "content" "payments"; do
    if [ -d "$app" ]; then
        echo "  ✅ $app directory exists"
    else
        echo "  ❌ $app directory missing"
    fi
done

# Test Django app imports with detailed error reporting
echo "�🔧 Testing Django app imports with detailed diagnostics..."
python -c "
import os
import sys
import traceback

print('🐍 Python executable:', sys.executable)
print('📁 Current working directory:', os.getcwd())
print('📋 Directory contents:', os.listdir('.'))

# Add current directory to Python path
sys.path.insert(0, os.getcwd())
print('🛤️  Updated Python path (first 3):', sys.path[:3])

# Determine which blog app directory exists
blog_app_dir = None
if os.path.exists('blogapp'):
    blog_app_dir = 'blogapp'
    print('✅ blogapp directory exists (lowercase)')
else:
    print('❌ No blog app directory found')
    # List all directories containing 'app'
    app_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and 'app' in d.lower()]
    print('📁 Directories containing app:', app_dirs)
    sys.exit(1)

print('📋', blog_app_dir, 'contents:', os.listdir(blog_app_dir))

# Check __init__.py
init_file = os.path.join(blog_app_dir, '__init__.py')
if os.path.exists(init_file):
    print('✅', blog_app_dir + '/__init__.py exists')
    with open(init_file, 'r') as f:
        content = f.read()
        print('📄 __init__.py content length:', len(content), 'characters')
else:
    print('❌', blog_app_dir + '/__init__.py missing')

# Test individual app imports with detailed error handling
print()
print('🔧 Testing imports...')
try:
    if blog_app_dir == 'blogapp':
        print('🔍 Attempting to import blogapp...')
        import blogapp as blog_module
        print('✅ blogapp module imported successfully')
        print('📍 blogapp module location:', blog_module.__file__)

        print('🔍 Attempting to import blogapp.apps...')
        import blogapp.apps
        print('✅ blogapp.apps imported successfully')

        print('🔍 Attempting to import BlogappConfig...')
        from blogapp.apps import BlogappConfig
        print('✅ BlogappConfig imported successfully')
        print('📍 BlogappConfig:', BlogappConfig)

    # Since we only support blogapp now, remove the blogApp case

except ImportError as e:
    print('❌ Import error:', str(e))
    print('🔍 Full traceback:')
    traceback.print_exc()

    # Additional debugging
    print()
    print('🔍 Additional debugging information:')
    non_hidden_files = [f for f in os.listdir('.') if not f.startswith('.')]
    print('📁 Current directory files:', non_hidden_files)

    # Try to find any *app* directories
    app_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and 'app' in d.lower()]
    print('📁 Directories containing app:', app_dirs)

    sys.exit(1)
"

# Check Django configuration
echo "🔧 Checking Django configuration..."
python manage.py check

# Verify crispy forms configuration
echo "🔧 Verifying crispy forms configuration..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()
from django.conf import settings

# Check crispy forms settings
if hasattr(settings, 'CRISPY_TEMPLATE_PACK'):
    print(f'✅ CRISPY_TEMPLATE_PACK: {settings.CRISPY_TEMPLATE_PACK}')
else:
    print('❌ CRISPY_TEMPLATE_PACK not configured')

if hasattr(settings, 'CRISPY_ALLOWED_TEMPLATE_PACKS'):
    print(f'✅ CRISPY_ALLOWED_TEMPLATE_PACKS: {settings.CRISPY_ALLOWED_TEMPLATE_PACKS}')
else:
    print('❌ CRISPY_ALLOWED_TEMPLATE_PACKS not configured')

# Check if crispy forms apps are in INSTALLED_APPS
if 'crispy_forms' in settings.INSTALLED_APPS:
    print('✅ crispy_forms in INSTALLED_APPS')
else:
    print('❌ crispy_forms not in INSTALLED_APPS')

if 'crispy_bootstrap5' in settings.INSTALLED_APPS:
    print('✅ crispy_bootstrap5 in INSTALLED_APPS')
else:
    print('❌ crispy_bootstrap5 not in INSTALLED_APPS')
"

# Collect static files for production
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create and apply database migrations
echo "🗄️  Preparing database migrations..."
python manage.py makemigrations --noinput

echo "🗄️  Applying database migrations..."
python manage.py migrate --noinput

# Test database connection
echo "🔍 Testing database connection..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT 1')
    print('✅ Database connection successful')
"

# Create superuser if it doesn't exist (optional)
echo "👤 Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('No superuser found. You can create one after deployment.')
else:
    print('Superuser already exists.')
"

echo "✅ Build completed successfully!"
echo "🌐 YITP is ready for deployment!"
echo "================================================"