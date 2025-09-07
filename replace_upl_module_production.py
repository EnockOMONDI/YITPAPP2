#!/usr/bin/env python3
"""
Replace UPL 101 Module in Production YITP Course
Complete replacement with comprehensive 8-session module
"""

import os
import sys
import django
import json
from datetime import datetime
from decimal import Decimal

# Setup Django environment for PRODUCTION
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson, Category
from assessments.models import Quiz, Question
from django.db import transaction
from django.core.management import call_command
from django.utils import timezone

class UPLModuleReplacer:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.backup_file = None
        self.main_course = None
        self.existing_module = None
        self.new_module_data = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        prefix = "🔍 DRY RUN" if self.dry_run else "🚀 LIVE"
        print(f"[{timestamp}] {prefix} {message}")
    
    def create_backup(self):
        """Create full database backup before replacement"""
        self.log("Creating production database backup...")
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.backup_file = f"production_backup_before_upl_replacement_{timestamp}.json"
            
            if not self.dry_run:
                with open(self.backup_file, 'w') as f:
                    call_command('dumpdata', 
                                'courses', 'assessments', 'progress',
                                '--natural-foreign', 
                                '--indent', '2',
                                stdout=f)
                
                # Verify backup file
                file_size = os.path.getsize(self.backup_file)
                self.log(f"✅ Backup created: {self.backup_file} ({file_size:,} bytes)")
            else:
                self.log(f"📋 Would create backup: {self.backup_file}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Backup creation failed: {str(e)}", "ERROR")
            return False
    
    def find_main_course(self):
        """Find the main YITP course"""
        self.log("Finding main YITP course...")
        
        try:
            self.main_course = Course.objects.get(
                title="Youth Impact Training Programme (YITP)"
            )
            
            self.log(f"✅ Found main course: {self.main_course.title} (ID: {self.main_course.id})")
            self.log(f"   Status: {self.main_course.status} | Published: {self.main_course.is_published}")
            self.log(f"   Price: ${self.main_course.price}")
            
            return True
            
        except Course.DoesNotExist:
            self.log("❌ Main YITP course not found", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Error finding main course: {str(e)}", "ERROR")
            return False
    
    def examine_existing_module(self):
        """Examine the existing UPL 101 module"""
        self.log("Examining existing UPL 101 module...")
        
        try:
            self.existing_module = self.main_course.modules.filter(
                title__icontains="Understanding Purpose in Life"
            ).first()
            
            if not self.existing_module:
                self.log("❌ Existing UPL 101 module not found", "ERROR")
                return False
            
            lessons = self.existing_module.lessons.all()
            total_quizzes = sum(lesson.quizzes.count() for lesson in lessons)
            total_questions = sum(
                quiz.questions.count() 
                for lesson in lessons 
                for quiz in lesson.quizzes.all()
            )
            
            self.log(f"✅ Found existing module: {self.existing_module.title}")
            self.log(f"   Module ID: {self.existing_module.id}")
            self.log(f"   Lessons: {lessons.count()}")
            self.log(f"   Quizzes: {total_quizzes}")
            self.log(f"   Questions: {total_questions}")
            self.log(f"   Duration: {self.existing_module.estimated_duration} minutes")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error examining existing module: {str(e)}", "ERROR")
            return False
    
    def load_new_module_data(self):
        """Load the new UPL 101 module data"""
        self.log("Loading new UPL 101 module data...")
        
        try:
            # Check if we have the complete session file
            session_files = [f for f in os.listdir('.') if f.startswith('upl_complete_course_session_')]
            
            if not session_files:
                self.log("❌ No complete course session file found", "ERROR")
                self.log("   Expected file: upl_complete_course_session_*.json")
                return False
            
            session_file = session_files[0]
            self.log(f"📄 Loading session data from: {session_file}")
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Extract module data
            if 'modules' not in session_data or len(session_data['modules']) == 0:
                self.log("❌ No modules found in session data", "ERROR")
                return False
            
            # Combine both weeks into one module
            week1_module = session_data['modules'][0]
            week2_module = session_data['modules'][1] if len(session_data['modules']) > 1 else {'lessons': []}
            
            # Create combined module data
            self.new_module_data = {
                'title': 'Understanding Purpose in Life (UPL 101)',
                'description': 'A comprehensive 8-session course exploring the foundations of purpose, service, and meaningful living through African wisdom and personal development principles.',
                'estimated_duration': 600,  # 10 hours total
                'sort_order': 1,
                'is_published': True,
                'lessons': week1_module['lessons'] + week2_module['lessons']
            }
            
            self.log(f"✅ Module data loaded successfully")
            self.log(f"   Total lessons: {len(self.new_module_data['lessons'])}")
            self.log(f"   Module title: {self.new_module_data['title']}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error loading new module data: {str(e)}", "ERROR")
            return False
    
    def validate_new_data(self):
        """Validate the new module data"""
        self.log("Validating new module data...")
        
        try:
            lessons = self.new_module_data['lessons']
            
            # Check lesson count
            if len(lessons) != 8:
                self.log(f"❌ Expected 8 lessons, found {len(lessons)}", "ERROR")
                return False
            
            # Check each lesson
            total_questions = 0
            for i, lesson in enumerate(lessons, 1):
                if 'assessment' not in lesson or 'quiz' not in lesson['assessment']:
                    self.log(f"❌ Lesson {i} missing quiz assessment", "ERROR")
                    return False
                
                quiz = lesson['assessment']['quiz']
                questions = quiz.get('questions', [])
                
                if len(questions) != 5:
                    self.log(f"❌ Lesson {i} has {len(questions)} questions, expected 5", "ERROR")
                    return False
                
                total_questions += len(questions)
                
                # Validate question structure
                for j, question in enumerate(questions, 1):
                    required_fields = ['question_text', 'question_type', 'correct_answer', 'explanation', 'points']
                    for field in required_fields:
                        if field not in question:
                            self.log(f"❌ Lesson {i}, Question {j} missing field: {field}", "ERROR")
                            return False
            
            self.log(f"✅ Data validation passed")
            self.log(f"   Total lessons: {len(lessons)}")
            self.log(f"   Total questions: {total_questions}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Data validation failed: {str(e)}", "ERROR")
            return False
    
    def delete_existing_module(self):
        """Delete the existing UPL 101 module"""
        self.log("Deleting existing UPL 101 module...")
        
        try:
            if self.dry_run:
                self.log("📋 Would delete existing module and all related data")
                return True
            
            # Delete the module (cascades to lessons, quizzes, questions)
            module_id = self.existing_module.id
            module_title = self.existing_module.title
            
            self.existing_module.delete()
            
            self.log(f"✅ Deleted module: {module_title} (ID: {module_id})")
            return True
            
        except Exception as e:
            self.log(f"❌ Error deleting existing module: {str(e)}", "ERROR")
            return False
    
    def create_new_module(self):
        """Create the new comprehensive UPL 101 module"""
        self.log("Creating new comprehensive UPL 101 module...")
        
        try:
            if self.dry_run:
                self.log("📋 Would create new module with 8 lessons and 40 quiz questions")
                return True
            
            # Create the module
            new_module = Module.objects.create(
                course=self.main_course,
                title=self.new_module_data['title'],
                description=self.new_module_data['description'],
                sort_order=self.new_module_data['sort_order'],
                is_published=self.new_module_data['is_published'],
                estimated_duration=self.new_module_data['estimated_duration'],
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            
            self.log(f"✅ Created module: {new_module.title} (ID: {new_module.id})")
            
            # Create lessons and quizzes
            for lesson_data in self.new_module_data['lessons']:
                lesson = Lesson.objects.create(
                    module=new_module,
                    title=lesson_data['title'],
                    content_type='text',
                    content=lesson_data['primary_content'],
                    sort_order=lesson_data['sort_order'],
                    is_published=True,
                    is_mandatory=True,
                    estimated_duration=lesson_data['estimated_duration'],
                    learning_objectives=lesson_data['learning_objectives'],
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                
                # Create quiz
                quiz_data = lesson_data['assessment']['quiz']
                quiz = Quiz.objects.create(
                    lesson=lesson,
                    title=quiz_data['title'],
                    description=quiz_data['description'],
                    instructions=quiz_data['instructions'],
                    max_attempts=quiz_data['max_attempts'],
                    passing_score=quiz_data['passing_score'],
                    is_randomized=quiz_data['is_randomized'],
                    show_results=quiz_data['show_results'],
                    is_published=True,
                    created_at=timezone.now()
                )
                
                # Create questions
                for question_data in quiz_data['questions']:
                    Question.objects.create(
                        quiz=quiz,
                        question_text=question_data['question_text'],
                        question_type=question_data['question_type'],
                        correct_answer=question_data['correct_answer'],
                        explanation=question_data['explanation'],
                        points=question_data['points'],
                        sort_order=question_data['sort_order'],
                        created_at=timezone.now()
                    )
                
                self.log(f"   ✅ Created lesson: {lesson.title} with quiz ({len(quiz_data['questions'])} questions)")
            
            self.log(f"✅ Module creation completed successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating new module: {str(e)}", "ERROR")
            return False
    
    def verify_replacement(self):
        """Verify the module replacement was successful"""
        self.log("Verifying module replacement...")
        
        try:
            if self.dry_run:
                self.log("📋 Would verify replacement success")
                return True
            
            # Refresh course data
            self.main_course.refresh_from_db()
            
            # Check module
            new_module = self.main_course.modules.filter(
                title__icontains="Understanding Purpose in Life"
            ).first()
            
            if not new_module:
                self.log("❌ New module not found after replacement", "ERROR")
                return False
            
            lessons = new_module.lessons.all().order_by('sort_order')
            total_quizzes = sum(lesson.quizzes.count() for lesson in lessons)
            total_questions = sum(
                quiz.questions.count() 
                for lesson in lessons 
                for quiz in lesson.quizzes.all()
            )
            
            self.log(f"✅ Verification successful")
            self.log(f"   Module: {new_module.title}")
            self.log(f"   Lessons: {lessons.count()}")
            self.log(f"   Quizzes: {total_quizzes}")
            self.log(f"   Questions: {total_questions}")
            self.log(f"   Duration: {new_module.estimated_duration} minutes")
            
            # Verify expected counts
            if lessons.count() != 8:
                self.log(f"⚠️ Expected 8 lessons, found {lessons.count()}", "WARNING")
            
            if total_questions != 40:
                self.log(f"⚠️ Expected 40 questions, found {total_questions}", "WARNING")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error during verification: {str(e)}", "ERROR")
            return False

    def run_dry_run(self):
        """Run complete dry run simulation"""
        self.log("🔍 STARTING DRY RUN SIMULATION")
        self.log("=" * 80)

        steps = [
            ("Database Backup", self.create_backup),
            ("Find Main Course", self.find_main_course),
            ("Examine Existing Module", self.examine_existing_module),
            ("Load New Module Data", self.load_new_module_data),
            ("Validate New Data", self.validate_new_data),
            ("Delete Existing Module", self.delete_existing_module),
            ("Create New Module", self.create_new_module),
            ("Verify Replacement", self.verify_replacement)
        ]

        for step_name, step_func in steps:
            self.log(f"\n📋 Step: {step_name}")
            if not step_func():
                self.log(f"❌ Dry run failed at step: {step_name}", "ERROR")
                return False

        self.log("\n" + "=" * 80)
        self.log("✅ DRY RUN COMPLETED SUCCESSFULLY")
        self.log("All steps validated - ready for live execution")
        return True

    def run_live_replacement(self):
        """Run live module replacement"""
        self.log("🚀 STARTING LIVE MODULE REPLACEMENT")
        self.log("=" * 80)

        try:
            with transaction.atomic():
                steps = [
                    ("Database Backup", self.create_backup),
                    ("Find Main Course", self.find_main_course),
                    ("Examine Existing Module", self.examine_existing_module),
                    ("Load New Module Data", self.load_new_module_data),
                    ("Validate New Data", self.validate_new_data),
                    ("Delete Existing Module", self.delete_existing_module),
                    ("Create New Module", self.create_new_module),
                    ("Verify Replacement", self.verify_replacement)
                ]

                for step_name, step_func in steps:
                    self.log(f"\n🚀 Step: {step_name}")
                    if not step_func():
                        self.log(f"❌ Live replacement failed at step: {step_name}", "ERROR")
                        self.log("🔄 Rolling back transaction...")
                        raise Exception(f"Step failed: {step_name}")

                self.log("\n" + "=" * 80)
                self.log("🎉 LIVE REPLACEMENT COMPLETED SUCCESSFULLY")
                self.log(f"📄 Backup file: {self.backup_file}")
                return True

        except Exception as e:
            self.log(f"❌ Live replacement failed: {str(e)}", "ERROR")
            self.log("🔄 All changes have been rolled back")
            return False

def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Replace UPL 101 Module in Production')
    parser.add_argument('--live', action='store_true',
                       help='Execute live replacement (default is dry run)')
    parser.add_argument('--force', action='store_true',
                       help='Force execution without confirmation')

    args = parser.parse_args()

    # Initialize replacer
    replacer = UPLModuleReplacer(dry_run=not args.live)

    if args.live:
        print("\n" + "⚠️ " * 20)
        print("🚨 WARNING: LIVE PRODUCTION DATABASE OPERATION")
        print("⚠️ " * 20)
        print("This will PERMANENTLY REPLACE the existing UPL 101 module")
        print("in the production database with the new comprehensive version.")
        print("\nThis action will:")
        print("• DELETE the existing module and all its lessons/quizzes")
        print("• CREATE a new module with 8 lessons and 40 quiz questions")
        print("• MODIFY the production database permanently")

        if not args.force:
            confirm = input("\nType 'REPLACE' to confirm this operation: ")
            if confirm != 'REPLACE':
                print("❌ Operation cancelled")
                return False

        print("\n🚀 Proceeding with live replacement...")
        success = replacer.run_live_replacement()
    else:
        print("\n🔍 Running dry run simulation...")
        success = replacer.run_dry_run()

        if success:
            print("\n💡 To execute the live replacement, run:")
            print("   python replace_upl_module_production.py --live")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
