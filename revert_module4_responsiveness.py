#!/usr/bin/env python3
"""
Revert Module 4 content to its original state before responsiveness fixes
"""

import os
import django
import json
from bs4 import BeautifulSoup

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson

def revert_module4_responsiveness():
    """Revert Module 4 content to original state"""
    
    print("🔄 REVERTING MODULE 4 TO ORIGINAL STATE")
    print("=" * 60)
    
    try:
        # Get the course and Module 4
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module4 = Module.objects.get(course=course, sort_order=4)
        
        print(f"✅ Found Module 4: {module4.title}")
        
        # Check if we have the original extracted content
        original_file = 'module4_lessons_extracted.json'
        if os.path.exists(original_file):
            print(f"📁 Found original content file: {original_file}")
            return restore_from_backup(module4, original_file)
        else:
            print(f"📁 Original content file not found, re-extracting from source...")
            return re_extract_from_source(module4)
        
    except Exception as e:
        print(f"❌ Error reverting Module 4: {e}")
        return False

def restore_from_backup(module4, backup_file):
    """Restore content from backup JSON file"""
    
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            original_lessons = json.load(f)
        
        print(f"📚 Loaded {len(original_lessons)} lessons from backup")
        
        # Get current lessons
        current_lessons = Lesson.objects.filter(module=module4).order_by('sort_order')
        
        restored_count = 0
        
        for i, lesson in enumerate(current_lessons):
            if i < len(original_lessons):
                original_content = original_lessons[i]['content']
                
                print(f"🔄 Restoring {lesson.title}...")
                
                # Restore original content
                lesson.content = original_content
                lesson.save()
                
                restored_count += 1
                print(f"   ✅ Restored successfully")
            else:
                print(f"   ⚠️  No backup content for {lesson.title}")
        
        print(f"\n📊 RESTORATION SUMMARY:")
        print(f"   • Total lessons: {current_lessons.count()}")
        print(f"   • Lessons restored: {restored_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error restoring from backup: {e}")
        return False

