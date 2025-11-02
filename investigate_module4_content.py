#!/usr/bin/env python3
"""
Investigate Module 4 content structure and identify rendering/responsiveness issues
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question

def investigate_module4_content():
    """Investigate Module 4 content structure and identify issues"""
    
    print("🔍 INVESTIGATING MODULE 4 CONTENT STRUCTURE")
    print("=" * 60)
    
    try:
        # Get the course and Module 4
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module4 = Module.objects.get(course=course, sort_order=4)
        
        print(f"✅ Found Module 4: {module4.title}")
        print(f"   Description: {module4.description}")
        print(f"   Duration: {module4.estimated_duration} minutes")
        print(f"   Published: {module4.is_published}")
        
        # Get all lessons in Module 4
        lessons = Lesson.objects.filter(module=module4).order_by('sort_order')
        print(f"\n📚 Module 4 Lessons ({lessons.count()} total):")
        
        for lesson in lessons:
            print(f"\n📖 Lesson {lesson.sort_order}: {lesson.title}")
            print(f"   Duration: {lesson.estimated_duration} minutes")
            print(f"   Content Type: {lesson.content_type}")
            print(f"   Published: {lesson.is_published}")
            
            # Analyze content structure
            if lesson.content:
                content_length = len(lesson.content)
                print(f"   Content Length: {content_length:,} characters")
                
                # Check for responsive issues
                content = lesson.content
                
                # Check for fixed widths
                fixed_width_count = content.count('width:') + content.count('width=')
                print(f"   Fixed Width Elements: {fixed_width_count}")
                
                # Check for responsive classes
                responsive_classes = [
                    'img-fluid', 'table-responsive', 'container-fluid', 
                    'col-', 'row', 'd-flex', 'flex-', 'w-100', 'mw-100'
                ]
                responsive_count = sum(content.count(cls) for cls in responsive_classes)
                print(f"   Bootstrap Responsive Classes: {responsive_count}")
                
                # Check for overflow issues
                overflow_indicators = ['overflow:', 'white-space:', 'text-overflow:']
                overflow_count = sum(content.count(indicator) for indicator in overflow_indicators)
                print(f"   Overflow-related CSS: {overflow_count}")
                
                # Check for embedded CSS
                embedded_css = content.count('<style>')
                print(f"   Embedded CSS blocks: {embedded_css}")
                
                # Check for inline styles
                inline_styles = content.count('style=')
                print(f"   Inline style attributes: {inline_styles}")
                
                # Check for images
                img_tags = content.count('<img')
                print(f"   Image tags: {img_tags}")
                
                # Check for tables
                table_tags = content.count('<table')
                print(f"   Table tags: {table_tags}")
                
                # Check for divs with data-page-no (original HTML structure)
                page_divs = content.count('data-page-no')
                print(f"   Original page divs: {page_divs}")
                
                # Show content structure preview
                if content.startswith('<div class="lesson-content"'):
                    print(f"   ✅ Has YITP lesson wrapper")
                else:
                    print(f"   ❌ Missing YITP lesson wrapper")
                
                # Check for specific problematic patterns
                problematic_patterns = [
                    ('Fixed pixel widths', 'width: [0-9]+px'),
                    ('Fixed pixel heights', 'height: [0-9]+px'),
                    ('Absolute positioning', 'position: absolute'),
                    ('Fixed positioning', 'position: fixed'),
                    ('Large fixed margins', 'margin: [0-9]{3,}px'),
                    ('Large fixed padding', 'padding: [0-9]{3,}px'),
                ]
                
                import re
                for pattern_name, pattern in problematic_patterns:
                    matches = len(re.findall(pattern, content))
                    if matches > 0:
                        print(f"   ⚠️  {pattern_name}: {matches} instances")
                
                # Show first 500 characters of content
                preview = content[:500].replace('\n', ' ')
                print(f"   Content Preview: {preview}...")
                
            else:
                print(f"   ❌ No content")
            
            # Check quiz
            quiz = Quiz.objects.filter(lesson=lesson).first()
            if quiz:
                questions = Question.objects.filter(quiz=quiz).count()
                print(f"   Quiz: {quiz.title} ({questions} questions)")
            else:
                print(f"   ❌ No quiz")
        
        return True
        
    except Module.DoesNotExist:
        print("❌ Module 4 not found")
        return False
    except Exception as e:
        print(f"❌ Error investigating Module 4: {e}")
        return False

def analyze_specific_lesson_content(lesson_number=1):
    """Analyze specific lesson content in detail"""
    
    print(f"\n🔬 DETAILED ANALYSIS OF LESSON {lesson_number}")
    print("=" * 50)
    
    try:
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module4 = Module.objects.get(course=course, sort_order=4)
        lesson = Lesson.objects.get(module=module4, sort_order=lesson_number)
        
        print(f"📖 Analyzing: {lesson.title}")
        
        content = lesson.content
        if not content:
            print("❌ No content to analyze")
            return
        
        # Save content to file for detailed inspection
        with open(f'module4_lesson{lesson_number}_content.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Content saved to: module4_lesson{lesson_number}_content.html")
        
        # Analyze HTML structure
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all elements with style attributes
        styled_elements = soup.find_all(attrs={'style': True})
        print(f"📊 Elements with inline styles: {len(styled_elements)}")
        
        # Find problematic styles
        problematic_styles = []
        for element in styled_elements:
            style = element.get('style', '')
            if 'width:' in style and 'px' in style:
                problematic_styles.append(f"Fixed width: {element.name} - {style[:100]}")
            if 'position: absolute' in style or 'position: fixed' in style:
                problematic_styles.append(f"Absolute/Fixed position: {element.name} - {style[:100]}")
        
        if problematic_styles:
            print(f"⚠️  Problematic styles found:")
            for style in problematic_styles[:10]:  # Show first 10
                print(f"   - {style}")
            if len(problematic_styles) > 10:
                print(f"   ... and {len(problematic_styles) - 10} more")
        else:
            print(f"✅ No obvious problematic styles found")
        
        # Check for responsive wrapper
        lesson_content_div = soup.find('div', class_='lesson-content')
        if lesson_content_div:
            print(f"✅ Has lesson-content wrapper")
        else:
            print(f"❌ Missing lesson-content wrapper")
        
        # Check for embedded CSS
        style_tags = soup.find_all('style')
        if style_tags:
            print(f"📝 Embedded CSS blocks: {len(style_tags)}")
            for i, style_tag in enumerate(style_tags[:3]):  # Show first 3
                css_content = style_tag.get_text()[:200]
                print(f"   CSS Block {i+1}: {css_content}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing lesson content: {e}")
        return False

def main():
    success = investigate_module4_content()
    
    if success:
        print(f"\n🔬 Performing detailed analysis of Lesson 1...")
        analyze_specific_lesson_content(1)
        
        print(f"\n📋 SUMMARY & RECOMMENDATIONS:")
        print(f"1. Check the generated HTML files for detailed content structure")
        print(f"2. Look for fixed-width elements that prevent responsiveness")
        print(f"3. Identify embedded CSS that may override responsive styles")
        print(f"4. Consider re-extracting content with better responsive wrappers")
    else:
        print(f"\n❌ Investigation failed")

if __name__ == "__main__":
    main()
