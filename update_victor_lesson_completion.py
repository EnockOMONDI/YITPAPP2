#!/usr/bin/env python3
"""
YITP Production Database Update Script
=====================================

Purpose: Mark all Course 6 (YITP) lessons as completed for test user Victor
Target User: info@youthimpactglobal.com (Victor)
Database: Production Supabase PostgreSQL

Safety Features:
- Transaction rollback on errors
- Comprehensive validation
- Backup queries for rollback
- Detailed logging

Author: YITP Development Team
Date: 2025-01-14
"""

import os
import sys
import django
from datetime import datetime
from decimal import Decimal

# Add the project directory to Python path
sys.path.append('/Users/djsean/Desktop/APPS2024/YITP2025/YITPAPP')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production environment

# Initialize Django
django.setup()

from django.db import transaction, connection
from django.contrib.auth.models import User
from django.utils import timezone
from courses.models import Course, Module, Lesson
from progress.models import Enrollment, LessonProgress, QuizAttempt
from assessments.models import Quiz


class VictorLessonCompletionUpdater:
    """
    Safe updater for marking all Course 6 lessons as completed for Victor
    """
    
    def __init__(self):
        self.target_email = 'info@youthimpactglobal.com'
        self.target_name = 'Victor'
        self.course_id = 6  # YITP Course
        self.user = None
        self.course = None
        self.enrollment = None
        self.updates_made = []
        self.rollback_queries = []
        
    def validate_environment(self):
        """Ensure we're in production environment"""
        print("🔍 Validating Environment...")
        
        # Check Django environment
        django_env = os.environ.get('DJANGO_ENV', 'development')
        if django_env != 'production':
            raise Exception(f"❌ Not in production environment. Current: {django_env}")
            
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            db_name = cursor.fetchone()[0]
            
        print(f"✅ Environment: {django_env}")
        print(f"✅ Database: {db_name}")
        print(f"✅ Connection: Active")
        
    def find_target_user(self):
        """Find and validate the target user"""
        print(f"\n🔍 Finding Target User...")
        
        try:
            self.user = User.objects.get(email=self.target_email)
            print(f"✅ Found user: {self.user.get_full_name()} ({self.user.email})")
            print(f"   User ID: {self.user.id}")
            print(f"   Username: {self.user.username}")
            print(f"   Active: {self.user.is_active}")
            print(f"   Joined: {self.user.date_joined}")
            
            # Validate this is Victor
            full_name = self.user.get_full_name().lower()
            if 'victor' not in full_name:
                print(f"⚠️  Warning: User name '{self.user.get_full_name()}' doesn't contain 'Victor'")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    raise Exception("User validation failed")
                    
        except User.DoesNotExist:
            raise Exception(f"❌ User with email {self.target_email} not found")
            
    def find_target_course(self):
        """Find and validate Course 6 (YITP)"""
        print(f"\n🔍 Finding Target Course...")
        
        try:
            self.course = Course.objects.get(id=self.course_id)
            print(f"✅ Found course: {self.course.title}")
            print(f"   Course ID: {self.course.id}")
            print(f"   Status: {self.course.status}")
            print(f"   Published: {self.course.is_published}")
            
            # Get modules and lessons
            modules = self.course.modules.filter(is_published=True).order_by('sort_order')
            total_lessons = 0
            
            print(f"\n📚 Course Structure:")
            for module in modules:
                lessons = module.lessons.filter(is_published=True).order_by('sort_order')
                lesson_count = lessons.count()
                total_lessons += lesson_count
                print(f"   Module {module.id}: {module.title} ({lesson_count} lessons)")
                
                for lesson in lessons:
                    print(f"     - Lesson {lesson.id}: {lesson.title}")
                    
            print(f"\n📊 Total Lessons: {total_lessons}")
            
        except Course.DoesNotExist:
            raise Exception(f"❌ Course with ID {self.course_id} not found")
            
    def check_enrollment(self):
        """Check or create enrollment for the user"""
        print(f"\n🔍 Checking Enrollment...")
        
        try:
            self.enrollment = Enrollment.objects.get(
                student=self.user,
                course=self.course
            )
            print(f"✅ Found existing enrollment:")
            print(f"   Enrollment ID: {self.enrollment.id}")
            print(f"   Status: {self.enrollment.status}")
            print(f"   Progress: {self.enrollment.progress_percentage}%")
            print(f"   Enrolled: {self.enrollment.enrollment_date}")
            
        except Enrollment.DoesNotExist:
            print(f"⚠️  No enrollment found. Creating new enrollment...")
            
            self.enrollment = Enrollment.objects.create(
                student=self.user,
                course=self.course,
                status='active',
                enrollment_type='paid',
                progress_percentage=Decimal('0.00')
            )
            
            print(f"✅ Created enrollment ID: {self.enrollment.id}")
            self.updates_made.append(f"Created enrollment {self.enrollment.id}")
            self.rollback_queries.append(
                f"DELETE FROM progress_enrollment WHERE id = {self.enrollment.id};"
            )
            
    def analyze_current_progress(self):
        """Analyze current lesson progress"""
        print(f"\n📊 Analyzing Current Progress...")
        
        # Get all lessons in the course
        all_lessons = []
        modules = self.course.modules.filter(is_published=True).order_by('sort_order')
        
        for module in modules:
            lessons = module.lessons.filter(is_published=True).order_by('sort_order')
            all_lessons.extend(lessons)
            
        print(f"Total lessons to check: {len(all_lessons)}")
        
        # Check current progress
        existing_progress = LessonProgress.objects.filter(
            enrollment=self.enrollment,
            lesson__in=all_lessons
        )
        
        progress_by_lesson = {lp.lesson_id: lp for lp in existing_progress}
        
        completed_count = 0
        in_progress_count = 0
        not_started_count = 0
        
        print(f"\n📋 Current Progress Status:")
        for lesson in all_lessons:
            if lesson.id in progress_by_lesson:
                progress = progress_by_lesson[lesson.id]
                status = progress.status
                if status == 'completed':
                    completed_count += 1
                elif status == 'in_progress':
                    in_progress_count += 1
                else:
                    not_started_count += 1
                print(f"   Lesson {lesson.id}: {status}")
            else:
                not_started_count += 1
                print(f"   Lesson {lesson.id}: no_record")
                
        print(f"\n📈 Summary:")
        print(f"   Completed: {completed_count}")
        print(f"   In Progress: {in_progress_count}")
        print(f"   Not Started: {not_started_count}")
        print(f"   Total: {len(all_lessons)}")
        
        return all_lessons, progress_by_lesson
        
    def update_lesson_progress(self, all_lessons, progress_by_lesson):
        """Update all lessons to completed status"""
        print(f"\n🔄 Updating Lesson Progress...")
        
        current_time = timezone.now()
        updates_count = 0
        creates_count = 0
        
        for lesson in all_lessons:
            if lesson.id in progress_by_lesson:
                # Update existing progress
                progress = progress_by_lesson[lesson.id]
                if progress.status != 'completed':
                    old_status = progress.status
                    old_completed_at = progress.completed_at
                    old_score = progress.score
                    
                    progress.status = 'completed'
                    progress.completed_at = current_time
                    progress.score = Decimal('100.00')  # Perfect score
                    if not progress.started_at:
                        progress.started_at = current_time
                    progress.save()
                    
                    updates_count += 1
                    self.updates_made.append(f"Updated lesson {lesson.id} progress")
                    
                    # Create rollback query
                    rollback_query = f"""
                    UPDATE progress_lessonprogress 
                    SET status = '{old_status}', 
                        completed_at = {'NULL' if old_completed_at is None else f"'{old_completed_at}'"}, 
                        score = {'NULL' if old_score is None else old_score}
                    WHERE id = {progress.id};
                    """
                    self.rollback_queries.append(rollback_query.strip())
                    
                    print(f"   ✅ Updated Lesson {lesson.id}: {old_status} → completed")
                else:
                    print(f"   ✓ Lesson {lesson.id}: already completed")
            else:
                # Create new progress record
                progress = LessonProgress.objects.create(
                    enrollment=self.enrollment,
                    lesson=lesson,
                    status='completed',
                    started_at=current_time,
                    completed_at=current_time,
                    score=Decimal('100.00'),
                    time_spent=lesson.estimated_duration * 60,  # Convert minutes to seconds
                    attempts=1
                )
                
                creates_count += 1
                self.updates_made.append(f"Created lesson {lesson.id} progress")
                self.rollback_queries.append(
                    f"DELETE FROM progress_lessonprogress WHERE id = {progress.id};"
                )
                
                print(f"   ✅ Created Lesson {lesson.id}: completed")
                
        print(f"\n📊 Update Summary:")
        print(f"   Records Updated: {updates_count}")
        print(f"   Records Created: {creates_count}")
        print(f"   Total Changes: {updates_count + creates_count}")
        
        return updates_count + creates_count
        
    def update_enrollment_progress(self):
        """Update overall enrollment progress"""
        print(f"\n🔄 Updating Enrollment Progress...")
        
        old_progress = self.enrollment.progress_percentage
        old_completion_date = self.enrollment.completion_date
        old_status = self.enrollment.status
        
        # Update enrollment to show 100% completion
        self.enrollment.progress_percentage = Decimal('100.00')
        self.enrollment.completion_date = timezone.now()
        self.enrollment.status = 'completed'
        self.enrollment.save()
        
        print(f"   ✅ Progress: {old_progress}% → 100%")
        print(f"   ✅ Status: {old_status} → completed")
        print(f"   ✅ Completion Date: {self.enrollment.completion_date}")
        
        self.updates_made.append("Updated enrollment progress to 100%")
        
        # Create rollback query
        rollback_query = f"""
        UPDATE progress_enrollment 
        SET progress_percentage = {old_progress}, 
            completion_date = {'NULL' if old_completion_date is None else f"'{old_completion_date}'"}, 
            status = '{old_status}'
        WHERE id = {self.enrollment.id};
        """
        self.rollback_queries.append(rollback_query.strip())
        
    def create_quiz_attempts(self, all_lessons):
        """Create passing quiz attempts for lessons that have quizzes"""
        print(f"\n🔄 Creating Quiz Attempts...")
        
        current_time = timezone.now()
        quiz_attempts_created = 0
        
        for lesson in all_lessons:
            # Check if lesson has quizzes
            quizzes = lesson.quizzes.filter(is_published=True)
            
            for quiz in quizzes:
                # Check if user already has a passing attempt
                existing_attempt = QuizAttempt.objects.filter(
                    student=self.user,
                    quiz=quiz,
                    is_passed=True
                ).first()
                
                if not existing_attempt:
                    # Create a passing quiz attempt
                    attempt = QuizAttempt.objects.create(
                        student=self.user,
                        quiz=quiz,
                        enrollment=self.enrollment,
                        attempt_number=1,
                        started_at=current_time,
                        completed_at=current_time,
                        score=Decimal('85.00'),  # Good passing score
                        answers={},  # Empty answers for now
                        time_taken=300,  # 5 minutes
                        is_passed=True
                    )
                    
                    quiz_attempts_created += 1
                    self.updates_made.append(f"Created quiz attempt for lesson {lesson.id}")
                    self.rollback_queries.append(
                        f"DELETE FROM progress_quizattempt WHERE id = {attempt.id};"
                    )
                    
                    print(f"   ✅ Created quiz attempt for Lesson {lesson.id}")
                else:
                    print(f"   ✓ Quiz attempt already exists for Lesson {lesson.id}")
                    
        print(f"\n📊 Quiz Attempts Summary:")
        print(f"   Created: {quiz_attempts_created}")
        
        return quiz_attempts_created
        
    def validate_final_state(self):
        """Validate that all updates were successful"""
        print(f"\n✅ Validating Final State...")
        
        # Re-fetch enrollment
        self.enrollment.refresh_from_db()
        
        # Check enrollment progress
        print(f"   Enrollment Progress: {self.enrollment.progress_percentage}%")
        print(f"   Enrollment Status: {self.enrollment.status}")
        print(f"   Completion Date: {self.enrollment.completion_date}")
        
        # Count completed lessons
        completed_lessons = LessonProgress.objects.filter(
            enrollment=self.enrollment,
            status='completed'
        ).count()
        
        total_lessons = 0
        modules = self.course.modules.filter(is_published=True)
        for module in modules:
            total_lessons += module.lessons.filter(is_published=True).count()
            
        print(f"   Completed Lessons: {completed_lessons}/{total_lessons}")
        
        # Check quiz attempts
        passing_attempts = QuizAttempt.objects.filter(
            student=self.user,
            quiz__lesson__module__course=self.course,
            is_passed=True
        ).count()
        
        print(f"   Passing Quiz Attempts: {passing_attempts}")
        
        if completed_lessons == total_lessons and self.enrollment.progress_percentage == 100:
            print(f"   ✅ All validations passed!")
            return True
        else:
            print(f"   ❌ Validation failed!")
            return False
            
    def generate_rollback_script(self):
        """Generate rollback script for emergency use"""
        print(f"\n📝 Generating Rollback Script...")
        
        rollback_content = f"""-- YITP Emergency Rollback Script
-- Generated: {datetime.now()}
-- User: {self.user.email} (ID: {self.user.id})
-- Course: {self.course.title} (ID: {self.course.id})
-- 
-- WARNING: This script will undo all lesson completion updates
-- Only run this if you need to revert the changes

BEGIN;

-- Rollback queries (in reverse order)
"""
        
        for query in reversed(self.rollback_queries):
            rollback_content += f"{query}\n"
            
        rollback_content += """
-- Verify rollback
SELECT 'Rollback completed' as status;

COMMIT;
"""
        
        rollback_filename = f"rollback_victor_completion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        with open(rollback_filename, 'w') as f:
            f.write(rollback_content)
            
        print(f"   ✅ Rollback script saved: {rollback_filename}")
        
    def run_update(self):
        """Main update process with transaction safety"""
        print("🚀 YITP Victor Lesson Completion Update")
        print("=" * 50)
        
        try:
            # Validation steps
            self.validate_environment()
            self.find_target_user()
            self.find_target_course()
            self.check_enrollment()
            
            # Analysis
            all_lessons, progress_by_lesson = self.analyze_current_progress()
            
            # Confirm before proceeding
            print(f"\n⚠️  CONFIRMATION REQUIRED")
            print(f"This will mark ALL {len(all_lessons)} lessons as completed for:")
            print(f"   User: {self.user.get_full_name()} ({self.user.email})")
            print(f"   Course: {self.course.title}")
            print(f"   Environment: PRODUCTION")
            
            response = input("\nProceed with updates? (yes/NO): ")
            if response.lower() != 'yes':
                print("❌ Update cancelled by user")
                return False
                
            # Perform updates in transaction
            with transaction.atomic():
                print(f"\n🔄 Starting Transaction...")
                
                # Update lesson progress
                changes_made = self.update_lesson_progress(all_lessons, progress_by_lesson)
                
                # Update enrollment progress
                self.update_enrollment_progress()
                
                # Create quiz attempts
                quiz_attempts = self.create_quiz_attempts(all_lessons)
                
                # Validate final state
                if not self.validate_final_state():
                    raise Exception("Final validation failed")
                    
                print(f"\n✅ Transaction completed successfully!")
                
            # Generate rollback script
            self.generate_rollback_script()
            
            # Final summary
            print(f"\n🎉 UPDATE COMPLETED SUCCESSFULLY!")
            print(f"   Total Changes: {len(self.updates_made)}")
            print(f"   Lesson Progress Updates: {changes_made}")
            print(f"   Quiz Attempts Created: {quiz_attempts}")
            print(f"   Final Progress: 100%")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            print(f"   All changes have been rolled back automatically")
            return False


if __name__ == "__main__":
    updater = VictorLessonCompletionUpdater()
    success = updater.run_update()
    
    if success:
        print(f"\n✅ Victor's account is now ready for testing!")
        print(f"   Login: {updater.target_email}")
        print(f"   All Course 6 lessons marked as completed")
        print(f"   Progress tracking and stats should now be visible")
    else:
        print(f"\n❌ Update failed. No changes were made to the database.")
        
    sys.exit(0 if success else 1)
