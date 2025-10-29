#!/usr/bin/env python3
"""
Module 4 Database Import Script
Imports Module 4 (Soft Skills for the Streets) into the YITP course database
"""

import os
import sys
import django
import json
from django.db import transaction

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question

def import_module4():
    """Import Module 4 data into the database"""
    
    print("=== Module 4 Database Import ===\n")
    
    try:
        # Load the JSON data
        with open('yitp_seed_module4.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get the YITP course
        try:
            course = Course.objects.get(slug='youth-impact-training-programme-yitp')
            print(f"Found course: {course.title}")
        except Course.DoesNotExist:
            print("ERROR: YITP course not found!")
            return False
        
        # Check if Module 4 already exists
        existing_module = Module.objects.filter(course=course, sort_order=4).first()
        if existing_module:
            print(f"WARNING: Module 4 already exists: {existing_module.title}")
            response = input("Do you want to delete and recreate it? (y/N): ")
            if response.lower() != 'y':
                print("Import cancelled.")
                return False
            
            print("Deleting existing Module 4...")
            existing_module.delete()
        
        # Start database transaction
        with transaction.atomic():
            # Create Module 4
            module_data = data['module']
            module = Module.objects.create(
                course=course,
                title=module_data['title'],
                description=module_data['description'],
                sort_order=module_data['sort_order'],
                is_published=module_data['is_published'],
                estimated_duration=300  # 5 hours for 10 lessons (30 min each)
            )
            
            print(f"Created module: {module.title}")
            
            # Import lessons
            lessons_data = data['lessons']
            lesson_count = 0
            quiz_count = 0
            question_count = 0
            
            for lesson_data in lessons_data:
                # Create lesson
                lesson = Lesson.objects.create(
                    module=module,
                    title=lesson_data['title'],
                    content=lesson_data['content'],
                    content_type='text',  # Rich text content
                    sort_order=lesson_data['lesson_number'],
                    is_published=True,
                    estimated_duration=30,  # 30 minutes per lesson
                    learning_objectives=lesson_data['description']
                )
                
                lesson_count += 1
                print(f"  Created lesson {lesson_data['lesson_number']}: {lesson.title}")
                
                # Create quiz for this lesson
                quiz = Quiz.objects.create(
                    lesson=lesson,
                    title=f"{lesson.title} - Quiz",
                    description=f"Test your knowledge of {lesson.title}",
                    passing_score=70,
                    is_published=True
                )
                
                quiz_count += 1
                
                # Create questions for this quiz
                for i, question_data in enumerate(lesson_data['quiz_questions'], 1):
                    # Map correct_answer index to letter
                    correct_mapping = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}

                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=question_data['question'],
                        question_type='multiple_choice',
                        options=question_data['options'],  # Store as JSON array
                        correct_answer=correct_mapping[question_data['correct_answer']],
                        explanation=question_data['explanation'],
                        sort_order=i,
                        points=1
                    )

                    question_count += 1
                
                print(f"    Created quiz with {len(lesson_data['quiz_questions'])} questions")
            
            print(f"\n=== Import Summary ===")
            print(f"Module: {module.title}")
            print(f"Lessons created: {lesson_count}")
            print(f"Quizzes created: {quiz_count}")
            print(f"Questions created: {question_count}")
            print(f"Module published: {module.is_published}")
            
            # Verify the import
            print(f"\n=== Verification ===")
            total_modules = Module.objects.filter(course=course).count()
            total_lessons = Lesson.objects.filter(module__course=course).count()
            
            print(f"Total modules in course: {total_modules}")
            print(f"Total lessons in course: {total_lessons}")
            
            # Show all modules
            print(f"\nAll modules in {course.title}:")
            for mod in Module.objects.filter(course=course).order_by('sort_order'):
                lesson_count = mod.lessons.count()
                print(f"  Module {mod.sort_order}: {mod.title} ({lesson_count} lessons) - Published: {mod.is_published}")
            
            return True
            
    except Exception as e:
        print(f"Error during import: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = import_module4()
    
    if success:
        print("\n✅ Module 4 import completed successfully!")
        print("\nNext steps:")
        print("1. Test the course detail page to ensure it loads without timeout")
        print("2. Verify all 4 modules are visible and accessible")
        print("3. Test lesson navigation and quiz functionality")
    else:
        print("\n❌ Module 4 import failed!")
        print("Please check the error messages above and try again.")
