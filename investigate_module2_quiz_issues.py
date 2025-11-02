#!/usr/bin/env python3
"""
Investigate Module 2 (Personal Initiative & Assessments) quiz issues
preventing users from passing quizzes
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question
from progress.models import LessonProgress, QuizAttempt

def investigate_user_quiz_attempts(email):
    """Investigate specific user's quiz attempts in Module 2"""
    
    print(f"🔍 INVESTIGATING USER QUIZ ATTEMPTS: {email}")
    print("=" * 60)
    
    try:
        user = User.objects.get(email=email)
        print(f"✅ Found user: {user.username} ({user.email})")
        print(f"   📅 Joined: {user.date_joined}")
        print(f"   🔐 Active: {user.is_active}")
    except User.DoesNotExist:
        print(f"❌ User not found: {email}")
        return None
    
    # Get Module 2 (Personal Initiative)
    try:
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module2 = Module.objects.get(course=course, sort_order=2)
        print(f"✅ Found Module 2: {module2.title}")
    except (Course.DoesNotExist, Module.DoesNotExist) as e:
        print(f"❌ Error finding Module 2: {e}")
        return None
    
    # Get all lessons in Module 2
    lessons = Lesson.objects.filter(module=module2).order_by('sort_order')
    print(f"📚 Module 2 has {lessons.count()} lessons")
    
    # Analyze quiz attempts for each lesson
    total_attempts = 0
    failed_attempts = 0
    passed_attempts = 0
    
    for lesson in lessons:
        print(f"\n📄 Lesson {lesson.sort_order}: {lesson.title}")
        
        # Get quizzes for this lesson
        quizzes = Quiz.objects.filter(lesson=lesson)
        
        for quiz in quizzes:
            print(f"   🧪 Quiz: {quiz.title}")
            print(f"      📊 Passing score: {quiz.passing_score}%")
            print(f"      🔄 Max attempts: {quiz.max_attempts}")
            
            # Get user's attempts for this quiz
            attempts = QuizAttempt.objects.filter(
                student=user,
                quiz=quiz
            ).order_by('attempt_number')

            print(f"      📝 User attempts: {attempts.count()}")

            for attempt in attempts:
                total_attempts += 1
                print(f"         🎯 Attempt {attempt.attempt_number}: {attempt.score}% (Passed: {attempt.is_passed})")

                if attempt.is_passed:
                    passed_attempts += 1
                else:
                    failed_attempts += 1

                # Analyze individual question answers from the answers JSON field
                answers = attempt.answers or {}
                questions = Question.objects.filter(quiz=quiz)
                print(f"            📋 Questions in quiz: {questions.count()}")
                print(f"            📋 Questions answered: {len(answers)}")

                correct_count = 0
                for question in questions:
                    student_answer = answers.get(str(question.id))
                    if student_answer:
                        is_correct = attempt._is_correct_answer(question, student_answer)
                        if is_correct:
                            correct_count += 1
                        else:
                            print(f"            ❌ Wrong: Q{question.id} - '{student_answer}' vs '{question.correct_answer}'")
                    else:
                        print(f"            ⚠️  No answer: Q{question.id}")

                print(f"            ✅ Correct answers: {correct_count}/{questions.count()}")
    
    print(f"\n📊 OVERALL QUIZ ATTEMPT SUMMARY:")
    print(f"   • Total attempts: {total_attempts}")
    print(f"   • Passed attempts: {passed_attempts}")
    print(f"   • Failed attempts: {failed_attempts}")
    print(f"   • Success rate: {(passed_attempts/total_attempts*100) if total_attempts > 0 else 0:.1f}%")
    
    return {
        'user': user,
        'total_attempts': total_attempts,
        'passed_attempts': passed_attempts,
        'failed_attempts': failed_attempts
    }

