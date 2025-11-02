#!/usr/bin/env python3
"""
Quick Quiz Issues Test for YITP Modules
=======================================

Fast investigation of quiz issues in three YITP modules:
1. "Soft Skills for the Streets"
2. "Understanding Purpose in Life (UPL)" 
3. "The Power of Mindset"

This is a simplified version to quickly identify the root cause of 0% scores.
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
from collections import Counter

def quick_quiz_investigation():
    """Quick investigation of quiz issues"""
    print("🚀 QUICK QUIZ ISSUES INVESTIGATION")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Find YITP course
    yitp_course = Course.objects.filter(title__icontains="Youth Impact Training Programme").first()
    
    if not yitp_course:
        print("❌ YITP course not found!")
        return
    
    print(f"✅ Found YITP Course: '{yitp_course.title}' (ID: {yitp_course.id})")
    
    # Target modules
    target_modules = [
        "Soft Skills for the Streets",
        "Understanding Purpose in Life (UPL)",
        "The Power of Mindset"
    ]
    
    # Find modules
    found_modules = {}
    all_modules = yitp_course.modules.filter(is_published=True)
    
    print(f"\n📚 All modules in YITP ({all_modules.count()}):")
    for module in all_modules:
        print(f"   - {module.title}")
        
        # Check if this matches any target
        for target in target_modules:
            if target.lower() in module.title.lower() or any(word in module.title.lower() for word in target.lower().split()):
                found_modules[target] = module
                print(f"     ✅ MATCHES: '{target}'")
                break
    
    print(f"\n📊 Found {len(found_modules)} out of {len(target_modules)} target modules")
    
    if not found_modules:
        print("❌ No target modules found!")
        return
    
    # Quick analysis of each module
    total_issues = 0
    
    for target_name, module in found_modules.items():
        print(f"\n🔍 ANALYZING: {module.title}")
        print("-" * 50)
        
        # Get all quizzes for this module
        quizzes = Quiz.objects.filter(
            lesson__module=module,
            is_published=True
        ).select_related('lesson')
        
        print(f"   📊 Quizzes: {quizzes.count()}")
        
        module_issues = []
        question_types = Counter()
        
        for quiz in quizzes:
            questions = quiz.questions.all()
            print(f"   🧩 {quiz.title}: {questions.count()} questions")
            
            for question in questions:
                question_types[question.question_type] += 1
                
                # Quick issue detection
                if question.question_type == 'multiple_choice':
                    options = question.options if question.options else []
                    correct_answer = question.correct_answer.strip()
                    
                    if not options:
                        module_issues.append(f"No options: {question.question_text[:50]}...")
                    elif not correct_answer:
                        module_issues.append(f"Empty correct answer: {question.question_text[:50]}...")
                    else:
                        # Check if correct answer matches any option
                        option_texts = []
                        for opt in options:
                            if isinstance(opt, dict):
                                option_texts.append(opt.get('text', '').strip().lower())
                            elif isinstance(opt, str):
                                option_texts.append(opt.strip().lower())
                        
                        if correct_answer.lower() not in option_texts:
                            module_issues.append(f"Correct answer '{correct_answer}' not in options: {question.question_text[:50]}...")
                            print(f"      ⚠️  MISMATCH: '{correct_answer}' not in {option_texts}")
                
                elif question.question_type == 'short_answer':
                    module_issues.append(f"Short answer (exact match issue): {question.question_text[:50]}...")
                    print(f"      ⚠️  SHORT ANSWER: {question.question_text[:50]}...")
                
                elif question.question_type == 'true_false':
                    correct_answer = question.correct_answer.strip().lower()
                    if correct_answer not in ['true', 'false', 'yes', 'no', '1', '0']:
                        module_issues.append(f"Invalid true/false answer '{correct_answer}': {question.question_text[:50]}...")
        
        print(f"   📈 Question Types: {dict(question_types)}")
        print(f"   ⚠️  Issues Found: {len(module_issues)}")
        
        if module_issues:
            print(f"   🔍 First 5 issues:")
            for i, issue in enumerate(module_issues[:5]):
                print(f"      {i+1}. {issue}")
            if len(module_issues) > 5:
                print(f"      ... and {len(module_issues) - 5} more")
        
        total_issues += len(module_issues)
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"📊 QUICK INVESTIGATION SUMMARY")
    print(f"=" * 60)
    print(f"✅ Modules analyzed: {len(found_modules)}")
    print(f"⚠️  Total issues found: {total_issues}")
    
    if total_issues > 0:
        print(f"\n🎯 LIKELY CAUSES OF 0% SCORES:")
        print(f"   1. Multiple choice questions with mismatched correct answers")
        print(f"   2. Short answer questions requiring exact string matches")
        print(f"   3. True/false questions with invalid correct answer values")
        print(f"\n💡 RECOMMENDATION:")
        print(f"   - Fix multiple choice answer matching (case sensitivity, spacing)")
        print(f"   - Convert short answer questions to multiple choice")
        print(f"   - Standardize true/false correct answer values")
    else:
        print(f"\n✅ No obvious issues found in quiz configuration")
        print(f"💡 The 0% score issue might be in the quiz scoring logic or user interface")
    
    print(f"\n🕒 Investigation completed at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    try:
        quick_quiz_investigation()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
