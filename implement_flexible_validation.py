#!/usr/bin/env python3
"""
Implement flexible validation for Module 2 short-answer questions
to resolve user lockout issues while maintaining educational quality
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

class FlexibleValidationImplementer:
    def __init__(self):
        self.changes_made = []
        self.test_results = []
        
    def analyze_problematic_questions(self):
        """Identify short answer questions that need flexible validation"""
        
        print("🔍 ANALYZING PROBLEMATIC SHORT ANSWER QUESTIONS")
        print("=" * 60)
        
        try:
            course = Course.objects.get(slug='youth-impact-training-programme-yitp')
            module2 = Module.objects.get(course=course, sort_order=2)
        except (Course.DoesNotExist, Module.DoesNotExist) as e:
            print(f"❌ Error finding Module 2: {e}")
            return []
        
        problematic_questions = []
        lessons = Lesson.objects.filter(module=module2).order_by('sort_order')
        
        for lesson in lessons:
            quizzes = Quiz.objects.filter(lesson=lesson)
            for quiz in quizzes:
                questions = Question.objects.filter(quiz=quiz, question_type='short_answer')
                
                for question in questions:
                    if self._is_problematic_question(question):
                        problematic_questions.append({
                            'id': question.id,
                            'lesson_title': lesson.title,
                            'quiz_title': quiz.title,
                            'question_text': question.question_text[:100] + "...",
                            'current_answer': question.correct_answer,
                            'issue_type': self._identify_issue_type(question)
                        })
        
        print(f"📊 Found {len(problematic_questions)} problematic questions")
        for q in problematic_questions:
            print(f"   • Q{q['id']}: {q['issue_type']}")
        
        return problematic_questions
    
    def _is_problematic_question(self, question):
        """Check if question needs flexible validation"""
        answer = question.correct_answer.lower()
        
        # Check for template/guidance answers
        problematic_indicators = [
            'sample answers:',
            'answers should include:',
            'example answers:',
            'possible answers:',
            'criteria:'
        ]
        
        for indicator in problematic_indicators:
            if indicator in answer:
                return True
        
        # Check for very long answers (likely templates)
        if len(question.correct_answer) > 150:
            return True
            
        return False
    
    def _identify_issue_type(self, question):
        """Identify the type of validation issue"""
        answer = question.correct_answer.lower()
        
        if 'sample answers:' in answer:
            return "Sample answer template"
        elif 'answers should include:' in answer:
            return "Criteria-based template"
        elif len(question.correct_answer) > 200:
            return "Very long template answer"
        else:
            return "Requires exact match for open-ended question"
    
    def convert_questions_to_flexible_format(self, problematic_questions):
        """Convert problematic questions to flexible validation format"""
        
        print("\n🔧 CONVERTING QUESTIONS TO FLEXIBLE FORMAT")
        print("=" * 60)
        
        for q_info in problematic_questions:
            question = Question.objects.get(id=q_info['id'])
            
            print(f"\n🔧 Converting Q{question.id}")
            print(f"   📝 Current: {question.correct_answer[:100]}...")
            
            new_answer = self._generate_flexible_answer(question)
            
            if new_answer != question.correct_answer:
                print(f"   ✅ New: {new_answer}")
                
                # Update the question
                old_answer = question.correct_answer
                question.correct_answer = new_answer
                question.save()
                
                self.changes_made.append({
                    'question_id': question.id,
                    'old_answer': old_answer,
                    'new_answer': new_answer,
                    'lesson': q_info['lesson_title']
                })
                
                print(f"   ✅ Updated and saved")
            else:
                print(f"   ⚠️  No conversion needed")
    
    def _generate_flexible_answer(self, question):
        """Generate flexible answer format based on question content"""
        
        current_answer = question.correct_answer
        
        # Handle "sample answers" format
        if "sample answers:" in current_answer.lower():
            # Extract the sample answers part
            parts = current_answer.split(":", 1)
            if len(parts) > 1:
                sample_content = parts[1].strip()
                keywords = self._extract_keywords_from_samples(sample_content)
                return f"KEYWORDS: {', '.join(keywords)}"
        
        # Handle "answers should include" format
        elif "answers should include:" in current_answer.lower():
            parts = current_answer.split(":", 1)
            if len(parts) > 1:
                criteria_content = parts[1].strip()
                criteria = self._extract_criteria(criteria_content)
                return f"CRITERIA: {', '.join(criteria)}"
        
        # Handle very long answers - extract key concepts
        elif len(current_answer) > 150:
            keywords = self._extract_key_concepts(current_answer)
            return f"KEYWORDS: {', '.join(keywords)}"
        
        # Return original if no conversion needed
        return current_answer
    
    def _extract_keywords_from_samples(self, sample_text):
        """Extract keywords from sample answers"""
        
        # Common benefit keywords for personal initiative
        keywords = []
        sample_lower = sample_text.lower()
        
        keyword_mapping = {
            'job satisfaction': ['job satisfaction', 'satisfaction', 'fulfillment'],
            'career advancement': ['career advancement', 'promotion', 'career growth'],
            'problem-solving': ['problem-solving', 'problem solving', 'solving problems'],
            'autonomy': ['autonomy', 'independence', 'self-direction'],
            'leadership': ['leadership', 'leading', 'leader'],
            'confidence': ['confidence', 'self-confidence'],
            'skills': ['skills', 'abilities', 'competencies'],
            'opportunities': ['opportunities', 'chances']
        }
        
        for key_concept, variations in keyword_mapping.items():
            for variation in variations:
                if variation in sample_lower:
                    keywords.append(key_concept)
                    break
        
        # If no specific keywords found, extract from text
        if not keywords:
            words = sample_text.replace(',', ' ').split()
            keywords = [w.strip('.,!?').lower() for w in words if len(w) > 4][:5]
        
        return keywords[:6]  # Limit to 6 keywords
    
    def _extract_criteria(self, criteria_text):
        """Extract criteria from criteria-based answers"""
        
        criteria = []
        criteria_lower = criteria_text.lower()
        
        # Common criteria for personal initiative examples
        criteria_mapping = {
            'opportunity identification': ['opportunity', 'problem', 'challenge', 'issue'],
            'self-directed action': ['action', 'initiative', 'took action', 'decided'],
            'positive outcome': ['outcome', 'result', 'success', 'achievement'],
            'reflection': ['learning', 'reflection', 'learned', 'insight']
        }
        
        for criterion, indicators in criteria_mapping.items():
            for indicator in indicators:
                if indicator in criteria_lower:
                    criteria.append(criterion)
                    break
        
        # If no specific criteria found, split by common separators
        if not criteria:
            parts = criteria_text.replace(',', ';').split(';')
            criteria = [part.strip() for part in parts if len(part.strip()) > 5][:4]
        
        return criteria[:4]  # Limit to 4 criteria
    
    def _extract_key_concepts(self, long_text):
        """Extract key concepts from long text"""
        
        # Simple keyword extraction for long answers
        important_terms = [
            'initiative', 'proactive', 'leadership', 'problem-solving',
            'career', 'growth', 'development', 'opportunity', 'action',
            'outcome', 'success', 'learning', 'improvement'
        ]
        
        text_lower = long_text.lower()
        found_keywords = []
        
        for term in important_terms:
            if term in text_lower:
                found_keywords.append(term)
        
        # If no keywords found, extract meaningful words
        if not found_keywords:
            words = long_text.split()
            found_keywords = [w.strip('.,!?').lower() for w in words 
                            if len(w) > 4 and w.isalpha()][:5]
        
        return found_keywords[:5]
    
    def test_with_user_attempts(self):
        """Test the new validation with existing user attempts"""
        
        print("\n🧪 TESTING WITH USER ATTEMPTS")
        print("=" * 60)
        
        try:
            user = User.objects.get(email='bomondi2727@gmail.com')
            print(f"✅ Testing with user: {user.username}")
        except User.DoesNotExist:
            print(f"❌ User not found")
            return False
        
        # Get Module 2 quiz attempts
        try:
            course = Course.objects.get(slug='youth-impact-training-programme-yitp')
            module2 = Module.objects.get(course=course, sort_order=2)
            lesson1 = Lesson.objects.filter(module=module2).order_by('sort_order').first()
            quiz = Quiz.objects.filter(lesson=lesson1).first()
        except Exception as e:
            print(f"❌ Error finding quiz: {e}")
            return False
        
        # Test all user attempts
        attempts = QuizAttempt.objects.filter(
            student=user,
            quiz=quiz
        ).order_by('attempt_number')
        
        print(f"📝 Found {attempts.count()} attempts to test")
        
        passing_attempts = 0
        for attempt in attempts:
            original_score = attempt.score
            
            # Recalculate with new validation
            attempt.calculate_score()
            new_score = attempt.score
            
            print(f"   🎯 Attempt {attempt.attempt_number}: {original_score}% → {new_score}%")
            
            if new_score >= quiz.passing_score:
                passing_attempts += 1
                print(f"      ✅ NOW PASSES!")
            else:
                print(f"      ❌ Still failing")
            
            self.test_results.append({
                'attempt_number': attempt.attempt_number,
                'original_score': original_score,
                'new_score': new_score,
                'now_passes': new_score >= quiz.passing_score
            })
        
        print(f"\n📊 TEST RESULTS:")
        print(f"   • Total attempts tested: {attempts.count()}")
        print(f"   • Now passing: {passing_attempts}")
        print(f"   • Success rate: {(passing_attempts/attempts.count()*100):.1f}%")
        
        return passing_attempts > 0
    
    def generate_implementation_report(self):
        """Generate comprehensive implementation report"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"flexible_validation_implementation_report_{timestamp}.md"
        
        report_content = f"""# Flexible Validation Implementation Report

## Summary
- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Changes Made:** {len(self.changes_made)}
- **Test Results:** {len(self.test_results)}

## Changes Applied

"""
        
        for i, change in enumerate(self.changes_made, 1):
            report_content += f"""### {i}. Question {change['question_id']} ({change['lesson']})
- **Old Answer:** {change['old_answer'][:100]}...
- **New Answer:** {change['new_answer']}

"""
        
        report_content += f"""## Test Results

"""
        
        for result in self.test_results:
            status = "✅ PASS" if result['now_passes'] else "❌ FAIL"
            report_content += f"""- **Attempt {result['attempt_number']}:** {result['original_score']}% → {result['new_score']}% {status}
"""
        
        with open(report_filename, 'w') as f:
            f.write(report_content)
        
        print(f"\n📄 Report saved: {report_filename}")
        return report_filename

    def create_validation_patch(self):
        """Create the enhanced validation logic patch for progress/models.py"""

        print("\n📝 CREATING VALIDATION LOGIC PATCH")
        print("=" * 60)

        patch_content = '''
    def _is_correct_answer(self, question, student_answer):
        """Enhanced answer validation with flexible short answer support"""
        # Handle None/empty answers
        if not student_answer:
            return False

        if question.question_type == 'multiple_choice':
            return student_answer.strip() == question.correct_answer.strip()
        elif question.question_type == 'true_false':
            return student_answer.lower().strip() == question.correct_answer.lower().strip()
        elif question.question_type == 'short_answer':
            return self._validate_short_answer_flexible(question, student_answer)
        elif question.question_type == 'essay':
            # Essays require manual grading
            return False
        elif question.question_type == 'matching':
            # Parse matching format: "A-3,B-2,C-1"
            try:
                student_pairs = {}
                for pair in student_answer.split(','):
                    if '-' in pair:
                        key, value = pair.strip().split('-', 1)
                        student_pairs[key.strip()] = value.strip()

                correct_pairs = {}
                for pair in question.correct_answer.split(','):
                    if '-' in pair:
                        key, value = pair.strip().split('-', 1)
                        correct_pairs[key.strip()] = value.strip()

                return student_pairs == correct_pairs
            except:
                return False
        elif question.question_type == 'fill_blank':
            # Case-insensitive comparison for fill-in-the-blank
            return student_answer.lower().strip() == question.correct_answer.lower().strip()

        return False

    def _validate_short_answer_flexible(self, question, student_answer):
        """Flexible validation for short answer questions"""
        correct_answer = question.correct_answer.strip()
        student_clean = student_answer.lower().strip()

        # Handle flexible validation formats
        if correct_answer.startswith('KEYWORDS:'):
            return self._validate_keywords(correct_answer, student_clean)
        elif correct_answer.startswith('CRITERIA:'):
            return self._validate_criteria(correct_answer, student_clean)
        else:
            # Default exact match for simple answers
            return student_clean == correct_answer.lower().strip()

    def _validate_keywords(self, correct_answer, student_answer):
        """Validate answer based on keyword matching"""
        keywords_text = correct_answer[9:].strip()  # Remove "KEYWORDS: "
        keywords = [k.strip().lower() for k in keywords_text.split(',')]

        # Count how many keywords are found in student answer
        matches = 0
        for keyword in keywords:
            if keyword in student_answer:
                matches += 1

        # Require 60% of keywords to be present
        required_matches = max(1, len(keywords) * 0.6)
        return matches >= required_matches

    def _validate_criteria(self, correct_answer, student_answer):
        """Validate answer based on criteria matching"""
        criteria_text = correct_answer[9:].strip()  # Remove "CRITERIA: "
        criteria = [c.strip().lower() for c in criteria_text.split(',')]

        # Count how many criteria are met in student answer
        matches = 0
        for criterion in criteria:
            # Check if criterion or related terms are in answer
            if self._check_criterion_match(criterion, student_answer):
                matches += 1

        # Require 70% of criteria to be met
        required_matches = max(1, len(criteria) * 0.7)
        return matches >= required_matches

    def _check_criterion_match(self, criterion, student_answer):
        """Check if a specific criterion is met in the student answer"""
        criterion = criterion.strip().lower()

        # Direct match
        if criterion in student_answer:
            return True

        # Check for related terms based on common criteria
        criterion_synonyms = {
            'opportunity identification': ['opportunity', 'problem', 'challenge', 'issue', 'gap', 'need'],
            'self-directed action': ['action', 'initiative', 'took', 'decided', 'started', 'began', 'implemented'],
            'positive outcome': ['outcome', 'result', 'success', 'achievement', 'improvement', 'benefit'],
            'reflection': ['learning', 'learned', 'reflection', 'insight', 'realized', 'understood']
        }

        # Check if any synonyms match
        for key_criterion, synonyms in criterion_synonyms.items():
            if key_criterion in criterion:
                for synonym in synonyms:
                    if synonym in student_answer:
                        return True

        return False
'''

        # Save patch to file
        patch_filename = f"validation_logic_patch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        with open(patch_filename, 'w') as f:
            f.write(patch_content)

        print(f"📄 Validation patch saved: {patch_filename}")
        print(f"🔧 Apply this patch to progress/models.py QuizAttempt class")

        return patch_filename

