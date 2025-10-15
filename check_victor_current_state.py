#!/usr/bin/env python3
"""
YITP Victor Account State Checker
=================================

Purpose: Check current state of Victor's account before making updates
Target User: info@youthimpactglobal.com (Victor)
Database: Production Supabase PostgreSQL

This script provides a safe way to inspect the current state without making changes.

Author: YITP Development Team
Date: 2025-01-14
"""

import os
import sys
import django
from datetime import datetime

# Add the project directory to Python path
sys.path.append('/Users/djsean/Desktop/APPS2024/YITP2025/YITPAPP')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production environment

# Initialize Django
django.setup()

from django.db import connection
from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson
from progress.models import Enrollment, LessonProgress, QuizAttempt
from assessments.models import Quiz


class VictorStateChecker:
    """
    Read-only checker for Victor's current account state
    """
    
    def __init__(self):
        self.target_email = 'info@youthimpactglobal.com'
        self.course_id = 6  # YITP Course
        
    def check_environment(self):
        """Check current environment"""
        print("🔍 Environment Check")
        print("=" * 30)
        
        django_env = os.environ.get('DJANGO_ENV', 'development')
        print(f"Django Environment: {django_env}")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user, inet_server_addr()")
            db_info = cursor.fetchone()
            
        print(f"Database Name: {db_info[0]}")
        print(f"Database User: {db_info[1]}")
        print(f"Database Host: {db_info[2] if db_info[2] else 'localhost'}")
        
    def find_user(self):
        """Find Victor's user account"""
        print(f"\n👤 User Account Check")
        print("=" * 30)
        
        try:
            user = User.objects.get(email=self.target_email)
            print(f"✅ User Found:")
            print(f"   ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Full Name: {user.get_full_name()}")
            print(f"   Active: {user.is_active}")
            print(f"   Staff: {user.is_staff}")
            print(f"   Superuser: {user.is_superuser}")
            print(f"   Date Joined: {user.date_joined}")
            print(f"   Last Login: {user.last_login}")
            
            # Check profile
            if hasattr(user, 'profile'):
                profile = user.profile
                print(f"\n📋 Profile Information:")
                print(f"   Phone: {profile.phone_number}")
                print(f"   Payment Status: {profile.payment_status}")
                print(f"   Email Verified: {profile.email_verified}")
                print(f"   Total Points: {profile.total_points}")
                print(f"   Current Streak: {profile.current_streak}")
                print(f"   Profile Completion: {profile.profile_completion_percentage}%")
            
            return user
            
        except User.DoesNotExist:
            print(f"❌ User with email {self.target_email} not found")
            return None
            
    def check_course(self):
        """Check Course 6 details"""
        print(f"\n📚 Course Check")
        print("=" * 30)
        
        try:
            course = Course.objects.get(id=self.course_id)
            print(f"✅ Course Found:")
            print(f"   ID: {course.id}")
            print(f"   Title: {course.title}")
            print(f"   Status: {course.status}")
            print(f"   Published: {course.is_published}")
            print(f"   Price: ${course.price}")
            print(f"   Duration: {course.estimated_duration} hours")
            
            # Get modules
            modules = course.modules.filter(is_published=True).order_by('sort_order')
            print(f"\n📖 Modules ({modules.count()}):")
            
            total_lessons = 0
            for module in modules:
                lessons = module.lessons.filter(is_published=True).order_by('sort_order')
                lesson_count = lessons.count()
                total_lessons += lesson_count
                
                print(f"   Module {module.id}: {module.title}")
                print(f"     - {lesson_count} lessons")
                print(f"     - {module.estimated_duration} minutes")
                
                # Show first few lessons
                for i, lesson in enumerate(lessons[:3]):
                    print(f"       {lesson.id}: {lesson.title[:50]}...")
                if lesson_count > 3:
                    print(f"       ... and {lesson_count - 3} more lessons")
                    
            print(f"\n📊 Course Summary:")
            print(f"   Total Modules: {modules.count()}")
            print(f"   Total Lessons: {total_lessons}")
            
            return course, total_lessons
            
        except Course.DoesNotExist:
            print(f"❌ Course with ID {self.course_id} not found")
            return None, 0
            
    def check_enrollment(self, user, course):
        """Check enrollment status"""
        print(f"\n🎓 Enrollment Check")
        print("=" * 30)
        
        try:
            enrollment = Enrollment.objects.get(student=user, course=course)
            print(f"✅ Enrollment Found:")
            print(f"   ID: {enrollment.id}")
            print(f"   Status: {enrollment.status}")
            print(f"   Type: {enrollment.enrollment_type}")
            print(f"   Progress: {enrollment.progress_percentage}%")
            print(f"   Enrolled: {enrollment.enrollment_date}")
            print(f"   Completed: {enrollment.completion_date}")
            
            return enrollment
            
        except Enrollment.DoesNotExist:
            print(f"❌ No enrollment found for this user in Course {course.id}")
            return None
            
    def check_lesson_progress(self, enrollment, course, total_lessons):
        """Check lesson progress details"""
        print(f"\n📈 Lesson Progress Check")
        print("=" * 30)
        
        if not enrollment:
            print("❌ Cannot check progress - no enrollment found")
            return
            
        # Get all lessons
        all_lessons = []
        modules = course.modules.filter(is_published=True).order_by('sort_order')
        
        for module in modules:
            lessons = module.lessons.filter(is_published=True).order_by('sort_order')
            all_lessons.extend(lessons)
            
        # Get progress records
        progress_records = LessonProgress.objects.filter(
            enrollment=enrollment,
            lesson__in=all_lessons
        ).order_by('lesson__module__sort_order', 'lesson__sort_order')
        
        progress_by_lesson = {lp.lesson_id: lp for lp in progress_records}
        
        # Count by status
        completed = 0
        in_progress = 0
        not_started = 0
        
        print(f"📋 Progress Details:")
        current_module_id = None
        
        for lesson in all_lessons:
            # Print module header when it changes
            if lesson.module.id != current_module_id:
                current_module_id = lesson.module.id
                print(f"\n   📖 {lesson.module.title}:")
                
            if lesson.id in progress_by_lesson:
                progress = progress_by_lesson[lesson.id]
                status_icon = "✅" if progress.status == 'completed' else "🔄" if progress.status == 'in_progress' else "⭕"
                
                print(f"     {status_icon} Lesson {lesson.id}: {progress.status}")
                print(f"        Title: {lesson.title[:60]}...")
                print(f"        Started: {progress.started_at}")
                print(f"        Completed: {progress.completed_at}")
                print(f"        Score: {progress.score}")
                print(f"        Time Spent: {progress.time_spent}s")
                
                if progress.status == 'completed':
                    completed += 1
                elif progress.status == 'in_progress':
                    in_progress += 1
                else:
                    not_started += 1
            else:
                print(f"     ⭕ Lesson {lesson.id}: no record")
                print(f"        Title: {lesson.title[:60]}...")
                not_started += 1
                
        print(f"\n📊 Progress Summary:")
        print(f"   Completed: {completed}/{total_lessons} ({completed/total_lessons*100:.1f}%)")
        print(f"   In Progress: {in_progress}")
        print(f"   Not Started: {not_started}")
        
        return completed, in_progress, not_started
        
    def check_quiz_attempts(self, user, course):
        """Check quiz attempt history"""
        print(f"\n🧪 Quiz Attempts Check")
        print("=" * 30)
        
        # Get all quizzes for the course
        quiz_attempts = QuizAttempt.objects.filter(
            student=user,
            quiz__lesson__module__course=course
        ).order_by('quiz__lesson__module__sort_order', 'quiz__lesson__sort_order', '-attempt_number')
        
        if not quiz_attempts.exists():
            print("❌ No quiz attempts found")
            return
            
        print(f"📋 Quiz Attempt History:")
        
        current_lesson_id = None
        passing_attempts = 0
        total_attempts = quiz_attempts.count()
        
        for attempt in quiz_attempts:
            lesson = attempt.quiz.lesson
            
            if lesson.id != current_lesson_id:
                current_lesson_id = lesson.id
                print(f"\n   📝 Lesson {lesson.id}: {lesson.title[:50]}...")
                
            status_icon = "✅" if attempt.is_passed else "❌"
            print(f"     {status_icon} Attempt {attempt.attempt_number}: {attempt.score}% ({'PASSED' if attempt.is_passed else 'FAILED'})")
            print(f"        Started: {attempt.started_at}")
            print(f"        Completed: {attempt.completed_at}")
            print(f"        Time Taken: {attempt.time_taken}s")
            
            if attempt.is_passed:
                passing_attempts += 1
                
        print(f"\n📊 Quiz Summary:")
        print(f"   Total Attempts: {total_attempts}")
        print(f"   Passing Attempts: {passing_attempts}")
        print(f"   Pass Rate: {passing_attempts/total_attempts*100:.1f}%" if total_attempts > 0 else "   Pass Rate: N/A")
        
    def run_check(self):
        """Run complete state check"""
        print("🔍 YITP Victor Account State Check")
        print("=" * 50)
        print(f"Target: {self.target_email}")
        print(f"Course: {self.course_id} (YITP)")
        print(f"Time: {datetime.now()}")
        
        # Environment check
        self.check_environment()
        
        # User check
        user = self.find_user()
        if not user:
            return False
            
        # Course check
        course, total_lessons = self.check_course()
        if not course:
            return False
            
        # Enrollment check
        enrollment = self.check_enrollment(user, course)
        
        # Progress check
        if enrollment:
            completed, in_progress, not_started = self.check_lesson_progress(enrollment, course, total_lessons)
            
            # Quiz attempts check
            self.check_quiz_attempts(user, course)
            
            # Final summary
            print(f"\n🎯 FINAL SUMMARY")
            print("=" * 30)
            print(f"User: {user.get_full_name()} ({user.email})")
            print(f"Course: {course.title}")
            print(f"Enrollment Status: {enrollment.status}")
            print(f"Overall Progress: {enrollment.progress_percentage}%")
            print(f"Lessons Completed: {completed}/{total_lessons}")
            
            if completed == total_lessons:
                print(f"✅ All lessons completed - ready for testing!")
            else:
                print(f"⚠️  {total_lessons - completed} lessons need completion")
                print(f"💡 Run update_victor_lesson_completion.py to mark all as completed")
        else:
            print(f"\n⚠️  No enrollment found - user needs to be enrolled first")
            
        return True


if __name__ == "__main__":
    checker = VictorStateChecker()
    success = checker.run_check()
    
    if not success:
        print(f"\n❌ State check failed")
        sys.exit(1)
    else:
        print(f"\n✅ State check completed successfully")
        sys.exit(0)
