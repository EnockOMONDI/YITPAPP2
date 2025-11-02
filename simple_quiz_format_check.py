#!/usr/bin/env python3
"""
Simple Quiz Format Check
========================

Quick check of how different modules store their quiz answers
to understand the working vs broken format.
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

def simple_format_check():
    """Simple check of quiz answer formats across modules"""
    print("🔍 SIMPLE QUIZ FORMAT CHECK")
    print("=" * 50)
    
    # Find YITP course
    yitp_course = Course.objects.filter(title__icontains="Youth Impact Training Programme").first()
    
    if not yitp_course:
        print("❌ YITP course not found!")
        return
    
    print(f"✅ Found YITP Course: '{yitp_course.title}'")
    
    # Get all modules
    all_modules = yitp_course.modules.filter(is_published=True)
    
    print(f"\n📚 Checking format across {all_modules.count()} modules:")
    print("=" * 50)
    
    for module in all_modules:
        print(f"\n📚 MODULE: {module.title}")
        print("-" * 40)
        
        # Get first quiz from this module
        first_quiz = Quiz.objects.filter(
            lesson__module=module,
            is_published=True
        ).first()
        
        if not first_quiz:
            print("   📭 No quizzes found")
            continue
            
        print(f"   🧩 Sample Quiz: {first_quiz.title}")
        
        # Get first few questions
        questions = first_quiz.questions.filter(question_type='multiple_choice')[:2]
        
        if not questions:
            print("   📭 No multiple choice questions found")
            continue
        
        for i, question in enumerate(questions):
            print(f"\n   📝 Question {i+1}: {question.question_text[:40]}...")
            print(f"      Correct Answer: '{question.correct_answer}'")
            
            options = question.options if question.options else []
            print(f"      Options ({len(options)}):")
            
            for j, option in enumerate(options[:3]):  # Show first 3 options
                if isinstance(option, dict):
                    option_text = option.get('text', '')
                    print(f"         {j}: {option_text[:40]}...")
                elif isinstance(option, str):
                    print(f"         {j}: {option[:40]}...")
            
            # Determine format type
            correct_answer = question.correct_answer.strip()
            
            if correct_answer in ['A', 'B', 'C', 'D']:
                print(f"      🔤 FORMAT: Letter-based (A, B, C, D)")
                format_type = "LETTER"
            elif correct_answer in ['1', '2', '3', '4', '5']:
                print(f"      🔢 FORMAT: Number-based (1, 2, 3, 4)")
                format_type = "NUMBER"
            elif len(correct_answer) > 5:  # Likely text
                print(f"      📝 FORMAT: Text-based (full option text)")
                format_type = "TEXT"
            else:
                print(f"      ❓ FORMAT: Unknown/Other")
                format_type = "OTHER"
            
            # Check if it matches any option (for text format)
            if format_type == "TEXT":
                matches = []
                for k, option in enumerate(options):
                    if isinstance(option, dict):
                        option_text = option.get('text', '').strip()
                        if option_text.lower() == correct_answer.lower():
                            matches.append(k)
                    elif isinstance(option, str):
                        if option.strip().lower() == correct_answer.lower():
                            matches.append(k)
                
                if matches:
                    print(f"      ✅ MATCHES option(s): {matches}")
                else:
                    print(f"      ❌ NO MATCH found")
            else:
                print(f"      ⚠️  PROBLEMATIC: Cannot match {format_type} format to text options")
    
    print(f"\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    print("🎯 Expected working format:")
    print("   correct_answer: 'Full text of the correct option'")
    print("   options: ['option 1 text', 'option 2 text', 'option 3 text']")
    print("")
    print("❌ Problematic formats found:")
    print("   correct_answer: 'A' or 'B' or '1' or '2'")
    print("   options: ['option 1 text', 'option 2 text', 'option 3 text']")
    print("")
    print("💡 Fix needed: Convert letter/number answers to full text")

if __name__ == "__main__":
    try:
        simple_format_check()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
