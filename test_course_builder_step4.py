#!/usr/bin/env python
"""
Test Course Builder Wizard Step 4 (Assessments) Functionality
Comprehensive testing of the assessment creation features
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
from assessments.models import Quiz, Question, Assignment, RubricCriteria
from users.models import InstructorProfile
from course_builder.models import CourseBuilderSession

def create_test_data():
    """Create test instructor, course, and lessons"""
    print("🔧 Setting up test data...")
    
    # Create instructor
    user, created = User.objects.get_or_create(
        username='test_instructor_step4',
        defaults={
            'email': 'step4@example.com',
            'first_name': 'Step4',
            'last_name': 'Instructor',
            'is_active': True,
            'is_staff': True,
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create instructor profile
    profile, profile_created = InstructorProfile.objects.get_or_create(
        user=user,
        defaults={
            'instructor_role': 'course_instructor',
            'bio': 'Test instructor for step 4 testing',
            'verification_status': 'verified',
            'is_active': True,
            'can_create_courses': True,
        }
    )
    
    # Create category
    category, cat_created = Category.objects.get_or_create(
        name='Test Category Step 4',
        defaults={'description': 'Category for step 4 testing', 'is_active': True}
    )
    
    # Create course
    course, course_created = Course.objects.get_or_create(
        title='Test Course for Step 4',
        instructor=user,
        defaults={
            'description': 'Testing step 4 assessments',
            'category': category,
            'difficulty_level': 'beginner',
            'estimated_duration': 5,
            'status': 'in_review'
        }
    )
    
    # Create module
    module, module_created = Module.objects.get_or_create(
        course=course,
        title='Test Module for Assessments',
        defaults={
            'description': 'Module for testing assessments',
            'sort_order': 1,
            'estimated_duration': 120
        }
    )
    
    # Create lessons
    lesson1, lesson1_created = Lesson.objects.get_or_create(
        module=module,
        title='Lesson 1: Introduction',
        defaults={
            'content_type': 'text',
            'content': 'Introduction lesson content',
            'sort_order': 1,
            'estimated_duration': 30
        }
    )
    
    lesson2, lesson2_created = Lesson.objects.get_or_create(
        module=module,
        title='Lesson 2: Advanced Topics',
        defaults={
            'content_type': 'video',
            'video_url': 'https://youtube.com/watch?v=test',
            'sort_order': 2,
            'estimated_duration': 45
        }
    )
    
    # Create course builder session
    session, session_created = CourseBuilderSession.objects.get_or_create(
        instructor=user,
        defaults={
            'course': course,
            'session_data': {
                'course': {
                    'title': course.title,
                    'description': course.description,
                    'category': course.category.id
                },
                'modules': [
                    {
                        'title': module.title,
                        'lessons': [
                            {'id': lesson1.id, 'title': lesson1.title, 'module_title': module.title},
                            {'id': lesson2.id, 'title': lesson2.title, 'module_title': module.title}
                        ]
                    }
                ]
            },
            'current_step': 4
        }
    )
    
    print(f"✅ Test data created:")
    print(f"   User: {user.username}")
    print(f"   Course: {course.title}")
    print(f"   Module: {module.title}")
    print(f"   Lessons: {lesson1.title}, {lesson2.title}")
    print(f"   Session: {session.id}")
    
    return user, course, module, [lesson1, lesson2], session

def test_step4_access(client, user):
    """Test Step 4 page access"""
    print("\n🧪 TESTING STEP 4 ACCESS")
    print("=" * 50)
    
    client.force_login(user)
    
    response = client.get('/course-builder/wizard/step/4/')
    print(f"   Step 4 access: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode()
        
        checks = [
            ('Assessment Type Selector', 'assessmentTypeSelector' in content),
            ('Quiz Creation Panel', 'quizCreationPanel' in content),
            ('Assignment Creation Panel', 'assignmentCreationPanel' in content),
            ('Assessment Management Sidebar', 'assessmentsList' in content),
            ('Question Builder', 'questionsList' in content),
            ('Rubric Builder', 'rubricCriteriaList' in content),
            ('Assessment Statistics', 'totalQuizzes' in content),
            ('JavaScript Functions', 'addQuestion' in content),
        ]
        
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"   {status} {check_name}")
        
        return all(check[1] for check in checks)
    else:
        print("   ❌ Step 4 not accessible")
        return False

def test_quiz_creation(client, user, lessons, session):
    """Test quiz creation functionality"""
    print("\n🧪 TESTING QUIZ CREATION")
    print("=" * 50)
    
    quiz_data = {
        'lesson_id': lessons[0].id,
        'title': 'Test Quiz 1',
        'description': 'A test quiz for validation',
        'instructions': 'Please answer all questions carefully',
        'time_limit': 30,
        'max_attempts': 2,
        'passing_score': 75,
        'is_randomized': True,
        'show_results': True,
        'questions': [
            {
                'question_text': 'What is the capital of France?',
                'question_type': 'multiple_choice',
                'options': ['London', 'Berlin', 'Paris', 'Madrid'],
                'correct_answer': '2',
                'points': 2,
                'explanation': 'Paris is the capital of France',
                'sort_order': 1
            },
            {
                'question_text': 'Python is a programming language.',
                'question_type': 'true_false',
                'options': [],
                'correct_answer': 'true',
                'points': 1,
                'explanation': 'Python is indeed a programming language',
                'sort_order': 2
            }
        ]
    }
    
    response = client.post('/course-builder/api/', {
        'action': 'create_quiz',
        'quiz_data': json.dumps(quiz_data),
        'csrfmiddlewaretoken': client.cookies.get('csrftoken', 'test-token')
    })
    
    print(f"   Quiz creation API: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            quiz_id = data.get('quiz_id')
            print(f"   ✅ Quiz created successfully (ID: {quiz_id})")
            
            # Verify quiz in database
            try:
                quiz = Quiz.objects.get(id=quiz_id)
                print(f"   ✅ Quiz found in database: {quiz.title}")
                print(f"   ✅ Quiz has {quiz.questions.count()} questions")
                print(f"   ✅ Quiz settings: {quiz.time_limit}min, {quiz.max_attempts} attempts, {quiz.passing_score}% pass")
                return True
            except Quiz.DoesNotExist:
                print(f"   ❌ Quiz not found in database")
                return False
        else:
            print(f"   ❌ Quiz creation failed: {data.get('error')}")
            return False
    else:
        print(f"   ❌ Quiz creation API failed")
        return False

def test_assignment_creation(client, user, lessons, session):
    """Test assignment creation functionality"""
    print("\n🧪 TESTING ASSIGNMENT CREATION")
    print("=" * 50)
    
    assignment_data = {
        'lesson_id': lessons[1].id,
        'title': 'Test Assignment 1',
        'assignment_type': 'business_plan',
        'description': 'Create a comprehensive business plan',
        'instructions': '<h2>Assignment Instructions</h2><p>Please create a detailed business plan including market analysis and financial projections.</p>',
        'submission_format': 'both',
        'max_score': 100,
        'due_date': '2025-12-31T23:59:00',
        'max_file_size': 20,
        'allowed_file_types': 'pdf,doc,docx',
        'peer_review_enabled': True,
        'rubric_criteria': [
            {
                'name': 'Content Quality',
                'description': 'Quality and depth of content',
                'max_points': 25,
                'weight': 30,
                'sort_order': 1
            },
            {
                'name': 'Organization',
                'description': 'Structure and organization of the plan',
                'max_points': 20,
                'weight': 25,
                'sort_order': 2
            },
            {
                'name': 'Research',
                'description': 'Quality of market research and analysis',
                'max_points': 25,
                'weight': 30,
                'sort_order': 3
            },
            {
                'name': 'Presentation',
                'description': 'Professional presentation and formatting',
                'max_points': 15,
                'weight': 15,
                'sort_order': 4
            }
        ]
    }
    
    response = client.post('/course-builder/api/', {
        'action': 'create_assignment',
        'assignment_data': json.dumps(assignment_data),
        'csrfmiddlewaretoken': client.cookies.get('csrftoken', 'test-token')
    })
    
    print(f"   Assignment creation API: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            assignment_id = data.get('assignment_id')
            print(f"   ✅ Assignment created successfully (ID: {assignment_id})")
            
            # Verify assignment in database
            try:
                assignment = Assignment.objects.get(id=assignment_id)
                print(f"   ✅ Assignment found in database: {assignment.title}")
                print(f"   ✅ Assignment type: {assignment.assignment_type}")
                print(f"   ✅ Assignment has {assignment.rubric_criteria.count()} rubric criteria")
                print(f"   ✅ Assignment settings: {assignment.max_score} points, {assignment.submission_format} submission")
                return True
            except Assignment.DoesNotExist:
                print(f"   ❌ Assignment not found in database")
                return False
        else:
            print(f"   ❌ Assignment creation failed: {data.get('error')}")
            return False
    else:
        print(f"   ❌ Assignment creation API failed")
        return False

def test_assessments_retrieval(client, user, session):
    """Test assessment retrieval functionality"""
    print("\n🧪 TESTING ASSESSMENTS RETRIEVAL")
    print("=" * 50)
    
    response = client.get(f'/course-builder/api/?action=get_assessments&session_id={session.id}')
    print(f"   Get assessments API: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            assessments = data.get('assessments', [])
            statistics = data.get('statistics', {})
            
            print(f"   ✅ Retrieved {len(assessments)} assessments")
            print(f"   ✅ Statistics: {statistics}")
            
            for assessment in assessments:
                print(f"   ✅ {assessment['type'].upper()}: {assessment['title']} ({assessment['lesson_title']})")
            
            return len(assessments) > 0
        else:
            print(f"   ❌ Get assessments failed: {data.get('error')}")
            return False
    else:
        print(f"   ❌ Get assessments API failed")
        return False

def run_step4_tests():
    """Run comprehensive Step 4 tests"""
    print("🧪 COURSE BUILDER WIZARD STEP 4 - COMPREHENSIVE TEST")
    print("=" * 80)
    
    # Setup
    client = Client()
    user, course, module, lessons, session = create_test_data()
    
    # Test results
    results = {}
    
    # Run tests
    results['step4_access'] = test_step4_access(client, user)
    results['quiz_creation'] = test_quiz_creation(client, user, lessons, session)
    results['assignment_creation'] = test_assignment_creation(client, user, lessons, session)
    results['assessments_retrieval'] = test_assessments_retrieval(client, user, session)
    
    # Summary
    print(f"\n🎯 STEP 4 TEST SUMMARY")
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
        print(f"🎉 ALL STEP 4 TESTS PASSED - ASSESSMENTS WORKING!")
    else:
        print(f"⚠️ SOME TESTS FAILED - REVIEW ISSUES ABOVE")
    
    return passed == total

if __name__ == '__main__':
    success = run_step4_tests()
    sys.exit(0 if success else 1)
