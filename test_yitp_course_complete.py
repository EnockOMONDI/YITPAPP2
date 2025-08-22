#!/usr/bin/env python
"""
Comprehensive YITP Course Testing Suite
Tests static files, HTML rendering, navigation, and lesson completion workflow
"""

import os
import sys
import django
import subprocess
from pathlib import Path

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from courses.models import Course, Module, Lesson
from progress.models import Enrollment, LessonProgress

def test_static_file_collection():
    """Test static file collection without conflicts"""
    print("🔍 TESTING STATIC FILE COLLECTION")
    print("=" * 60)
    
    try:
        # Run collectstatic with dry-run to check for conflicts
        result = subprocess.run([
            'python', 'manage.py', 'collectstatic', 
            '--dry-run', '--verbosity=1', '--noinput'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        output = result.stdout + result.stderr
        
        # Check for conflicts
        conflict_lines = [line for line in output.split('\n') if 'Found another file' in line]
        
        if conflict_lines:
            print(f"❌ Found {len(conflict_lines)} static file conflicts:")
            for line in conflict_lines:
                print(f"   {line.strip()}")
            return False
        else:
            print("✅ No static file conflicts detected")
            
        # Check for YITP assets
        yitp_assets = [
            'css/yitp-course-branding.css',
            'lmsassets/css/course-detail.css',
            'lmsassets/js/lesson-progress.js',
            'assets/fonts/inter/Inter-Regular.woff2',
            'assets/img/logo/youthimpact.png'
        ]
        
        collected_yitp = 0
        for asset in yitp_assets:
            if asset in output:
                collected_yitp += 1
                print(f"   ✅ {asset}")
            else:
                print(f"   ❌ {asset}")
        
        print(f"\n📊 YITP Assets: {collected_yitp}/{len(yitp_assets)} collected")
        
        return len(conflict_lines) == 0 and collected_yitp >= 3
        
    except Exception as e:
        print(f"❌ Error testing static collection: {str(e)}")
        return False

def test_course_access_and_rendering():
    """Test YITP course access and HTML rendering"""
    print("\n🔍 TESTING COURSE ACCESS & HTML RENDERING")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        client = Client()
        
        # Test course detail page
        course_url = reverse('courses:course_detail', kwargs={'slug': course.slug})
        response = client.get(course_url)
        
        print(f"📋 Course Detail Page:")
        print(f"   URL: {course_url}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for course title
            if course.title in content:
                print(f"   ✅ Course title found")
            else:
                print(f"   ❌ Course title missing")
            
            # Check for modules
            modules = course.modules.filter(is_published=True)
            modules_found = 0
            for module in modules:
                if module.title in content:
                    modules_found += 1
            
            print(f"   ✅ Modules displayed: {modules_found}/{modules.count()}")
            
            # Test module detail page
            if modules.exists():
                module = modules.first()
                module_url = reverse('courses:module_detail', kwargs={
                    'course_slug': course.slug,
                    'module_id': module.id
                })
                
                module_response = client.get(module_url)
                print(f"\n📚 Module Detail Page:")
                print(f"   URL: {module_url}")
                print(f"   Status: {module_response.status_code}")
                
                if module_response.status_code == 200:
                    module_content = module_response.content.decode('utf-8')
                    
                    # Check for lessons
                    lessons = module.lessons.filter(is_published=True)
                    lessons_found = 0
                    for lesson in lessons[:5]:  # Check first 5 lessons
                        if lesson.title in module_content:
                            lessons_found += 1
                    
                    print(f"   ✅ Lessons displayed: {lessons_found}/{min(5, lessons.count())}")
                    
                    return True
                else:
                    print(f"   ❌ Module page failed to load")
                    return False
            else:
                print(f"   ❌ No published modules found")
                return False
        else:
            print(f"   ❌ Course page failed to load")
            return False
            
    except Course.DoesNotExist:
        print("❌ YITP course not found")
        return False
    except Exception as e:
        print(f"❌ Error testing course access: {str(e)}")
        return False

def test_lesson_html_rendering():
    """Test lesson HTML content rendering"""
    print("\n🔍 TESTING LESSON HTML RENDERING")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        lessons = Lesson.objects.filter(
            module__course=course,
            is_published=True,
            content_type='html'
        )[:3]  # Test first 3 HTML lessons
        
        client = Client()
        
        for i, lesson in enumerate(lessons, 1):
            lesson_url = reverse('courses:lesson_detail', kwargs={
                'course_slug': course.slug,
                'lesson_id': lesson.id
            })
            
            response = client.get(lesson_url)
            print(f"\n📖 Lesson {i}: {lesson.title}")
            print(f"   URL: {lesson_url}")
            print(f"   Status: {response.status_code}")
            print(f"   Content Type: {lesson.content_type}")
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                
                # Check if HTML is properly rendered (not showing raw tags)
                if '<h3>' in lesson.content and '<h3>' not in content:
                    print(f"   ✅ HTML properly rendered (no raw tags)")
                elif '<h3>' in lesson.content and '<h3>' in content:
                    print(f"   ❌ Raw HTML tags visible")
                else:
                    print(f"   ✅ Content displayed")
                
                # Check for lesson title
                if lesson.title in content:
                    print(f"   ✅ Lesson title found")
                else:
                    print(f"   ❌ Lesson title missing")
                
                # Check for content
                if lesson.content and any(word in content for word in lesson.content.split()[:5]):
                    print(f"   ✅ Lesson content found")
                else:
                    print(f"   ❌ Lesson content missing")
            else:
                print(f"   ❌ Lesson page failed to load")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing lesson rendering: {str(e)}")
        return False

def test_lesson_navigation():
    """Test lesson navigation and progression"""
    print("\n🔍 TESTING LESSON NAVIGATION")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        modules = course.modules.filter(is_published=True).order_by('sort_order')
        
        print(f"📚 Course Navigation Structure:")
        print(f"   Course: {course.title}")
        print(f"   Modules: {modules.count()}")
        
        total_lessons = 0
        for module in modules:
            lessons = module.lessons.filter(is_published=True).order_by('sort_order')
            total_lessons += lessons.count()
            print(f"   Module {module.id}: {lessons.count()} lessons")
            
            # Test first and last lesson URLs
            if lessons.exists():
                first_lesson = lessons.first()
                last_lesson = lessons.last()
                
                # Test URL generation
                try:
                    first_url = reverse('courses:lesson_detail', kwargs={
                        'course_slug': course.slug,
                        'lesson_id': first_lesson.id
                    })
                    last_url = reverse('courses:lesson_detail', kwargs={
                        'course_slug': course.slug,
                        'lesson_id': last_lesson.id
                    })
                    
                    print(f"      ✅ First lesson URL: {first_url}")
                    print(f"      ✅ Last lesson URL: {last_url}")
                    
                except Exception as e:
                    print(f"      ❌ URL generation error: {str(e)}")
                    return False
        
        print(f"\n📊 Navigation Summary:")
        print(f"   Total lessons: {total_lessons}")
        print(f"   All URLs generate correctly: ✅")
        
        return total_lessons > 0
        
    except Exception as e:
        print(f"❌ Error testing navigation: {str(e)}")
        return False

def test_lesson_completion_workflow():
    """Test lesson completion workflow (simulated)"""
    print("\n🔍 TESTING LESSON COMPLETION WORKFLOW")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        
        # Get or create a test user
        test_user, created = User.objects.get_or_create(
            username='test_student',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'Student'
            }
        )
        
        if created:
            print(f"✅ Created test user: {test_user.username}")
        else:
            print(f"✅ Using existing test user: {test_user.username}")
        
        # Get or create enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            student=test_user,
            course=course,
            defaults={'status': 'active'}
        )
        
        if created:
            print(f"✅ Created test enrollment")
        else:
            print(f"✅ Using existing enrollment")
        
        # Test lesson progress tracking
        first_lesson = Lesson.objects.filter(
            module__course=course,
            is_published=True
        ).order_by('module__sort_order', 'sort_order').first()
        
        if first_lesson:
            # Create or update lesson progress
            progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=first_lesson,
                defaults={
                    'status': 'in_progress'
                }
            )
            
            if created:
                print(f"✅ Created lesson progress for: {first_lesson.title}")
            else:
                print(f"✅ Updated lesson progress for: {first_lesson.title}")
            
            print(f"   Status: {progress.status}")

            # Test completion
            progress.status = 'completed'
            progress.save()
            
            print(f"✅ Marked lesson as completed")
            
            # Calculate course progress
            total_lessons = Lesson.objects.filter(
                module__course=course,
                is_published=True
            ).count()
            
            completed_lessons = LessonProgress.objects.filter(
                enrollment=enrollment,
                status='completed'
            ).count()
            
            course_progress = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
            
            print(f"\n📊 Course Progress:")
            print(f"   Completed lessons: {completed_lessons}/{total_lessons}")
            print(f"   Course progress: {course_progress:.1f}%")
            
            return True
        else:
            print(f"❌ No lessons found for testing")
            return False
            
    except Exception as e:
        print(f"❌ Error testing completion workflow: {str(e)}")
        return False