def analyze_module2_quiz_integrity():
    """Analyze Module 2 quiz data integrity"""
    
    print(f"\n🔍 ANALYZING MODULE 2 QUIZ DATA INTEGRITY")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module2 = Module.objects.get(course=course, sort_order=2)
        print(f"✅ Analyzing Module: {module2.title}")
    except (Course.DoesNotExist, Module.DoesNotExist) as e:
        print(f"❌ Error finding Module 2: {e}")
        return None
    
    lessons = Lesson.objects.filter(module=module2).order_by('sort_order')
    
    total_quizzes = 0
    total_questions = 0
    issues_found = []
    
    for lesson in lessons:
        print(f"\n📄 Lesson {lesson.sort_order}: {lesson.title}")
        
        quizzes = Quiz.objects.filter(lesson=lesson)
        
        for quiz in quizzes:
            total_quizzes += 1
            print(f"   🧪 Quiz: {quiz.title}")
            print(f"      📊 Passing score: {quiz.passing_score}%")
            print(f"      🔄 Max attempts: {quiz.max_attempts}")
            
            questions = Question.objects.filter(quiz=quiz).order_by('id')
            quiz_questions = questions.count()
            total_questions += quiz_questions
            
            print(f"      ❓ Questions: {quiz_questions}")
            
            # Analyze each question
            for i, question in enumerate(questions, 1):
                print(f"         Q{i}: {question.question_type}")
                
                # Check for issues
                question_issues = []
                
                # Check if question has text
                if not question.question_text or question.question_text.strip() == "":
                    question_issues.append("Empty question text")
                
                # Check if question has correct answer
                if not question.correct_answer or question.correct_answer.strip() == "":
                    question_issues.append("Missing correct answer")
                
                # Check multiple choice questions
                if question.question_type == 'multiple_choice':
                    if not question.options:
                        question_issues.append("Missing options for multiple choice")
                    else:
                        try:
                            options = question.options if isinstance(question.options, list) else json.loads(question.options)
                            if len(options) < 2:
                                question_issues.append("Insufficient options for multiple choice")
                            
                            # Check if correct answer matches one of the options
                            if question.correct_answer not in options:
                                question_issues.append(f"Correct answer '{question.correct_answer}' not in options {options}")
                        except (json.JSONDecodeError, TypeError) as e:
                            question_issues.append(f"Invalid options format: {e}")
                
                # Check true/false questions
                elif question.question_type == 'true/false':
                    if question.correct_answer.lower() not in ['true', 'false']:
                        question_issues.append(f"Invalid true/false answer: '{question.correct_answer}'")
                
                # Check points
                if question.points <= 0:
                    question_issues.append("Invalid points value")
                
                if question_issues:
                    print(f"            ⚠️  Issues: {', '.join(question_issues)}")
                    issues_found.extend([f"Q{question.id}: {issue}" for issue in question_issues])
                else:
                    print(f"            ✅ Valid")
    
    print(f"\n📊 MODULE 2 QUIZ INTEGRITY SUMMARY:")
    print(f"   • Total lessons: {lessons.count()}")
    print(f"   • Total quizzes: {total_quizzes}")
    print(f"   • Total questions: {total_questions}")
    print(f"   • Issues found: {len(issues_found)}")
    
    if issues_found:
        print(f"\n⚠️  ISSUES DETECTED:")
        for issue in issues_found:
            print(f"   • {issue}")
    else:
        print(f"\n✅ No integrity issues found!")
    
    return {
        'total_quizzes': total_quizzes,
        'total_questions': total_questions,
        'issues_found': issues_found
    }

def compare_with_answer_key():
    """Compare Module 2 database data with answer key JSON"""
    
    print(f"\n🔍 COMPARING WITH ANSWER KEY DATA")
    print("=" * 60)
    
    # Load answer key data
    answer_key_file = 'yitp_quiz_answers_complete.json'
    
    if not os.path.exists(answer_key_file):
        print(f"❌ Answer key file not found: {answer_key_file}")
        return None
    
    try:
        with open(answer_key_file, 'r', encoding='utf-8') as f:
            answer_key_data = json.load(f)
        print(f"✅ Loaded answer key data")
    except Exception as e:
        print(f"❌ Error loading answer key: {e}")
        return None
    
    # Find Module 2 in answer key
    module2_answer_key = None
    for module in answer_key_data.get('modules', []):
        if module.get('module_sort_order') == 2:
            module2_answer_key = module
            break
    
    if not module2_answer_key:
        print(f"❌ Module 2 not found in answer key")
        return None
    
    print(f"✅ Found Module 2 in answer key: {module2_answer_key.get('module_title')}")
    print(f"   📚 Lessons: {module2_answer_key.get('lesson_count')}")
    print(f"   🧪 Quizzes: {module2_answer_key.get('quiz_count')}")
    print(f"   ❓ Questions: {module2_answer_key.get('question_count')}")
    
    # Compare with database
    try:
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module2_db = Module.objects.get(course=course, sort_order=2)
    except (Course.DoesNotExist, Module.DoesNotExist) as e:
        print(f"❌ Error finding Module 2 in database: {e}")
        return None
    
    lessons_db = Lesson.objects.filter(module=module2_db).order_by('sort_order')
    
    discrepancies = []
    
    # Compare lesson count
    answer_key_lessons = module2_answer_key.get('lessons', [])
    if len(answer_key_lessons) != lessons_db.count():
        discrepancies.append(f"Lesson count mismatch: DB={lessons_db.count()}, Answer Key={len(answer_key_lessons)}")
    
    # Compare each lesson's quiz data
    for i, lesson_db in enumerate(lessons_db):
        if i < len(answer_key_lessons):
            lesson_ak = answer_key_lessons[i]
            
            quizzes_db = Quiz.objects.filter(lesson=lesson_db)
            quizzes_ak = lesson_ak.get('quizzes', [])
            
            if quizzes_db.count() != len(quizzes_ak):
                discrepancies.append(f"Lesson {i+1} quiz count mismatch: DB={quizzes_db.count()}, Answer Key={len(quizzes_ak)}")
            
            # Compare quiz questions
            for j, quiz_db in enumerate(quizzes_db):
                if j < len(quizzes_ak):
                    quiz_ak = quizzes_ak[j]
                    
                    questions_db = Question.objects.filter(quiz=quiz_db).order_by('id')
                    questions_ak = quiz_ak.get('questions', [])
                    
                    if questions_db.count() != len(questions_ak):
                        discrepancies.append(f"Lesson {i+1} Quiz {j+1} question count mismatch: DB={questions_db.count()}, Answer Key={len(questions_ak)}")
                    
                    # Compare individual questions
                    for k, question_db in enumerate(questions_db):
                        if k < len(questions_ak):
                            question_ak = questions_ak[k]
                            
                            # Compare correct answers
                            if question_db.correct_answer != question_ak.get('correct_answer'):
                                discrepancies.append(f"Q{question_db.id} answer mismatch: DB='{question_db.correct_answer}', Answer Key='{question_ak.get('correct_answer')}'")
    
    print(f"\n📊 COMPARISON RESULTS:")
    print(f"   • Discrepancies found: {len(discrepancies)}")
    
    if discrepancies:
        print(f"\n⚠️  DISCREPANCIES DETECTED:")
        for discrepancy in discrepancies:
            print(f"   • {discrepancy}")
    else:
        print(f"\n✅ Database matches answer key!")
    
    return {
        'discrepancies': discrepancies,
        'answer_key_data': module2_answer_key
    }

