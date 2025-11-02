#!/usr/bin/env python3
"""
Verify Module 4 responsiveness fixes
"""

import os
import django
import re
from bs4 import BeautifulSoup

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson

def verify_module4_responsiveness():
    """Verify that Module 4 responsiveness fixes were applied correctly"""
    
    print("🔍 VERIFYING MODULE 4 RESPONSIVENESS FIXES")
    print("=" * 60)
    
    try:
        # Get the course and Module 4
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module4 = Module.objects.get(course=course, sort_order=4)
        
        print(f"✅ Found Module 4: {module4.title}")
        
        # Get all lessons in Module 4
        lessons = Lesson.objects.filter(module=module4).order_by('sort_order')
        print(f"📚 Analyzing {lessons.count()} lessons...")
        
        total_responsive_elements = 0
        total_fixed_elements = 0
        lessons_with_responsive_css = 0
        lessons_with_bootstrap_classes = 0
        
        for lesson in lessons:
            print(f"\n📖 Analyzing {lesson.title}...")
            
            if not lesson.content:
                print(f"   ⚠️  No content to analyze")
                continue
            
            # Parse the content
            soup = BeautifulSoup(lesson.content, 'html.parser')
            
            # Check for responsive CSS
            has_responsive_css = check_responsive_css(lesson.content)
            if has_responsive_css:
                lessons_with_responsive_css += 1
                print(f"   ✅ Has responsive CSS overrides")
            else:
                print(f"   ❌ Missing responsive CSS overrides")
            
            # Check for Bootstrap classes
            has_bootstrap = check_bootstrap_classes(soup)
            if has_bootstrap:
                lessons_with_bootstrap_classes += 1
                print(f"   ✅ Has Bootstrap responsive classes")
            else:
                print(f"   ❌ Missing Bootstrap responsive classes")
            
            # Count responsive vs fixed elements
            responsive_count, fixed_count = count_responsive_elements(lesson.content)
            total_responsive_elements += responsive_count
            total_fixed_elements += fixed_count
            
            print(f"   📊 Responsive elements: {responsive_count}")
            print(f"   📊 Fixed-width elements remaining: {fixed_count}")
            
            # Check content length
            content_length = len(lesson.content)
            print(f"   📏 Content length: {content_length:,} characters")
            
            # Estimate responsiveness score
            responsiveness_score = calculate_responsiveness_score(
                has_responsive_css, has_bootstrap, responsive_count, fixed_count
            )
            print(f"   📈 Responsiveness score: {responsiveness_score}/100")
        
        print(f"\n📊 OVERALL SUMMARY:")
        print(f"   • Total lessons: {lessons.count()}")
        print(f"   • Lessons with responsive CSS: {lessons_with_responsive_css}/{lessons.count()}")
        print(f"   • Lessons with Bootstrap classes: {lessons_with_bootstrap_classes}/{lessons.count()}")
        print(f"   • Total responsive elements: {total_responsive_elements}")
        print(f"   • Total fixed elements remaining: {total_fixed_elements}")
        
        # Overall assessment
        overall_score = (
            (lessons_with_responsive_css / lessons.count() * 40) +
            (lessons_with_bootstrap_classes / lessons.count() * 30) +
            (min(total_responsive_elements / max(total_fixed_elements, 1), 5) * 6)
        )
        
        print(f"   📈 Overall responsiveness score: {overall_score:.1f}/100")
        
        if overall_score >= 80:
            print(f"   🎉 EXCELLENT - Module 4 is highly responsive!")
        elif overall_score >= 60:
            print(f"   ✅ GOOD - Module 4 has good responsiveness")
        elif overall_score >= 40:
            print(f"   ⚠️  FAIR - Module 4 has basic responsiveness")
        else:
            print(f"   ❌ POOR - Module 4 needs more responsiveness work")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying Module 4 responsiveness: {e}")
        return False

def check_responsive_css(content):
    """Check if content has responsive CSS overrides"""
    responsive_indicators = [
        'max-width: 100%',
        'overflow-x: auto',
        '@media',
        'container-fluid',
        'position: relative !important'
    ]
    
    return any(indicator in content for indicator in responsive_indicators)

def check_bootstrap_classes(soup):
    """Check if content has Bootstrap responsive classes"""
    bootstrap_classes = [
        'container-fluid',
        'img-fluid',
        'table-responsive',
        'col-',
        'row'
    ]
    
    for element in soup.find_all():
        if element.get('class'):
            classes = ' '.join(element.get('class'))
            if any(bootstrap_class in classes for bootstrap_class in bootstrap_classes):
                return True
    
    return False

def count_responsive_elements(content):
    """Count responsive vs fixed-width elements"""
    
    # Count responsive indicators
    responsive_patterns = [
        r'max-width:\s*100%',
        r'width:\s*100%',
        r'position:\s*relative',
        r'overflow:\s*visible',
        r'@media'
    ]
    
    responsive_count = 0
    for pattern in responsive_patterns:
        responsive_count += len(re.findall(pattern, content, re.IGNORECASE))
    
    # Count fixed-width indicators
    fixed_patterns = [
        r'width:\s*\d+px',
        r'min-width:\s*\d+px',
        r'position:\s*absolute',
        r'position:\s*fixed'
    ]
    
    fixed_count = 0
    for pattern in fixed_patterns:
        fixed_count += len(re.findall(pattern, content, re.IGNORECASE))
    
    return responsive_count, fixed_count

def calculate_responsiveness_score(has_css, has_bootstrap, responsive_count, fixed_count):
    """Calculate a responsiveness score out of 100"""
    
    score = 0
    
    # Responsive CSS (40 points)
    if has_css:
        score += 40
    
    # Bootstrap classes (30 points)
    if has_bootstrap:
        score += 30
    
    # Element ratio (30 points)
    if fixed_count == 0:
        score += 30
    elif responsive_count > fixed_count:
        score += 20
    elif responsive_count > 0:
        score += 10
    
    return min(score, 100)

def main():
    success = verify_module4_responsiveness()
    
    if success:
        print(f"\n🔍 Module 4 responsiveness verification completed!")
        print(f"📱 Check the summary above for detailed results")
    else:
        print(f"\n❌ Failed to verify Module 4 responsiveness")

if __name__ == "__main__":
    main()