def main():
    print("🚀 IMPLEMENTING FLEXIBLE VALIDATION FOR MODULE 2")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    implementer = FlexibleValidationImplementer()

    # Step 1: Analyze problematic questions
    problematic_questions = implementer.analyze_problematic_questions()

    if not problematic_questions:
        print("✅ No problematic questions found!")
        return

    # Step 2: Convert questions to flexible format
    implementer.convert_questions_to_flexible_format(problematic_questions)

    # Step 3: Create validation patch
    patch_file = implementer.create_validation_patch()

    # Step 4: Test with user attempts (will need validation patch applied first)
    print(f"\n⚠️  NOTE: Apply validation patch before testing")

    # Step 5: Generate report
    report_file = implementer.generate_implementation_report()

    # Summary
    print(f"\n📋 IMPLEMENTATION SUMMARY")
    print("=" * 60)
    print(f"✅ Questions converted: {len(implementer.changes_made)}")
    print(f"📄 Validation patch created: {patch_file}")
    print(f"📊 Implementation report: {report_file}")

    print(f"\n🔄 Next Steps:")
    print(f"1. Apply validation patch to progress/models.py")
    print(f"2. Run test_with_user_attempts() to verify")
    print(f"3. Test with live user attempts")
    print(f"4. Monitor quiz pass rates")
    print(f"\n💡 To apply patch: Replace _is_correct_answer method in progress/models.py")

if __name__ == "__main__":
    main()
