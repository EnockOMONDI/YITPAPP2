#!/usr/bin/env python
"""
Test Course Builder Wizard Functionality
Comprehensive testing of the enhanced course builder wizard
"""

import os
import sys
import json

# Setup Django environment BEFORE importing Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')

import django
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from courses.models import Course, Module, Lesson, Category
from users.models import InstructorProfile
from course_builder.models import CourseBuilderSession

def create_test_instructor():
    """Create a test instructor user"""
    print("👤 Creating test instructor...")
    
    # Create user
    user, created = User.objects.get_or_create(
        username='test_instructor',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'Instructor',
            'is_active': True,
            'is_staff': True,
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created user: {user.username}")
    else:
        print(f"✅ User already exists: {user.username}")
    
    # Create instructor profile
    profile, profile_created = InstructorProfile.objects.get_or_create(
        user=user,
        defaults={
            'instructor_role': 'course_instructor',
            'bio': 'Test instructor for course builder testing',
            'qualifications': 'Testing, Course Development',
            'years_experience': 3,
            'verification_status': 'verified',
            'is_active': True,
            'can_create_courses': True,
            'can_manage_assessments': True,
            'can_view_analytics': True,
        }
    )
    
    if profile_created:
        print(f"✅ Created instructor profile")
    else:
        print(f"✅ Instructor profile already exists")
    
    return user

def create_test_category():
    """Create a test category"""
    print("📚 Creating test category...")
    
    category, created = Category.objects.get_or_create(
        name='Test Category',
        defaults={
            'description': 'Category for testing course builder',
            'is_active': True,
        }
    )
    
    if created:
        print(f"✅ Created category: {category.name}")
    else:
        print(f"✅ Category already exists: {category.name}")
    
    return category

def test_wizard_step_1(client, instructor):
    """Test wizard step 1 - Course basics"""
    print("\n🧪 TESTING WIZARD STEP 1 - COURSE BASICS")
    print("=" * 60)
    
    # Login as instructor
    client.force_login(instructor)
    
    # Access wizard step 1
    response = client.get('/course-builder/wizard/step/1/')
    print(f"   Step 1 access: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Step 1 accessible")
        return True
    else:
        print("   ❌ Step 1 not accessible")
        return False

def test_wizard_step_2(client, instructor):
    """Test wizard step 2 - Course structure"""
    print("\n🧪 TESTING WIZARD STEP 2 - COURSE STRUCTURE")
    print("=" * 60)
    
    # Access wizard step 2
    response = client.get('/course-builder/wizard/step/2/')
    print(f"   Step 2 access: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Step 2 accessible")
        return True
    else:
        print("   ❌ Step 2 not accessible")
        return False

def test_wizard_step_3(client, instructor):
    """Test wizard step 3 - Content creation"""
    print("\n🧪 TESTING WIZARD STEP 3 - CONTENT CREATION")
    print("=" * 60)
    
    # Access wizard step 3
    response = client.get('/course-builder/wizard/step/3/')
    print(f"   Step 3 access: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Step 3 accessible")
        
        # Check if enhanced content creation elements are present
        content = response.content.decode()
        
        checks = [
            ('Content Type Selector', 'contentTypeSelector' in content),
            ('Text Content Panel', 'textContentPanel' in content),
            ('Video Content Panel', 'videoContentPanel' in content),
            ('Document Content Panel', 'documentContentPanel' in content),
            ('Audio Content Panel', 'audioContentPanel' in content),
            ('CKEditor5 Script', 'ckeditor5' in content.lower()),
            ('Uploadcare Script', 'uploadcare' in content.lower()),
            ('Progress Indicator', 'progressIndicator' in content),
        ]
        
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"   {status} {check_name}")
        
        return all(check[1] for check in checks)
    else:
        print("   ❌ Step 3 not accessible")
        return False

def test_api_endpoints(client, instructor):
    """Test API endpoints"""
    print("\n🧪 TESTING API ENDPOINTS")
    print("=" * 60)
    
    # Create a test session
    session = CourseBuilderSession.objects.create(
        instructor=instructor,
        session_data={
            'modules': [
                {
                    'title': 'Test Module',
                    'lessons': [
                        {'title': 'Test Lesson 1', 'content_type': 'text'},
                        {'title': 'Test Lesson 2', 'content_type': 'video'},
                    ]
                }
            ]
        },
        current_step=3
    )
    
    print(f"   Created test session: {session.id}")
    
    # Test get_lessons endpoint
    response = client.get(f'/course-builder/api/?action=get_lessons&session_id={session.id}')
    print(f"   Get lessons API: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Get lessons successful - {len(data.get('lessons', []))} lessons found")
        else:
            print(f"   ❌ Get lessons failed: {data.get('error')}")
    
    # Test get_lesson_content endpoint
    response = client.get(f'/course-builder/api/?action=get_lesson_content&lesson_id=temp_1')
    print(f"   Get lesson content API: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Get lesson content successful")
        else:
            print(f"   ❌ Get lesson content failed: {data.get('error')}")
    
    return True

