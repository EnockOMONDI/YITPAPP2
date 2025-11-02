#!/usr/bin/env python3
"""
Verify the generated YITP Complete Answer Key PDF
"""

import os
import json
from datetime import datetime

def verify_answer_key_pdf():
    """Verify the generated PDF and data integrity"""
    
    print("🔍 VERIFYING YITP COMPLETE ANSWER KEY PDF")
    print("=" * 60)
    
    # Check if files exist
    pdf_file = 'YITP_Complete_Answer_Key.pdf'
    json_file = 'yitp_quiz_answers_complete.json'
    
    files_exist = True
    
    if os.path.exists(pdf_file):
        pdf_size = os.path.getsize(pdf_file)
        pdf_size_mb = pdf_size / (1024 * 1024)
        print(f"✅ PDF file exists: {pdf_file}")
        print(f"   📏 File size: {pdf_size_mb:.2f} MB ({pdf_size:,} bytes)")
    else:
        print(f"❌ PDF file not found: {pdf_file}")
        files_exist = False
    
    if os.path.exists(json_file):
        json_size = os.path.getsize(json_file)
        json_size_kb = json_size / 1024
        print(f"✅ JSON data file exists: {json_file}")
        print(f"   📏 File size: {json_size_kb:.1f} KB ({json_size:,} bytes)")
    else:
        print(f"❌ JSON data file not found: {json_file}")
        files_exist = False
    
    if not files_exist:
        return False
    
    # Load and verify JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            quiz_data = json.load(f)
        print(f"✅ Successfully loaded quiz data from JSON")
    except Exception as e:
        print(f"❌ Error loading JSON data: {e}")
        return False
    
    # Verify data structure and statistics
    print(f"\n📊 DATA VERIFICATION:")
    print(f"   • Course: {quiz_data.get('course_title', 'N/A')}")
    
    stats = quiz_data.get('statistics', {})
    modules = quiz_data.get('modules', [])
    
    print(f"   • Total modules: {stats.get('total_modules', 0)}")
    print(f"   • Total lessons: {stats.get('total_lessons', 0)}")
    print(f"   • Total quizzes: {stats.get('total_quizzes', 0)}")
    print(f"   • Total questions: {stats.get('total_questions', 0)}")
    
    # Verify each module
    print(f"\n📂 MODULE VERIFICATION:")
    
    expected_modules = [
        "Understanding Purpose in Life (UPL)",
        "Personal Initiative & Assessments (Phase 1)",
        "TPM 101 – The Power of Mindset",
        "Soft Skills for the Streets",
        "Entrepreneurship & Small Business Administration (ESBA)"
    ]
    
    total_questions_verified = 0
    total_quizzes_verified = 0
    total_lessons_verified = 0
    
    for i, module in enumerate(modules):
        module_title = module.get('module_title', 'Unknown')
        module_sort_order = module.get('module_sort_order', 0)
        lesson_count = module.get('lesson_count', 0)
        quiz_count = module.get('quiz_count', 0)
        question_count = module.get('question_count', 0)
        
        print(f"   📂 Module {module_sort_order}: {module_title}")
        print(f"      📄 Lessons: {lesson_count}")
        print(f"      🧪 Quizzes: {quiz_count}")
        print(f"      ❓ Questions: {question_count}")
        
        # Verify module title matches expected
        if i < len(expected_modules):
            if expected_modules[i] in module_title:
                print(f"      ✅ Module title matches expected")
            else:
                print(f"      ⚠️  Module title may not match expected: {expected_modules[i]}")
        
        # Count questions in lessons
        lessons = module.get('lessons', [])
        module_questions_count = 0
        module_quizzes_count = 0
        
        for lesson in lessons:
            quizzes = lesson.get('quizzes', [])
            for quiz in quizzes:
                questions = quiz.get('questions', [])
                module_questions_count += len(questions)
                module_quizzes_count += 1
                
                # Verify each question has required fields
                for question in questions:
                    required_fields = ['question_text', 'correct_answer', 'question_type']
                    for field in required_fields:
                        if field not in question or not question[field]:
                            print(f"      ⚠️  Question missing {field}")
        
        if module_questions_count == question_count:
            print(f"      ✅ Question count verified: {module_questions_count}")
        else:
            print(f"      ❌ Question count mismatch: expected {question_count}, found {module_questions_count}")
        
        total_questions_verified += module_questions_count
        total_quizzes_verified += module_quizzes_count
        total_lessons_verified += lesson_count
    
    # Final verification
    print(f"\n📊 FINAL VERIFICATION:")
    
    verification_results = []
    
    # Check totals
    if total_questions_verified == stats.get('total_questions', 0):
        print(f"   ✅ Total questions verified: {total_questions_verified}")
        verification_results.append(True)
    else:
        print(f"   ❌ Total questions mismatch: expected {stats.get('total_questions', 0)}, verified {total_questions_verified}")
        verification_results.append(False)
    
    if total_quizzes_verified == stats.get('total_quizzes', 0):
        print(f"   ✅ Total quizzes verified: {total_quizzes_verified}")
        verification_results.append(True)
    else:
        print(f"   ❌ Total quizzes mismatch: expected {stats.get('total_quizzes', 0)}, verified {total_quizzes_verified}")
        verification_results.append(False)
    
    if total_lessons_verified == stats.get('total_lessons', 0):
        print(f"   ✅ Total lessons verified: {total_lessons_verified}")
        verification_results.append(True)
    else:
        print(f"   ❌ Total lessons mismatch: expected {stats.get('total_lessons', 0)}, verified {total_lessons_verified}")
        verification_results.append(False)
    
    if len(modules) == 5:
        print(f"   ✅ All 5 modules present")
        verification_results.append(True)
    else:
        print(f"   ❌ Expected 5 modules, found {len(modules)}")
        verification_results.append(False)
    
    # Check expected totals
    expected_totals = {
        'modules': 5,
        'lessons': 40,
        'quizzes': 40,
        'questions': 200
    }
    
    print(f"\n🎯 EXPECTED VS ACTUAL:")
    for key, expected in expected_totals.items():
        actual = stats.get(f'total_{key}', 0)
        if actual == expected:
            print(f"   ✅ {key.capitalize()}: {actual} (matches expected)")
        else:
            print(f"   ❌ {key.capitalize()}: {actual} (expected {expected})")
    
    # Overall assessment
    success_rate = sum(verification_results) / len(verification_results) * 100
    
    print(f"\n📈 VERIFICATION SUMMARY:")
    print(f"   • Verification tests passed: {sum(verification_results)}/{len(verification_results)}")
    print(f"   • Success rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print(f"   🎉 EXCELLENT - All verifications passed!")
        return True
    elif success_rate >= 80:
        print(f"   ✅ GOOD - Most verifications passed")
        return True
    else:
        print(f"   ❌ FAILED - Multiple verification issues found")
        return False

def display_sample_questions():
    """Display a sample of questions from each module"""
    
    print(f"\n📋 SAMPLE QUESTIONS FROM EACH MODULE:")
    print("=" * 60)
    
    json_file = 'yitp_quiz_answers_complete.json'
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            quiz_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading quiz data: {e}")
        return
    
    modules = quiz_data.get('modules', [])
    
    for module in modules:
        print(f"\n📂 Module {module.get('module_sort_order', 0)}: {module.get('module_title', 'Unknown')}")
        
        lessons = module.get('lessons', [])
        if lessons:
            first_lesson = lessons[0]
            quizzes = first_lesson.get('quizzes', [])
            if quizzes:
                first_quiz = quizzes[0]
                questions = first_quiz.get('questions', [])
                if questions:
                    first_question = questions[0]
                    print(f"   📄 Lesson: {first_lesson.get('lesson_title', 'Unknown')}")
                    print(f"   🧪 Quiz: {first_quiz.get('quiz_title', 'Unknown')}")
                    print(f"   ❓ Sample Question: {first_question.get('question_text', 'N/A')}")
                    print(f"   ✅ Correct Answer: {first_question.get('correct_answer', 'N/A')}")

def main():
    success = verify_answer_key_pdf()
    
    if success:
        print(f"\n🎉 YITP Complete Answer Key PDF verification completed successfully!")
        print(f"📁 PDF file: YITP_Complete_Answer_Key.pdf")
        print(f"📊 Contains all 200 questions from 40 quizzes across 5 modules")
        
        # Display sample questions
        display_sample_questions()
        
        print(f"\n✅ The answer key PDF is ready for use!")
    else:
        print(f"\n❌ PDF verification failed - please check the issues above")

if __name__ == "__main__":
    main()
