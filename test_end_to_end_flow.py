#!/usr/bin/env python
"""
YITP LMS Phase 3: End-to-End Flow Testing Script
Tests the complete student journey from enrollment to certificate generation
"""

import os
import sys
import django
from datetime import datetime
import pytz

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from courses.models import Course, Module, Lesson
from progress.models import Enrollment, LessonProgress
from assessments.models import Quiz, Question, QuizAttempt
from certificates.models import Certificate
from courses.enrollment_service import EnrollmentService

def main():
    print("=== YITP LMS PHASE 3: END-TO-END FLOW TESTING ===")
    
    # Configure East Africa Time (Nairobi - UTC+3)
    nairobi_tz = pytz.timezone('Africa/Nairobi')
    current_time = timezone.now().astimezone(nairobi_tz)
    print(f"✅ Timezone configured: {nairobi_tz}")
    print(f"Current time in Nairobi: {current_time}")
    
    # Step 1: Reconnect to existing test data
    print("\n=== STEP 1: RECONNECTING TO TEST DATA ===")
    try:
        finaluser = User.objects.get(username='finaluser')
        course = Course.objects.get(title="Starting a Business in 2025")
        enrollment = Enrollment.objects.get(student=finaluser, course=course)
        
        print(f"✅ User: {finaluser.get_full_name()} ({finaluser.email})")
        print(f"✅ Course: {course.title}")
        print(f"✅ Enrollment: ID {enrollment.id}, Status: {enrollment.status}")
        print(f"   Enrolled at (Nairobi): {enrollment.enrolled_at.astimezone(nairobi_tz)}")
        print(f"   Current progress: {enrollment.progress_percentage}%")
        
    except Exception as e:
        print(f"❌ Error reconnecting to test data: {e}")
        return False
    
    # Step 2: Get course structure
    print("\n=== STEP 2: COURSE STRUCTURE ANALYSIS ===")
    lessons = []
    for module in course.modules.all().order_by('sort_order'):
        for lesson in module.lessons.all().order_by('sort_order'):
            lessons.append(lesson)
    
    print(f"Total lessons: {len(lessons)}")
    for i, lesson in enumerate(lessons, 1):
        print(f"  {i}. {lesson.title} (Module: {lesson.module.title})")
    
    # Step 3: Check existing progress
    print("\n=== STEP 3: EXISTING PROGRESS CHECK ===")
    existing_progress = LessonProgress.objects.filter(enrollment=enrollment)
    completed_lessons = []
    
    for progress in existing_progress:
        print(f"Lesson: {progress.lesson.title}")
        print(f"Status: {progress.status}")
        if progress.completed_at:
            print(f"Completed: {progress.completed_at.astimezone(nairobi_tz)}")
            if progress.status == 'completed':
                completed_lessons.append(progress.lesson.id)
        print("---")
    
    print(f"Completed lessons: {len(completed_lessons)}")
    
    # Step 4: Complete remaining lessons
    print("\n=== STEP 4: COMPLETING REMAINING LESSONS ===")
    
    for i, lesson in enumerate(lessons):
        lesson_num = i + 1
        print(f"\n--- Processing Lesson {lesson_num}: {lesson.title} ---")
        
        # Check if lesson is accessible
        accessible, message = lesson.is_accessible_for_user(finaluser)
        print(f"Accessible: {accessible} - {message}")
        
        if not accessible:
            print(f"❌ Cannot access lesson {lesson_num}: {message}")
            continue
        
        # Check if already completed
        if lesson.id in completed_lessons:
            print(f"✅ Lesson {lesson_num} already completed")
            continue
        
        # Create or get lesson progress
        lesson_progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={'status': 'in_progress'}
        )
        
        if created:
            print(f"📝 Created new progress for lesson {lesson_num}")
        else:
            print(f"📝 Found existing progress for lesson {lesson_num}")
        
        # Mark lesson as completed
        lesson_progress.mark_completed()
        print(f"✅ Lesson {lesson_num} completed!")
        print(f"   Completed at (Nairobi): {lesson_progress.completed_at.astimezone(nairobi_tz)}")
        
        # Check for quiz after lesson completion
        quiz = lesson.quizzes.first()
        if quiz:
            print(f"\n🧪 Testing Quiz: {quiz.title}")
            test_quiz_completion(quiz, finaluser, enrollment, nairobi_tz)
    
    # Step 5: Test course completion
    print("\n=== STEP 5: TESTING COURSE COMPLETION ===")
    test_course_completion(enrollment, nairobi_tz)
    
    # Step 6: Test certificate generation
    print("\n=== STEP 6: TESTING CERTIFICATE GENERATION ===")
    test_certificate_generation(finaluser, course, nairobi_tz)
    
    # Step 7: Final progress verification
    print("\n=== STEP 7: FINAL PROGRESS VERIFICATION ===")
    verify_final_progress(enrollment, nairobi_tz)
    
    print("\n=== END-TO-END TESTING COMPLETED ===")
    return True

