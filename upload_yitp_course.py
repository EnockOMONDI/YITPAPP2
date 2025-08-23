#!/usr/bin/env python
"""
Upload YITP Course from yitpcours001.json
Creates instructor 'yitp1' and uploads course to both development and production
"""

import os
import sys
import django
import json
from decimal import Decimal
from datetime import datetime

def setup_django_environment(environment='development'):
    """Setup Django environment for specified database"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    
    if environment == 'production':
        os.environ['DJANGO_ENV'] = 'production'
    else:
        os.environ.pop('DJANGO_ENV', None)  # Remove to ensure development mode
    
    django.setup()

def create_instructor_user(environment):
    """Create instructor user 'yitp1' if not exists"""
    print(f"👤 CREATING INSTRUCTOR USER - {environment.upper()}")
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
            print(f"   Email: {instructor_user.email}")
            print(f"   Password: YITPInstructor2025!")
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

def fix_course_data(course_data):
    """Fix course data to match our model requirements"""
    print("🔧 FIXING COURSE DATA STRUCTURE")
    print("=" * 60)
    
    # Fix learning_objectives (array to string)
    if isinstance(course_data['learning_objectives'], list):
        course_data['learning_objectives'] = '\n'.join(f"• {obj}" for obj in course_data['learning_objectives'])
        print("✅ Fixed learning_objectives format")
    
    # Add missing required fields
    course_data['estimated_duration'] = 10  # 10 hours estimated
    course_data['price'] = Decimal('39.00')  # $39 as specified
    print("✅ Added estimated_duration and price")
    
    return course_data

def fix_lesson_data(lesson_data):
    """Fix lesson data to match our model requirements"""
    # Fix resources format
    if 'resources' in lesson_data and isinstance(lesson_data['resources'], list):
        # Convert to our JSONField format
        lesson_data['resources'] = lesson_data['resources']
    
    # Remove presentation_file for now (we'll handle file uploads separately)
    if 'presentation_file' in lesson_data:
        del lesson_data['presentation_file']
    
    return lesson_data

def fix_question_data(question_data):
    """Fix question data to match our model requirements"""
    # Fix true_false correct_answer format
    if question_data['question_type'] == 'true_false':
        if isinstance(question_data['correct_answer'], bool):
            question_data['correct_answer'] = str(question_data['correct_answer']).lower()
    
    # Ensure options is a list for multiple_choice
    if question_data['question_type'] == 'multiple_choice':
        if 'options' not in question_data:
            question_data['options'] = []
    
    return question_data

def upload_course_to_database(course_json, instructor_user, category, environment):
    """Upload course data to database"""
    print(f"📤 UPLOADING COURSE TO {environment.upper()} DATABASE")
    print("=" * 60)
    
    try:
        from courses.models import Course, Module, Lesson
        from assessments.models import Quiz, Question
        
        # Fix course data
        course_data = fix_course_data(course_json['course'].copy())
        
        # Check if course with same title exists and delete it
        existing_courses = Course.objects.filter(title=course_data['title'])
        if existing_courses.exists():
            print(f"   ⚠️ Found existing course with same title, deleting...")
            for existing_course in existing_courses:
                print(f"      Deleting: {existing_course.title} (ID: {existing_course.id})")
                existing_course.delete()

        # Create course
        course = Course.objects.create(
            title=course_data['title'],
            description=course_data['description'],
            learning_objectives=course_data['learning_objectives'],
            prerequisites=course_data.get('prerequisites', ''),
            difficulty_level=course_data['difficulty_level'],
            estimated_duration=course_data['estimated_duration'],
            status=course_data['status'],
            is_published=course_data['is_published'],
            is_featured=course_data['is_featured'],
            price=course_data['price'],
            instructor=instructor_user,
            category=category,
        )
        
        print(f"✅ Created course: {course.title}")
        print(f"   Course ID: {course.id}")
        print(f"   Course Slug: {course.slug}")
        
        # Create modules and lessons
        for module_data in course_json['modules']:
            module = Module.objects.create(
                course=course,
                title=module_data['title'],
                description=module_data['description'],
                sort_order=module_data['sort_order'],
                estimated_duration=module_data['estimated_duration'],
                is_published=module_data['is_published'],
                unlock_criteria=module_data.get('unlock_criteria', {}),
            )
            
            print(f"✅ Created module: {module.title}")
            
            # Create lessons
            for lesson_data in module_data['lessons']:
                fixed_lesson_data = fix_lesson_data(lesson_data.copy())
                
                lesson = Lesson.objects.create(
                    module=module,
                    title=fixed_lesson_data['title'],
                    content_type=fixed_lesson_data['content_type'],
                    content=fixed_lesson_data['content'],
                    sort_order=fixed_lesson_data['sort_order'],
                    estimated_duration=fixed_lesson_data['estimated_duration'],
                    is_mandatory=fixed_lesson_data['is_mandatory'],
                    is_published=fixed_lesson_data['is_published'],
                    learning_objectives=fixed_lesson_data.get('learning_objectives', ''),
                    resources=fixed_lesson_data.get('resources', []),
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
                        is_published=quiz_data['is_published'],
                    )
                    
                    print(f"      ✅ Created quiz: {quiz.title}")
                    
                    # Create questions
                    for question_data in quiz_data['questions']:
                        fixed_question_data = fix_question_data(question_data.copy())
                        
                        question = Question.objects.create(
                            quiz=quiz,
                            question_text=fixed_question_data['question_text'],
                            question_type=fixed_question_data['question_type'],
                            options=fixed_question_data.get('options', []),
                            correct_answer=fixed_question_data['correct_answer'],
                            explanation=fixed_question_data.get('explanation', ''),
                            points=fixed_question_data['points'],
                            sort_order=fixed_question_data['sort_order'],
                        )
                        
                        print(f"         ✅ Created question {question.sort_order}")
        
        return course
        
    except Exception as e:
        print(f"❌ Error uploading course: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def verify_upload(course, environment):
    """Verify the uploaded course"""
    print(f"✅ VERIFYING UPLOAD - {environment.upper()}")
    print("=" * 60)
    
    try:
        print(f"📊 COURSE VERIFICATION:")
        print(f"   Title: {course.title}")
        print(f"   ID: {course.id}")
        print(f"   Slug: {course.slug}")
        print(f"   Price: ${course.price}")
        print(f"   Instructor: {course.instructor.username}")
        print(f"   Category: {course.category.name}")
        
        modules = course.modules.all()
        print(f"   Modules: {modules.count()}")
        
        total_lessons = 0
        total_quizzes = 0
        total_questions = 0
        
        for module in modules:
            lessons = module.lessons.all()
            total_lessons += lessons.count()
            
            for lesson in lessons:
                quizzes = lesson.quizzes.all()
                total_quizzes += quizzes.count()
                
                for quiz in quizzes:
                    total_questions += quiz.questions.count()
        
        print(f"   Lessons: {total_lessons}")
        print(f"   Quizzes: {total_quizzes}")
        print(f"   Questions: {total_questions}")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def upload_to_environment(environment, course_json):
    """Upload course to specific environment"""
    print(f"\n🚀 UPLOADING TO {environment.upper()} ENVIRONMENT")
    print("=" * 80)
    
    # Setup environment
    setup_django_environment(environment)
    
    # Create instructor
    instructor_user = create_instructor_user(environment)
    if not instructor_user:
        print(f"❌ Failed to create instructor for {environment}")
        return False
    
    # Create category
    category = create_category_if_needed()
    if not category:
        print(f"❌ Failed to create category for {environment}")
        return False
    
    # Upload course
    course = upload_course_to_database(course_json, instructor_user, category, environment)
    if not course:
        print(f"❌ Failed to upload course to {environment}")
        return False
    
    # Verify upload
    success = verify_upload(course, environment)
    
    if success:
        print(f"\n🎉 {environment.upper()} UPLOAD SUCCESSFUL!")
        print(f"   Course: {course.title}")
        print(f"   ID: {course.id}")
        print(f"   URL: /lms/courses/{course.slug}/")
    else:
        print(f"\n❌ {environment.upper()} UPLOAD FAILED!")
    
    return success

def main():
    """Main upload function"""
    print("📤 YITP COURSE UPLOAD UTILITY")
    print("=" * 80)
    print("Uploading course from yitpcours001.json to both databases")
    print()
    
    # Load course JSON
    try:
        with open('yitpcours001.json', 'r') as f:
            course_json = json.load(f)
        print("✅ Loaded course JSON successfully")
    except Exception as e:
        print(f"❌ Failed to load course JSON: {str(e)}")
        return
    
    # Upload to both environments
    results = {}
    
    # Development upload
    results['development'] = upload_to_environment('development', course_json)
    
    # Production upload
    results['production'] = upload_to_environment('production', course_json)
    
    # Final summary
    print(f"\n🎯 UPLOAD SUMMARY")
    print("=" * 80)
    
    for env, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {env.title()}: {status}")
    
    all_success = all(results.values())
    
    if all_success:
        print(f"\n🎉 ALL UPLOADS COMPLETED SUCCESSFULLY!")
        print(f"   Course uploaded to both development and production")
        print(f"   Instructor 'yitp1' created in both environments")
        print(f"   Course price set to $39.00 USD")
        print(f"   Ready for testing and deployment")
    else:
        print(f"\n⚠️ SOME UPLOADS FAILED")
        print(f"   Please review the logs above for details")

if __name__ == '__main__':
    main()
