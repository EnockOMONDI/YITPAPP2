#!/usr/bin/env python
"""
Fix critical YITP course issues:
1. HTML content rendering problem
2. LMS URL pattern error with empty module_id
3. Missing static assets
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson
from django.contrib.auth.models import User

def analyze_course_issues():
    """Analyze the specific issues with the YITP course"""
    print("🔍 ANALYZING YITP COURSE ISSUES")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        print(f"✅ Found course: {course.title} (ID: {course.id})")
        
        # Check modules
        modules = course.modules.all()
        print(f"📚 Modules: {modules.count()}")
        
        for module in modules:
            print(f"   Module {module.id}: {module.title}")
            print(f"   Published: {module.is_published}")
            
            # Check lessons
            lessons = module.lessons.all()
            print(f"   Lessons: {lessons.count()}")
            
            # Check for HTML content issues
            html_issues = 0
            for lesson in lessons[:3]:  # Check first 3 lessons
                if '<' in lesson.content and '>' in lesson.content:
                    html_issues += 1
                    print(f"   ⚠️ Lesson '{lesson.title}' contains HTML tags")
                    print(f"      Content preview: {lesson.content[:100]}...")
            
            if html_issues > 0:
                print(f"   🚨 Found {html_issues} lessons with HTML content issues")
        
        # Check module publishing status
        unpublished_modules = modules.filter(is_published=False)
        if unpublished_modules.exists():
            print(f"\n🚨 ISSUE FOUND: {unpublished_modules.count()} modules are not published")
            for module in unpublished_modules:
                print(f"   ❌ Module {module.id}: {module.title} (is_published=False)")
        
        # Check lesson publishing status
        unpublished_lessons = Lesson.objects.filter(module__course=course, is_published=False)
        if unpublished_lessons.exists():
            print(f"\n🚨 ISSUE FOUND: {unpublished_lessons.count()} lessons are not published")
            print(f"   This will cause empty module_id in URLs")
        
        return course, modules, unpublished_modules, unpublished_lessons
        
    except Course.DoesNotExist:
        print("❌ YITP course not found!")
        return None, None, None, None

def fix_module_publishing():
    """Fix module publishing status"""
    print("\n🔧 FIXING MODULE PUBLISHING STATUS")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        
        # Publish all modules
        unpublished_modules = course.modules.filter(is_published=False)
        if unpublished_modules.exists():
            updated_count = unpublished_modules.update(is_published=True)
            print(f"✅ Published {updated_count} modules")
            
            for module in unpublished_modules:
                print(f"   ✅ Module {module.id}: {module.title} → is_published=True")
        else:
            print("✅ All modules are already published")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing module publishing: {str(e)}")
        return False

def fix_lesson_publishing():
    """Fix lesson publishing status"""
    print("\n🔧 FIXING LESSON PUBLISHING STATUS")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        
        # Publish all lessons
        unpublished_lessons = Lesson.objects.filter(module__course=course, is_published=False)
        if unpublished_lessons.exists():
            updated_count = unpublished_lessons.update(is_published=True)
            print(f"✅ Published {updated_count} lessons")
            
            # Show sample of updated lessons
            for lesson in unpublished_lessons[:5]:
                print(f"   ✅ Lesson {lesson.id}: {lesson.title} → is_published=True")
            
            if unpublished_lessons.count() > 5:
                print(f"   ... and {unpublished_lessons.count() - 5} more lessons")
        else:
            print("✅ All lessons are already published")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing lesson publishing: {str(e)}")
        return False

def analyze_html_content_issues():
    """Analyze HTML content rendering issues"""
    print("\n🔍 ANALYZING HTML CONTENT ISSUES")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        lessons = Lesson.objects.filter(module__course=course)
        
        html_lessons = []
        for lesson in lessons:
            if lesson.content and ('<h' in lesson.content or '<p' in lesson.content or '<div' in lesson.content):
                html_lessons.append(lesson)
        
        print(f"📊 Analysis Results:")
        print(f"   Total Lessons: {lessons.count()}")
        print(f"   Lessons with HTML: {len(html_lessons)}")
        
        if html_lessons:
            print(f"\n📝 HTML CONTENT SAMPLES:")
            for lesson in html_lessons[:3]:
                print(f"   Lesson: {lesson.title}")
                print(f"   Content Type: {lesson.content_type}")
                print(f"   Content Preview: {lesson.content[:150]}...")
                print()
        
        # Check if content_type is correct
        text_type_with_html = [l for l in html_lessons if l.content_type == 'text']
        if text_type_with_html:
            print(f"🚨 ISSUE: {len(text_type_with_html)} lessons have content_type='text' but contain HTML")
            print("   These should be content_type='html' for proper rendering")
        
        return html_lessons, text_type_with_html
        
    except Exception as e:
        print(f"❌ Error analyzing HTML content: {str(e)}")
        return [], []

def fix_content_type_for_html():
    """Fix content_type for lessons with HTML content"""
    print("\n🔧 FIXING CONTENT TYPE FOR HTML LESSONS")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        lessons = Lesson.objects.filter(module__course=course, content_type='text')
        
        html_lessons = []
        for lesson in lessons:
            if lesson.content and ('<h' in lesson.content or '<p' in lesson.content or '<div' in lesson.content):
                html_lessons.append(lesson)
        
        if html_lessons:
            # Update content_type to 'html' for proper rendering
            updated_count = 0
            for lesson in html_lessons:
                lesson.content_type = 'html'
                lesson.save()
                updated_count += 1
                print(f"   ✅ Lesson {lesson.id}: {lesson.title} → content_type='html'")
            
            print(f"\n✅ Updated {updated_count} lessons to content_type='html'")
        else:
            print("✅ No lessons need content_type updates")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing content types: {str(e)}")
        return False

def check_static_assets():
    """Check for missing static assets"""
    print("\n🔍 CHECKING STATIC ASSETS")
    print("=" * 60)
    
    import os
    from django.conf import settings
    
    # Check for missing assets
    missing_assets = []
    
    # Check Inter font
    inter_font_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'assets/fonts/inter/Inter-Regular.woff2')
    if not os.path.exists(inter_font_path):
        missing_assets.append('assets/fonts/inter/Inter-Regular.woff2')
        print("❌ Missing: Inter-Regular.woff2 font file")
    else:
        print("✅ Found: Inter-Regular.woff2 font file")
    
    # Check YITP logo
    logo_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'assets/img/logo/youthimpact.png')
    if not os.path.exists(logo_path):
        missing_assets.append('assets/img/logo/youthimpact.png')
        print("❌ Missing: youthimpact.png logo file")
    else:
        print("✅ Found: youthimpact.png logo file")
    
    # Check static directories
    print(f"\n📁 Static Configuration:")
    print(f"   STATIC_URL: {settings.STATIC_URL}")
    print(f"   STATIC_ROOT: {settings.STATIC_ROOT}")
    if hasattr(settings, 'STATICFILES_DIRS'):
        print(f"   STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
    
    return missing_assets

def create_missing_static_assets():
    """Create placeholder for missing static assets"""
    print("\n🔧 CREATING MISSING STATIC ASSETS")
    print("=" * 60)
    
    import os
    from django.conf import settings
    
    # Create directories if they don't exist
    static_dir = settings.STATIC_ROOT or (settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else 'static')
    
    # Create font directory
    font_dir = os.path.join(static_dir, 'assets/fonts/inter')
    os.makedirs(font_dir, exist_ok=True)
    
    # Create logo directory
    logo_dir = os.path.join(static_dir, 'assets/img/logo')
    os.makedirs(logo_dir, exist_ok=True)
    
    print(f"✅ Created directories:")
    print(f"   {font_dir}")
    print(f"   {logo_dir}")
    
    # Note: Actual font and logo files need to be provided separately
    print(f"\n📝 NOTE: You'll need to add the actual files:")
    print(f"   - Inter-Regular.woff2 font file")
    print(f"   - youthimpact.png logo file")

def test_course_access():
    """Test course access and URL generation"""
    print("\n🧪 TESTING COURSE ACCESS")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        
        # Test module access
        modules = course.modules.filter(is_published=True)
        print(f"📚 Published Modules: {modules.count()}")
        
        for module in modules:
            print(f"   Module {module.id}: {module.title}")
            
            # Test lesson access
            lessons = module.lessons.filter(is_published=True)
            print(f"      Published Lessons: {lessons.count()}")
            
            if lessons.exists():
                first_lesson = lessons.first()
                print(f"      First Lesson: {first_lesson.id} - {first_lesson.title}")
                print(f"      Content Type: {first_lesson.content_type}")
            else:
                print("      ❌ No published lessons found")
        
        # Test URL generation
        if modules.exists():
            first_module = modules.first()
            print(f"\n🔗 URL Testing:")
            print(f"   Course URL: /lms/courses/{course.slug}/")
            print(f"   Module URL: /lms/courses/{course.slug}/modules/{first_module.id}/")
            
            if first_module.lessons.filter(is_published=True).exists():
                first_lesson = first_module.lessons.filter(is_published=True).first()
                print(f"   Lesson URL: /lms/courses/{course.slug}/lessons/{first_lesson.id}/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing course access: {str(e)}")
        return False

def main():
    """Main function to fix all YITP course issues"""
    print("🔧 YITP COURSE ISSUES FIX")
    print("=" * 80)
    
    # Analyze issues
    course, modules, unpublished_modules, unpublished_lessons = analyze_course_issues()
    
    if not course:
        print("❌ Cannot proceed without course")
        return False
    
    fixes_applied = []
    
    # Fix 1: Module publishing (fixes empty module_id issue)
    if unpublished_modules and unpublished_modules.exists():
        if fix_module_publishing():
            fixes_applied.append("Module publishing")
    
    # Fix 2: Lesson publishing (fixes URL pattern issues)
    if unpublished_lessons and unpublished_lessons.exists():
        if fix_lesson_publishing():
            fixes_applied.append("Lesson publishing")
    
    # Fix 3: HTML content rendering
    html_lessons, text_type_with_html = analyze_html_content_issues()
    if text_type_with_html:
        if fix_content_type_for_html():
            fixes_applied.append("HTML content rendering")
    
    # Fix 4: Static assets
    missing_assets = check_static_assets()
    if missing_assets:
        create_missing_static_assets()
        fixes_applied.append("Static asset directories")
    
    # Test final state
    test_course_access()
    
    # Summary
    print(f"\n📊 FIX SUMMARY")
    print("=" * 60)
    print(f"   Fixes Applied: {len(fixes_applied)}")
    
    if fixes_applied:
        print(f"\n✅ FIXES APPLIED:")
        for fix in fixes_applied:
            print(f"   • {fix}")
        
        print(f"\n📝 NEXT STEPS:")
        print(f"   1. Test course access: /lms/courses/{course.slug}/")
        print(f"   2. Verify HTML content renders properly")
        print(f"   3. Check module navigation works")
        print(f"   4. Add missing static asset files")
        print(f"   5. Test lesson progression")
        
        return True
    else:
        print(f"\n✅ No fixes needed - course appears to be working correctly")
        return True

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎉 YITP course issues have been addressed!")
    else:
        print("\n⚠️ Some issues may require manual intervention")
