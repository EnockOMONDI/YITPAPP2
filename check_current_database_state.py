#!/usr/bin/env python3
"""
Quick Database State Check
==========================

Check the current state of Course 6 lessons and quizzes after implementation.
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set up Django environment for PRODUCTION database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode to connect to Supabase

import django
django.setup()

from django.db import connection
from django.conf import settings
from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question
from progress.models import Enrollment, QuizAttempt

def check_database_state():
    """Check current database state"""
    print("🔍 CURRENT DATABASE STATE CHECK")
    print("=" * 50)
    
    try:
        # Get course and module info
        course = Course.objects.get(id=6)
        module = Module.objects.get(id=14, course=course)
        
        print(f"📚 Course: {course.title}")
        print(f"📖 Module: {module.title}")
        
        # Get all lessons in Module 1
        lessons = Lesson.objects.filter(module=module).order_by('sort_order')
        print(f"📄 Total Lessons in Module: {lessons.count()}")
        
        print(f"\n📋 LESSON BREAKDOWN:")
        for lesson in lessons:
            quizzes = Quiz.objects.filter(lesson=lesson)
            total_questions = 0
            for quiz in quizzes:
                total_questions += Question.objects.filter(quiz=quiz).count()
            
            print(f"   Lesson {lesson.id}: {lesson.title}")
            print(f"      Sort Order: {lesson.sort_order}")
            print(f"      Quizzes: {quizzes.count()}")
            print(f"      Questions: {total_questions}")
            print()
        
        # Check for duplicate questions
        print(f"🔍 DUPLICATE QUESTION ANALYSIS:")
        from collections import defaultdict
        question_fingerprints = defaultdict(list)
        
        for lesson in lessons:
            quizzes = Quiz.objects.filter(lesson=lesson)
            for quiz in quizzes:
                questions = Question.objects.filter(quiz=quiz)
                for question in questions:
                    fingerprint = f"{question.question_text}|{question.question_type}|{question.correct_answer}"
                    question_fingerprints[fingerprint].append({
                        'lesson_id': lesson.id,
                        'lesson_title': lesson.title,
                        'quiz_id': quiz.id,
                        'question_id': question.id
                    })
        
        duplicates = {fp: locations for fp, locations in question_fingerprints.items() if len(locations) > 1}
        
        print(f"   Total Unique Questions: {len(question_fingerprints)}")
        print(f"   Duplicated Questions: {len(duplicates)}")
        
        if duplicates:
            print(f"\n⚠️ FOUND {len(duplicates)} DUPLICATED QUESTIONS:")
            for i, (fingerprint, locations) in enumerate(duplicates.items(), 1):
                question_text = fingerprint.split('|')[0][:60] + "..."
                print(f"   {i}. '{question_text}' appears in {len(locations)} lessons:")
                for loc in locations:
                    print(f"      - Lesson {loc['lesson_id']}: {loc['lesson_title']}")
        else:
            print(f"✅ NO DUPLICATE QUESTIONS FOUND!")
        
        # Check student data
        print(f"\n👥 STUDENT DATA:")
        enrollments = Enrollment.objects.filter(course=course)
        quiz_attempts = QuizAttempt.objects.filter(enrollment__course=course)
        
        print(f"   Total Enrollments: {enrollments.count()}")
        print(f"   Total Quiz Attempts: {quiz_attempts.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    check_database_state()
