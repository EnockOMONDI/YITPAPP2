#!/usr/bin/env python3
"""
YITP Modules Quiz Issues Investigation Script
============================================

Investigates quiz issues across three YITP modules within the main YITP course:
1. "Soft Skills for the Streets"
2. "Understanding Purpose in Life (UPL)" 
3. "The Power of Mindset"

These are MODULES within the "Youth Impact Training Programme (YITP)" course, not separate courses.
"""

import os
import sys
import django
from datetime import datetime
from collections import defaultdict, Counter

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question
from progress.models import QuizAttempt, Enrollment
from django.contrib.auth import get_user_model
from django.db.models import Count, Q

User = get_user_model()

class YITPModulesQuizInvestigator:
    def __init__(self):
        self.target_modules = [
            "Soft Skills for the Streets",
            "Understanding Purpose in Life (UPL)",
            "The Power of Mindset"
        ]
        self.yitp_course_title = "Youth Impact Training Programme (YITP)"
        self.investigation_results = {}
        self.report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def find_yitp_course_and_modules(self):
        """Find the YITP course and target modules"""
        print("🔍 STEP 1: Identifying YITP Course and Target Modules")
        print("=" * 60)
        
        # Find the main YITP course
        yitp_course = Course.objects.filter(title__icontains="Youth Impact Training Programme").first()
        
        if not yitp_course:
            print("❌ YITP course not found!")
            return None, {}
        
        print(f"✅ Found YITP Course: '{yitp_course.title}' (ID: {yitp_course.id})")
        print(f"   📊 Published: {yitp_course.is_published}")
        print(f"   📅 Created: {yitp_course.created_at.strftime('%Y-%m-%d')}")
        print(f"   👥 Enrollments: {yitp_course.enrollments.count()}")
        
        # Get all modules in the course
        all_modules = yitp_course.modules.filter(is_published=True).order_by('sort_order')
        print(f"\n📚 All modules in YITP course ({all_modules.count()}):")
        
        found_modules = {}
        
        for i, module in enumerate(all_modules, 1):
            print(f"   {i}. {module.title}")
            
            # Check if this module matches any of our target modules
            for target_module in self.target_modules:
                if target_module.lower() in module.title.lower() or module.title.lower() in target_module.lower():
                    found_modules[target_module] = module
                    print(f"      ✅ MATCHES TARGET: '{target_module}'")
                    break
        
        print(f"\n📊 Target modules found: {len(found_modules)} out of {len(self.target_modules)}")
        
        # If exact matches not found, try partial matching
        if len(found_modules) < len(self.target_modules):
            print("\n🔍 Trying partial keyword matching...")
            
            for target_module in self.target_modules:
                if target_module not in found_modules:
                    keywords = target_module.lower().split()
                    for module in all_modules:
                        module_words = module.title.lower().split()
                        # Check if any keyword matches
                        if any(keyword in ' '.join(module_words) for keyword in keywords):
                            found_modules[target_module] = module
                            print(f"   ✅ Partial match: '{target_module}' → '{module.title}'")
                            break
                    
                    if target_module not in found_modules:
                        print(f"   ❌ No match found for: '{target_module}'")
        
        return yitp_course, found_modules
    
    def analyze_module_structure(self, yitp_course, modules):
        """Analyze the structure of each target module"""
        print("\n🏗️ STEP 2: Analyzing Module Structure")
        print("=" * 60)
        
        module_analysis = {}
        
        for target_name, module in modules.items():
            print(f"\n📚 Analyzing Module: {module.title}")
            print("-" * 40)
            
            # Get lessons in this module
            lessons = module.lessons.filter(is_published=True).order_by('sort_order')
            total_quizzes = 0
            
            lesson_data = []
            for lesson in lessons:
                lesson_quizzes = lesson.quizzes.filter(is_published=True).count()
                total_quizzes += lesson_quizzes
                
                lesson_data.append({
                    'lesson': lesson,
                    'quizzes_count': lesson_quizzes
                })
            
            module_analysis[target_name] = {
                'module': module,
                'target_name': target_name,
                'lessons_count': lessons.count(),
                'total_quizzes': total_quizzes,
                'lessons_data': lesson_data
            }
            
            print(f"   📄 Lessons: {lessons.count()}")
            print(f"   ❓ Quizzes: {total_quizzes}")
            
            for lesson_info in lesson_data:
                lesson = lesson_info['lesson']
                if lesson_info['quizzes_count'] > 0:
                    print(f"      └─ {lesson.title}: {lesson_info['quizzes_count']} quiz(es)")
        
        return module_analysis
    
    def analyze_quiz_questions(self, module_analysis):
        """Analyze quiz questions for each module"""
        print("\n❓ STEP 3: Analyzing Quiz Questions in Target Modules")
        print("=" * 60)
        
        quiz_analysis = {}
        all_questions = []  # For duplication analysis
        
        for target_name, analysis in module_analysis.items():
            module = analysis['module']
            print(f"\n📚 Analyzing quizzes in module: {module.title}")
            print("-" * 40)
            
            # Get all quizzes for this module
            quizzes = Quiz.objects.filter(
                lesson__module=module,
                is_published=True
            ).select_related('lesson')
            
            module_questions = []
            question_types = Counter()
            issues_found = []
            
            for quiz in quizzes:
                print(f"\n   🧩 Quiz: {quiz.title} (Lesson: {quiz.lesson.title})")
                
                questions = quiz.questions.all().order_by('sort_order')
                print(f"      📊 Questions: {questions.count()}")
                
                for question in questions:
                    question_data = {
                        'quiz': quiz,
                        'question': question,
                        'module_name': target_name,
                        'lesson_title': quiz.lesson.title
                    }
                    
                    # Analyze question type
                    question_types[question.question_type] += 1
                    
                    # Analyze question options and correct answers based on question type
                    if question.question_type == 'multiple_choice':
                        # For multiple choice, options are in JSON format
                        options = question.options if question.options else []
                        correct_answer = question.correct_answer.strip()
                        
                        # Count options and check for correct answers
                        total_options = len(options)
                        correct_options = []
                        
                        # Check if correct_answer matches any option
                        for i, option in enumerate(options):
                            if isinstance(option, dict):
                                option_text = option.get('text', '').strip()
                                if option_text.lower() == correct_answer.lower():
                                    correct_options.append(i)
                            elif isinstance(option, str):
                                if option.strip().lower() == correct_answer.lower():
                                    correct_options.append(i)
                        
                        question_data.update({
                            'total_answers': total_options,
                            'correct_answers_count': len(correct_options),
                            'options': options,
                            'correct_answer': correct_answer,
                            'correct_option_indices': correct_options
                        })
                        
                        # Check for issues
                        if len(correct_options) == 0 and total_options > 0:
                            issues_found.append(f"Multiple choice question '{question.question_text[:50]}...' has NO matching correct answer")
                            print(f"         ⚠️  NO CORRECT MATCH: '{correct_answer}' not found in options")
                            print(f"             Options: {[opt.get('text', opt) if isinstance(opt, dict) else opt for opt in options]}")
                        elif len(correct_options) == total_options and total_options > 1:
                            issues_found.append(f"Multiple choice question '{question.question_text[:50]}...' has ALL options as correct")
                    
                    elif question.question_type in ['true_false']:
                        # For true/false questions
                        correct_answer = question.correct_answer.strip().lower()
                        valid_answers = ['true', 'false', 'yes', 'no', '1', '0']
                        
                        question_data.update({
                            'total_answers': 2,
                            'correct_answers_count': 1 if correct_answer in valid_answers else 0,
                            'correct_answer': question.correct_answer
                        })
                        
                        if correct_answer not in valid_answers:
                            issues_found.append(f"True/False question '{question.question_text[:50]}...' has invalid correct answer: '{question.correct_answer}'")
                    
                    elif question.question_type == 'short_answer':
                        # Short answer questions - potential exact match issues
                        question_data.update({
                            'total_answers': 1,
                            'correct_answers_count': 1 if question.correct_answer.strip() else 0,
                            'correct_answer': question.correct_answer
                        })
                        
                        issues_found.append(f"Short-answer question found: '{question.question_text[:50]}...' (potential exact match issue)")
                        print(f"         ⚠️  SHORT ANSWER: Potential exact string matching issue")
                        
                        if not question.correct_answer.strip():
                            issues_found.append(f"Short-answer question '{question.question_text[:50]}...' has empty correct answer")
                    
                    else:
                        # Other question types
                        question_data.update({
                            'total_answers': 1,
                            'correct_answers_count': 1 if question.correct_answer.strip() else 0,
                            'correct_answer': question.correct_answer
                        })
                        
                        if not question.correct_answer.strip():
                            issues_found.append(f"Question '{question.question_text[:50]}...' has empty correct answer")
                    
                    module_questions.append(question_data)
                    all_questions.append(question_data)
            
            quiz_analysis[target_name] = {
                'module': module,
                'total_quizzes': quizzes.count(),
                'total_questions': len(module_questions),
                'question_types': dict(question_types),
                'questions': module_questions,
                'issues_found': issues_found
            }
            
            print(f"   📊 Total Questions: {len(module_questions)}")
            print(f"   📈 Question Types: {dict(question_types)}")
            if issues_found:
                print(f"   ⚠️  Issues Found: {len(issues_found)}")
                for issue in issues_found[:3]:  # Show first 3 issues
                    print(f"      - {issue}")
                if len(issues_found) > 3:
                    print(f"      ... and {len(issues_found) - 3} more issues")
            else:
                print(f"   ✅ No obvious issues found")
        
        return quiz_analysis, all_questions
    
    def check_quiz_duplication(self, all_questions):
        """Check for duplicate questions across modules"""
        print("\n🔄 STEP 4: Checking for Quiz Duplication Across Modules")
        print("=" * 60)
        
        # Group questions by text content
        questions_by_text = defaultdict(list)
        
        for q_data in all_questions:
            question_text = q_data['question'].question_text.strip().lower()
            questions_by_text[question_text].append(q_data)
        
        duplicates = {text: questions for text, questions in questions_by_text.items() if len(questions) > 1}
        
        print(f"📊 Total unique question texts: {len(questions_by_text)}")
        print(f"🔄 Duplicate question texts: {len(duplicates)}")
        
        if duplicates:
            print("\n🔍 Duplicate Questions Found:")
            for i, (question_text, question_list) in enumerate(duplicates.items()):
                if i >= 10:  # Show only first 10 duplicates
                    print(f"   ... and {len(duplicates) - 10} more duplicate question sets")
                    break
                
                print(f"\n   {i+1}. Question: '{question_text[:80]}...'")
                print(f"      Found in {len(question_list)} places:")
                for q_data in question_list:
                    print(f"         - {q_data['module_name']} > {q_data['lesson_title']} > {q_data['quiz'].title}")
                    
                # Check if the duplicates have the same correct answers
                correct_answers = set(q_data.get('correct_answer', '') for q_data in question_list)
                if len(correct_answers) > 1:
                    print(f"      ⚠️  Different correct answers: {correct_answers}")
        else:
            print("✅ No duplicate questions found across modules")
        
        return duplicates
    
    def generate_comprehensive_report(self, yitp_course, module_analysis, quiz_analysis, duplicates):
        """Generate comprehensive investigation report"""
        print("\n📋 STEP 5: Generating Comprehensive Report")
        print("=" * 60)
        
        report_filename = f"yitp_modules_quiz_issues_report_{self.report_timestamp}.md"
        
        with open(report_filename, 'w') as f:
            f.write("# YITP Modules Quiz Issues Investigation Report\n\n")
            f.write(f"**Investigation Date:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}\n")
            f.write(f"**YITP Course:** {yitp_course.title} (ID: {yitp_course.id})\n")
            f.write(f"**Target Modules:** {', '.join(self.target_modules)}\n")
            f.write(f"**Modules Found:** {len(module_analysis)} out of {len(self.target_modules)}\n\n")
            
            f.write("## Executive Summary\n\n")
            
            # Calculate totals
            total_quizzes = sum(analysis['total_quizzes'] for analysis in quiz_analysis.values())
            total_questions = sum(analysis['total_questions'] for analysis in quiz_analysis.values())
            total_issues = sum(len(analysis['issues_found']) for analysis in quiz_analysis.values())
            
            f.write(f"- **YITP Course:** {yitp_course.title}\n")
            f.write(f"- **Total Modules Analyzed:** {len(module_analysis)}\n")
            f.write(f"- **Total Quizzes Analyzed:** {total_quizzes}\n")
            f.write(f"- **Total Questions Analyzed:** {total_questions}\n")
            f.write(f"- **Duplicate Question Sets:** {len(duplicates)}\n")
            f.write(f"- **Issues Found:** {total_issues}\n\n")
            
            # Module-by-module analysis
            f.write("## Module-by-Module Analysis\n\n")
            
            for target_name, analysis in quiz_analysis.items():
                f.write(f"### {target_name}\n\n")
                
                module = analysis['module']
                f.write(f"- **Module ID:** {module.id}\n")
                f.write(f"- **Module Title:** {module.title}\n")
                f.write(f"- **Module Order:** {module.sort_order}\n")
                f.write(f"- **Published:** {module.is_published}\n")
                f.write(f"- **Total Lessons:** {module_analysis[target_name]['lessons_count']}\n")
                f.write(f"- **Total Quizzes:** {analysis['total_quizzes']}\n")
                f.write(f"- **Total Questions:** {analysis['total_questions']}\n")
                f.write(f"- **Question Types:** {analysis['question_types']}\n\n")
                
                # Issues for this module
                module_issues = analysis['issues_found']
                if module_issues:
                    f.write(f"#### Issues Found ({len(module_issues)})\n\n")
                    
                    # Categorize issues
                    short_answer_issues = [issue for issue in module_issues if 'short-answer' in issue.lower()]
                    no_correct_issues = [issue for issue in module_issues if 'no matching correct answer' in issue.lower()]
                    empty_answer_issues = [issue for issue in module_issues if 'empty correct answer' in issue.lower()]
                    
                    if short_answer_issues:
                        f.write(f"**Short-Answer Questions (Exact Match Issues):** {len(short_answer_issues)}\n")
                    if no_correct_issues:
                        f.write(f"**No Matching Correct Answer:** {len(no_correct_issues)}\n")
                    if empty_answer_issues:
                        f.write(f"**Empty Correct Answers:** {len(empty_answer_issues)}\n")
                    
                    f.write("\n**Detailed Issues:**\n\n")
                    for i, issue in enumerate(module_issues[:15]):  # Show first 15 issues
                        f.write(f"{i+1}. {issue}\n")
                    
                    if len(module_issues) > 15:
                        f.write(f"   ... and {len(module_issues) - 15} more issues\n\n")
                else:
                    f.write("#### ✅ No Issues Found\n\n")
            
            # Duplication analysis
            f.write("## Quiz Duplication Analysis\n\n")
            
            if duplicates:
                f.write(f"Found {len(duplicates)} sets of duplicate questions across modules.\n\n")
                
                f.write("### Duplicate Questions\n\n")
                for i, (question_text, question_list) in enumerate(duplicates.items()):
                    if i >= 15:  # Show first 15 duplicates
                        f.write(f"... and {len(duplicates) - 15} more duplicate question sets\n\n")
                        break
                    
                    f.write(f"**{i+1}. Question:** {question_text[:100]}...\n\n")
                    f.write(f"**Found in {len(question_list)} locations:**\n")
                    for q_data in question_list:
                        f.write(f"- {q_data['module_name']} > {q_data['lesson_title']} > {q_data['quiz'].title}\n")
                    
                    # Check for different correct answers
                    correct_answers = set(q_data.get('correct_answer', '') for q_data in question_list)
                    if len(correct_answers) > 1:
                        f.write(f"**⚠️ Different correct answers:** {list(correct_answers)}\n")
                    
                    f.write("\n")
            else:
                f.write("✅ No duplicate questions found across the analyzed modules.\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            
            if total_issues > 0:
                f.write("### Immediate Actions Required\n\n")
                
                # Check for short-answer questions
                short_answer_count = sum(1 for analysis in quiz_analysis.values() 
                                       for issue in analysis['issues_found'] 
                                       if 'short-answer' in issue.lower())
                if short_answer_count > 0:
                    f.write(f"1. **Convert Short-Answer Questions to Multiple Choice** ({short_answer_count} questions)\n")
                    f.write("   - Short-answer questions use exact string matching which causes user lockouts\n")
                    f.write("   - This is the same issue we previously fixed in Module 2\n")
                    f.write("   - Recommend converting all short-answer questions to multiple-choice format\n\n")
                
                # Check for missing correct answers
                no_correct_count = sum(1 for analysis in quiz_analysis.values() 
                                     for issue in analysis['issues_found'] 
                                     if 'no matching correct answer' in issue.lower())
                if no_correct_count > 0:
                    f.write(f"2. **Fix Questions with No Matching Correct Answers** ({no_correct_count} questions)\n")
                    f.write("   - These questions will always result in 0% scores\n")
                    f.write("   - Review correct_answer field and ensure it matches one of the options exactly\n")
                    f.write("   - Check for case sensitivity, extra spaces, or formatting differences\n\n")
            
            if duplicates:
                f.write("### Quiz Content Review\n\n")
                f.write("3. **Review Duplicate Questions**\n")
                f.write("   - Consider if duplicate questions across modules are intentional\n")
                f.write("   - If not intentional, diversify quiz content for each module\n")
                f.write("   - Ensure each module has unique, relevant assessment questions\n\n")
            
            f.write("### Testing and Validation\n\n")
            f.write("4. **Test Quiz Functionality**\n")
            f.write("   - After implementing fixes, test quiz completion with actual user accounts\n")
            f.write("   - Verify that correct answers result in passing scores\n")
            f.write("   - Test specifically with the three problematic modules\n\n")
            
            f.write("---\n")
            f.write(f"*Report generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}*\n")
        
        print(f"📄 Report saved as: {report_filename}")
        return report_filename
    
    def run_investigation(self):
        """Run the complete investigation"""
        print("🚀 YITP Modules Quiz Issues Investigation")
        print("=" * 60)
        print(f"Target Modules: {', '.join(self.target_modules)}")
        print(f"Investigation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # Step 1: Find YITP course and target modules
            yitp_course, modules = self.find_yitp_course_and_modules()
            
            if not yitp_course or not modules:
                print("\n❌ ERROR: YITP course or target modules not found. Investigation cannot continue.")
                return None
            
            # Step 2: Analyze module structure
            module_analysis = self.analyze_module_structure(yitp_course, modules)
            
            # Step 3: Analyze quiz questions
            quiz_analysis, all_questions = self.analyze_quiz_questions(module_analysis)
            
            # Step 4: Check for duplication
            duplicates = self.check_quiz_duplication(all_questions)
            
            # Step 5: Generate report
            report_file = self.generate_comprehensive_report(
                yitp_course, module_analysis, quiz_analysis, duplicates
            )
            
            print("\n" + "=" * 60)
            print("🎉 INVESTIGATION COMPLETE")
            print("=" * 60)
            print(f"📄 Report: {report_file}")
            
            # Summary
            total_issues = sum(len(analysis['issues_found']) for analysis in quiz_analysis.values())
            print(f"📊 Summary:")
            print(f"   - Modules analyzed: {len(modules)}")
            print(f"   - Total questions: {len(all_questions)}")
            print(f"   - Duplicate question sets: {len(duplicates)}")
            print(f"   - Issues found: {total_issues}")
            
            if total_issues > 0:
                print(f"\n⚠️  ACTION REQUIRED: {total_issues} issues need to be addressed")
                
                # Categorize issues for summary
                short_answer_issues = sum(1 for analysis in quiz_analysis.values() 
                                        for issue in analysis['issues_found'] 
                                        if 'short-answer' in issue.lower())
                no_correct_issues = sum(1 for analysis in quiz_analysis.values() 
                                      for issue in analysis['issues_found'] 
                                      if 'no matching correct answer' in issue.lower())
                
                if short_answer_issues > 0:
                    print(f"   - Short-answer questions (exact match issues): {short_answer_issues}")
                if no_correct_issues > 0:
                    print(f"   - Questions with no matching correct answers: {no_correct_issues}")
            else:
                print(f"\n✅ No critical issues found")
            
            return report_file
            
        except Exception as e:
            print(f"\n❌ ERROR during investigation: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    investigator = YITPModulesQuizInvestigator()
    investigator.run_investigation()
