#!/usr/bin/env python3
"""
Convert all short-answer questions in Module 2 (Personal Initiative & Assessments)
to multiple-choice format to resolve user lockout issues
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

class Module2QuestionConverter:
    def __init__(self):
        self.backup_data = []
        self.converted_questions = []
        self.conversion_errors = []
        
    def identify_short_answer_questions(self):
        """Find all short-answer questions in Module 2"""
        
        print("🔍 IDENTIFYING SHORT-ANSWER QUESTIONS IN MODULE 2")
        print("=" * 60)
        
        try:
            course = Course.objects.get(slug='youth-impact-training-programme-yitp')
            module2 = Module.objects.get(course=course, sort_order=2)
            print(f"✅ Found Module 2: {module2.title}")
        except (Course.DoesNotExist, Module.DoesNotExist) as e:
            print(f"❌ Error finding Module 2: {e}")
            return []
        
        short_answer_questions = []
        lessons = Lesson.objects.filter(module=module2).order_by('sort_order')
        
        for lesson in lessons:
            print(f"\n📄 Lesson {lesson.sort_order}: {lesson.title}")
            
            quizzes = Quiz.objects.filter(lesson=lesson)
            for quiz in quizzes:
                print(f"   🧪 Quiz: {quiz.title}")
                
                questions = Question.objects.filter(
                    quiz=quiz, 
                    question_type='short_answer'
                ).order_by('sort_order')
                
                for question in questions:
                    question_info = {
                        'id': question.id,
                        'lesson_title': lesson.title,
                        'lesson_sort_order': lesson.sort_order,
                        'quiz_title': quiz.title,
                        'quiz_id': quiz.id,
                        'question_text': question.question_text,
                        'current_answer': question.correct_answer,
                        'points': question.points,
                        'sort_order': question.sort_order,
                        'explanation': question.explanation,
                        'options': question.options
                    }
                    
                    short_answer_questions.append(question_info)
                    print(f"      ❓ Q{question.id}: {question.question_text[:80]}...")
                    print(f"         💡 Current answer: {question.correct_answer[:60]}...")
        
        print(f"\n📊 SUMMARY:")
        print(f"   • Total short-answer questions found: {len(short_answer_questions)}")
        
        return short_answer_questions
    
    def backup_original_data(self, questions_data):
        """Create backup of original question data"""
        
        print(f"\n💾 CREATING BACKUP OF ORIGINAL DATA")
        print("=" * 60)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"module2_short_answer_backup_{timestamp}.json"
        
        backup_data = {
            'backup_timestamp': datetime.now().isoformat(),
            'module_title': 'Personal Initiative & Assessments (Phase 1)',
            'total_questions': len(questions_data),
            'questions': questions_data
        }
        
        try:
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Backup saved: {backup_filename}")
            print(f"   📊 Questions backed up: {len(questions_data)}")
            
            self.backup_data = backup_data
            return backup_filename
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return None
    
    def generate_multiple_choice_options(self, question_info):
        """Generate multiple choice options based on the current expected answer"""
        
        question_text = question_info['question_text'].lower()
        current_answer = question_info['current_answer']
        
        # Analyze question type and generate appropriate options
        if 'benefit' in question_text or 'advantage' in question_text:
            return self._generate_benefits_options(current_answer)
        elif 'example' in question_text or 'describe' in question_text or 'share' in question_text:
            return self._generate_example_options(current_answer)
        elif 'barrier' in question_text or 'challenge' in question_text:
            return self._generate_barriers_options(current_answer)
        elif 'goal' in question_text or 'smart' in question_text:
            return self._generate_goals_options(current_answer)
        else:
            return self._generate_generic_options(current_answer)
    
    def _generate_benefits_options(self, current_answer):
        """Generate options for benefits/advantages questions"""
        
        # Extract key benefits from current answer
        if 'sample answers:' in current_answer.lower():
            # Parse sample answers
            parts = current_answer.split(':', 1)
            if len(parts) > 1:
                benefits_text = parts[1].strip()
                correct_option = f"All of the above: {benefits_text}"
            else:
                correct_option = "Increased job satisfaction, career advancement, and improved problem-solving skills"
        else:
            correct_option = current_answer[:100] + "..." if len(current_answer) > 100 else current_answer
        
        options = [
            correct_option,
            "Only financial benefits and salary increases",
            "Reduced workload and fewer responsibilities", 
            "Guaranteed promotion within 6 months",
            "Elimination of all workplace challenges"
        ]
        
        return {
            'options': options,
            'correct_answer': options[0]
        }
    
    def _generate_example_options(self, current_answer):
        """Generate options for example/description questions"""
        
        if 'answers should include:' in current_answer.lower():
            # Parse criteria
            parts = current_answer.split(':', 1)
            if len(parts) > 1:
                criteria_text = parts[1].strip()
                correct_option = f"An example that includes: {criteria_text}"
            else:
                correct_option = "A comprehensive example with problem identification, action taken, and positive outcome"
        else:
            correct_option = "A detailed example showing initiative, action, and positive results"
        
        options = [
            correct_option,
            "Any workplace story regardless of initiative shown",
            "A description of assigned tasks completed on time",
            "An example of following instructions exactly as given",
            "A situation where someone else took the initiative"
        ]
        
        return {
            'options': options,
            'correct_answer': options[0]
        }
    
    def _generate_barriers_options(self, current_answer):
        """Generate options for barriers/challenges questions"""
        
        correct_option = "Internal barriers like fear of failure, external barriers like resource constraints, and systemic barriers"
        
        options = [
            correct_option,
            "Only financial barriers and budget limitations",
            "Barriers that cannot be overcome under any circumstances",
            "Only barriers created by other people",
            "Barriers that only affect certain types of people"
        ]
        
        return {
            'options': options,
            'correct_answer': options[0]
        }
    
    def _generate_goals_options(self, current_answer):
        """Generate options for goals/SMART goals questions"""
        
        correct_option = "Specific, Measurable, Achievable, Relevant, and Time-bound goals with personal initiative elements"
        
        options = [
            correct_option,
            "Any goal regardless of specificity or timeline",
            "Only long-term goals that take over 5 years",
            "Goals that depend entirely on other people's actions",
            "Vague aspirations without specific outcomes"
        ]
        
        return {
            'options': options,
            'correct_answer': options[0]
        }
    
    def _generate_generic_options(self, current_answer):
        """Generate generic options when question type is unclear"""
        
        # Use the current answer as the correct option (truncated if too long)
        if len(current_answer) > 150:
            correct_option = current_answer[:147] + "..."
        else:
            correct_option = current_answer
        
        options = [
            correct_option,
            "A partially correct but incomplete answer",
            "An answer that misses the key concepts",
            "An irrelevant or off-topic response",
            "No clear answer or understanding shown"
        ]
        
        return {
            'options': options,
            'correct_answer': options[0]
        }
    
    def convert_questions_to_multiple_choice(self, questions_data):
        """Convert all short-answer questions to multiple choice"""
        
        print(f"\n🔧 CONVERTING QUESTIONS TO MULTIPLE CHOICE")
        print("=" * 60)
        
        for i, question_info in enumerate(questions_data, 1):
            print(f"\n🔧 Converting Question {i}/{len(questions_data)}")
            print(f"   📝 Q{question_info['id']}: {question_info['question_text'][:60]}...")
            
            try:
                # Get the question object
                question = Question.objects.get(id=question_info['id'])
                
                # Generate multiple choice options
                mc_data = self.generate_multiple_choice_options(question_info)
                
                # Update the question
                question.question_type = 'multiple_choice'
                question.options = mc_data['options']
                question.correct_answer = mc_data['correct_answer']
                question.save()
                
                print(f"   ✅ Converted successfully")
                print(f"      🔹 Options: {len(mc_data['options'])}")
                print(f"      🔹 Correct: {mc_data['correct_answer'][:50]}...")
                
                self.converted_questions.append({
                    'question_id': question_info['id'],
                    'lesson_title': question_info['lesson_title'],
                    'quiz_title': question_info['quiz_title'],
                    'original_answer': question_info['current_answer'],
                    'new_options': mc_data['options'],
                    'new_correct_answer': mc_data['correct_answer']
                })
                
            except Exception as e:
                error_msg = f"Error converting Q{question_info['id']}: {e}"
                print(f"   ❌ {error_msg}")
                self.conversion_errors.append(error_msg)
        
        print(f"\n📊 CONVERSION SUMMARY:")
        print(f"   ✅ Successfully converted: {len(self.converted_questions)}")
        print(f"   ❌ Errors: {len(self.conversion_errors)}")
        
        return len(self.converted_questions) > 0
    
    def verify_conversions(self):
        """Verify all conversions were successful"""
        
        print(f"\n🔍 VERIFYING CONVERSIONS")
        print("=" * 60)
        
        verification_results = []
        
        for conversion in self.converted_questions:
            try:
                question = Question.objects.get(id=conversion['question_id'])
                
                verification = {
                    'question_id': conversion['question_id'],
                    'type_correct': question.question_type == 'multiple_choice',
                    'has_options': len(question.options) > 0,
                    'has_correct_answer': bool(question.correct_answer),
                    'correct_answer_in_options': question.correct_answer in question.options
                }
                
                all_checks_pass = all(verification.values())
                verification['all_checks_pass'] = all_checks_pass
                
                verification_results.append(verification)
                
                status = "✅" if all_checks_pass else "❌"
                print(f"   {status} Q{conversion['question_id']}: {all_checks_pass}")
                
            except Exception as e:
                print(f"   ❌ Q{conversion['question_id']}: Verification error - {e}")
                verification_results.append({
                    'question_id': conversion['question_id'],
                    'error': str(e),
                    'all_checks_pass': False
                })
        
        successful_verifications = sum(1 for v in verification_results if v.get('all_checks_pass', False))
        
        print(f"\n📊 VERIFICATION SUMMARY:")
        print(f"   ✅ Verified successful: {successful_verifications}")
        print(f"   ❌ Verification failed: {len(verification_results) - successful_verifications}")
        
        return verification_results
    
    def test_with_user_quiz(self):
        """Test that user can now potentially pass quizzes"""
        
        print(f"\n🧪 TESTING WITH USER QUIZ ACCESS")
        print("=" * 60)
        
        try:
            user = User.objects.get(email='bomondi2727@gmail.com')
            print(f"✅ Found user: {user.username}")
        except User.DoesNotExist:
            print(f"❌ User not found")
            return False
        
        try:
            course = Course.objects.get(slug='youth-impact-training-programme-yitp')
            module2 = Module.objects.get(course=course, sort_order=2)
            lesson1 = Lesson.objects.filter(module=module2).order_by('sort_order').first()
            quiz = Quiz.objects.filter(lesson=lesson1).first()
            
            print(f"✅ Found quiz: {quiz.title}")
        except Exception as e:
            print(f"❌ Error finding quiz: {e}")
            return False
        
        # Check quiz questions
        questions = Question.objects.filter(quiz=quiz)
        mc_questions = questions.filter(question_type='multiple_choice').count()
        total_questions = questions.count()
        
        print(f"📊 Quiz Analysis:")
        print(f"   • Total questions: {total_questions}")
        print(f"   • Multiple choice: {mc_questions}")
        print(f"   • Conversion rate: {(mc_questions/total_questions*100):.1f}%")
        
        if mc_questions == total_questions:
            print(f"   ✅ All questions are now multiple choice!")
            return True
        else:
            print(f"   ⚠️  Some questions may still need conversion")
            return False

    def generate_conversion_report(self):
        """Generate comprehensive conversion report"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"module2_conversion_report_{timestamp}.md"

        report_content = f"""# Module 2 Short-Answer to Multiple Choice Conversion Report

## Summary
- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Module:** Personal Initiative & Assessments (Phase 1)
- **Questions Converted:** {len(self.converted_questions)}
- **Conversion Errors:** {len(self.conversion_errors)}

## Conversion Details

"""

        for i, conversion in enumerate(self.converted_questions, 1):
            report_content += f"""### {i}. Question {conversion['question_id']} ({conversion['lesson_title']})

**Quiz:** {conversion['quiz_title']}

**Original Answer:**
```
{conversion['original_answer'][:200]}...
```

**New Multiple Choice Options:**
"""
            for j, option in enumerate(conversion['new_options'], 1):
                marker = "✅" if option == conversion['new_correct_answer'] else "  "
                report_content += f"{marker} {j}. {option}\n"

            report_content += "\n---\n\n"

        if self.conversion_errors:
            report_content += f"""## Conversion Errors

"""
            for error in self.conversion_errors:
                report_content += f"- {error}\n"

        report_content += f"""## Next Steps

1. ✅ All short-answer questions converted to multiple choice
2. 🧪 Test with user `bomondi2727@gmail.com`
3. 📊 Monitor quiz pass rates
4. 🔄 Apply to other modules if needed

## Files Generated

- Backup: `module2_short_answer_backup_*.json`
- Report: `{report_filename}`
"""

        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"📄 Report saved: {report_filename}")
            return report_filename

        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return None

