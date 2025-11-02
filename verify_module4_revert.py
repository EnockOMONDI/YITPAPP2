#!/usr/bin/env python3
"""
Verify that Module 4 has been successfully reverted to original state
"""

import os
import django
import re
from bs4 import BeautifulSoup

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson

def verify_module4_revert():
    """Verify that Module 4 has been reverted to original state"""
    
    print("🔍 VERIFYING MODULE 4 REVERT TO ORIGINAL STATE")
    print("=" * 60)
    
    try:
        # Get the course and Module 4
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module4 = Module.objects.get(course=course, sort_order=4)
        
        print(f"✅ Found Module 4: {module4.title}")
        
        # Get all lessons in Module 4
        lessons = Lesson.objects.filter(module=module4).order_by('sort_order')
        print(f"📚 Analyzing {lessons.count()} lessons...")
        
        total_original_indicators = 0
        total_responsive_indicators = 0
        lessons_with_original_structure = 0
        lessons_with_pdf2htmlex_css = 0
        
        for lesson in lessons:
            print(f"\n📖 Analyzing {lesson.title}...")
            
            if not lesson.content:
                print(f"   ⚠️  No content to analyze")
                continue
            
            # Check for original structure indicators
            has_original_structure = check_original_structure(lesson.content)
            if has_original_structure:
                lessons_with_original_structure += 1
                print(f"   ✅ Has original YITP structure")
            else:
                print(f"   ❌ Missing original YITP structure")
            
            # Check for pdf2htmlEX CSS
            has_pdf2htmlex = check_pdf2htmlex_css(lesson.content)
            if has_pdf2htmlex:
                lessons_with_pdf2htmlex_css += 1
                print(f"   ✅ Has original pdf2htmlEX CSS")
            else:
                print(f"   ❌ Missing pdf2htmlEX CSS")
            
            # Check for responsive fixes (should be ABSENT)
            has_responsive_fixes = check_responsive_fixes(lesson.content)
            if has_responsive_fixes:
                print(f"   ❌ Still contains responsive fixes (should be removed)")
            else:
                print(f"   ✅ No responsive fixes found (correct)")
            
            # Count original vs responsive indicators
            original_count, responsive_count = count_structure_indicators(lesson.content)
            total_original_indicators += original_count
            total_responsive_indicators += responsive_count
            
            print(f"   📊 Original structure indicators: {original_count}")
            print(f"   📊 Responsive fix indicators: {responsive_count}")
            
            # Check content characteristics
            content_length = len(lesson.content)
            print(f"   📏 Content length: {content_length:,} characters")
            
            # Calculate revert success score
            revert_score = calculate_revert_score(
                has_original_structure, has_pdf2htmlex, not has_responsive_fixes, 
                original_count, responsive_count
            )
            print(f"   📈 Revert success score: {revert_score}/100")
        
        print(f"\n📊 OVERALL REVERT SUMMARY:")
        print(f"   • Total lessons: {lessons.count()}")
        print(f"   • Lessons with original structure: {lessons_with_original_structure}/{lessons.count()}")
        print(f"   • Lessons with pdf2htmlEX CSS: {lessons_with_pdf2htmlex_css}/{lessons.count()}")
        print(f"   • Total original indicators: {total_original_indicators}")
        print(f"   • Total responsive indicators remaining: {total_responsive_indicators}")
        
        # Overall assessment
        overall_score = (
            (lessons_with_original_structure / lessons.count() * 40) +
            (lessons_with_pdf2htmlex_css / lessons.count() * 40) +
            (max(0, 20 - (total_responsive_indicators * 2)))  # Penalty for remaining responsive fixes
        )
        
        print(f"   📈 Overall revert success score: {overall_score:.1f}/100")
        
        if overall_score >= 90:
            print(f"   🎉 EXCELLENT - Module 4 successfully reverted to original state!")
        elif overall_score >= 70:
            print(f"   ✅ GOOD - Module 4 mostly reverted successfully")
        elif overall_score >= 50:
            print(f"   ⚠️  PARTIAL - Module 4 partially reverted")
        else:
            print(f"   ❌ FAILED - Module 4 revert was not successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying Module 4 revert: {e}")
        return False

def check_original_structure(content):
    """Check if content has original YITP structure"""
    original_indicators = [
        'class="lesson-content"',
        'class="lesson-header"',
        'class="lesson-body"',
        'class="lesson-footer"',
        'background: linear-gradient(135deg, #ff5d15, #1a2e53)',
        'Complete this lesson and take the quiz'
    ]
    
    return all(indicator in content for indicator in original_indicators)

def check_pdf2htmlex_css(content):
    """Check if content has original pdf2htmlEX CSS"""
    pdf2htmlex_indicators = [
        'Base CSS for pdf2htmlEX',
        'Lu Wang <coolwanglu@gmail.com>',
        '.pf{position:relative',
        '.pc{position:absolute',
        '.t{position:absolute',
        'data-page-no'
    ]
    
    return any(indicator in content for indicator in pdf2htmlex_indicators)

def check_responsive_fixes(content):
    """Check if content still contains responsive fixes (should be absent)"""
    responsive_fix_indicators = [
        'YITP Responsive Overrides',
        'max-width: 100% !important',
        'overflow-x: auto !important',
        'position: relative !important',
        '@media (max-width: 768px)',
        'container-fluid'
    ]
    
    return any(indicator in content for indicator in responsive_fix_indicators)

def count_structure_indicators(content):
    """Count original vs responsive structure indicators"""
    
    # Count original structure indicators
    original_patterns = [
        r'class="lesson-content"',
        r'class="lesson-header"',
        r'class="lesson-body"',
        r'class="page-content"',
        r'data-page-no=',
        r'\.pf\{',
        r'\.pc\{',
        r'\.t\{'
    ]
    
    original_count = 0
    for pattern in original_patterns:
        original_count += len(re.findall(pattern, content, re.IGNORECASE))
    
    # Count responsive fix indicators (should be 0)
    responsive_patterns = [
        r'max-width:\s*100%\s*!important',
        r'overflow-x:\s*auto\s*!important',
        r'position:\s*relative\s*!important',
        r'@media\s*\(',
        r'container-fluid'
    ]
    
    responsive_count = 0
    for pattern in responsive_patterns:
        responsive_count += len(re.findall(pattern, content, re.IGNORECASE))
    
    return original_count, responsive_count

def calculate_revert_score(has_original, has_pdf2htmlex, no_responsive_fixes, original_count, responsive_count):
    """Calculate a revert success score out of 100"""
    
    score = 0
    
    # Original structure (30 points)
    if has_original:
        score += 30
    
    # pdf2htmlEX CSS (30 points)
    if has_pdf2htmlex:
        score += 30
    
    # No responsive fixes (20 points)
    if no_responsive_fixes:
        score += 20
    
    # Structure indicators ratio (20 points)
    if responsive_count == 0:
        score += 20
    elif original_count > responsive_count * 5:
        score += 15
    elif original_count > responsive_count:
        score += 10
    elif original_count > 0:
        score += 5
    
    return min(score, 100)

def main():
    success = verify_module4_revert()
    
    if success:
        print(f"\n🔍 Module 4 revert verification completed!")
        print(f"📊 Check the summary above for detailed results")
    else:
        print(f"\n❌ Failed to verify Module 4 revert")

if __name__ == "__main__":
    main()
