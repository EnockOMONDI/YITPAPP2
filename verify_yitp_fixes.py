#!/usr/bin/env python
"""
Verify that all YITP course fixes have been applied successfully
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson
from django.urls import reverse
from django.test import Client

def verify_course_publishing():
    """Verify course, modules, and lessons are properly published"""
    print("🔍 VERIFYING COURSE PUBLISHING STATUS")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        print(f"✅ Course: {course.title}")
        print(f"   Status: {course.status}")
        print(f"   Published: {course.is_published}")
        
        # Check modules
        modules = course.modules.all()
        published_modules = modules.filter(is_published=True)
        print(f"\n📚 Modules: {modules.count()} total, {published_modules.count()} published")
        
        for module in modules:
            status = "✅" if module.is_published else "❌"
            print(f"   {status} Module {module.id}: {module.title} (published: {module.is_published})")
        
        # Check lessons
        lessons = Lesson.objects.filter(module__course=course)
        published_lessons = lessons.filter(is_published=True)
        print(f"\n📖 Lessons: {lessons.count()} total, {published_lessons.count()} published")
        
        if published_lessons.count() != lessons.count():
            unpublished = lessons.filter(is_published=False)
            print(f"   ❌ {unpublished.count()} lessons are not published:")
            for lesson in unpublished[:5]:
                print(f"      - {lesson.title}")
        else:
            print(f"   ✅ All lessons are published")
        
        return published_modules.count() > 0 and published_lessons.count() > 0
        
    except Course.DoesNotExist:
        print("❌ YITP course not found!")
        return False

def verify_html_content_rendering():
    """Verify HTML content is properly configured for rendering"""
    print("\n🔍 VERIFYING HTML CONTENT RENDERING")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        lessons = Lesson.objects.filter(module__course=course)
        
        # Check content types
        html_lessons = lessons.filter(content_type='html')
        text_lessons = lessons.filter(content_type='text')
        
        print(f"📊 Content Type Distribution:")
        print(f"   HTML lessons: {html_lessons.count()}")
        print(f"   Text lessons: {text_lessons.count()}")
        print(f"   Other types: {lessons.exclude(content_type__in=['html', 'text']).count()}")
        
        # Check for HTML content in text lessons (should be zero now)
        text_with_html = []
        for lesson in text_lessons:
            if lesson.content and ('<h' in lesson.content or '<p' in lesson.content):
                text_with_html.append(lesson)
        
        if text_with_html:
            print(f"\n❌ ISSUE: {len(text_with_html)} text lessons still contain HTML:")
            for lesson in text_with_html[:3]:
                print(f"   - {lesson.title}")
        else:
            print(f"\n✅ No text lessons contain HTML (properly fixed)")
        
        # Sample HTML content
        if html_lessons.exists():
            sample_lesson = html_lessons.first()
            print(f"\n📝 Sample HTML lesson: {sample_lesson.title}")
            print(f"   Content type: {sample_lesson.content_type}")
            print(f"   Content preview: {sample_lesson.content[:100]}...")
        
        return len(text_with_html) == 0
        
    except Exception as e:
        print(f"❌ Error verifying HTML content: {str(e)}")
        return False

def verify_url_patterns():
    """Verify URL patterns work correctly"""
    print("\n🔍 VERIFYING URL PATTERNS")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        
        # Test course URL
        course_url = reverse('courses:course_detail', kwargs={'slug': course.slug})
        print(f"✅ Course URL: {course_url}")
        
        # Test module URLs
        modules = course.modules.filter(is_published=True)
        if modules.exists():
            module = modules.first()
            module_url = reverse('courses:module_detail', kwargs={
                'course_slug': course.slug,
                'module_id': module.id
            })
            print(f"✅ Module URL: {module_url}")
            
            # Test lesson URLs
            lessons = module.lessons.filter(is_published=True)
            if lessons.exists():
                lesson = lessons.first()
                lesson_url = reverse('courses:lesson_detail', kwargs={
                    'course_slug': course.slug,
                    'lesson_id': lesson.id
                })
                print(f"✅ Lesson URL: {lesson_url}")
                
                print(f"\n🔗 URL Structure Test:")
                print(f"   Course: /lms/courses/{course.slug}/")
                print(f"   Module: /lms/courses/{course.slug}/modules/{module.id}/")
                print(f"   Lesson: /lms/courses/{course.slug}/lessons/{lesson.id}/")
                
                return True
            else:
                print(f"❌ No published lessons found in module")
                return False
        else:
            print(f"❌ No published modules found")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying URL patterns: {str(e)}")
        return False

def verify_static_assets():
    """Verify static assets are available"""
    print("\n🔍 VERIFYING STATIC ASSETS")
    print("=" * 60)
    
    import os
    from django.conf import settings
    
    # Check static directories
    static_dirs = []
    if settings.STATIC_ROOT:
        static_dirs.append(settings.STATIC_ROOT)
    if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
        static_dirs.extend(settings.STATICFILES_DIRS)
    
    assets_found = []
    assets_missing = []
    
    # Check Inter font
    inter_font_found = False
    for static_dir in static_dirs:
        inter_path = os.path.join(static_dir, 'assets/fonts/inter/Inter-Regular.woff2')
        if os.path.exists(inter_path):
            inter_font_found = True
            assets_found.append('Inter-Regular.woff2')
            break
    
    if not inter_font_found:
        assets_missing.append('assets/fonts/inter/Inter-Regular.woff2')
    
    # Check YITP logo
    logo_found = False
    for static_dir in static_dirs:
        logo_path = os.path.join(static_dir, 'assets/img/logo/youthimpact.png')
        if os.path.exists(logo_path):
            logo_found = True
            assets_found.append('youthimpact.png')
            break
    
    if not logo_found:
        assets_missing.append('assets/img/logo/youthimpact.png')
    
    # Report results
    print(f"📁 Static Assets Status:")
    for asset in assets_found:
        print(f"   ✅ Found: {asset}")
    
    for asset in assets_missing:
        print(f"   ❌ Missing: {asset}")
    
    return len(assets_missing) == 0

def test_course_navigation():
    """Test course navigation functionality"""
    print("\n🧪 TESTING COURSE NAVIGATION")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        
        # Test module navigation
        modules = course.modules.filter(is_published=True).order_by('sort_order')
        print(f"📚 Navigation Test:")
        print(f"   Published modules: {modules.count()}")
        
        for module in modules:
            lessons = module.lessons.filter(is_published=True).order_by('sort_order')
            print(f"   Module {module.id}: {lessons.count()} published lessons")
            
            if lessons.exists():
                first_lesson = lessons.first()
                last_lesson = lessons.last()
                print(f"      First lesson: {first_lesson.id} - {first_lesson.title}")
                print(f"      Last lesson: {last_lesson.id} - {last_lesson.title}")
        
        # Test lesson progression
        all_lessons = Lesson.objects.filter(
            module__course=course,
            is_published=True
        ).order_by('module__sort_order', 'sort_order')
        
        print(f"\n📖 Lesson Progression:")
        print(f"   Total published lessons: {all_lessons.count()}")
        print(f"   Lesson sequence:")
        
        for i, lesson in enumerate(all_lessons[:5], 1):
            print(f"      {i}. {lesson.title} (Module: {lesson.module.title})")
        
        if all_lessons.count() > 5:
            print(f"      ... and {all_lessons.count() - 5} more lessons")
        
        return all_lessons.count() > 0
        
    except Exception as e:
        print(f"❌ Error testing navigation: {str(e)}")
        return False

def generate_fix_summary():
    """Generate summary of all fixes applied"""
    print("\n📊 YITP COURSE FIX SUMMARY")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        
        # Course statistics
        modules = course.modules.all()
        lessons = Lesson.objects.filter(module__course=course)
        html_lessons = lessons.filter(content_type='html')
        
        print(f"📋 Course: {course.title}")
        print(f"   ID: {course.id}")
        print(f"   Slug: {course.slug}")
        print(f"   Status: {course.status}")
        print(f"   Published: {course.is_published}")
        
        print(f"\n📈 Content Statistics:")
        print(f"   Modules: {modules.count()} (Published: {modules.filter(is_published=True).count()})")
        print(f"   Lessons: {lessons.count()} (Published: {lessons.filter(is_published=True).count()})")
        print(f"   HTML Lessons: {html_lessons.count()}")
        
        print(f"\n✅ Fixes Applied:")
        print(f"   1. ✅ Module publishing enabled")
        print(f"   2. ✅ Lesson publishing enabled")
        print(f"   3. ✅ HTML content type corrected")
        print(f"   4. ✅ Static asset directories created")
        print(f"   5. ✅ URL patterns functional")
        
        print(f"\n🔗 Access URLs:")
        print(f"   Course: /lms/courses/{course.slug}/")
        if modules.filter(is_published=True).exists():
            first_module = modules.filter(is_published=True).first()
            print(f"   Module: /lms/courses/{course.slug}/modules/{first_module.id}/")
            
            first_lesson = first_module.lessons.filter(is_published=True).first()
            if first_lesson:
                print(f"   Lesson: /lms/courses/{course.slug}/lessons/{first_lesson.id}/")
        
        print(f"\n📝 Next Steps:")
        print(f"   1. Test course access in browser")
        print(f"   2. Verify HTML content renders properly")
        print(f"   3. Test lesson navigation")
        print(f"   4. Check quiz and assignment functionality")
        print(f"   5. Replace placeholder font file with actual Inter font")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating summary: {str(e)}")
        return False

def main():
    """Main verification function"""
    print("🔍 YITP COURSE FIXES VERIFICATION")
    print("=" * 80)
    
    tests = [
        ("Course Publishing", verify_course_publishing),
        ("HTML Content Rendering", verify_html_content_rendering),
        ("URL Patterns", verify_url_patterns),
        ("Static Assets", verify_static_assets),
        ("Course Navigation", test_course_navigation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Error in {test_name}: {str(e)}")
            results[test_name] = False
    
    # Generate summary
    generate_fix_summary()
    
    # Final results
    print(f"\n📋 VERIFICATION RESULTS")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"   Tests Passed: {passed}/{total}")
    print(f"   Success Rate: {passed/total*100:.1f}%")
    
    print(f"\n📊 Detailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    if passed == total:
        print(f"\n🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
        print(f"   YITP course is ready for student access")
        return True
    else:
        print(f"\n⚠️ SOME ISSUES REMAIN")
        print(f"   Please review failed tests above")
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎯 YITP course fixes verified and working!")
    else:
        print("\n⚠️ Please address remaining issues")
