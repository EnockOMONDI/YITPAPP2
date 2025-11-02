#!/usr/bin/env python3
"""
Convert all remaining short-answer questions across ALL modules (3, 4, 5) 
to multiple-choice format to prevent user lockout issues
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

class AllModulesQuestionConverter:
    def __init__(self):
        self.modules_to_convert = [3, 4, 5]  # Skip Module 1 (works fine) and Module 2 (already done)
        self.backup_files = {}
        self.conversion_results = {}
        self.total_converted = 0
        self.total_errors = 0
        
    def scan_all_modules_for_short_answers(self):
        """Scan all modules to identify short-answer questions"""
        
        print("🔍 SCANNING ALL MODULES FOR SHORT-ANSWER QUESTIONS")
        print("=" * 60)
        
        try:
            course = Course.objects.get(slug='youth-impact-training-programme-yitp')
            print(f"✅ Found course: {course.title}")
        except Course.DoesNotExist:
            print(f"❌ Course not found")
            return {}
        
        scan_results = {}
        
        for module_num in range(1, 6):  # Scan all 5 modules for reporting
            try:
                module = Module.objects.get(course=course, sort_order=module_num)
                print(f"\n📚 Module {module_num}: {module.title}")
                
                lessons = Lesson.objects.filter(module=module).order_by('sort_order')
                module_short_answers = []
                
                for lesson in lessons:
                    quizzes = Quiz.objects.filter(lesson=lesson)
                    
                    for quiz in quizzes:
                        short_answer_questions = Question.objects.filter(
                            quiz=quiz, 
                            question_type='short_answer'
                        ).order_by('sort_order')
                        
                        for question in short_answer_questions:
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
                            
                            module_short_answers.append(question_info)
                            print(f"   ❓ Q{question.id}: {question.question_text[:60]}...")
                
                scan_results[module_num] = {
                    'module_title': module.title,
                    'short_answer_count': len(module_short_answers),
                    'questions': module_short_answers,
                    'needs_conversion': module_num in self.modules_to_convert and len(module_short_answers) > 0
                }
                
                status = "🔄 NEEDS CONVERSION" if scan_results[module_num]['needs_conversion'] else "✅ SKIP"
                if module_num == 2:
                    status = "✅ ALREADY DONE"
                elif module_num == 1:
                    status = "✅ WORKS FINE"
                    
                print(f"   📊 Found {len(module_short_answers)} short-answer questions - {status}")
                
            except Module.DoesNotExist:
                print(f"   ❌ Module {module_num} not found")
                scan_results[module_num] = {
                    'module_title': f'Module {module_num}',
                    'short_answer_count': 0,
                    'questions': [],
                    'needs_conversion': False
                }
        
        # Summary
        total_questions = sum(result['short_answer_count'] for result in scan_results.values())
        conversion_needed = sum(result['short_answer_count'] for module_num, result in scan_results.items() 
                              if module_num in self.modules_to_convert)
        
        print(f"\n📊 SCAN SUMMARY:")
        print(f"   • Total short-answer questions found: {total_questions}")
        print(f"   • Questions needing conversion: {conversion_needed}")
        print(f"   • Modules to convert: {[f'Module {n}' for n in self.modules_to_convert]}")
        
        return scan_results
    
    def backup_module_data(self, module_num, questions_data):
        """Create backup for a specific module"""
        
        if not questions_data:
            print(f"   ⚠️  No questions to backup for Module {module_num}")
            return None
        
        print(f"\n💾 CREATING BACKUP FOR MODULE {module_num}")
        print("-" * 40)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"module{module_num}_short_answer_backup_{timestamp}.json"
        
        backup_data = {
            'backup_timestamp': datetime.now().isoformat(),
            'module_number': module_num,
            'module_title': questions_data[0]['lesson_title'].split(' – ')[0] if questions_data else f'Module {module_num}',
            'total_questions': len(questions_data),
            'questions': questions_data
        }
        
        try:
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ Backup saved: {backup_filename}")
            print(f"   📊 Questions backed up: {len(questions_data)}")
            
            self.backup_files[module_num] = backup_filename
            return backup_filename
            
        except Exception as e:
            print(f"   ❌ Error creating backup: {e}")
            return None
    
    def generate_multiple_choice_options(self, question_info, module_num):
        """Generate multiple choice options based on question content and module context"""
        
        question_text = question_info['question_text'].lower()
        current_answer = question_info['current_answer']
        
        # Module-specific option generation
        if module_num == 3:  # TPM 101 - The Power of Mindset
            return self._generate_mindset_options(question_text, current_answer)
        elif module_num == 4:  # Soft Skills for the Streets
            return self._generate_soft_skills_options(question_text, current_answer)
        elif module_num == 5:  # ESBA - Entrepreneurship & Small Business
            return self._generate_entrepreneurship_options(question_text, current_answer)
        else:
            return self._generate_generic_options(current_answer)
    
    def _generate_mindset_options(self, question_text, current_answer):
        """Generate options for mindset-related questions"""
        
        if 'growth mindset' in question_text or 'fixed mindset' in question_text:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "A mindset that believes abilities are completely unchangeable",
                "A mindset focused only on immediate results and outcomes",
                "A mindset that avoids all challenges and difficulties",
                "A mindset that depends entirely on external validation"
            ]
        elif 'belief' in question_text or 'limiting' in question_text:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "Beliefs that are always based on factual evidence",
                "Beliefs that only affect other people, not yourself",
                "Beliefs that cannot be changed under any circumstances",
                "Beliefs that are universally true for everyone"
            ]
        elif 'resilience' in question_text or 'overcome' in question_text:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "Avoiding all difficult situations and challenges",
                "Relying completely on others for emotional support",
                "Ignoring problems until they resolve themselves",
                "Maintaining the same approach regardless of outcomes"
            ]
        else:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "A superficial understanding without practical application",
                "An approach that works only in ideal circumstances",
                "A method that requires no effort or commitment",
                "A concept that applies only to certain types of people"
            ]
        
        return {
            'options': options,
            'correct_answer': options[0]
        }
    
    def _generate_soft_skills_options(self, question_text, current_answer):
        """Generate options for soft skills questions"""
        
        if 'communication' in question_text or 'listening' in question_text:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "Speaking loudly and clearly without considering the audience",
                "Using complex technical language in all situations",
                "Focusing only on getting your point across quickly",
                "Avoiding difficult conversations entirely"
            ]
        elif 'teamwork' in question_text or 'collaboration' in question_text:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "Working independently without consulting team members",
                "Always agreeing with others to avoid conflict",
                "Taking control of all decisions and tasks",
                "Competing with team members for recognition"
            ]
        elif 'leadership' in question_text or 'influence' in question_text:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "Using authority to force compliance from others",
                "Making all decisions without input from others",
                "Focusing only on short-term results and outcomes",
                "Avoiding responsibility when things go wrong"
            ]
        elif 'conflict' in question_text or 'problem' in question_text:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "Avoiding all conflicts and disagreements",
                "Always compromising regardless of the situation",
                "Using aggressive tactics to win arguments",
                "Ignoring problems until they escalate"
            ]
        else:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "A skill that only applies in formal work environments",
                "An ability that cannot be developed through practice",
                "A talent that some people are born with and others lack",
                "A concept that is only relevant for management positions"
            ]
        
        return {
            'options': options,
            'correct_answer': options[0]
        }
    
    def _generate_entrepreneurship_options(self, question_text, current_answer):
        """Generate options for entrepreneurship and business questions"""
        
        if 'business plan' in question_text or 'strategy' in question_text:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "A simple one-page document with basic business information",
                "A detailed plan that never needs to be updated or changed",
                "A document that focuses only on financial projections",
                "A plan that guarantees business success if followed exactly"
            ]
        elif 'market' in question_text or 'customer' in question_text:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "Selling to everyone without targeting specific groups",
                "Focusing only on the cheapest possible products",
                "Copying exactly what successful competitors are doing",
                "Assuming all customers have the same needs and preferences"
            ]
        elif 'funding' in question_text or 'finance' in question_text:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "Using only personal savings and avoiding all external funding",
                "Borrowing as much money as possible from any available source",
                "Focusing only on getting investment from venture capitalists",
                "Starting a business without any financial planning or budgeting"
            ]
        elif 'risk' in question_text or 'challenge' in question_text:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "Avoiding all risks and only pursuing guaranteed opportunities",
                "Taking maximum risks to achieve the highest possible returns",
                "Ignoring potential problems and focusing only on opportunities",
                "Letting fear of failure prevent any action or decision-making"
            ]
        else:
            correct_option = self._extract_correct_answer(current_answer)
            options = [
                correct_option,
                "A concept that only applies to large corporations",
                "An approach that works only in developed economies",
                "A strategy that requires significant initial capital",
                "A method that guarantees success if implemented correctly"
            ]
        
        return {
            'options': options,
            'correct_answer': options[0]
        }
    
    def _extract_correct_answer(self, current_answer):
        """Extract or format the correct answer from the current expected answer"""
        
        # Handle template answers
        if 'sample answers:' in current_answer.lower():
            parts = current_answer.split(':', 1)
            if len(parts) > 1:
                content = parts[1].strip()
                if len(content) > 150:
                    return content[:147] + "..."
                return content
        
        elif 'answers should include:' in current_answer.lower():
            parts = current_answer.split(':', 1)
            if len(parts) > 1:
                content = parts[1].strip()
                return f"A comprehensive answer that includes: {content[:100]}..."
        
        # Handle long answers
        elif len(current_answer) > 150:
            return current_answer[:147] + "..."
        
        # Return as-is for shorter answers
        return current_answer
    
    def _generate_generic_options(self, current_answer):
        """Generate generic options when question type is unclear"""
        
        correct_option = self._extract_correct_answer(current_answer)
        
        options = [
            correct_option,
            "A partially correct but incomplete understanding",
            "An approach that misses key concepts and principles",
            "A superficial response without depth or insight",
            "An irrelevant answer that doesn't address the question"
        ]
        
        return {
            'options': options,
            'correct_answer': options[0]
        }

    def convert_module_questions(self, module_num, questions_data):
        """Convert all short-answer questions in a specific module"""

        if not questions_data:
            print(f"   ⚠️  No questions to convert for Module {module_num}")
            return True

        print(f"\n🔧 CONVERTING MODULE {module_num} QUESTIONS")
        print("-" * 40)

        converted_questions = []
        conversion_errors = []

        for i, question_info in enumerate(questions_data, 1):
            print(f"\n   🔧 Converting Question {i}/{len(questions_data)}")
            print(f"      📝 Q{question_info['id']}: {question_info['question_text'][:50]}...")

            try:
                # Get the question object
                question = Question.objects.get(id=question_info['id'])

                # Generate multiple choice options
                mc_data = self.generate_multiple_choice_options(question_info, module_num)

                # Update the question
                question.question_type = 'multiple_choice'
                question.options = mc_data['options']
                question.correct_answer = mc_data['correct_answer']
                question.save()

                print(f"      ✅ Converted successfully")
                print(f"         🔹 Options: {len(mc_data['options'])}")
                print(f"         🔹 Correct: {mc_data['correct_answer'][:40]}...")

                converted_questions.append({
                    'question_id': question_info['id'],
                    'lesson_title': question_info['lesson_title'],
                    'quiz_title': question_info['quiz_title'],
                    'original_answer': question_info['current_answer'],
                    'new_options': mc_data['options'],
                    'new_correct_answer': mc_data['correct_answer']
                })

            except Exception as e:
                error_msg = f"Error converting Q{question_info['id']}: {e}"
                print(f"      ❌ {error_msg}")
                conversion_errors.append(error_msg)

        # Store results
        self.conversion_results[module_num] = {
            'converted_questions': converted_questions,
            'conversion_errors': conversion_errors,
            'success_count': len(converted_questions),
            'error_count': len(conversion_errors)
        }

        self.total_converted += len(converted_questions)
        self.total_errors += len(conversion_errors)

        print(f"\n   📊 Module {module_num} Conversion Summary:")
        print(f"      ✅ Successfully converted: {len(converted_questions)}")
        print(f"      ❌ Errors: {len(conversion_errors)}")

        return len(conversion_errors) == 0

    def verify_module_conversions(self, module_num):
        """Verify conversions for a specific module"""

        if module_num not in self.conversion_results:
            print(f"   ⚠️  No conversion results for Module {module_num}")
            return True

        print(f"\n🔍 VERIFYING MODULE {module_num} CONVERSIONS")
        print("-" * 40)

        converted_questions = self.conversion_results[module_num]['converted_questions']
        verification_results = []

        for conversion in converted_questions:
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
                print(f"      {status} Q{conversion['question_id']}: {all_checks_pass}")

            except Exception as e:
                print(f"      ❌ Q{conversion['question_id']}: Verification error - {e}")
                verification_results.append({
                    'question_id': conversion['question_id'],
                    'error': str(e),
                    'all_checks_pass': False
                })

        successful_verifications = sum(1 for v in verification_results if v.get('all_checks_pass', False))

        print(f"\n   📊 Module {module_num} Verification Summary:")
        print(f"      ✅ Verified successful: {successful_verifications}")
        print(f"      ❌ Verification failed: {len(verification_results) - successful_verifications}")

        return successful_verifications == len(verification_results)

    def convert_all_modules(self):
        """Convert all modules that need conversion"""

        print(f"\n🚀 STARTING CONVERSION OF ALL MODULES")
        print("=" * 60)

        # First, scan all modules
        scan_results = self.scan_all_modules_for_short_answers()

        # Convert each module that needs conversion
        for module_num in self.modules_to_convert:
            if module_num in scan_results and scan_results[module_num]['needs_conversion']:
                questions_data = scan_results[module_num]['questions']

                print(f"\n🔄 PROCESSING MODULE {module_num}")
                print("=" * 60)

                # Create backup
                backup_file = self.backup_module_data(module_num, questions_data)
                if not backup_file:
                    print(f"❌ Failed to create backup for Module {module_num}. Skipping.")
                    continue

                # Convert questions
                conversion_success = self.convert_module_questions(module_num, questions_data)

                # Verify conversions
                verification_success = self.verify_module_conversions(module_num)

                if conversion_success and verification_success:
                    print(f"✅ Module {module_num} conversion completed successfully!")
                else:
                    print(f"⚠️  Module {module_num} conversion had issues - check logs above")
            else:
                print(f"\n⚠️  Module {module_num}: No short-answer questions found or already converted")

        return scan_results

    def generate_comprehensive_report(self, scan_results):
        """Generate comprehensive conversion report for all modules"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"all_modules_conversion_report_{timestamp}.md"

        report_content = f"""# All Modules Short-Answer to Multiple Choice Conversion Report

## Summary
- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Course:** Youth Impact Training Programme (YITP)
- **Total Questions Converted:** {self.total_converted}
- **Total Conversion Errors:** {self.total_errors}

## Module Overview

"""

        for module_num in range(1, 6):
            if module_num in scan_results:
                result = scan_results[module_num]
                status = "✅ ALREADY DONE" if module_num == 2 else "✅ WORKS FINE" if module_num == 1 else "🔄 CONVERTED" if result['needs_conversion'] else "✅ NO CONVERSION NEEDED"

                report_content += f"""### Module {module_num}: {result['module_title']} {status}
- **Short-Answer Questions Found:** {result['short_answer_count']}
- **Conversion Needed:** {'Yes' if result['needs_conversion'] else 'No'}
"""

                if module_num in self.conversion_results:
                    conv_result = self.conversion_results[module_num]
                    report_content += f"""- **Questions Converted:** {conv_result['success_count']}
- **Conversion Errors:** {conv_result['error_count']}
"""

                report_content += "\n"

        # Detailed conversion results
        report_content += f"""## Detailed Conversion Results

"""

        for module_num, result in self.conversion_results.items():
            report_content += f"""### Module {module_num} Conversions

"""
            for i, conversion in enumerate(result['converted_questions'], 1):
                report_content += f"""#### {i}. Question {conversion['question_id']} ({conversion['lesson_title']})

**Quiz:** {conversion['quiz_title']}

**Original Answer:**
```
{conversion['original_answer'][:150]}...
```

**New Multiple Choice Options:**
"""
                for j, option in enumerate(conversion['new_options'], 1):
                    marker = "✅" if option == conversion['new_correct_answer'] else "  "
                    report_content += f"{marker} {j}. {option[:80]}...\n"

                report_content += "\n---\n\n"

        # Backup files
        report_content += f"""## Backup Files Created

"""
        for module_num, backup_file in self.backup_files.items():
            report_content += f"- **Module {module_num}:** `{backup_file}`\n"

        report_content += f"""

## Next Steps

1. ✅ All short-answer questions converted to multiple choice
2. 🧪 Test with users across all modules
3. 📊 Monitor quiz pass rates
4. 📝 Update instructor documentation

## Files Generated

- **Conversion Report:** `{report_filename}`
- **Verification Script:** `verify_all_modules_conversion.py`
"""

        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"📄 Comprehensive report saved: {report_filename}")
            return report_filename

        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return None

