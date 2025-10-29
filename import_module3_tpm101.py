#!/usr/bin/env python
"""
Import Module 3 (TPM 101) from yitp_seed_module3.json into YITP platform
Uses the same methodology as Module 1 import
"""

import os
import sys
import django
import json
from decimal import Decimal
from datetime import datetime
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson, Category
from assessments.models import Quiz, Question
from django.db import transaction

class Module3Importer:
    def __init__(self, json_file='yitp_seed_module3.json'):
        self.json_file = json_file
        self.data = None
        self.course = None
        self.modules = {}
        self.lessons = {}
        self.quizzes = {}
        
    def load_json(self):
        """Load and validate JSON data"""
        print("📂 Loading Module 3 JSON data...")
        
        try:
            with open(self.json_file, 'r') as f:
                self.data = json.load(f)
            print(f"✅ JSON loaded successfully from {self.json_file}")
            
            # Quick validation
            if 'modules' not in self.data or 'lessons' not in self.data:
                print("❌ Invalid JSON: missing 'modules' or 'lessons' section")
                return False
            
            module_title = self.data['modules'][0].get('title', 'Unknown')
            print(f"📋 Module to import: {module_title}")
            print(f"📖 Lessons to import: {len(self.data['lessons'])}")
            return True
            
        except FileNotFoundError:
            print(f"❌ File not found: {self.json_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format: {str(e)}")
            return False
    
    def validate_prerequisites(self):
        """Validate that prerequisites exist in database"""
        print("🔍 Validating prerequisites...")
        
        # Check if YITP course exists
        try:
            self.course = Course.objects.get(slug='youth-impact-training-programme-yitp')
            print(f"✅ YITP Course found: {self.course.title} (ID: {self.course.id})")
        except Course.DoesNotExist:
            print("❌ YITP Course not found. Please ensure the main course exists.")
            return False
        
        # Check if Module 3 already exists
        if Module.objects.filter(course=self.course, sort_order=3).exists():
            print("⚠️  Module 3 already exists. This will update existing content.")
        
        return True
    
    def import_module(self):
        """Import Module 3"""
        print("📚 Importing Module 3...")
        
        module_data = self.data['modules'][0]
        
        try:
            # Check if module already exists by sort_order
            try:
                module = Module.objects.get(course=self.course, sort_order=module_data['sort_order'])
                created = False
            except Module.DoesNotExist:
                module = Module.objects.create(
                    course=self.course,
                    title=module_data['title'],
                    description=module_data['description'],
                    sort_order=module_data['sort_order'],
                    is_published=module_data['is_published'],
                    unlock_criteria=module_data.get('unlock_criteria', {}),
                    estimated_duration=module_data['estimated_duration']
                )
                created = True
            
            if not created:
                # Update existing module
                module.title = module_data['title']
                module.description = module_data['description']
                module.is_published = module_data['is_published']
                module.unlock_criteria = module_data.get('unlock_criteria', {})
                module.estimated_duration = module_data['estimated_duration']
                module.save()
                print(f"🔄 Updated existing module: {module.title}")
            else:
                print(f"✅ Created new module: {module.title}")
            
            # Store module reference
            self.modules[module_data['id']] = module
            
            print(f"   ID: {module.id}")
            print(f"   Duration: {module.estimated_duration} minutes")
            return True
            
        except Exception as e:
            print(f"❌ Error creating/updating module: {str(e)}")
            return False
    
    def import_lessons(self):
        """Import lessons for Module 3"""
        print("📖 Importing lessons...")
        
        lessons_data = self.data['lessons']
        
        for lesson_data in lessons_data:
            try:
                # Get the module for this lesson
                module = self.modules.get(lesson_data['module_id'])
                if not module:
                    print(f"❌ Module {lesson_data['module_id']} not found for lesson {lesson_data['id']}")
                    continue
                
                # Check if lesson already exists by sort_order
                try:
                    lesson = Lesson.objects.get(module=module, sort_order=lesson_data['sort_order'])
                    created = False
                except Lesson.DoesNotExist:
                    lesson = Lesson.objects.create(
                        module=module,
                        title=lesson_data['title'],
                        content_type=lesson_data['content_type'],
                        content=lesson_data['content'],
                        video_url=lesson_data.get('video_url', ''),
                        presentation_file=lesson_data.get('presentation_file', ''),
                        sort_order=lesson_data['sort_order'],
                        is_published=lesson_data['is_published'],
                        is_mandatory=lesson_data['is_mandatory'],
                        estimated_duration=lesson_data['estimated_duration'],
                        learning_objectives=lesson_data['learning_objectives'],
                        resources=lesson_data.get('resources', [])
                    )
                    created = True
                
                if not created:
                    # Update existing lesson
                    lesson.title = lesson_data['title']
                    lesson.content_type = lesson_data['content_type']
                    lesson.content = lesson_data['content']
                    lesson.video_url = lesson_data.get('video_url', '')
                    lesson.presentation_file = lesson_data.get('presentation_file', '')
                    lesson.is_published = lesson_data['is_published']
                    lesson.is_mandatory = lesson_data['is_mandatory']
                    lesson.estimated_duration = lesson_data['estimated_duration']
                    lesson.learning_objectives = lesson_data['learning_objectives']
                    lesson.resources = lesson_data.get('resources', [])
                    lesson.save()
                    print(f"🔄 Updated lesson: {lesson.title}")
                else:
                    print(f"✅ Created lesson: {lesson.title}")
                
                # Store lesson reference for quizzes
                self.lessons[lesson_data['id']] = lesson
                
                print(f"   ID: {lesson.id}, Type: {lesson.content_type}, Duration: {lesson.estimated_duration}min")
                
            except Exception as e:
                print(f"❌ Error creating/updating lesson {lesson_data['id']}: {str(e)}")
                return False
        
        print(f"✅ All {len(lessons_data)} lessons processed successfully")
        return True
    
    def import_quizzes(self):
        """Import quizzes for Module 3 lessons"""
        print("🧩 Importing quizzes...")
        
        quiz_count = 0
        question_count = 0
        
        for lesson_data in self.data['lessons']:
            if 'assessment' not in lesson_data or 'quiz' not in lesson_data['assessment']:
                continue
            
            quiz_data = lesson_data['assessment']['quiz']
            lesson = self.lessons.get(lesson_data['id'])
            
            if not lesson:
                print(f"❌ Lesson {lesson_data['id']} not found for quiz")
                continue
            
            try:
                # Check if quiz already exists for this lesson
                quiz, created = Quiz.objects.get_or_create(
                    lesson=lesson,
                    defaults={
                        'title': quiz_data['title'],
                        'description': quiz_data['description'],
                        'instructions': quiz_data['instructions'],
                        'max_attempts': quiz_data['max_attempts'],
                        'passing_score': quiz_data['passing_score'],
                        'is_randomized': quiz_data['is_randomized'],
                        'show_results': quiz_data['show_results'],
                        'time_limit': quiz_data.get('time_limit'),
                        'is_published': quiz_data['is_published']
                    }
                )
                
                if not created:
                    # Update existing quiz
                    quiz.title = quiz_data['title']
                    quiz.description = quiz_data['description']
                    quiz.instructions = quiz_data['instructions']
                    quiz.max_attempts = quiz_data['max_attempts']
                    quiz.passing_score = quiz_data['passing_score']
                    quiz.is_randomized = quiz_data['is_randomized']
                    quiz.show_results = quiz_data['show_results']
                    quiz.time_limit = quiz_data.get('time_limit')
                    quiz.is_published = quiz_data['is_published']
                    quiz.save()
                    
                    # Delete existing questions to replace them
                    quiz.questions.all().delete()
                    print(f"🔄 Updated quiz: {quiz.title}")
                else:
                    print(f"✅ Created quiz: {quiz.title}")
                
                quiz_count += 1
                
                # Import questions
                for question_data in quiz_data['questions']:
                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=question_data['question_text'],
                        question_type=question_data['question_type'],
                        options=question_data.get('options', []),
                        correct_answer=question_data['correct_answer'],
                        points=question_data['points'],
                        explanation=question_data.get('explanation', ''),
                        sort_order=question_data['sort_order']
                    )
                    question_count += 1
                
                print(f"   Quiz ID: {quiz.id}, Questions: {len(quiz_data['questions'])}")
                
            except Exception as e:
                print(f"❌ Error creating quiz for lesson {lesson_data['id']}: {str(e)}")
                return False
        
        print(f"✅ Imported {quiz_count} quizzes with {question_count} questions")
        return True
    
    def run_import(self):
        """Run the complete import process"""
        print("🚀 STARTING MODULE 3 IMPORT")
        print("=" * 50)
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            with transaction.atomic():
                # Load and validate JSON
                if not self.load_json():
                    return False
                
                # Validate prerequisites
                if not self.validate_prerequisites():
                    return False
                
                # Import module
                if not self.import_module():
                    return False
                
                # Import lessons
                if not self.import_lessons():
                    return False
                
                # Import quizzes
                if not self.import_quizzes():
                    return False
                
                print()
                print("=" * 50)
                print("🎉 MODULE 3 IMPORT COMPLETED SUCCESSFULLY!")
                print("=" * 50)
                print(f"✅ Module: {list(self.modules.values())[0].title}")
                print(f"✅ Lessons: {len(self.lessons)}")
                print(f"✅ Quizzes: {len([l for l in self.data['lessons'] if 'assessment' in l])}")
                print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                return True
                
        except Exception as e:
            print(f"❌ Import failed: {str(e)}")
            return False

def main():
    """Main function"""
    importer = Module3Importer()
    success = importer.run_import()
    
    if success:
        print("\n🎉 Module 3 import completed successfully!")
        return True
    else:
        print("\n❌ Module 3 import failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
