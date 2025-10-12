#!/usr/bin/env python3
"""
Data Safety Analysis for Lesson Deletion
=========================================

Analyze the potential impact of deleting lessons 103-110 on student data.
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set up Django environment for PRODUCTION database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode

django.setup()

from django.db import connection
from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question
from progress.models import Enrollment, LessonProgress, QuizAttempt

def analyze_data_safety():
    """Analyze what student data would be affected by deleting lessons 103-110"""
    print("🔍 DATA SAFETY ANALYSIS FOR LESSON DELETION")
    print("=" * 60)
    
    try:
        # Get course and module
        course = Course.objects.get(id=6)
        module = Module.objects.get(id=14, course=course)
        
        # Get lessons to be deleted (103-110)
        original_lessons = Lesson.objects.filter(
            module=module, 
            id__in=[103, 104, 105, 106, 107, 108, 109, 110]
        ).order_by('id')
        
        # Get lessons to be kept (111-117)
        new_lessons = Lesson.objects.filter(
            module=module,
            id__in=[111, 112, 113, 114, 115, 116, 117]
        ).order_by('id')
        
        print(f"📚 Course: {course.title}")
        print(f"📖 Module: {module.title}")
        print(f"📄 Original Lessons (to delete): {original_lessons.count()}")
        print(f"📄 New Lessons (to keep): {new_lessons.count()}")
        print()
        
        # Analyze student data that would be affected
        print("🚨 STUDENT DATA IMPACT ANALYSIS")
        print("-" * 40)
        
        # 1. Enrollments (should NOT be affected)
        enrollments = Enrollment.objects.filter(course=course)
        print(f"👥 Course Enrollments: {enrollments.count()}")
        print(f"   ✅ SAFE: Enrollments are linked to Course, not individual lessons")
        print()
        
        # 2. Lesson Progress (WILL BE DELETED - CASCADE)
        total_lesson_progress = 0
        for lesson in original_lessons:
            progress_count = LessonProgress.objects.filter(lesson=lesson).count()
            total_lesson_progress += progress_count
            if progress_count > 0:
                print(f"   ⚠️ Lesson {lesson.id} ({lesson.title[:50]}...): {progress_count} progress records")
        
        print(f"📊 Total Lesson Progress Records to be DELETED: {total_lesson_progress}")
        print(f"   ❌ RISK: LessonProgress has CASCADE delete on lesson")
        print()
        
        # 3. Quiz Attempts (WILL BE DELETED - CASCADE)
        total_quiz_attempts = 0
        for lesson in original_lessons:
            quizzes = Quiz.objects.filter(lesson=lesson)
            for quiz in quizzes:
                attempt_count = QuizAttempt.objects.filter(quiz=quiz).count()
                total_quiz_attempts += attempt_count
                if attempt_count > 0:
                    print(f"   ⚠️ Quiz {quiz.id} (Lesson {lesson.id}): {attempt_count} quiz attempts")
        
        print(f"📊 Total Quiz Attempts to be DELETED: {total_quiz_attempts}")
        print(f"   ❌ RISK: QuizAttempt has CASCADE delete on quiz")
        print()
        
        # 4. Quizzes and Questions (WILL BE DELETED - CASCADE)
        total_quizzes = 0
        total_questions = 0
        for lesson in original_lessons:
            quiz_count = Quiz.objects.filter(lesson=lesson).count()
            total_quizzes += quiz_count
            for quiz in Quiz.objects.filter(lesson=lesson):
                question_count = Question.objects.filter(quiz=quiz).count()
                total_questions += question_count
        
        print(f"📊 Total Quizzes to be DELETED: {total_quizzes}")
        print(f"📊 Total Questions to be DELETED: {total_questions}")
        print(f"   ❌ RISK: Quiz has CASCADE delete on lesson")
        print(f"   ❌ RISK: Question has CASCADE delete on quiz")
        print()
        
        # 5. Study Sessions (lesson field is SET_NULL - SAFE)
        from progress.models import StudySession
        study_sessions = StudySession.objects.filter(lesson__in=original_lessons)
        print(f"📊 Study Sessions with deleted lessons: {study_sessions.count()}")
        print(f"   ✅ SAFE: StudySession has SET_NULL on lesson deletion")
        print()
        
        # Summary of data loss
        print("📋 DATA LOSS SUMMARY")
        print("-" * 30)
        print(f"❌ Lesson Progress Records: {total_lesson_progress}")
        print(f"❌ Quiz Attempts: {total_quiz_attempts}")
        print(f"❌ Quizzes: {total_quizzes}")
        print(f"❌ Questions: {total_questions}")
        print(f"✅ Course Enrollments: 0 (preserved)")
        print(f"✅ Study Sessions: 0 (lesson field set to NULL)")
        print()
        
        # Analyze student progress impact
        print("📊 STUDENT PROGRESS IMPACT")
        print("-" * 30)
        
        for enrollment in enrollments:
            student = enrollment.student
            
            # Current progress on original lessons
            original_progress = LessonProgress.objects.filter(
                enrollment=enrollment,
                lesson__in=original_lessons
            )
            
            # Current progress on new lessons
            new_progress = LessonProgress.objects.filter(
                enrollment=enrollment,
                lesson__in=new_lessons
            )
            
            # Quiz attempts on original lessons
            original_attempts = QuizAttempt.objects.filter(
                enrollment=enrollment,
                quiz__lesson__in=original_lessons
            )
            
            print(f"👤 {student.username}:")
            print(f"   📚 Progress on original lessons: {original_progress.count()}")
            print(f"   📚 Progress on new lessons: {new_progress.count()}")
            print(f"   🎯 Quiz attempts on original lessons: {original_attempts.count()}")
            print(f"   ❌ Will lose: {original_progress.count()} progress + {original_attempts.count()} attempts")
            print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 20)
        print("1. ⚠️ SIGNIFICANT DATA LOSS: Deleting lessons 103-110 will permanently delete:")
        print(f"   - {total_lesson_progress} lesson progress records")
        print(f"   - {total_quiz_attempts} quiz attempts")
        print("2. 🔄 ALTERNATIVE APPROACH: Instead of deleting, consider:")
        print("   - Mark original lessons as 'inactive' or 'deprecated'")
        print("   - Hide them from student view")
        print("   - Preserve historical data")
        print("3. 📊 PROGRESS RECALCULATION: After deletion, student progress will:")
        print("   - Drop significantly (fewer total lessons)")
        print("   - Lose historical learning data")
        print("   - Require manual explanation to students")
        
        return {
            'lesson_progress_loss': total_lesson_progress,
            'quiz_attempts_loss': total_quiz_attempts,
            'quizzes_loss': total_quizzes,
            'questions_loss': total_questions,
            'enrollments_safe': enrollments.count(),
            'safe_to_delete': total_lesson_progress == 0 and total_quiz_attempts == 0
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    result = analyze_data_safety()
    if result:
        print(f"\n🎯 FINAL ASSESSMENT:")
        if result['safe_to_delete']:
            print("✅ SAFE TO DELETE: No student data will be lost")
        else:
            print("❌ NOT SAFE TO DELETE: Student data will be permanently lost")
            print(f"   - {result['lesson_progress_loss']} progress records")
            print(f"   - {result['quiz_attempts_loss']} quiz attempts")
