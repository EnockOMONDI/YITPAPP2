#!/usr/bin/env python3
"""
Import Module 5 (ESBA) into YITP database
Imports module, lessons, quizzes, and questions with transaction safety
"""

import os
import sys
import django
import json
from django.db import transaction
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question

def import_module5():
    """Import Module 5 with transaction safety"""
    
    print("=== IMPORTING MODULE 5: ESBA INTO DATABASE ===")
    
    # Load seed data
    try:
        with open('yitp_seed_module5.json', 'r', encoding='utf-8') as f:
            seed_data = json.load(f)
        print(f"✅ Loaded seed data: {seed_data['module']['title']}")
    except FileNotFoundError:
        print("❌ Error: yitp_seed_module5.json not found. Run create_module5_seed.py first.")
        return False
    
    try:
        with transaction.atomic():
            print("\n🔄 Starting database import with transaction safety...")
            
            # Get the YITP course
            try:
                course = Course.objects.get(slug='youth-impact-training-programme-yitp')
                print(f"✅ Found course: {course.title}")
            except Course.DoesNotExist:
                print("❌ Error: YITP course not found")
                return False
            
            # Check if Module 5 already exists
            existing_module = Module.objects.filter(course=course, sort_order=5).first()
            if existing_module:
                print(f"⚠️  Module 5 already exists: {existing_module.title}")
                response = input("Do you want to replace it? (y/N): ").strip().lower()
                if response != 'y':
                    print("❌ Import cancelled")
                    return False
                
                # Delete existing module and all related content
                print("🗑️  Deleting existing Module 5...")
                existing_module.delete()
                print("✅ Existing Module 5 deleted")
            
            # Create Module 5
            module_data = seed_data['module']
            module = Module.objects.create(
                course=course,
                title=module_data['title'],
                description=module_data['description'],
                sort_order=module_data['sort_order'],
                is_published=module_data['is_published'],
                estimated_duration=module_data['estimated_duration']
            )
            print(f"✅ Created module: {module.title}")
            
            # Import lessons
            lesson_mapping = {}  # Map seed lesson IDs to actual lesson IDs
            
            for lesson_data in seed_data['lessons']:
                lesson = Lesson.objects.create(
                    module=module,
                    title=lesson_data['title'],
                    content_type=lesson_data['content_type'],
                    content=lesson_data['content'],
                    learning_objectives=lesson_data['learning_objectives'],
                    resources=lesson_data['resources'],
                    sort_order=lesson_data['sort_order'],
                    estimated_duration=lesson_data['estimated_duration'],
                    is_published=lesson_data['is_published']
                )
                lesson_mapping[lesson_data['id']] = lesson.id
                print(f"✅ Created lesson {lesson_data['sort_order']}: {lesson.title}")
            
            # Import quizzes
            quiz_mapping = {}  # Map seed quiz IDs to actual quiz IDs
            
            for quiz_data in seed_data['quizzes']:
                # Get the actual lesson ID
                actual_lesson_id = lesson_mapping[quiz_data['lesson_id']]
                lesson = Lesson.objects.get(id=actual_lesson_id)
                
                quiz = Quiz.objects.create(
                    lesson=lesson,
                    title=quiz_data['title'],
                    description=quiz_data['description'],
                    passing_score=quiz_data['passing_score'],
                    time_limit=quiz_data['time_limit'],
                    max_attempts=quiz_data['max_attempts'],
                    is_published=quiz_data['is_published']
                )
                quiz_mapping[quiz_data['id']] = quiz.id
                print(f"✅ Created quiz: {quiz.title}")
            
            # Import questions
            question_count = 0
            for question_data in seed_data['questions']:
                # Get the actual quiz ID
                actual_quiz_id = quiz_mapping[question_data['quiz_id']]
                quiz = Quiz.objects.get(id=actual_quiz_id)
                
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=question_data['question_text'],
                    question_type=question_data['question_type'],
                    options=question_data['options'],
                    correct_answer=question_data['correct_answer'],
                    explanation=question_data['explanation'],
                    points=question_data['points']
                )
                question_count += 1
            
            print(f"✅ Created {question_count} questions")
            
            # Verify the import
            print(f"\n📊 IMPORT VERIFICATION:")
            print(f"   • Module: {module.title}")
            print(f"   • Lessons: {module.lessons.count()}")
            print(f"   • Quizzes: {Quiz.objects.filter(lesson__module=module).count()}")
            print(f"   • Questions: {Question.objects.filter(quiz__lesson__module=module).count()}")
            print(f"   • Total Duration: {module.estimated_duration} minutes")
            
            # Check total course structure
            total_modules = course.modules.filter(is_published=True).count()
            total_lessons = Lesson.objects.filter(module__course=course, is_published=True).count()
            
            print(f"\n🎯 COMPLETE COURSE STRUCTURE:")
            print(f"   • Total Modules: {total_modules}")
            print(f"   • Total Lessons: {total_lessons}")
            
            print(f"\n✅ MODULE 5 IMPORT SUCCESSFUL!")
            print(f"🌐 Course detail page: http://127.0.0.1:8000/lms/courses/youth-impact-training-programme-yitp/")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during import: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = import_module5()
    if success:
        print("\n🎉 Module 5 import completed successfully!")
        print("🔄 Next step: Test the course detail page to ensure it loads without timeout")
    else:
        print("\n❌ Module 5 import failed")

if __name__ == "__main__":
    main()