def main():
    print("🚀 CONVERTING ALL MODULES SHORT-ANSWER TO MULTIPLE CHOICE")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target Modules: 3 (TPM 101), 4 (Soft Skills), 5 (ESBA)")
    print(f"⚠️  Skipping: Module 1 (works fine), Module 2 (already done)")

    converter = AllModulesQuestionConverter()

    # Convert all modules
    scan_results = converter.convert_all_modules()

    # Generate comprehensive report
    report_file = converter.generate_comprehensive_report(scan_results)

    # Final summary
    print(f"\n🎉 ALL MODULES CONVERSION COMPLETED!")
    print("=" * 60)
    print(f"✅ Total questions converted: {converter.total_converted}")
    print(f"❌ Total conversion errors: {converter.total_errors}")
    print(f"📁 Backup files created: {len(converter.backup_files)}")

    if converter.total_errors == 0:
        print(f"\n🎯 COMPLETE SUCCESS!")
        print(f"   • All short-answer questions converted successfully")
        print(f"   • No user data was modified")
        print(f"   • Users should now be able to pass all quizzes")
    else:
        print(f"\n⚠️  PARTIAL SUCCESS")
        print(f"   • {converter.total_errors} conversion errors occurred")
        print(f"   • Review error details above")

    if report_file:
        print(f"\n📄 Detailed report: {report_file}")

    print(f"\n🔄 Next Steps:")
    print(f"1. 📊 Run verification script: verify_all_modules_conversion.py")
    print(f"2. 🧪 Test with users across all modules")
    print(f"3. 📈 Monitor quiz pass rates")
    print(f"4. 📝 Update documentation")

if __name__ == "__main__":
    main()
