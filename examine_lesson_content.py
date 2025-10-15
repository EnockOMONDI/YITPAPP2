#!/usr/bin/env python3
"""
Examine Lesson Content Structure
===============================

Examine the actual content structure of lessons to understand the styling format.
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set up Django environment for PRODUCTION database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode

django.setup()

from courses.models import Lesson

def examine_lesson_content(lesson_id, lesson_name):
    """Examine the content structure of a specific lesson"""
    print(f"\n🔍 EXAMINING {lesson_name}")
    print("=" * 60)
    
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        print(f"📚 Lesson: {lesson.title}")
        print(f"📊 Content length: {len(lesson.content)} characters")
        
        if lesson.content:
            # Save full content to file for examination
            filename = f"lesson_{lesson_id}_content.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(lesson.content)
            print(f"💾 Full content saved to: {filename}")
            
            # Show first 1000 characters
            print(f"\n📄 CONTENT PREVIEW (first 1000 chars):")
            print("-" * 50)
            print(lesson.content[:1000])
            print("-" * 50)
            
            # Show last 500 characters
            print(f"\n📄 CONTENT ENDING (last 500 chars):")
            print("-" * 50)
            print(lesson.content[-500:])
            print("-" * 50)
        else:
            print("❌ No content found")
            
    except Exception as e:
        print(f"❌ Error examining lesson: {str(e)}")

if __name__ == "__main__":
    print("🔍 LESSON CONTENT EXAMINATION")
    print("=" * 60)
    
    # Examine lesson 1 (needs styling)
    examine_lesson_content(103, "LESSON 1 (NEEDS STYLING)")
    
    # Examine lesson 2 (has good styling)
    examine_lesson_content(111, "LESSON 2 (TEMPLATE)")
    
    print(f"\n✅ EXAMINATION COMPLETE")
    print(f"📄 Content files saved for detailed review")
