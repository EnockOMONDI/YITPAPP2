#!/usr/bin/env python
"""
Upload YITP Course to Production Only
Re-upload the course to production database
"""

import os
import sys
import django
import json
from decimal import Decimal

# Setup production environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'
django.setup()

def create_instructor_user():
    """Create instructor user 'yitp1' in production"""
    print("👤 CREATING INSTRUCTOR USER - PRODUCTION")
    print("=" * 60)
    
    try:
        from django.contrib.auth.models import User
        from users.models import InstructorProfile
        
        # Check if user exists
        instructor_user, created = User.objects.get_or_create(
            username='yitp1',
            defaults={
                'email': 'yitp1@youthimpactglobal.com',
                'first_name': 'YITP',
                'last_name': 'Instructor',
                'is_active': True,
                'is_staff': True,
            }
        )
        
        if created:
            instructor_user.set_password('YITPInstructor2025!')
            instructor_user.save()
            print(f"✅ Created instructor user: {instructor_user.username}")
        else:
            print(f"✅ Instructor user already exists: {instructor_user.username}")
        
        # Create or get instructor profile
        instructor_profile, profile_created = InstructorProfile.objects.get_or_create(
            user=instructor_user,
            defaults={
                'instructor_role': 'course_instructor',
                'bio': 'YITP Course Instructor specializing in youth development and purpose-driven training.',
                'qualifications': 'Youth Development, Purpose Discovery, Leadership Training',
                'years_experience': 5,
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
        
        return instructor_user
        
    except Exception as e:
        print(f"❌ Error creating instructor: {str(e)}")
        return None

def create_category_if_needed():
    """Create Personal Development category if not exists"""
    try:
        from courses.models import Category
        
        category, created = Category.objects.get_or_create(
            name='Personal Development',
            defaults={
                'description': 'Courses focused on personal growth, self-discovery, and life skills development.',
                'is_active': True,
            }
        )
        
        if created:
            print(f"✅ Created category: {category.name}")
        else:
            print(f"✅ Category already exists: {category.name}")
        
        return category
        
    except Exception as e:
        print(f"❌ Error creating category: {str(e)}")
        return None

def upload_course():
    """Upload the YITP course to production"""
    print("📤 UPLOADING COURSE TO PRODUCTION")
    print("=" * 60)
    
    try:
        # Load course JSON
        with open('yitpcours001.json', 'r') as f:
            course_json = json.load(f)
        
        from courses.models import Course, Module, Lesson
        from assessments.models import Quiz, Question
        
        # Create instructor
        instructor_user = create_instructor_user()
        if not instructor_user:
            return False
        
        # Create category
        category = create_category_if_needed()
        if not category:
            return False
        
        # Fix course data
        course_data = course_json['course'].copy()
        
        # Fix learning_objectives (array to string)
        if isinstance(course_data['learning_objectives'], list):
            course_data['learning_objectives'] = '\n'.join(f"• {obj}" for obj in course_data['learning_objectives'])
        
        # Add missing required fields
        course_data['estimated_duration'] = 10  # 10 hours estimated
        course_data['price'] = Decimal('39.00')  # $39 as specified
        
        # Check if course exists and delete it
        existing_courses = Course.objects.filter(title=course_data['title'])
        if existing_courses.exists():
            print(f"⚠️ Found existing course, deleting...")
            for existing_course in existing_courses:
                existing_course.delete()
        
        # Create course
        course = Course.objects.create(
            title=course_data['title'],
            description=course_data['description'],
            learning_objectives=course_data['learning_objectives'],
            prerequisites=course_data.get('prerequisites', ''),
            difficulty_level=course_data['difficulty_level'],
            estimated_duration=course_data['estimated_duration'],
            status='published',  # Set to published
            is_published=True,   # Make it published
            is_featured=course_data['is_featured'],
            price=course_data['price'],
            instructor=instructor_user,
            category=category,
        )
        
        print(f"✅ Created course: {course.title}")
        print(f"   Course ID: {course.id}")
        print(f"   Status: {course.status}")
        print(f"   Published: {course.is_published}")
        
        # Create modules and lessons
        for module_data in course_json['modules']:
            module = Module.objects.create(
                course=course,
                title=module_data['title'],
                description=module_data['description'],
                sort_order=module_data['sort_order'],
                estimated_duration=module_data['estimated_duration'],
                is_published=True,  # Publish module
                unlock_criteria=module_data.get('unlock_criteria', {}),
            )
            
            print(f"✅ Created module: {module.title}")
            
            # Create lessons
            for lesson_data in module_data['lessons']:
                lesson = Lesson.objects.create(
                    module=module,
                    title=lesson_data['title'],
                    content_type=lesson_data['content_type'],
                    content=lesson_data['content'],
                    sort_order=lesson_data['sort_order'],
                    estimated_duration=lesson_data['estimated_duration'],
                    is_mandatory=lesson_data['is_mandatory'],
                    is_published=True,  # Publish lesson
                    learning_objectives=lesson_data.get('learning_objectives', ''),
                    resources=lesson_data.get('resources', []),
                )
                
                print(f"   ✅ Created lesson: {lesson.title}")
                
                # Create quiz if exists
                if 'quiz' in lesson_data:
                    quiz_data = lesson_data['quiz']
                    
                    quiz = Quiz.objects.create(
                        lesson=lesson,
                        title=quiz_data['title'],
                        description=quiz_data['description'],
                        instructions=quiz_data['instructions'],
                        time_limit=quiz_data.get('time_limit'),
                        max_attempts=quiz_data['max_attempts'],
                        passing_score=quiz_data['passing_score'],
                        is_randomized=quiz_data['is_randomized'],
                        show_results=quiz_data['show_results'],
                        is_published=True,  # Publish quiz
                    )
                    
                    print(f"      ✅ Created quiz: {quiz.title}")
                    
                    # Create questions
                    for question_data in quiz_data['questions']:
                        # Fix question data
                        if question_data['question_type'] == 'true_false':
                            if isinstance(question_data['correct_answer'], bool):
                                question_data['correct_answer'] = str(question_data['correct_answer']).lower()
                        
                        question = Question.objects.create(
                            quiz=quiz,
                            question_text=question_data['question_text'],
                            question_type=question_data['question_type'],
                            options=question_data.get('options', []),
                            correct_answer=question_data['correct_answer'],
                            explanation=question_data.get('explanation', ''),
                            points=question_data['points'],
                            sort_order=question_data['sort_order'],
                        )
        
        print(f"\n🎉 PRODUCTION UPLOAD SUCCESSFUL!")
        print(f"   Course: {course.title}")
        print(f"   ID: {course.id}")
        print(f"   Status: {course.status}")
        print(f"   Published: {course.is_published}")
        print(f"   Price: ${course.price}")
        print(f"   URL: https://www.youthimpactglobal.com/lms/courses/{course.slug}/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error uploading course: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("📤 YITP COURSE UPLOAD TO PRODUCTION")
    print("=" * 80)
    
    success = upload_course()
    
    if success:
        print(f"\n✅ UPLOAD COMPLETED SUCCESSFULLY!")
        print(f"   Course is now PUBLISHED and visible to students")
        print(f"   Students can enroll at $39.00 USD")
    else:
        print(f"\n❌ UPLOAD FAILED")

if __name__ == '__main__':
    main()
