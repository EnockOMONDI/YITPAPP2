#!/usr/bin/env python3
"""
Fix Quiz Answer Format
======================

Convert letter/number-based correct answers to text-based format
to match the working modules and fix 0% score issue.

Target modules:
- "Soft Skills for the Streets" (letter format: A, B, C, D)
- "Entrepreneurship & Small Business Administration" (number format: 1, 2, 3, 4)
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
from django.db import transaction

def fix_quiz_answer_formats():
    """Fix quiz answer formats to match working modules"""
    print("🔧 FIXING QUIZ ANSWER FORMATS")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Find YITP course
    yitp_course = Course.objects.filter(title__icontains="Youth Impact Training Programme").first()
    
    if not yitp_course:
        print("❌ YITP course not found!")
        return
    
    print(f"✅ Found YITP Course: '{yitp_course.title}'")
    
    # Target modules with problematic formats
    target_modules = [
        "Soft Skills for the Streets",  # Uses A, B, C, D
        "Entrepreneurship & Small Business Administration"  # Uses 1, 2, 3, 4
    ]
    
    # Also check for the third module mentioned by user
    target_modules.append("Understanding Purpose in Life (UPL)")  # Just to verify it's working
    target_modules.append("The Power of Mindset")  # User mentioned this one
    
    print(f"\n🎯 TARGET MODULES:")
    for module_name in target_modules:
        print(f"   - {module_name}")
    
    # Find modules
    found_modules = {}
    all_modules = yitp_course.modules.filter(is_published=True)
    
    for module in all_modules:
        for target in target_modules:
            if target.lower() in module.title.lower() or any(word in module.title.lower() for word in target.lower().split()):
                found_modules[target] = module
                break
    
    print(f"\n📚 Found {len(found_modules)} modules to process:")
    for target_name, module in found_modules.items():
        print(f"   ✅ '{target_name}' -> '{module.title}'")
    
    # Process each module
    total_fixed = 0
    
    for target_name, module in found_modules.items():
        print(f"\n🔍 PROCESSING: {module.title}")
        print("-" * 50)
        
        # Get all quizzes for this module
        quizzes = Quiz.objects.filter(
            lesson__module=module,
            is_published=True
        ).select_related('lesson')
        
        print(f"   📊 Quizzes found: {quizzes.count()}")
        
        module_fixes = 0
        
        for quiz in quizzes:
            questions = quiz.questions.filter(question_type='multiple_choice')
            
            print(f"   🧩 {quiz.title}: {questions.count()} multiple choice questions")
            
            quiz_fixes = 0
            
            for question in questions:
                correct_answer = question.correct_answer.strip()
                options = question.options if question.options else []
                
                # Check if this needs fixing
                needs_fix = False
                new_correct_answer = None
                
                # Letter format (A, B, C, D)
                if correct_answer in ['A', 'B', 'C', 'D']:
                    letter_index = ord(correct_answer) - ord('A')  # A=0, B=1, C=2, D=3
                    if letter_index < len(options):
                        option = options[letter_index]
                        if isinstance(option, dict):
                            new_correct_answer = option.get('text', '').strip()
                        elif isinstance(option, str):
                            new_correct_answer = option.strip()
                        needs_fix = True
                        print(f"      🔤 Letter '{correct_answer}' -> '{new_correct_answer[:50]}...'")
                
                # Number format (1, 2, 3, 4, 5)
                elif correct_answer in ['1', '2', '3', '4', '5']:
                    number_index = int(correct_answer) - 1  # 1=0, 2=1, 3=2, 4=3
                    if number_index < len(options):
                        option = options[number_index]
                        if isinstance(option, dict):
                            new_correct_answer = option.get('text', '').strip()
                        elif isinstance(option, str):
                            new_correct_answer = option.strip()
                        needs_fix = True
                        print(f"      🔢 Number '{correct_answer}' -> '{new_correct_answer[:50]}...'")
                
                # Apply fix if needed
                if needs_fix and new_correct_answer:
                    try:
                        with transaction.atomic():
                            question.correct_answer = new_correct_answer
                            question.save()
                            quiz_fixes += 1
                            print(f"         ✅ FIXED")
                    except Exception as e:
                        print(f"         ❌ ERROR: {str(e)}")
                elif needs_fix:
                    print(f"         ⚠️  SKIPPED: Could not determine new answer")
                
            print(f"      📊 Fixed {quiz_fixes} questions in this quiz")
            module_fixes += quiz_fixes
        
        print(f"   📊 Total fixes in module: {module_fixes}")
        total_fixed += module_fixes
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"📊 FIX SUMMARY")
    print(f"=" * 60)
    print(f"✅ Total questions fixed: {total_fixed}")
    print(f"🎯 Expected result: Users should now be able to pass quizzes")
    print(f"💡 Next step: Test quiz completion with a user account")
    
    if total_fixed > 0:
        print(f"\n🎉 SUCCESS: Quiz answer formats have been standardized!")
        print(f"   All modules now use the same text-based format:")
        print(f"   correct_answer: 'Full text of the correct option'")
        print(f"   options: ['option 1 text', 'option 2 text', 'option 3 text']")
    else:
        print(f"\n⚠️  No fixes applied. All modules may already be using correct format.")
    
    print(f"\n🕒 Fix completed at {datetime.now().strftime('%H:%M:%S')}")

def verify_fixes():
    """Verify that the fixes were applied correctly"""
    print(f"\n🔍 VERIFYING FIXES")
    print("=" * 30)
    
    # Quick verification
    yitp_course = Course.objects.filter(title__icontains="Youth Impact Training Programme").first()
    
    problematic_questions = Question.objects.filter(
        quiz__lesson__module__course=yitp_course,
        question_type='multiple_choice',
        correct_answer__in=['A', 'B', 'C', 'D', '1', '2', '3', '4', '5']
    )
    
    print(f"🔍 Remaining problematic questions: {problematic_questions.count()}")
    
    if problematic_questions.count() == 0:
        print(f"✅ SUCCESS: No more letter/number format answers found!")
    else:
        print(f"⚠️  Still found {problematic_questions.count()} questions with letter/number format")
        for q in problematic_questions[:5]:
            print(f"   - '{q.correct_answer}' in quiz: {q.quiz.title}")

if __name__ == "__main__":
    try:
        fix_quiz_answer_formats()
        verify_fixes()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
