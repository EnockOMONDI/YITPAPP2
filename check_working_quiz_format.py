#!/usr/bin/env python3
"""
Check Working Quiz Format
========================

This script examines how the working quizzes store their correct answers
to ensure our fix matches the existing working format.
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module
from assessments.models import Quiz, Question
from progress.models import QuizAttempt
from collections import Counter

def check_working_quiz_formats():
    """Check how working quizzes store their correct answers"""
    print("🔍 CHECKING WORKING QUIZ FORMATS")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Find YITP course
    yitp_course = Course.objects.filter(title__icontains="Youth Impact Training Programme").first()
    
    if not yitp_course:
        print("❌ YITP course not found!")
        return
    
    print(f"✅ Found YITP Course: '{yitp_course.title}' (ID: {yitp_course.id})")
    
    # Get all modules
    all_modules = yitp_course.modules.filter(is_published=True)
    
    print(f"\n📚 All modules in YITP ({all_modules.count()}):")
    
    # Check quiz attempts to see which quizzes have successful completions
    successful_attempts = QuizAttempt.objects.filter(
        quiz__lesson__module__course=yitp_course,
        is_passed=True,
        score__gt=0
    ).select_related('quiz', 'quiz__lesson', 'quiz__lesson__module')
    
    print(f"\n✅ Found {successful_attempts.count()} successful quiz attempts")
    
    if successful_attempts.count() > 0:
        print("\n🎯 ANALYZING WORKING QUIZZES (with successful attempts):")
        print("-" * 60)
        
        working_quizzes = set()
        for attempt in successful_attempts:
            working_quizzes.add(attempt.quiz)
        
        print(f"📊 Unique working quizzes: {len(working_quizzes)}")
        
        # Analyze format of working quizzes
        for i, quiz in enumerate(list(working_quizzes)[:5]):  # Check first 5 working quizzes
            print(f"\n🧩 Working Quiz {i+1}: {quiz.title}")
            print(f"   Module: {quiz.lesson.module.title}")
            
            questions = quiz.questions.all()[:3]  # Check first 3 questions
            
            for j, question in enumerate(questions):
                print(f"\n   📝 Question {j+1}: {question.question_text[:50]}...")
                print(f"      Type: {question.question_type}")
                print(f"      Correct Answer: '{question.correct_answer}'")
                
                if question.question_type == 'multiple_choice':
                    options = question.options if question.options else []
                    print(f"      Options ({len(options)}):")
                    for k, option in enumerate(options):
                        if isinstance(option, dict):
                            option_text = option.get('text', '')
                            print(f"         {k}: {option_text[:50]}...")
                        elif isinstance(option, str):
                            print(f"         {k}: {option[:50]}...")
                    
                    # Check if correct answer matches any option
                    correct_answer = question.correct_answer.strip()
                    matches = []
                    for k, option in enumerate(options):
                        if isinstance(option, dict):
                            option_text = option.get('text', '').strip()
                            if option_text.lower() == correct_answer.lower():
                                matches.append(f"Index {k}: {option_text[:30]}...")
                        elif isinstance(option, str):
                            if option.strip().lower() == correct_answer.lower():
                                matches.append(f"Index {k}: {option[:30]}...")
                    
                    if matches:
                        print(f"      ✅ MATCHES: {matches}")
                    else:
                        print(f"      ❌ NO MATCH FOUND")
    
    # Also check some modules that might be working
    print(f"\n🔍 CHECKING ALL MODULES FOR COMPARISON:")
    print("-" * 60)
    
    for module in all_modules:
        print(f"\n📚 Module: {module.title}")
        
        # Get first quiz from this module
        first_quiz = Quiz.objects.filter(
            lesson__module=module,
            is_published=True
        ).first()
        
        if first_quiz:
            # Get first question
            first_question = first_quiz.questions.first()
            
            if first_question and first_question.question_type == 'multiple_choice':
                print(f"   📝 Sample Question: {first_question.question_text[:50]}...")
                print(f"   ✅ Correct Answer: '{first_question.correct_answer}'")
                
                options = first_question.options if first_question.options else []
                print(f"   📋 Options Format: {type(options)} with {len(options)} items")
                
                if options:
                    first_option = options[0]
                    print(f"   📄 First Option Type: {type(first_option)}")
                    if isinstance(first_option, dict):
                        print(f"   📄 First Option Content: {first_option}")
                    else:
                        print(f"   📄 First Option Content: '{first_option}'")
                
                # Check if this follows the problematic pattern
                correct_answer = first_question.correct_answer.strip()
                if correct_answer in ['A', 'B', 'C', 'D', '1', '2', '3', '4']:
                    print(f"   ❌ PROBLEMATIC: Uses letter/number format")
                else:
                    print(f"   ✅ GOOD: Uses text format")
        else:
            print(f"   📭 No quizzes found")
    
    print(f"\n🕒 Analysis completed at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    try:
        check_working_quiz_formats()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