def main():
    print("🔍 MODULE 2 QUIZ ISSUES INVESTIGATION")
    print("=" * 60)
    print(f"📅 Investigation started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Investigate specific user
    user_email = 'bomondi2727@gmail.com'
    user_analysis = investigate_user_quiz_attempts(user_email)
    
    # 2. Analyze quiz data integrity
    integrity_analysis = analyze_module2_quiz_integrity()
    
    # 3. Compare with answer key
    comparison_analysis = compare_with_answer_key()
    
    # Generate summary report
    print(f"\n📋 INVESTIGATION SUMMARY REPORT")
    print("=" * 60)
    
    if user_analysis:
        print(f"👤 USER ANALYSIS ({user_email}):")
        print(f"   • Total quiz attempts: {user_analysis['total_attempts']}")
        print(f"   • Passed attempts: {user_analysis['passed_attempts']}")
        print(f"   • Failed attempts: {user_analysis['failed_attempts']}")
        
        if user_analysis['failed_attempts'] > 0:
            print(f"   ⚠️  User is experiencing quiz failures")
        else:
            print(f"   ✅ User has no failed attempts")
    
    if integrity_analysis:
        print(f"\n🔍 QUIZ INTEGRITY ANALYSIS:")
        print(f"   • Total quizzes: {integrity_analysis['total_quizzes']}")
        print(f"   • Total questions: {integrity_analysis['total_questions']}")
        print(f"   • Issues found: {len(integrity_analysis['issues_found'])}")
        
        if integrity_analysis['issues_found']:
            print(f"   ⚠️  Quiz integrity issues detected")
        else:
            print(f"   ✅ No quiz integrity issues")
    
    if comparison_analysis:
        print(f"\n📊 ANSWER KEY COMPARISON:")
        print(f"   • Discrepancies found: {len(comparison_analysis['discrepancies'])}")
        
        if comparison_analysis['discrepancies']:
            print(f"   ⚠️  Database doesn't match answer key")
        else:
            print(f"   ✅ Database matches answer key")
    
    # Determine next steps
    print(f"\n🎯 RECOMMENDED NEXT STEPS:")
    
    issues_found = False
    
    if integrity_analysis and integrity_analysis['issues_found']:
        print(f"   1. Fix quiz integrity issues in database")
        issues_found = True
    
    if comparison_analysis and comparison_analysis['discrepancies']:
        print(f"   2. Sync database with answer key data")
        issues_found = True
    
    if user_analysis and user_analysis['failed_attempts'] > 0:
        print(f"   3. Test quiz validation logic")
        issues_found = True
    
    if not issues_found:
        print(f"   ✅ No major issues detected - investigate quiz validation logic")
    
    print(f"\n🔄 Next: Run fix_module2_quiz_issues.py to address identified problems")

if __name__ == "__main__":
    main()