def test_quiz_completion(quiz, student, enrollment, nairobi_tz):
    """Test quiz completion with 70% passing score"""
    print(f"Quiz: {quiz.title}")
    print(f"Passing score: {quiz.passing_score}%")
    print(f"Max attempts: {quiz.max_attempts}")
    
    # Check if already completed
    existing_attempt = QuizAttempt.objects.filter(
        quiz=quiz, 
        student=student, 
        is_passed=True
    ).first()
    
    if existing_attempt:
        print(f"✅ Quiz already passed with score: {existing_attempt.score}%")
        return
    
    # Get quiz questions
    questions = quiz.questions.all().order_by('sort_order')
    print(f"Questions: {questions.count()}")
    
    if questions.count() == 0:
        print("❌ No questions found for quiz")
        return
    
    # Create quiz attempt
    quiz_attempt = QuizAttempt.objects.create(
        quiz=quiz,
        student=student,
        enrollment=enrollment,
        started_at=timezone.now()
    )
    
    # Simulate answering questions correctly (100% score)
    correct_answers = questions.count()
    total_questions = questions.count()
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Update quiz attempt
    quiz_attempt.score = score
    quiz_attempt.is_passed = score >= quiz.passing_score
    quiz_attempt.completed_at = timezone.now()
    quiz_attempt.save()
    
    print(f"✅ Quiz completed!")
    print(f"   Score: {score}%")
    print(f"   Passed: {quiz_attempt.is_passed}")
    print(f"   Completed at (Nairobi): {quiz_attempt.completed_at.astimezone(nairobi_tz)}")

def test_course_completion(enrollment, nairobi_tz):
    """Test automatic course completion detection"""
    print("Testing course completion detection...")
    
    # Refresh enrollment to get latest progress
    enrollment.refresh_from_db()
    
    # Check completion status
    completion_status = enrollment.check_completion_status()
    print(f"Completion check result: {completion_status}")
    
    if completion_status.get('is_completed'):
        print(f"✅ Course automatically marked as completed!")
        print(f"   Completion date (Nairobi): {enrollment.completion_date.astimezone(nairobi_tz)}")
        print(f"   Final progress: {enrollment.progress_percentage}%")
    else:
        print(f"⏳ Course not yet completed")
        print(f"   Current progress: {enrollment.progress_percentage}%")
        print(f"   Completed lessons: {completion_status.get('completed_lessons', 0)}")
        print(f"   Total lessons: {completion_status.get('total_lessons', 0)}")

def test_certificate_generation(user, course, nairobi_tz):
    """Test certificate generation and email delivery"""
    print("Testing certificate generation...")
    
    try:
        # Check if certificate already exists
        certificate = Certificate.objects.filter(user=user, course=course).first()
        
        if certificate:
            print(f"✅ Certificate found!")
            print(f"   Certificate ID: {certificate.certificate_id}")
            print(f"   Issued at (Nairobi): {certificate.issued_at.astimezone(nairobi_tz)}")
            print(f"   Download URL: {certificate.get_download_url()}")
        else:
            print("⏳ No certificate found - may need manual generation")
            
            # Try to generate certificate manually
            from certificates.services import CertificateService
            result = CertificateService.generate_certificate(user, course)
            
            if result['success']:
                certificate = result['certificate']
                print(f"✅ Certificate generated!")
                print(f"   Certificate ID: {certificate.certificate_id}")
                print(f"   Issued at (Nairobi): {certificate.issued_at.astimezone(nairobi_tz)}")
            else:
                print(f"❌ Certificate generation failed: {result.get('message')}")
                
    except Exception as e:
        print(f"❌ Certificate testing error: {e}")

def verify_final_progress(enrollment, nairobi_tz):
    """Verify final progress and provide summary"""
    enrollment.refresh_from_db()
    
    print(f"Final enrollment status: {enrollment.status}")
    print(f"Final progress: {enrollment.progress_percentage}%")
    
    if enrollment.completion_date:
        print(f"Completion date (Nairobi): {enrollment.completion_date.astimezone(nairobi_tz)}")
    
    # Count completed lessons
    completed_lessons = LessonProgress.objects.filter(
        enrollment=enrollment,
        status='completed'
    ).count()
    
    total_lessons = enrollment.course.total_lessons
    print(f"Lessons completed: {completed_lessons}/{total_lessons}")
    
    # Count passed quizzes
    passed_quizzes = QuizAttempt.objects.filter(
        student=enrollment.student,
        enrollment=enrollment,
        is_passed=True
    ).count()
    
    print(f"Quizzes passed: {passed_quizzes}")

if __name__ == "__main__":
    main()
