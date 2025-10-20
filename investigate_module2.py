#!/usr/bin/env python
"""
Quick Module 2 Content Investigation Script
==========================================

This script safely connects to production database and investigates
Module 2 content format to understand rendering issues.

SAFETY: All operations are read-only with automatic rollback.
"""

import os
import django
from django.db import transaction

def main():
    print("🔍 INVESTIGATING MODULE 2 CONTENT FORMAT")
    print("=" * 60)
    
    # Setup production environment
    original_env = os.environ.get('DJANGO_ENV')
    
    try:
        print("🔌 Connecting to production database (READ-ONLY)...")
        os.environ['DJANGO_ENV'] = 'production'
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
        django.setup()
        
        # Import models after Django setup
        from courses.models import Course, Module, Lesson
        import json
        
        print("✅ Connected to production database")
        print("🔒 All operations will be rolled back automatically")
        print()
        
        # Use transaction rollback for safety
        try:
            with transaction.atomic():
                # Get Course 6 and Module 2
                course = Course.objects.get(id=6)
                module_2 = Module.objects.filter(
                    course=course, 
                    title__icontains='Personal Initiative'
                ).first()
                
                if not module_2:
                    print("❌ Module 2 not found")
                    return
                    
                print(f"✅ Found Module 2: {module_2.title}")
                print(f"   Module ID: {module_2.id}")
                print()
                
                # Get all lessons
                lessons = Lesson.objects.filter(module=module_2).order_by('id')
                print(f"📖 Total Lessons: {lessons.count()}")
                print()
                
                # Analyze each lesson
                for i, lesson in enumerate(lessons, 1):
                    print(f"🔍 LESSON {i}: {lesson.title}")
                    print(f"   ID: {lesson.id}")
                    
                    if not lesson.content:
                        print("   ❌ NO CONTENT")
                        print()
                        continue
                        
                    content = lesson.content
                    print(f"   📏 Content Length: {len(content)} characters")
                    
                    # Analyze content format
                    try:
                        # Try to parse as JSON
                        json_data = json.loads(content)
                        print("   📋 Format: JSON")
                        
                        if isinstance(json_data, dict):
                            print(f"   🔑 JSON Keys: {list(json_data.keys())}")
                            
                            # Look for content in common keys
                            for key in ['content', 'html', 'body', 'text', 'sections']:
                                if key in json_data:
                                    value = json_data[key]
                                    print(f"      • {key}: {type(value).__name__} ({len(str(value))} chars)")
                                    
                                    # If it's HTML content, analyze it
                                    if isinstance(value, str) and ('<' in value and '>' in value):
                                        if 'style=' in value:
                                            print(f"        ⚠️  Contains inline styles")
                                        if 'class=' in value:
                                            print(f"        📋 Contains CSS classes")
                                            
                    except json.JSONDecodeError:
                        # Not JSON, analyze as HTML/text
                        print("   📝 Format: HTML/Text")
                        
                        if '<html>' in content or '<!DOCTYPE' in content:
                            print("   🌐 Full HTML document")
                        elif '<div>' in content or '<p>' in content:
                            print("   📄 HTML fragment")
                        else:
                            print("   📝 Plain text")
                            
                        # Check for styling
                        if 'style=' in content:
                            print("   ⚠️  Contains inline styles")
                        if 'class=' in content:
                            print("   📋 Contains CSS classes")
                            
                    # Show content preview
                    preview = content[:200].replace('\n', ' ').replace('\r', ' ')
                    print(f"   📄 Preview: {preview}...")
                    print()
                    
                # Force rollback to prevent any accidental writes
                raise Exception("Forced rollback - investigation complete")
                
        except Exception as e:
            if "Forced rollback" in str(e):
                print("✅ Investigation complete - all operations rolled back")
            else:
                print(f"❌ Error during investigation: {e}")
                
    finally:
        # Restore original environment
        if original_env:
            os.environ['DJANGO_ENV'] = original_env
        else:
            os.environ.pop('DJANGO_ENV', None)
            
        print("🏠 Restored local environment")

if __name__ == "__main__":
    main()