def re_extract_from_source(module4):
    """Re-extract content from original source file"""
    
    source_file = 'courseunits/Soft Skills for the streets content.html'
    
    if not os.path.exists(source_file):
        print(f"❌ Source file not found: {source_file}")
        return False
    
    print(f"📁 Re-extracting from source: {source_file}")
    
    try:
        # Read the original HTML file
        with open(source_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract CSS content
        css_content = extract_css_content(soup)
        
        # Define lesson structure (same as original extraction)
        lesson_structure = [
            {
                "title": "Introduction to Soft Skills",
                "description": "Overview of soft skills and their importance in personal and professional development.",
                "pages": [1, 2, 3, 4, 5]
            },
            {
                "title": "Core Soft Skills Overview", 
                "description": "Comprehensive overview of essential soft skills for professional success.",
                "pages": [6, 7, 8, 9, 10, 11]
            },
            {
                "title": "Leadership Styles and Self-Awareness",
                "description": "Understanding different leadership approaches and developing self-awareness.",
                "pages": [12, 13, 14, 15, 16, 17, 18, 19]
            },
            {
                "title": "Strategic Planning and Goal Setting",
                "description": "Techniques for effective strategic planning and achieving goals.",
                "pages": [20, 21, 22, 23, 24]
            },
            {
                "title": "Critical Thinking and Problem Solving",
                "description": "Developing analytical skills and systematic problem-solving approaches.",
                "pages": [25, 26, 27, 28, 29]
            },
            {
                "title": "Communication and Adaptability",
                "description": "Mastering effective communication and developing adaptability skills.",
                "pages": [30, 31, 32, 33, 34, 35]
            },
            {
                "title": "Time Management and Decision Making",
                "description": "Optimizing time management and improving decision-making processes.",
                "pages": [36, 37, 38, 39, 40, 41]
            },
            {
                "title": "Emotional Intelligence Fundamentals",
                "description": "Understanding and developing emotional intelligence for better relationships.",
                "pages": [42, 43, 44, 45]
            },
            {
                "title": "Teamwork, Collaboration, and Networking",
                "description": "Building effective teams and professional networks.",
                "pages": [46, 47, 48, 49]
            },
            {
                "title": "Practical Applications and Case Studies",
                "description": "Real-world applications and case studies of soft skills in action.",
                "pages": [47, 48, 49]  # Use the last available pages
            }
        ]
        
        # Get all page divs
        page_divs = soup.find_all('div', {'data-page-no': True})
        print(f"📄 Found {len(page_divs)} pages in source file")

        # Get current lessons
        current_lessons = Lesson.objects.filter(module=module4).order_by('sort_order')

        restored_count = 0

        for i, lesson_info in enumerate(lesson_structure):
            if i < current_lessons.count():
                current_lesson = current_lessons[i]

                print(f"🔄 Re-extracting {lesson_info['title']}...")

                # Get pages for this lesson
                lesson_pages = []
                for page_num in lesson_info['pages']:
                    # Find page div with safe parsing
                    for div in page_divs:
                        try:
                            div_page_no = div.get('data-page-no', '0')
                            if div_page_no.isdigit() and int(div_page_no) == page_num:
                                lesson_pages.append(div)
                                break
                        except (ValueError, TypeError):
                            continue
                
                if lesson_pages:
                    # Extract lesson HTML with original methodology
                    original_content = extract_original_lesson_html(lesson_pages, css_content, lesson_info)
                    
                    # Update lesson content
                    current_lesson.content = original_content
                    current_lesson.save()
                    
                    restored_count += 1
                    print(f"   ✅ Re-extracted successfully ({len(lesson_pages)} pages)")
                else:
                    print(f"   ⚠️  No pages found for {lesson_info['title']}")
        
        print(f"\n📊 RE-EXTRACTION SUMMARY:")
        print(f"   • Total lessons: {current_lessons.count()}")
        print(f"   • Lessons re-extracted: {restored_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error re-extracting from source: {e}")
        return False

def extract_css_content(soup):
    """Extract CSS content from the HTML"""
    css_content = ""
    
    # Find all style tags
    style_tags = soup.find_all('style')
    for style_tag in style_tags:
        if style_tag.string:
            css_content += style_tag.string + "\n"
    
    return css_content

def extract_original_lesson_html(lesson_pages, css_content, lesson_info):
    """Extract lesson HTML using original methodology (without responsive fixes)"""
    
    # Create lesson HTML with YITP styling wrapper (ORIGINAL VERSION)
    lesson_html = f'''
    <div class="lesson-content" style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div class="lesson-header" style="background: linear-gradient(135deg, #ff5d15, #1a2e53); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 24px; font-weight: bold;">{lesson_info['title']}</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">{lesson_info['description']}</p>
        </div>
        
        <div class="lesson-body" style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    '''
    
    # Add embedded CSS styles (ORIGINAL - includes pdf2htmlEX CSS)
    lesson_html += f'<style>{css_content}</style>\n'
    
    # Add each page's content (ORIGINAL - no responsive modifications)
    for page in lesson_pages:
        page_content = str(page)
        lesson_html += f'<div class="page-content">{page_content}</div>\n'
    
    # Close the lesson wrapper (ORIGINAL)
    lesson_html += '''
        </div>
        
        <div class="lesson-footer" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #ff5d15;">
            <p style="margin: 0; color: #666; font-style: italic;">
                Complete this lesson and take the quiz to continue to the next lesson.
            </p>
        </div>
    </div>
    '''
    
    return lesson_html

def main():
    success = revert_module4_responsiveness()
    
    if success:
        print(f"\n🎉 Module 4 successfully reverted to original state!")
        print(f"📄 All lessons restored to pre-responsiveness-fix content")
        print(f"🔄 Next step: Verify the revert was successful")
    else:
        print(f"\n❌ Failed to revert Module 4 content")

if __name__ == "__main__":
    main()
