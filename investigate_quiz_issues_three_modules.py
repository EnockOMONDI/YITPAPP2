#!/usr/bin/env python3
"""
YITP Quiz Issues Investigation Script
=====================================

Investigates quiz issues across three YITP modules where users are unable to pass quizzes:
1. "Soft Skills for the Streets"
2. "Understanding Purpose in Life (UPL)" 
3. "The Power of Mindset"

This script will:
- Identify the courses and their basic information
- Analyze quiz structure and question types
- Check for quiz duplication across courses
- Validate correct answers configuration
- Test quiz scoring logic
- Generate comprehensive report with recommendations
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

class QuizIssueInvestigator:
    def __init__(self):
        self.target_courses = [
            "Soft Skills for the Streets",
            "Understanding Purpose in Life (UPL)",
            "The Power of Mindset"
        ]
        self.investigation_results = {}
        self.report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def find_target_courses(self):
        """Find the three target courses in the database"""
        print("🔍 STEP 1: Identifying Target Courses")
        print("=" * 60)
        
        found_courses = {}
        
        for course_title in self.target_courses:
            # Try exact match first
            course = Course.objects.filter(title__iexact=course_title).first()
            
            if not course:
                # Try partial match
                course = Course.objects.filter(title__icontains=course_title.split()[0]).first()
            
            if course:
                found_courses[course_title] = course
                print(f"✅ Found: '{course.title}' (ID: {course.id}, Slug: {course.slug})")
                print(f"   📊 Published: {course.is_published}")
                print(f"   📅 Created: {course.created_at.strftime('%Y-%m-%d')}")
                print(f"   👥 Enrollments: {course.enrollments.count()}")
            else:
                print(f"❌ NOT FOUND: '{course_title}'")
                # Search for similar titles
                similar = Course.objects.filter(
                    Q(title__icontains=course_title.split()[0]) |
                    Q(title__icontains=course_title.split()[-1])
                )[:5]
                if similar:
                    print(f"   🔍 Similar courses found:")
                    for sim_course in similar:
                        print(f"      - '{sim_course.title}' (ID: {sim_course.id})")
        
        print(f"\n📊 Summary: Found {len(found_courses)} out of {len(self.target_courses)} target courses")
        return found_courses
    
    def analyze_course_structure(self, courses):
        """Analyze the structure of each course"""
        print("\n🏗️ STEP 2: Analyzing Course Structure")
        print("=" * 60)
        
        course_analysis = {}
        
        for course_title, course in courses.items():
            print(f"\n📚 Analyzing: {course.title}")
            print("-" * 40)
            
            # Get modules and lessons
            modules = course.modules.filter(is_published=True).order_by('order')
            total_lessons = 0
            total_quizzes = 0
            
            module_data = []
            for module in modules:
                lessons = module.lessons.filter(is_published=True).order_by('order')
                module_quizzes = 0
                
                for lesson in lessons:
                    lesson_quizzes = lesson.quizzes.filter(is_published=True).count()
                    module_quizzes += lesson_quizzes
                
                module_data.append({
                    'module': module,
                    'lessons_count': lessons.count(),
                    'quizzes_count': module_quizzes
                })
                
                total_lessons += lessons.count()
                total_quizzes += module_quizzes
            
            course_analysis[course_title] = {
                'course': course,
                'modules_count': modules.count(),
                'total_lessons': total_lessons,
                'total_quizzes': total_quizzes,
                'modules_data': module_data
            }
            
            print(f"   📖 Modules: {modules.count()}")
            print(f"   📄 Lessons: {total_lessons}")
            print(f"   ❓ Quizzes: {total_quizzes}")
            
            for module_info in module_data:
                module = module_info['module']
                print(f"      └─ {module.title}: {module_info['lessons_count']} lessons, {module_info['quizzes_count']} quizzes")
        
        return course_analysis
    
    def analyze_quiz_questions(self, course_analysis):
        """Analyze quiz questions for each course"""
        print("\n❓ STEP 3: Analyzing Quiz Questions")
        print("=" * 60)
        
        quiz_analysis = {}
        all_questions = []  # For duplication analysis
        
        for course_title, analysis in course_analysis.items():
            course = analysis['course']
            print(f"\n📚 Analyzing quizzes in: {course.title}")
            print("-" * 40)
            
            # Get all quizzes for this course
            quizzes = Quiz.objects.filter(
                lesson__module__course=course,
                is_published=True
            ).select_related('lesson', 'lesson__module')
            
            course_questions = []
            question_types = Counter()
            issues_found = []
            
            for quiz in quizzes:
                print(f"\n   🧩 Quiz: {quiz.title} (Lesson: {quiz.lesson.title})")
                
                questions = quiz.questions.all().order_by('order')
                print(f"      📊 Questions: {questions.count()}")
                
                for question in questions:
                    question_data = {
                        'quiz': quiz,
                        'question': question,
                        'course_title': course_title,
                        'lesson_title': quiz.lesson.title
                    }

                    # Analyze question type
                    question_types[question.question_type] += 1

                    # Analyze question options and correct answers based on question type
                    if question.question_type == 'multiple_choice':
                        # For multiple choice, options are in JSON format
                        options = question.options if question.options else []
                        correct_answer = question.correct_answer

                        # Count options and check for correct answers
                        total_options = len(options)
                        correct_options = []

                        # Check if correct_answer matches any option
                        for i, option in enumerate(options):
                            if isinstance(option, dict):
                                option_text = option.get('text', '')
                                if option_text.strip().lower() == correct_answer.strip().lower():
                                    correct_options.append(i)
                            elif isinstance(option, str):
                                if option.strip().lower() == correct_answer.strip().lower():
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

                    course_questions.append(question_data)
                    all_questions.append(question_data)
            
            quiz_analysis[course_title] = {
                'course': course,
                'total_quizzes': quizzes.count(),
                'total_questions': len(course_questions),
                'question_types': dict(question_types),
                'questions': course_questions,
                'issues_found': issues_found
            }
            
            print(f"   📊 Total Questions: {len(course_questions)}")
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
        """Check for duplicate questions across courses"""
        print("\n🔄 STEP 4: Checking for Quiz Duplication")
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
                if i >= 5:  # Show only first 5 duplicates
                    print(f"   ... and {len(duplicates) - 5} more duplicate question sets")
                    break
                
                print(f"\n   {i+1}. Question: '{question_text[:80]}...'")
                print(f"      Found in {len(question_list)} places:")
                for q_data in question_list:
                    print(f"         - {q_data['course_title']} > {q_data['lesson_title']} > {q_data['quiz'].title}")
        else:
            print("✅ No duplicate questions found across courses")
        
        return duplicates
    
    def validate_quiz_scoring(self, quiz_analysis):
        """Validate quiz scoring logic"""
        print("\n🎯 STEP 5: Validating Quiz Scoring Logic")
        print("=" * 60)
        
        scoring_issues = {}
        
        for course_title, analysis in quiz_analysis.items():
            print(f"\n📚 Validating scoring for: {course_title}")
            print("-" * 40)
            
            course_issues = []
            questions = analysis['questions']
            
            # Check each question's scoring potential
            for q_data in questions:
                question = q_data['question']
                correct_count = q_data['correct_answers_count']
                total_count = q_data['total_answers']

                # Issue: No correct answers
                if correct_count == 0:
                    course_issues.append({
                        'type': 'no_correct_answers',
                        'question': question.question_text[:100],
                        'quiz': q_data['quiz'].title,
                        'lesson': q_data['lesson_title'],
                        'question_type': question.question_type
                    })

                # Issue: All answers correct (for multiple choice)
                elif correct_count == total_count and total_count > 1 and question.question_type == 'multiple_choice':
                    course_issues.append({
                        'type': 'all_answers_correct',
                        'question': question.question_text[:100],
                        'quiz': q_data['quiz'].title,
                        'lesson': q_data['lesson_title'],
                        'question_type': question.question_type
                    })

                # Issue: Short answer (exact match problems)
                elif question.question_type == 'short_answer':
                    course_issues.append({
                        'type': 'short_answer_exact_match',
                        'question': question.question_text[:100],
                        'quiz': q_data['quiz'].title,
                        'lesson': q_data['lesson_title'],
                        'question_type': question.question_type
                    })

                # Issue: Multiple choice with no matching correct answer
                elif question.question_type == 'multiple_choice' and 'correct_option_indices' in q_data and len(q_data['correct_option_indices']) == 0:
                    course_issues.append({
                        'type': 'no_matching_correct_option',
                        'question': question.question_text[:100],
                        'quiz': q_data['quiz'].title,
                        'lesson': q_data['lesson_title'],
                        'question_type': question.question_type,
                        'correct_answer': q_data.get('correct_answer', ''),
                        'options': q_data.get('options', [])
                    })
            
            scoring_issues[course_title] = course_issues
            
            print(f"   📊 Questions analyzed: {len(questions)}")
            print(f"   ⚠️  Scoring issues found: {len(course_issues)}")
            
            # Summarize issue types
            issue_types = Counter(issue['type'] for issue in course_issues)
            for issue_type, count in issue_types.items():
                print(f"      - {issue_type.replace('_', ' ').title()}: {count}")
        
        return scoring_issues
    
    def generate_comprehensive_report(self, courses, course_analysis, quiz_analysis, duplicates, scoring_issues):
        """Generate comprehensive investigation report"""
        print("\n📋 STEP 6: Generating Comprehensive Report")
        print("=" * 60)
        
        report_filename = f"quiz_issues_investigation_report_{self.report_timestamp}.md"
        
        with open(report_filename, 'w') as f:
            f.write("# YITP Quiz Issues Investigation Report\n\n")
            f.write(f"**Investigation Date:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}\n")
            f.write(f"**Target Courses:** {', '.join(self.target_courses)}\n")
            f.write(f"**Courses Found:** {len(courses)} out of {len(self.target_courses)}\n\n")
            
            f.write("## Executive Summary\n\n")
            
            # Calculate totals
            total_quizzes = sum(analysis['total_quizzes'] for analysis in quiz_analysis.values())
            total_questions = sum(analysis['total_questions'] for analysis in quiz_analysis.values())
            total_issues = sum(len(issues) for issues in scoring_issues.values())
            
            f.write(f"- **Total Quizzes Analyzed:** {total_quizzes}\n")
            f.write(f"- **Total Questions Analyzed:** {total_questions}\n")
            f.write(f"- **Duplicate Question Sets:** {len(duplicates)}\n")
            f.write(f"- **Scoring Issues Found:** {total_issues}\n\n")
            
            # Course-by-course analysis
            f.write("## Course-by-Course Analysis\n\n")
            
            for course_title, analysis in quiz_analysis.items():
                f.write(f"### {course_title}\n\n")
                
                course = analysis['course']
                f.write(f"- **Course ID:** {course.id}\n")
                f.write(f"- **Course Slug:** {course.slug}\n")
                f.write(f"- **Published:** {course.is_published}\n")
                f.write(f"- **Total Modules:** {course_analysis[course_title]['modules_count']}\n")
                f.write(f"- **Total Lessons:** {course_analysis[course_title]['total_lessons']}\n")
                f.write(f"- **Total Quizzes:** {analysis['total_quizzes']}\n")
                f.write(f"- **Total Questions:** {analysis['total_questions']}\n")
                f.write(f"- **Question Types:** {analysis['question_types']}\n\n")
                
                # Issues for this course
                course_issues = scoring_issues.get(course_title, [])
                if course_issues:
                    f.write(f"#### Issues Found ({len(course_issues)})\n\n")
                    
                    issue_types = Counter(issue['type'] for issue in course_issues)
                    for issue_type, count in issue_types.items():
                        f.write(f"- **{issue_type.replace('_', ' ').title()}:** {count} questions\n")
                    
                    f.write("\n**Detailed Issues:**\n\n")
                    for i, issue in enumerate(course_issues[:10]):  # Show first 10 issues
                        f.write(f"{i+1}. **{issue['type'].replace('_', ' ').title()}**\n")
                        f.write(f"   - Quiz: {issue['quiz']}\n")
                        f.write(f"   - Lesson: {issue['lesson']}\n")
                        f.write(f"   - Question: {issue['question']}...\n\n")
                    
                    if len(course_issues) > 10:
                        f.write(f"   ... and {len(course_issues) - 10} more issues\n\n")
                else:
                    f.write("#### ✅ No Issues Found\n\n")
            
            # Duplication analysis
            f.write("## Quiz Duplication Analysis\n\n")
            
            if duplicates:
                f.write(f"Found {len(duplicates)} sets of duplicate questions across courses.\n\n")
                
                f.write("### Duplicate Questions\n\n")
                for i, (question_text, question_list) in enumerate(duplicates.items()):
                    if i >= 10:  # Show first 10 duplicates
                        f.write(f"... and {len(duplicates) - 10} more duplicate question sets\n\n")
                        break
                    
                    f.write(f"**{i+1}. Question:** {question_text[:100]}...\n\n")
                    f.write(f"**Found in {len(question_list)} locations:**\n")
                    for q_data in question_list:
                        f.write(f"- {q_data['course_title']} > {q_data['lesson_title']} > {q_data['quiz'].title}\n")
                    f.write("\n")
            else:
                f.write("✅ No duplicate questions found across the analyzed courses.\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            
            if total_issues > 0:
                f.write("### Immediate Actions Required\n\n")
                
                # Check for short-answer questions
                short_answer_issues = sum(1 for issues in scoring_issues.values() 
                                        for issue in issues if issue['type'] == 'short_answer_exact_match')
                if short_answer_issues > 0:
                    f.write(f"1. **Convert Short-Answer Questions to Multiple Choice** ({short_answer_issues} questions)\n")
                    f.write("   - Short-answer questions use exact string matching which causes user lockouts\n")
                    f.write("   - This is the same issue we fixed in Module 2\n")
                    f.write("   - Recommend converting all short-answer questions to multiple-choice format\n\n")
                
                # Check for missing correct answers
                no_correct_issues = sum(1 for issues in scoring_issues.values() 
                                      for issue in issues if issue['type'] == 'no_correct_answers')
                if no_correct_issues > 0:
                    f.write(f"2. **Fix Questions with No Correct Answers** ({no_correct_issues} questions)\n")
                    f.write("   - These questions will always result in 0% scores\n")
                    f.write("   - Review and mark appropriate answers as correct\n\n")
                
                # Check for all-correct answers
                all_correct_issues = sum(1 for issues in scoring_issues.values() 
                                       for issue in issues if issue['type'] == 'all_answers_correct')
                if all_correct_issues > 0:
                    f.write(f"3. **Fix Questions with All Answers Marked Correct** ({all_correct_issues} questions)\n")
                    f.write("   - These questions provide no assessment value\n")
                    f.write("   - Review and mark only the truly correct answers\n\n")
            
            if duplicates:
                f.write("### Quiz Content Review\n\n")
                f.write("4. **Review Duplicate Questions**\n")
                f.write("   - Consider if duplicate questions across courses are intentional\n")
                f.write("   - If not intentional, diversify quiz content for each course\n")
                f.write("   - Ensure each course has unique, relevant assessment questions\n\n")
            
            f.write("### Testing and Validation\n\n")
            f.write("5. **Test Quiz Functionality**\n")
            f.write("   - After implementing fixes, test quiz completion with actual user accounts\n")
            f.write("   - Verify that correct answers result in passing scores\n")
            f.write("   - Ensure quiz progression works correctly\n\n")
            
            f.write("6. **Monitor User Feedback**\n")
            f.write("   - Track user quiz completion rates after fixes\n")
            f.write("   - Monitor for continued reports of 0% scores\n")
            f.write("   - Implement logging for quiz scoring issues\n\n")
            
            # Technical details
            f.write("## Technical Details\n\n")
            f.write("### Investigation Methodology\n\n")
            f.write("1. **Course Identification:** Searched database for target course titles\n")
            f.write("2. **Structure Analysis:** Analyzed modules, lessons, and quiz distribution\n")
            f.write("3. **Question Analysis:** Examined question types, answers, and correct answer configuration\n")
            f.write("4. **Duplication Check:** Compared question text across all courses\n")
            f.write("5. **Scoring Validation:** Identified potential scoring issues\n\n")
            
            f.write("### Database Queries Used\n\n")
            f.write("- Course.objects.filter() for course identification\n")
            f.write("- Quiz.objects.filter() for quiz retrieval\n")
            f.write("- Question.answers.filter(is_correct=True) for correct answer validation\n")
            f.write("- Text comparison for duplication detection\n\n")
            
            f.write("---\n")
            f.write(f"*Report generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}*\n")
        
        print(f"📄 Report saved as: {report_filename}")
        return report_filename
    
    def run_investigation(self):
        """Run the complete investigation"""
        print("🚀 YITP Quiz Issues Investigation")
        print("=" * 60)
        print(f"Target Courses: {', '.join(self.target_courses)}")
        print(f"Investigation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # Step 1: Find target courses
            courses = self.find_target_courses()
            
            if not courses:
                print("\n❌ ERROR: No target courses found. Investigation cannot continue.")
                return None
            
            # Step 2: Analyze course structure
            course_analysis = self.analyze_course_structure(courses)
            
            # Step 3: Analyze quiz questions
            quiz_analysis, all_questions = self.analyze_quiz_questions(course_analysis)
            
            # Step 4: Check for duplication
            duplicates = self.check_quiz_duplication(all_questions)
            
            # Step 5: Validate scoring
            scoring_issues = self.validate_quiz_scoring(quiz_analysis)
            
            # Step 6: Generate report
            report_file = self.generate_comprehensive_report(
                courses, course_analysis, quiz_analysis, duplicates, scoring_issues
            )
            
            print("\n" + "=" * 60)
            print("🎉 INVESTIGATION COMPLETE")
            print("=" * 60)
            print(f"📄 Report: {report_file}")
            
            # Summary
            total_issues = sum(len(issues) for issues in scoring_issues.values())
            print(f"📊 Summary:")
            print(f"   - Courses analyzed: {len(courses)}")
            print(f"   - Total questions: {len(all_questions)}")
            print(f"   - Duplicate question sets: {len(duplicates)}")
            print(f"   - Scoring issues found: {total_issues}")
            
            if total_issues > 0:
                print(f"\n⚠️  ACTION REQUIRED: {total_issues} issues need to be addressed")
            else:
                print(f"\n✅ No critical issues found")
            
            return report_file
            
        except Exception as e:
            print(f"\n❌ ERROR during investigation: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    investigator = QuizIssueInvestigator()
    investigator.run_investigation()