def main():
    print("🚀 CONVERTING MODULE 2 SHORT-ANSWER TO MULTIPLE CHOICE")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    converter = Module2QuestionConverter()

    # Step 1: Identify all short-answer questions
    questions_data = converter.identify_short_answer_questions()

    if not questions_data:
        print("✅ No short-answer questions found to convert!")
        return

    # Step 2: Create backup
    backup_file = converter.backup_original_data(questions_data)
    if not backup_file:
        print("❌ Failed to create backup. Aborting conversion.")
        return

    # Step 3: Convert questions
    conversion_success = converter.convert_questions_to_multiple_choice(questions_data)

    if not conversion_success:
        print("❌ Conversion failed. Check errors above.")
        return

    # Step 4: Verify conversions
    verification_results = converter.verify_conversions()

    # Step 5: Test with user quiz
    test_success = converter.test_with_user_quiz()

    # Step 6: Generate report
    report_file = converter.generate_conversion_report()

    # Final summary
    print(f"\n🎉 CONVERSION COMPLETED!")
    print("=" * 60)
    print(f"✅ Questions converted: {len(converter.converted_questions)}")
    print(f"❌ Conversion errors: {len(converter.conversion_errors)}")

    if test_success:
        print(f"🎯 SUCCESS: User should now be able to pass quizzes!")
    else:
        print(f"⚠️  PARTIAL: Some questions may need manual review")

    print(f"\n📁 Files Generated:")
    print(f"   • Backup: {backup_file}")
    if report_file:
        print(f"   • Report: {report_file}")

    print(f"\n🔄 Next Steps:")
    print(f"1. Review conversion report")
    print(f"2. Test with user bomondi2727@gmail.com")
    print(f"3. Monitor quiz pass rates")
    print(f"4. Apply to other modules if needed")

if __name__ == "__main__":
    main()