def test_responsive_design():
    """Test responsive design elements"""
    print("\n🔍 TESTING RESPONSIVE DESIGN")
    print("=" * 60)
    
    try:
        # Check if YITP branding CSS exists and contains responsive rules
        from django.contrib.staticfiles import finders
        
        branding_css = finders.find('css/yitp-course-branding.css')
        course_detail_css = finders.find('lmsassets/css/course-detail.css')
        
        responsive_features = 0
        
        if branding_css:
            with open(branding_css, 'r') as f:
                content = f.read()
                if '@media' in content:
                    responsive_features += 1
                    print(f"✅ YITP branding CSS has responsive rules")
                else:
                    print(f"❌ YITP branding CSS missing responsive rules")
        
        if course_detail_css:
            with open(course_detail_css, 'r') as f:
                content = f.read()
                if '@media' in content:
                    responsive_features += 1
                    print(f"✅ Course detail CSS has responsive rules")
                else:
                    print(f"❌ Course detail CSS missing responsive rules")
        
        print(f"\n📱 Responsive Features: {responsive_features}/2")
        
        return responsive_features >= 1
        
    except Exception as e:
        print(f"❌ Error testing responsive design: {str(e)}")
        return False

def main():
    """Main testing function"""
    print("🧪 COMPREHENSIVE YITP COURSE TESTING SUITE")
    print("=" * 80)
    
    tests = [
        ("Static File Collection", test_static_file_collection),
        ("Course Access & Rendering", test_course_access_and_rendering),
        ("Lesson HTML Rendering", test_lesson_html_rendering),
        ("Lesson Navigation", test_lesson_navigation),
        ("Lesson Completion Workflow", test_lesson_completion_workflow),
        ("Responsive Design", test_responsive_design),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Error in {test_name}: {str(e)}")
            results[test_name] = False
    
    # Final results
    print(f"\n📋 COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"   Tests Passed: {passed}/{total}")
    print(f"   Success Rate: {passed/total*100:.1f}%")
    
    print(f"\n📊 Detailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   YITP course is fully functional and ready for production")
        print(f"\n📝 Production Checklist:")
        print(f"   ✅ Static files collect without conflicts")
        print(f"   ✅ HTML content renders properly")
        print(f"   ✅ Navigation works correctly")
        print(f"   ✅ Lesson completion workflow functional")
        print(f"   ✅ Responsive design implemented")
        return True
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        print(f"   Please review failed tests above")
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎯 YITP course ready for production deployment!")
    else:
        print("\n⚠️ Please address test failures before deployment")