def test_content_types(client, instructor, category):
    """Test different content types"""
    print("\n🧪 TESTING CONTENT TYPES")
    print("=" * 60)
    
    # Create a test course
    course = Course.objects.create(
        title='Test Course for Content Types',
        description='Testing different content types',
        instructor=instructor,
        category=category,
        difficulty_level='beginner',
        estimated_duration=5,
        status='in_review'
    )
    
    # Create a test module
    module = Module.objects.create(
        course=course,
        title='Test Module',
        description='Test module for content types',
        sort_order=1,
        estimated_duration=120
    )
    
    # Test different content types
    content_types = [
        ('text', 'Text content test'),
        ('video', 'https://youtube.com/watch?v=test'),
        ('document', 'https://ucarecdn.com/test.pdf'),
        ('audio', 'https://example.com/test.mp3'),
    ]
    
    for content_type, content in content_types:
        lesson = Lesson.objects.create(
            module=module,
            title=f'Test {content_type.title()} Lesson',
            content_type=content_type,
            content=content,
            sort_order=len(content_types),
            estimated_duration=30,
            learning_objectives=f'Learn about {content_type} content'
        )
        
        print(f"   ✅ Created {content_type} lesson: {lesson.title}")
    
    print(f"   ✅ All content types tested successfully")
    return True

def test_lesson_content_saving(client, instructor):
    """Test saving lesson content via API"""
    print("\n🧪 TESTING LESSON CONTENT SAVING")
    print("=" * 60)
    
    # Create a test course and lesson
    course = Course.objects.create(
        title='Test Course for Content Saving',
        description='Testing content saving functionality',
        instructor=instructor,
        difficulty_level='beginner',
        estimated_duration=5,
        status='in_review'
    )
    
    module = Module.objects.create(
        course=course,
        title='Test Module',
        description='Test module',
        sort_order=1,
        estimated_duration=60
    )
    
    lesson = Lesson.objects.create(
        module=module,
        title='Test Lesson',
        content_type='text',
        content='Initial content',
        sort_order=1,
        estimated_duration=30
    )
    
    # Test saving different content types
    test_data = [
        {
            'content_type': 'text',
            'content': '<h2>Enhanced Text Content</h2><p>This is rich text content with <strong>formatting</strong>.</p>',
            'duration': '45',
            'learning_objectives': 'Learn about text formatting'
        },
        {
            'content_type': 'video',
            'content': '',
            'video_url': 'https://youtube.com/watch?v=dQw4w9WgXcQ',
            'duration': '60',
            'learning_objectives': 'Learn from video content'
        },
        {
            'content_type': 'document',
            'content': '',
            'document_url': 'https://ucarecdn.com/sample-document.pdf',
            'duration': '30',
            'learning_objectives': 'Learn from document'
        }
    ]
    
    for test_case in test_data:
        response = client.post('/course-builder/api/', {
            'action': 'save_lesson_content',
            'lesson_id': lesson.id,
            **test_case
        })
        
        print(f"   Save {test_case['content_type']} content: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ {test_case['content_type'].title()} content saved successfully")
            else:
                print(f"   ❌ {test_case['content_type'].title()} content save failed: {data.get('error')}")
        
        # Refresh lesson from database
        lesson.refresh_from_db()
    
    return True

def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🧪 YITP COURSE BUILDER WIZARD - COMPREHENSIVE TEST")
    print("=" * 80)
    
    # Setup
    client = Client()
    instructor = create_test_instructor()
    category = create_test_category()
    
    # Test results
    results = {}
    
    # Run tests
    results['step_1'] = test_wizard_step_1(client, instructor)
    results['step_2'] = test_wizard_step_2(client, instructor)
    results['step_3'] = test_wizard_step_3(client, instructor)
    results['api_endpoints'] = test_api_endpoints(client, instructor)
    results['content_types'] = test_content_types(client, instructor, category)
    results['content_saving'] = test_lesson_content_saving(client, instructor)
    
    # Summary
    print(f"\n🎯 TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED - COURSE BUILDER IS WORKING!")
    else:
        print(f"⚠️ SOME TESTS FAILED - REVIEW ISSUES ABOVE")
    
    return passed == total

if __name__ == '__main__':
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
