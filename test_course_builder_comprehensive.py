#!/usr/bin/env python
"""
Comprehensive Course Builder Wizard Testing
Tests the complete workflow and identifies issues with lesson dropdown
"""

import os
import sys
import json

# Setup Django environment
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
    """Create test instructor for comprehensive testing"""
    print("👤 Creating comprehensive test instructor...")
    
    user, created = User.objects.get_or_create(
        username='comprehensive_test_instructor',
        defaults={
            'email': 'comprehensive@example.com',
            'first_name': 'Comprehensive',
            'last_name': 'Tester',
            'is_active': True,
            'is_staff': True,
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
    
    profile, profile_created = InstructorProfile.objects.get_or_create(
        user=user,
        defaults={
            'instructor_role': 'course_instructor',
            'bio': 'Comprehensive testing instructor',
            'verification_status': 'verified',
            'is_active': True,
            'can_create_courses': True,
        }
    )
    
    print(f"✅ Instructor created: {user.username}")
    return user

def test_complete_wizard_workflow(client, user):
    """Test the complete wizard workflow from Step 1 to Step 5"""
    print("\n🧪 TESTING COMPLETE WIZARD WORKFLOW")
    print("=" * 60)
    
    client.force_login(user)
    
    # Test Step 1 - Course Basics
    print("   Testing Step 1 - Course Basics...")
    response = client.get('/course-builder/wizard/step/1/')
    if response.status_code != 200:
        print(f"   ❌ Step 1 access failed: {response.status_code}")
        return False
    
    # Create course basics using save_session
    step1_data = {
        'action': 'save_session',
        'session_data': json.dumps({
            'course': {
                'title': 'Comprehensive Test Course',
                'description': 'A comprehensive test course for wizard testing',
                'category': '1',  # Assuming category 1 exists
                'difficulty_level': 'beginner',
                'estimated_duration': '10'
            }
        }),
        'current_step': '1',
        'csrfmiddlewaretoken': client.cookies.get('csrftoken', 'test-token')
    }
    
    response = client.post('/course-builder/api/', step1_data)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            session_id = data.get('session_id')
            print(f"   ✅ Step 1 completed - Session ID: {session_id}")
        else:
            print(f"   ❌ Step 1 save failed: {data.get('error')}")
            return False
    else:
        print(f"   ❌ Step 1 API failed: {response.status_code}")
        return False
    
    # Test Step 2 - Course Structure
    print("   Testing Step 2 - Course Structure...")
    response = client.get(f'/course-builder/wizard/step/2/?session={session_id}')
    if response.status_code != 200:
        print(f"   ❌ Step 2 access failed: {response.status_code}")
        return False
    
    # Create course structure using save_session
    structure_data = {
        'action': 'save_session',
        'session_id': session_id,
        'session_data': json.dumps({
            'course': {
                'title': 'Comprehensive Test Course',
                'description': 'A comprehensive test course for wizard testing',
                'category': '1',
                'difficulty_level': 'beginner',
                'estimated_duration': '10'
            },
            'modules': [
                {
                    'title': 'Module 1: Introduction',
                    'description': 'Introduction to the course',
                    'lessons': [
                        {'title': 'Lesson 1: Welcome', 'content_type': 'text', 'estimated_duration': 30},
                        {'title': 'Lesson 2: Overview', 'content_type': 'video', 'estimated_duration': 45}
                    ]
                },
                {
                    'title': 'Module 2: Advanced Topics',
                    'description': 'Advanced course content',
                    'lessons': [
                        {'title': 'Lesson 3: Deep Dive', 'content_type': 'text', 'estimated_duration': 60},
                        {'title': 'Lesson 4: Case Study', 'content_type': 'document', 'estimated_duration': 30}
                    ]
                }
            ]
        }),
        'current_step': '2',
        'csrfmiddlewaretoken': client.cookies.get('csrftoken', 'test-token')
    }
    
    response = client.post('/course-builder/api/', structure_data)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Step 2 completed - Structure saved")
        else:
            print(f"   ❌ Step 2 save failed: {data.get('error')}")
            return False
    else:
        print(f"   ❌ Step 2 API failed: {response.status_code}")
        return False
    
    # Test Step 3 - Content Creation (THE PROBLEMATIC STEP)
    print("   Testing Step 3 - Content Creation...")
    response = client.get(f'/course-builder/wizard/step/3/?session={session_id}')
    if response.status_code != 200:
        print(f"   ❌ Step 3 access failed: {response.status_code}")
        return False
    
    # Test lesson dropdown population
    print("   Testing lesson dropdown API...")
    response = client.get(f'/course-builder/api/?action=get_lessons&session_id={session_id}')
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            lessons = data.get('lessons', [])
            print(f"   ✅ Lessons API working - Found {len(lessons)} lessons")
            for lesson in lessons:
                print(f"      - {lesson['module_title']}: {lesson['title']} (ID: {lesson['id']})")
            
            if len(lessons) == 0:
                print("   ⚠️ WARNING: No lessons found in session data!")
                return False
        else:
            print(f"   ❌ Lessons API failed: {data.get('error')}")
            return False
    else:
        print(f"   ❌ Lessons API request failed: {response.status_code}")
        return False
    
    # Test Step 4 - Assessments
    print("   Testing Step 4 - Assessments...")
    response = client.get(f'/course-builder/wizard/step/4/?session={session_id}')
    if response.status_code != 200:
        print(f"   ❌ Step 4 access failed: {response.status_code}")
        return False
    else:
        print(f"   ✅ Step 4 accessible")
    
    # Test Step 5 - Publishing
    print("   Testing Step 5 - Publishing...")
    response = client.get(f'/course-builder/wizard/step/5/?session={session_id}')
    if response.status_code != 200:
        print(f"   ❌ Step 5 access failed: {response.status_code}")
        return False
    else:
        print(f"   ✅ Step 5 accessible")
    
    return True, session_id

def test_session_data_persistence(client, user, session_id):
    """Test session data persistence across steps"""
    print("\n🧪 TESTING SESSION DATA PERSISTENCE")
    print("=" * 60)
    
    # Get session data
    response = client.post('/course-builder/api/', {
        'action': 'get_session',
        'session_id': session_id,
        'csrfmiddlewaretoken': client.cookies.get('csrftoken', 'test-token')
    })
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            session_data = data.get('session_data', {})
            print(f"   ✅ Session data retrieved")
            print(f"   Course: {session_data.get('course', {}).get('title', 'N/A')}")
            
            modules = session_data.get('modules', [])
            print(f"   Modules: {len(modules)}")
            
            total_lessons = 0
            for i, module in enumerate(modules):
                lessons = module.get('lessons', [])
                total_lessons += len(lessons)
                print(f"      Module {i+1}: {module.get('title', 'Untitled')} - {len(lessons)} lessons")
            
            print(f"   Total lessons: {total_lessons}")
            return total_lessons > 0
        else:
            print(f"   ❌ Session data retrieval failed: {data.get('error')}")
            return False
    else:
        print(f"   ❌ Session API failed: {response.status_code}")
        return False

def test_lesson_content_management(client, user, session_id):
    """Test lesson content management functionality"""
    print("\n🧪 TESTING LESSON CONTENT MANAGEMENT")
    print("=" * 60)
    
    # Get lessons first
    response = client.get(f'/course-builder/api/?action=get_lessons&session_id={session_id}')
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('lessons'):
            lesson = data['lessons'][0]  # Test with first lesson
            lesson_id = lesson['id']
            
            print(f"   Testing with lesson: {lesson['title']} (ID: {lesson_id})")
            
            # Test getting lesson content
            response = client.get(f'/course-builder/api/?action=get_lesson_content&lesson_id={lesson_id}')
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ Lesson content retrieval working")
                    
                    # Test saving lesson content
                    content_data = {
                        'action': 'save_lesson_content',
                        'lesson_id': lesson_id,
                        'content_type': 'text',
                        'content': '<h2>Test Content</h2><p>This is test content for the lesson.</p>',
                        'duration': '45',
                        'learning_objectives': 'Test learning objectives',
                        'csrfmiddlewaretoken': client.cookies.get('csrftoken', 'test-token')
                    }
                    
                    response = client.post('/course-builder/api/', content_data)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success'):
                            print(f"   ✅ Lesson content saving working")
                            return True
                        else:
                            print(f"   ❌ Lesson content save failed: {data.get('error')}")
                    else:
                        print(f"   ❌ Lesson content save API failed: {response.status_code}")
                else:
                    print(f"   ❌ Lesson content retrieval failed: {data.get('error')}")
            else:
                print(f"   ❌ Lesson content API failed: {response.status_code}")
        else:
            print(f"   ❌ No lessons available for testing")
    else:
        print(f"   ❌ Get lessons API failed: {response.status_code}")
    
    return False

def run_comprehensive_tests():
    """Run comprehensive Course Builder Wizard tests"""
    print("🧪 COURSE BUILDER WIZARD - COMPREHENSIVE TESTING")
    print("=" * 80)
    
    # Setup
    client = Client()
    user = create_test_instructor()
    
    # Test results
    results = {}
    
    # Run tests
    workflow_result = test_complete_wizard_workflow(client, user)
    if isinstance(workflow_result, tuple):
        results['complete_workflow'] = workflow_result[0]
        session_id = workflow_result[1]
        
        # Continue with other tests using the session
        results['session_persistence'] = test_session_data_persistence(client, user, session_id)
        results['content_management'] = test_lesson_content_management(client, user, session_id)
    else:
        results['complete_workflow'] = workflow_result
        results['session_persistence'] = False
        results['content_management'] = False
    
    # Summary
    print(f"\n🎯 COMPREHENSIVE TEST SUMMARY")
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
        print(f"🎉 ALL TESTS PASSED - COURSE BUILDER WORKING!")
    else:
        print(f"⚠️ SOME TESTS FAILED - ISSUES IDENTIFIED")
        
        if not results.get('complete_workflow'):
            print("🔍 ISSUE: Complete workflow failed - check lesson dropdown population")
        if not results.get('session_persistence'):
            print("🔍 ISSUE: Session data persistence failed")
        if not results.get('content_management'):
            print("🔍 ISSUE: Lesson content management failed")
    
    return passed == total

if __name__ == '__main__':
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
