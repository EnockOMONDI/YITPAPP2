#!/usr/bin/env python3
"""
Fix Module 4 responsiveness issues by updating the content with proper responsive CSS
"""

import os
import django
import re

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson

def fix_module4_responsiveness():
    """Fix Module 4 responsiveness issues"""
    
    print("🔧 FIXING MODULE 4 RESPONSIVENESS ISSUES")
    print("=" * 60)
    
    try:
        # Get the course and Module 4
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module4 = Module.objects.get(course=course, sort_order=4)
        
        print(f"✅ Found Module 4: {module4.title}")
        
        # Get all lessons in Module 4
        lessons = Lesson.objects.filter(module=module4).order_by('sort_order')
        print(f"📚 Processing {lessons.count()} lessons...")
        
        total_fixes = 0
        
        for lesson in lessons:
            print(f"\n🔄 Processing {lesson.title}...")
            
            if not lesson.content:
                print(f"   ⚠️  No content to fix")
                continue
            
            original_content = lesson.content
            fixed_content = apply_responsive_fixes(original_content)
            
            if fixed_content != original_content:
                lesson.content = fixed_content
                lesson.save()
                total_fixes += 1
                print(f"   ✅ Applied responsive fixes")
            else:
                print(f"   ✅ No fixes needed")
        
        print(f"\n📊 SUMMARY:")
        print(f"   • Total lessons processed: {lessons.count()}")
        print(f"   • Lessons with fixes applied: {total_fixes}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing Module 4 responsiveness: {e}")
        return False

def apply_responsive_fixes(content):
    """Apply responsive fixes to lesson content"""
    
    # 1. Add responsive CSS override at the beginning
    responsive_css = '''
    <style>
    /* YITP Responsive Overrides for pdf2htmlEX content */
    .lesson-content {
        max-width: 100% !important;
        overflow-x: auto !important;
    }
    
    .lesson-body {
        max-width: 100% !important;
        overflow-x: auto !important;
        padding: 15px !important;
    }
    
    /* Make pdf2htmlEX containers responsive */
    .pf {
        position: relative !important;
        width: 100% !important;
        max-width: 100% !important;
        margin: 10px 0 !important;
        overflow: visible !important;
        box-shadow: none !important;
    }
    
    .pc {
        position: relative !important;
        width: 100% !important;
        height: auto !important;
        overflow: visible !important;
        transform: none !important;
        -ms-transform: none !important;
        -webkit-transform: none !important;
    }
    
    /* Make text elements responsive */
    .t {
        position: relative !important;
        white-space: normal !important;
        font-size: inherit !important;
        transform: none !important;
        -ms-transform: none !important;
        -webkit-transform: none !important;
        line-height: 1.4 !important;
        margin: 2px 0 !important;
    }
    
    /* Make content blocks responsive */
    .c {
        position: relative !important;
        width: 100% !important;
        max-width: 100% !important;
        overflow: visible !important;
        margin: 5px 0 !important;
    }
    
    /* Hide background images and decorative elements */
    .bi {
        display: none !important;
    }
    
    /* Responsive images */
    img {
        max-width: 100% !important;
        height: auto !important;
    }
    
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .lesson-body {
            padding: 10px !important;
        }
        
        .lesson-header h1 {
            font-size: 1.5rem !important;
        }
        
        .lesson-header p {
            font-size: 0.9rem !important;
        }
        
        .pf {
            margin: 5px 0 !important;
        }
        
        .t {
            font-size: 14px !important;
        }
    }
    
    /* Tablet responsive adjustments */
    @media (min-width: 769px) and (max-width: 1024px) {
        .lesson-body {
            padding: 15px !important;
        }
        
        .t {
            font-size: 15px !important;
        }
    }
    
    /* Desktop adjustments */
    @media (min-width: 1025px) {
        .lesson-body {
            padding: 20px !important;
        }
        
        .t {
            font-size: 16px !important;
        }
    }
    </style>
    '''
    
    # 2. Insert responsive CSS after the existing embedded CSS
    if '<style>' in content:
        # Find the last </style> tag and insert our CSS after it
        last_style_end = content.rfind('</style>')
        if last_style_end != -1:
            insertion_point = last_style_end + len('</style>')
            content = content[:insertion_point] + '\n' + responsive_css + content[insertion_point:]
    else:
        # If no existing style tags, add at the beginning of lesson-body
        lesson_body_start = content.find('<div class="lesson-body"')
        if lesson_body_start != -1:
            # Find the end of the opening div tag
            div_end = content.find('>', lesson_body_start)
            if div_end != -1:
                insertion_point = div_end + 1
                content = content[:insertion_point] + '\n' + responsive_css + content[insertion_point:]
    
    # 3. Add Bootstrap responsive classes to the main containers
    content = re.sub(
        r'<div class="lesson-content"([^>]*)>',
        r'<div class="lesson-content container-fluid\1">',
        content
    )
    
    content = re.sub(
        r'<div class="lesson-body"([^>]*)>',
        r'<div class="lesson-body\1">',
        content
    )
    
    # 4. Make any remaining fixed-width elements responsive
    # Remove fixed widths from style attributes
    content = re.sub(r'width:\s*\d+px;?', '', content)
    content = re.sub(r'min-width:\s*\d+px;?', '', content)
    
    # 5. Fix any remaining absolute positioning that might cause overflow
    content = re.sub(r'position:\s*absolute;?', 'position: relative;', content)
    
    # 6. Add word-wrap for long text
    content = re.sub(
        r'(<div[^>]*class="[^"]*page-content[^"]*"[^>]*>)',
        r'\1<div style="word-wrap: break-word; overflow-wrap: break-word;">',
        content
    )
    
    # Close the word-wrap div
    content = re.sub(
        r'(</div>\s*</div>\s*<div class="lesson-footer")',
        r'</div>\1',
        content
    )
    
    return content

def main():
    success = fix_module4_responsiveness()
    
    if success:
        print(f"\n🎉 Module 4 responsiveness fixes applied successfully!")
        print(f"📱 Content should now be responsive on mobile, tablet, and desktop")
        print(f"🔄 Next step: Test the lessons on different screen sizes")
    else:
        print(f"\n❌ Failed to apply responsiveness fixes")

if __name__ == "__main__":
    main()
