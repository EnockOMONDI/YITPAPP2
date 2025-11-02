#!/usr/bin/env python3
"""
Fix Module 2 (Personal Initiative & Assessments) quiz issues
by improving short answer validation logic and updating problematic questions
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
from progress.models import QuizAttempt

def analyze_short_answer_questions():
    """Analyze short answer questions in Module 2 that are causing issues"""
    
    print(f"🔍 ANALYZING SHORT ANSWER QUESTIONS IN MODULE 2")
    print("=" * 60)
    
    try:
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module2 = Module.objects.get(course=course, sort_order=2)
        print(f"✅ Analyzing Module: {module2.title}")
    except (Course.DoesNotExist, Module.DoesNotExist) as e:
        print(f"❌ Error finding Module 2: {e}")
        return None
    
    lessons = Lesson.objects.filter(module=module2).order_by('sort_order')
    
    problematic_questions = []
    
    for lesson in lessons:
        print(f"\n📄 Lesson {lesson.sort_order}: {lesson.title}")
        
        quizzes = Quiz.objects.filter(lesson=lesson)
        
        for quiz in quizzes:
            print(f"   🧪 Quiz: {quiz.title}")
            
            questions = Question.objects.filter(quiz=quiz, question_type='short_answer').order_by('id')
            
            for question in questions:
                print(f"      ❓ Q{question.id}: {question.question_type}")
                print(f"         📝 Question: {question.question_text[:100]}...")
                print(f"         ✅ Expected Answer: {question.correct_answer}")
                
                # Check if this is a problematic question (expecting exact match for open-ended questions)
                if _is_problematic_short_answer(question):
                    problematic_questions.append({
                        'question_id': question.id,
                        'lesson_title': lesson.title,
                        'quiz_title': quiz.title,
                        'question_text': question.question_text,
                        'current_answer': question.correct_answer,
                        'issue_type': _identify_issue_type(question)
                    })
                    print(f"         ⚠️  PROBLEMATIC: {_identify_issue_type(question)}")
                else:
                    print(f"         ✅ OK")
    
    print(f"\n📊 ANALYSIS SUMMARY:")
    print(f"   • Problematic short answer questions: {len(problematic_questions)}")
    
    if problematic_questions:
        print(f"\n⚠️  PROBLEMATIC QUESTIONS FOUND:")
        for i, q in enumerate(problematic_questions, 1):
            print(f"   {i}. Q{q['question_id']} ({q['lesson_title']}): {q['issue_type']}")
    
    return problematic_questions

def _is_problematic_short_answer(self, question):
    """Check if a short answer question is problematic (requires exact match for open-ended content)"""
    
    # Check for indicators that this should be flexible validation
    indicators = [
        'sample answers',
        'answers should include',
        'example',
        'describe',
        'explain',
        'list three',
        'provide an example',
        'share a time when'
    ]
    
    question_lower = question.question_text.lower()
    answer_lower = question.correct_answer.lower()
    
    # If question asks for examples/descriptions but answer expects exact match
    for indicator in indicators:
        if indicator in question_lower or indicator in answer_lower:
            return True
    
    # If the correct answer is very long (likely a sample/template answer)
    if len(question.correct_answer) > 100:
        return True
    
    return False

def _identify_issue_type(self, question):
    """Identify the type of issue with the question"""
    
    answer_lower = question.correct_answer.lower()
    
    if 'sample answers' in answer_lower:
        return "Sample answer format - needs flexible validation"
    elif 'answers should include' in answer_lower:
        return "Criteria-based answer - needs keyword validation"
    elif len(question.correct_answer) > 200:
        return "Very long answer - likely template/example"
    else:
        return "Requires exact match for open-ended question"

def fix_short_answer_validation():
    """Fix short answer questions by updating their validation approach"""
    
    print(f"\n🔧 FIXING SHORT ANSWER VALIDATION")
    print("=" * 60)
    
    # Get problematic questions
    problematic_questions = analyze_short_answer_questions()
    
    if not problematic_questions:
        print(f"✅ No problematic questions found to fix")
        return True
    
    fixes_applied = 0
    
    for q_info in problematic_questions:
        question = Question.objects.get(id=q_info['question_id'])
        
        print(f"\n🔧 Fixing Q{question.id}: {q_info['issue_type']}")
        print(f"   📝 Question: {question.question_text[:100]}...")
        print(f"   🔄 Current answer: {question.correct_answer[:100]}...")
        
        # Apply appropriate fix based on issue type
        new_answer = self._generate_flexible_answer(question, q_info['issue_type'])
        
        if new_answer != question.correct_answer:
            print(f"   ✅ New answer: {new_answer[:100]}...")
            
            # Update the question
            question.correct_answer = new_answer
            question.save()
            
            fixes_applied += 1
            print(f"   ✅ Fixed and saved")
        else:
            print(f"   ⚠️  No change needed")
    
    print(f"\n📊 FIXES APPLIED: {fixes_applied}/{len(problematic_questions)}")
    
    return fixes_applied > 0

def _generate_flexible_answer(self, question, issue_type):
    """Generate a more flexible answer format for validation"""
    
    current_answer = question.correct_answer
    
    # For questions with "sample answers" format
    if "sample answers" in current_answer.lower():
        # Extract key concepts from the sample answers
        if ":" in current_answer:
            parts = current_answer.split(":", 1)
            if len(parts) > 1:
                concepts = parts[1].strip()
                # Convert to keyword-based validation
                return f"KEYWORDS: {concepts}"
    
    # For questions with "answers should include" format
    elif "answers should include" in current_answer.lower():
        # Already in a good format, just standardize
        if ":" in current_answer:
            parts = current_answer.split(":", 1)
            if len(parts) > 1:
                criteria = parts[1].strip()
                return f"CRITERIA: {criteria}"
    
    # For very long answers, create keyword version
    elif len(current_answer) > 200:
        # Extract key concepts (this is a simplified approach)
        key_phrases = self._extract_key_phrases(current_answer)
        return f"KEYWORDS: {', '.join(key_phrases)}"
    
    # Default: return original answer
    return current_answer

def _extract_key_phrases(self, text):
    """Extract key phrases from long text for keyword validation"""
    
    # Simple keyword extraction (can be enhanced)
    important_words = [
        'initiative', 'proactive', 'leadership', 'problem-solving', 
        'career advancement', 'job satisfaction', 'autonomy', 'growth',
        'opportunity', 'action', 'outcome', 'learning', 'reflection'
    ]
    
    text_lower = text.lower()
    found_keywords = []
    
    for word in important_words:
        if word in text_lower:
            found_keywords.append(word)
    
    # If no keywords found, extract first few meaningful words
    if not found_keywords:
        words = text.split()[:10]  # First 10 words
        found_keywords = [w.strip('.,!?') for w in words if len(w) > 3]
    
    return found_keywords[:5]  # Return top 5 keywords

def update_quiz_validation_logic():
    """Update the quiz validation logic to handle flexible short answers"""
    
    print(f"\n🔧 UPDATING QUIZ VALIDATION LOGIC")
    print("=" * 60)
    
    # Note: The actual validation logic is in progress/models.py QuizAttempt._is_correct_answer()
    # We need to enhance that method to handle flexible validation
    
    print(f"📝 Current validation logic location: progress/models.py QuizAttempt._is_correct_answer()")
    print(f"🔄 Recommended enhancement: Add flexible validation for short answers")
    print(f"   • KEYWORDS: format - check if answer contains key terms")
    print(f"   • CRITERIA: format - check if answer meets criteria")
    print(f"   • Partial matching for comprehensive answers")
    
    # For now, we'll create a patch that can be applied
    validation_patch = '''
def _is_correct_answer_enhanced(self, question, student_answer):
    """Enhanced answer validation with flexible short answer support"""
    
    # Handle None/empty answers
    if not student_answer:
        return False

    if question.question_type == 'multiple_choice':
        return student_answer.strip() == question.correct_answer.strip()
    elif question.question_type == 'true_false':
        return student_answer.lower().strip() == question.correct_answer.lower().strip()
    elif question.question_type == 'short_answer':
        return self._validate_short_answer(question, student_answer)
    # ... other question types
    
    return False

def _validate_short_answer(self, question, student_answer):
    """Flexible validation for short answer questions"""
    
    correct_answer = question.correct_answer.strip()
    student_clean = student_answer.lower().strip()
    
    # Check for flexible validation formats
    if correct_answer.startswith('KEYWORDS:'):
        keywords = correct_answer[9:].strip().split(',')
        keywords = [k.strip().lower() for k in keywords]
        
        # Check if student answer contains most keywords
        matches = sum(1 for keyword in keywords if keyword in student_clean)
        return matches >= len(keywords) * 0.6  # 60% keyword match
        
    elif correct_answer.startswith('CRITERIA:'):
        criteria = correct_answer[9:].strip().split(',')
        criteria = [c.strip().lower() for c in criteria]
        
        # Check if student answer meets most criteria
        matches = sum(1 for criterion in criteria if criterion in student_clean)
        return matches >= len(criteria) * 0.7  # 70% criteria match
        
    else:
        # Default exact match for simple answers
        return student_clean == correct_answer.lower().strip()
'''
    
    print(f"📄 Validation patch created (needs manual application to progress/models.py)")
    
    return validation_patch

def test_fixes_with_user_attempts():
    """Test the fixes by re-evaluating user attempts"""
    
    print(f"\n🧪 TESTING FIXES WITH USER ATTEMPTS")
    print("=" * 60)
    
    try:
        user = User.objects.get(email='bomondi2727@gmail.com')
        print(f"✅ Testing with user: {user.username}")
    except User.DoesNotExist:
        print(f"❌ User not found")
        return False
    
    # Get Module 2 Lesson 1 quiz attempts
    try:
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module2 = Module.objects.get(course=course, sort_order=2)
        lesson1 = Lesson.objects.filter(module=module2).order_by('sort_order').first()
        quiz = Quiz.objects.filter(lesson=lesson1).first()
        
        print(f"✅ Testing quiz: {quiz.title}")
    except Exception as e:
        print(f"❌ Error finding quiz: {e}")
        return False
    
    # Get user's latest attempt
    latest_attempt = QuizAttempt.objects.filter(
        student=user,
        quiz=quiz
    ).order_by('-attempt_number').first()
    
    if not latest_attempt:
        print(f"❌ No attempts found")
        return False
    
    print(f"📝 Testing latest attempt (#{latest_attempt.attempt_number})")
    print(f"   🎯 Original score: {latest_attempt.score}%")
    
    # Re-calculate score with current logic
    original_score = latest_attempt.score
    latest_attempt.calculate_score()
    new_score = latest_attempt.score
    
    print(f"   🔄 Recalculated score: {new_score}%")
    print(f"   📊 Score change: {new_score - original_score:+.2f}%")
    
    if new_score >= quiz.passing_score:
        print(f"   ✅ WOULD NOW PASS! (≥{quiz.passing_score}%)")
        return True
    else:
        print(f"   ❌ Still failing (need ≥{quiz.passing_score}%)")
        return False

def main():
    print("🔧 MODULE 2 QUIZ ISSUES FIX")
    print("=" * 60)
    print(f"📅 Fix started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Analyze problematic questions
    problematic_questions = analyze_short_answer_questions()
    
    # 2. Fix short answer validation
    fixes_applied = fix_short_answer_validation()
    
    # 3. Update validation logic (create patch)
    validation_patch = update_quiz_validation_logic()
    
    # 4. Test fixes
    test_result = test_fixes_with_user_attempts()
    
    # Generate summary
    print(f"\n📋 FIX SUMMARY REPORT")
    print("=" * 60)
    
    if problematic_questions:
        print(f"🔍 ISSUES IDENTIFIED:")
        print(f"   • Problematic short answer questions: {len(problematic_questions)}")
        print(f"   • Main issue: Exact string matching for open-ended questions")
        print(f"   • User providing correct content but failing due to format mismatch")
    
    if fixes_applied:
        print(f"\n🔧 FIXES APPLIED:")
        print(f"   • Updated question answer formats for flexible validation")
        print(f"   • Converted sample answers to keyword-based validation")
        print(f"   • Enhanced criteria-based answer checking")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Apply validation logic patch to progress/models.py")
    print(f"   2. Test with user attempts")
    print(f"   3. Verify users can now pass quizzes")
    
    if test_result:
        print(f"   ✅ User would now pass with current fixes!")
    else:
        print(f"   ⚠️  Additional validation logic updates needed")
    
    print(f"\n🔄 Next: Run verify_module2_quiz_fixes.py to test all scenarios")

if __name__ == "__main__":
    main()
