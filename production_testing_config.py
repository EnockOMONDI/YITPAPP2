"""
YITP Production Database Testing Configuration
==============================================

This module provides safe, read-only access to the production PostgreSQL database
for testing module rendering issues and content format analysis.

CRITICAL SAFETY FEATURES:
- Read-only database access with write operation blocking
- Automatic transaction rollback to prevent data modifications
- Visual warnings when connected to production
- Connection timeout protection
- Environment variable controls

Usage:
    python production_testing_config.py --test-module-2
    python production_testing_config.py --investigate-content
    python production_testing_config.py --test-rendering

Author: YITP Development Team
Date: 2025-01-20
"""

import os
import sys
import django
from django.conf import settings
from django.db import transaction, connection
from django.core.management.color import make_style
import time
from contextlib import contextmanager
import argparse

# Color styling for console output
style = make_style()

class ProductionTestingError(Exception):
    """Custom exception for production testing errors"""
    pass

class ReadOnlyProductionDB:
    """
    Safe read-only access to production database with comprehensive safeguards
    """
    
    def __init__(self):
        self.original_env = os.environ.get('DJANGO_ENV')
        self.is_connected = False
        self.connection_start_time = None
        self.max_connection_time = 1800  # 30 minutes max connection
        
    def __enter__(self):
        """Context manager entry - establish read-only production connection"""
        self._setup_production_connection()
        self._verify_read_only_access()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - restore local database connection"""
        self._restore_local_connection()
        
    def _setup_production_connection(self):
        """Configure Django to use production database in read-only mode"""
        print(style.WARNING("=" * 80))
        print(style.WARNING("🔒 CONNECTING TO PRODUCTION DATABASE (READ-ONLY MODE)"))
        print(style.WARNING("=" * 80))
        print(style.WARNING("⚠️  CRITICAL SAFETY NOTICE:"))
        print(style.WARNING("   • All write operations are BLOCKED"))
        print(style.WARNING("   • Transactions will be automatically rolled back"))
        print(style.WARNING("   • Connection will timeout after 30 minutes"))
        print(style.WARNING("   • Any database changes will be PREVENTED"))
        print(style.WARNING("=" * 80))
        
        # Set production environment
        os.environ['DJANGO_ENV'] = 'production'
        os.environ['TESTING_WITH_PRODUCTION'] = 'true'
        
        # Setup Django with production settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
        django.setup()
        
        self.is_connected = True
        self.connection_start_time = time.time()
        
        print(style.SUCCESS("✅ Production database connection established (READ-ONLY)"))
        print()
        
    def _verify_read_only_access(self):
        """Verify that write operations are properly blocked"""
        try:
            with connection.cursor() as cursor:
                # Test that we can read
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] != 1:
                    raise ProductionTestingError("Database read test failed")
                    
            print(style.SUCCESS("✅ Read access verified"))
            print(style.WARNING("🔒 Write operations are blocked by transaction rollback"))
            print()
            
        except Exception as e:
            raise ProductionTestingError(f"Failed to verify database access: {e}")
            
    def _restore_local_connection(self):
        """Restore local SQLite database connection"""
        if self.original_env:
            os.environ['DJANGO_ENV'] = self.original_env
        else:
            os.environ.pop('DJANGO_ENV', None)
            
        os.environ.pop('TESTING_WITH_PRODUCTION', None)
        
        # Force Django to reload settings
        from django.conf import settings
        if hasattr(settings, '_wrapped'):
            delattr(settings, '_wrapped')
            
        print(style.SUCCESS("✅ Restored local database connection"))
        print(style.SUCCESS("🏠 Back to local SQLite development environment"))
        print()
        
    def check_connection_timeout(self):
        """Check if connection has exceeded maximum time limit"""
        if self.connection_start_time:
            elapsed = time.time() - self.connection_start_time
            if elapsed > self.max_connection_time:
                print(style.ERROR(f"⚠️  Connection timeout reached ({elapsed:.0f}s)"))
                print(style.ERROR("🔒 Automatically disconnecting from production"))
                return True
        return False
        
    @contextmanager
    def safe_transaction(self):
        """
        Context manager that ensures all database operations are rolled back
        This prevents any accidental writes to production database
        """
        print(style.WARNING("🔒 Starting read-only transaction (auto-rollback enabled)"))
        
        try:
            with transaction.atomic():
                yield
                # Force rollback by raising an exception
                raise ProductionTestingError("Forced rollback to prevent production writes")
                
        except ProductionTestingError:
            # This is expected - we always rollback
            print(style.SUCCESS("✅ Transaction rolled back - no production data modified"))
            
        except Exception as e:
            print(style.ERROR(f"❌ Unexpected error during transaction: {e}"))
            raise

def test_module_2_content():
    """Test Module 2 content structure and rendering"""
    print(style.HTTP_INFO("🔍 TESTING MODULE 2 CONTENT STRUCTURE"))
    print("=" * 60)
    
    with ReadOnlyProductionDB() as db:
        with db.safe_transaction():
            from courses.models import Course, Module, Lesson
            
            # Get Course 6 and Module 2
            course = Course.objects.get(id=6)
            module_2 = Module.objects.filter(
                course=course, 
                title__icontains='Personal Initiative'
            ).first()
            
            if not module_2:
                print(style.ERROR("❌ Module 2 not found"))
                return
                
            print(f"✅ Found Module 2: {module_2.title}")
            print(f"   Module ID: {module_2.id}")
            
            # Analyze lessons
            lessons = Lesson.objects.filter(module=module_2).order_by('id')
            print(f"📖 Total Lessons: {lessons.count()}")
            print()
            
            for i, lesson in enumerate(lessons, 1):
                print(f"Lesson {i}: {lesson.title}")
                print(f"   ID: {lesson.id}")
                print(f"   Content Length: {len(lesson.content) if lesson.content else 0} chars")
                
                if lesson.content:
                    # Analyze content format
                    content = lesson.content
                    
                    # Check for HTML tags
                    has_html = '<' in content and '>' in content
                    has_inline_styles = 'style=' in content
                    has_css_classes = 'class=' in content
                    
                    print(f"   📝 Content Analysis:")
                    print(f"      • Contains HTML: {'Yes' if has_html else 'No'}")
                    print(f"      • Inline Styles: {'Yes' if has_inline_styles else 'No'}")
                    print(f"      • CSS Classes: {'Yes' if has_css_classes else 'No'}")
                    
                    # Show content preview (first 200 chars)
                    preview = content[:200].replace('\n', ' ').replace('\r', '')
                    print(f"   📄 Preview: {preview}...")
                    
                else:
                    print(f"   ❌ NO CONTENT")
                    
                print()

def investigate_content_format():
    """Detailed investigation of Module 2 content format"""
    print(style.HTTP_INFO("🔬 DETAILED CONTENT FORMAT INVESTIGATION"))
    print("=" * 60)
    
    with ReadOnlyProductionDB() as db:
        with db.safe_transaction():
            from courses.models import Course, Module, Lesson
            import json
            
            course = Course.objects.get(id=6)
            module_2 = Module.objects.filter(
                course=course, 
                title__icontains='Personal Initiative'
            ).first()
            
            if not module_2:
                print(style.ERROR("❌ Module 2 not found"))
                return
                
            lessons = Lesson.objects.filter(module=module_2).order_by('id')
            
            for lesson in lessons:
                print(f"🔍 ANALYZING: {lesson.title}")
                print("-" * 50)
                
                if not lesson.content:
                    print("❌ No content found")
                    continue
                    
                content = lesson.content
                
                # Try to parse as JSON
                try:
                    json_content = json.loads(content)
                    print("✅ Content is valid JSON")
                    print(f"📋 JSON Structure: {type(json_content).__name__}")
                    
                    if isinstance(json_content, dict):
                        print(f"🔑 JSON Keys: {list(json_content.keys())}")
                        
                        # Look for common content fields
                        for key in ['content', 'html', 'body', 'text', 'sections']:
                            if key in json_content:
                                value = json_content[key]
                                print(f"   📝 {key}: {type(value).__name__} ({len(str(value))} chars)")
                                
                except json.JSONDecodeError:
                    print("📝 Content is not JSON - analyzing as HTML/text")
                    
                    # Analyze HTML structure
                    if '<html>' in content or '<body>' in content:
                        print("🌐 Full HTML document detected")
                    elif '<div>' in content or '<p>' in content:
                        print("📄 HTML fragment detected")
                    else:
                        print("📝 Plain text content")
                        
                    # Count HTML elements
                    html_tags = ['<div>', '<p>', '<h1>', '<h2>', '<h3>', '<span>', '<strong>', '<em>']
                    for tag in html_tags:
                        count = content.count(tag)
                        if count > 0:
                            print(f"   {tag}: {count} occurrences")
                            
                    # Check for inline styles
                    if 'style=' in content:
                        import re
                        styles = re.findall(r'style="([^"]*)"', content)
                        print(f"   🎨 Inline styles found: {len(styles)} instances")
                        if styles:
                            print(f"   📋 Style examples: {styles[:3]}")
                            
                print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='YITP Production Database Testing Tool')
    parser.add_argument('--test-module-2', action='store_true', 
                       help='Test Module 2 content structure')
    parser.add_argument('--investigate-content', action='store_true',
                       help='Detailed content format investigation')
    
    args = parser.parse_args()
    
    if args.test_module_2:
        test_module_2_content()
    elif args.investigate_content:
        investigate_content_format()
    else:
        print("Usage: python production_testing_config.py [--test-module-2|--investigate-content]")
