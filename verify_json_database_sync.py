#!/usr/bin/env python3
"""
Verify JSON Database Synchronization
===================================

Verify that the exported JSON file exactly matches the production database state.
"""

import os
import sys
import django
import json

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set up Django environment for PRODUCTION database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode

django.setup()

from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question

class JSONDatabaseVerifier:
    def __init__(self):
        self.json_file_path = "courseunits/YITP_Course6_Module1_UPDATED_with_quizzes.json"
        self.course_id = 6
        self.module_id = 14
        self.verification_results = {
            'course_match': False,
            'module_match': False,
            'lessons_match': 0,
            'total_lessons': 0,
            'quizzes_match': 0,
            'total_quizzes': 0,
            'questions_match': 0,
            'total_questions': 0,
            'styling_verified': 0,
            'issues': []
        }

    def load_json_data(self):
        """Load the JSON file"""
        print("📄 LOADING JSON FILE")
        print("=" * 50)
        
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ JSON file loaded: {self.json_file_path}")
            print(f"📊 File size: {os.path.getsize(self.json_file_path):,} bytes")
            
            return data
            
        except Exception as e:
            print(f"❌ Error loading JSON: {str(e)}")
            return None

    def verify_course_info(self, json_data):
        """Verify course information matches"""
        print(f"\n📚 VERIFYING COURSE INFORMATION")
        print("=" * 50)
        
        try:
            course = Course.objects.get(id=self.course_id)
            json_course = json_data.get('course_info', {})
            
            # Check key fields
            matches = []
            matches.append(course.id == json_course.get('id'))
            matches.append(course.title == json_course.get('title'))
            matches.append(course.is_published == json_course.get('is_published'))
            matches.append(float(course.price) == json_course.get('price'))
            
            all_match = all(matches)
            self.verification_results['course_match'] = all_match
            
            print(f"Course ID: {'✅' if course.id == json_course.get('id') else '❌'}")
            print(f"Title: {'✅' if course.title == json_course.get('title') else '❌'}")
            print(f"Published: {'✅' if course.is_published == json_course.get('is_published') else '❌'}")
            print(f"Price: {'✅' if float(course.price) == json_course.get('price') else '❌'}")
            
            if all_match:
                print(f"✅ Course information matches perfectly")
            else:
                print(f"❌ Course information mismatch detected")
                self.verification_results['issues'].append("Course information mismatch")
            
            return all_match
            
        except Exception as e:
            print(f"❌ Error verifying course: {str(e)}")
            self.verification_results['issues'].append(f"Course verification error: {str(e)}")
            return False

    def verify_lessons(self, json_data):
        """Verify all lessons match"""
        print(f"\n📖 VERIFYING LESSONS")
        print("=" * 50)
        
        try:
            # Get database lessons
            module = Module.objects.get(id=self.module_id)
            db_lessons = Lesson.objects.filter(module=module).order_by('sort_order')
            
            # Get JSON lessons
            json_module = json_data.get('modules', [{}])[0]
            json_lessons = json_module.get('lessons', [])
            
            self.verification_results['total_lessons'] = len(json_lessons)
            
            print(f"Database lessons: {db_lessons.count()}")
            print(f"JSON lessons: {len(json_lessons)}")
            
            if db_lessons.count() != len(json_lessons):
                print(f"❌ Lesson count mismatch")
                self.verification_results['issues'].append("Lesson count mismatch")
                return False
            
            # Verify each lesson
            matches = 0
            for db_lesson in db_lessons:
                # Find corresponding JSON lesson
                json_lesson = next((l for l in json_lessons if l['id'] == db_lesson.id), None)
                
                if not json_lesson:
                    print(f"❌ Lesson {db_lesson.id} not found in JSON")
                    self.verification_results['issues'].append(f"Lesson {db_lesson.id} missing from JSON")
                    continue
                
                # Verify lesson fields
                lesson_matches = []
                lesson_matches.append(db_lesson.title == json_lesson.get('title'))
                lesson_matches.append(db_lesson.content == json_lesson.get('content'))
                lesson_matches.append(db_lesson.estimated_duration == json_lesson.get('estimated_duration'))
                lesson_matches.append(db_lesson.sort_order == json_lesson.get('sort_order'))
                lesson_matches.append(db_lesson.is_published == json_lesson.get('is_published'))
                
                # Check YITP styling
                has_styling = 'yitp-lesson-content' in (db_lesson.content or '')
                json_has_styling = 'yitp-lesson-content' in (json_lesson.get('content', ''))
                styling_match = has_styling == json_has_styling
                
                if styling_match and has_styling:
                    self.verification_results['styling_verified'] += 1
                
                if all(lesson_matches) and styling_match:
                    matches += 1
                    print(f"✅ Lesson {db_lesson.id}: {db_lesson.title}")
                else:
                    print(f"❌ Lesson {db_lesson.id}: Mismatch detected")
                    self.verification_results['issues'].append(f"Lesson {db_lesson.id} content mismatch")
            
            self.verification_results['lessons_match'] = matches
            
            print(f"\n📊 Lesson Verification Results:")
            print(f"   Matching lessons: {matches}/{len(json_lessons)}")
            print(f"   Lessons with YITP styling: {self.verification_results['styling_verified']}/{len(json_lessons)}")
            
            return matches == len(json_lessons)
            
        except Exception as e:
            print(f"❌ Error verifying lessons: {str(e)}")
            self.verification_results['issues'].append(f"Lesson verification error: {str(e)}")
            return False

    def verify_quizzes_and_questions(self, json_data):
        """Verify all quizzes and questions match"""
        print(f"\n🧩 VERIFYING QUIZZES AND QUESTIONS")
        print("=" * 50)
        
        try:
            json_module = json_data.get('modules', [{}])[0]
            json_lessons = json_module.get('lessons', [])
            
            quiz_matches = 0
            question_matches = 0
            total_quizzes = 0
            total_questions = 0
            
            for json_lesson in json_lessons:
                lesson_id = json_lesson['id']
                json_quiz_data = json_lesson.get('assessment', {}).get('quiz')
                
                if not json_quiz_data:
                    continue
                
                total_quizzes += 1
                
                # Get database quiz
                try:
                    db_lesson = Lesson.objects.get(id=lesson_id)
                    db_quiz = Quiz.objects.filter(lesson=db_lesson, is_published=True).first()
                    
                    if not db_quiz:
                        print(f"❌ Quiz for lesson {lesson_id} not found in database")
                        self.verification_results['issues'].append(f"Quiz for lesson {lesson_id} missing from database")
                        continue
                    
                    # Verify quiz fields
                    quiz_field_matches = []
                    quiz_field_matches.append(db_quiz.title == json_quiz_data.get('title'))
                    quiz_field_matches.append(db_quiz.passing_score == json_quiz_data.get('passing_score'))
                    quiz_field_matches.append(db_quiz.max_attempts == json_quiz_data.get('max_attempts'))
                    quiz_field_matches.append(db_quiz.is_randomized == json_quiz_data.get('is_randomized'))
                    
                    if all(quiz_field_matches):
                        quiz_matches += 1
                        print(f"✅ Quiz for lesson {lesson_id}: Metadata matches")
                    else:
                        print(f"❌ Quiz for lesson {lesson_id}: Metadata mismatch")
                        self.verification_results['issues'].append(f"Quiz {db_quiz.id} metadata mismatch")
                    
                    # Verify questions
                    db_questions = Question.objects.filter(quiz=db_quiz).order_by('sort_order')
                    json_questions = json_quiz_data.get('questions', [])
                    
                    total_questions += len(json_questions)
                    
                    if db_questions.count() != len(json_questions):
                        print(f"❌ Question count mismatch for lesson {lesson_id}")
                        self.verification_results['issues'].append(f"Question count mismatch for lesson {lesson_id}")
                        continue
                    
                    lesson_question_matches = 0
                    for db_question in db_questions:
                        json_question = next((q for q in json_questions if q['id'] == db_question.id), None)
                        
                        if not json_question:
                            continue
                        
                        # Verify question fields
                        question_field_matches = []
                        question_field_matches.append(db_question.question_text == json_question.get('question_text'))
                        question_field_matches.append(db_question.question_type == json_question.get('question_type'))
                        question_field_matches.append(db_question.correct_answer == json_question.get('correct_answer'))
                        question_field_matches.append(db_question.points == json_question.get('points'))
                        question_field_matches.append(db_question.sort_order == json_question.get('sort_order'))
                        
                        # Check options for multiple choice
                        if db_question.question_type == 'multiple_choice':
                            question_field_matches.append(db_question.options == json_question.get('options'))
                        
                        if all(question_field_matches):
                            lesson_question_matches += 1
                    
                    question_matches += lesson_question_matches
                    print(f"   Questions: {lesson_question_matches}/{len(json_questions)} match")
                    
                except Exception as e:
                    print(f"❌ Error verifying quiz for lesson {lesson_id}: {str(e)}")
                    self.verification_results['issues'].append(f"Quiz verification error for lesson {lesson_id}")
            
            self.verification_results['quizzes_match'] = quiz_matches
            self.verification_results['total_quizzes'] = total_quizzes
            self.verification_results['questions_match'] = question_matches
            self.verification_results['total_questions'] = total_questions
            
            print(f"\n📊 Quiz Verification Results:")
            print(f"   Matching quizzes: {quiz_matches}/{total_quizzes}")
            print(f"   Matching questions: {question_matches}/{total_questions}")
            
            return quiz_matches == total_quizzes and question_matches == total_questions
            
        except Exception as e:
            print(f"❌ Error verifying quizzes: {str(e)}")
            self.verification_results['issues'].append(f"Quiz verification error: {str(e)}")
            return False

    def generate_verification_report(self):
        """Generate comprehensive verification report"""
        print(f"\n📊 GENERATING VERIFICATION REPORT")
        print("=" * 50)
        
        # Calculate overall success rate
        total_checks = 4  # course, module, lessons, quizzes
        passed_checks = 0
        
        if self.verification_results['course_match']:
            passed_checks += 1
        if self.verification_results['lessons_match'] == self.verification_results['total_lessons']:
            passed_checks += 1
        if self.verification_results['quizzes_match'] == self.verification_results['total_quizzes']:
            passed_checks += 1
        if self.verification_results['questions_match'] == self.verification_results['total_questions']:
            passed_checks += 1
        
        success_rate = (passed_checks / total_checks) * 100
        
        report_content = f"""# JSON Database Synchronization Verification Report

**Verification Date:** {django.utils.timezone.now().strftime('%Y-%m-%d %H:%M:%S')}  
**JSON File:** {self.json_file_path}  
**Database:** Production Supabase PostgreSQL  

## 🎯 Overall Verification Results

**Success Rate:** {success_rate:.1f}% ({passed_checks}/{total_checks} checks passed)  
**Status:** {'✅ SYNCHRONIZED' if success_rate == 100 else '⚠️ ISSUES DETECTED'}  

## 📊 Detailed Results

### Course Information
- **Match Status:** {'✅ PASS' if self.verification_results['course_match'] else '❌ FAIL'}

### Lessons
- **Total Lessons:** {self.verification_results['total_lessons']}
- **Matching Lessons:** {self.verification_results['lessons_match']}/{self.verification_results['total_lessons']}
- **YITP Styling Verified:** {self.verification_results['styling_verified']}/{self.verification_results['total_lessons']}
- **Status:** {'✅ PASS' if self.verification_results['lessons_match'] == self.verification_results['total_lessons'] else '❌ FAIL'}

### Quizzes
- **Total Quizzes:** {self.verification_results['total_quizzes']}
- **Matching Quizzes:** {self.verification_results['quizzes_match']}/{self.verification_results['total_quizzes']}
- **Status:** {'✅ PASS' if self.verification_results['quizzes_match'] == self.verification_results['total_quizzes'] else '❌ FAIL'}

### Questions
- **Total Questions:** {self.verification_results['total_questions']}
- **Matching Questions:** {self.verification_results['questions_match']}/{self.verification_results['total_questions']}
- **Status:** {'✅ PASS' if self.verification_results['questions_match'] == self.verification_results['total_questions'] else '❌ FAIL'}

## 🔍 Issues Detected

{chr(10).join([f"- {issue}" for issue in self.verification_results['issues']]) if self.verification_results['issues'] else "✅ No issues detected"}

## ✅ Verification Summary

- **Database → JSON Sync:** {'✅ COMPLETE' if success_rate == 100 else '⚠️ PARTIAL'}
- **Content Integrity:** {'✅ VERIFIED' if self.verification_results['lessons_match'] == self.verification_results['total_lessons'] else '❌ ISSUES'}
- **Quiz Integrity:** {'✅ VERIFIED' if self.verification_results['questions_match'] == self.verification_results['total_questions'] else '❌ ISSUES'}
- **YITP Styling:** {'✅ VERIFIED' if self.verification_results['styling_verified'] == self.verification_results['total_lessons'] else '⚠️ PARTIAL'}

---
**Verification Status:** {'✅ SUCCESS' if success_rate == 100 else '❌ FAILED'}
"""
        
        report_filename = f"json_database_verification_report_{django.utils.timezone.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 Verification report saved: {report_filename}")
        
        # Print summary
        print(f"\n📊 VERIFICATION SUMMARY:")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Lessons: {self.verification_results['lessons_match']}/{self.verification_results['total_lessons']}")
        print(f"   Questions: {self.verification_results['questions_match']}/{self.verification_results['total_questions']}")
        print(f"   YITP Styling: {self.verification_results['styling_verified']}/{self.verification_results['total_lessons']}")
        
        return success_rate == 100

    def execute_verification(self):
        """Execute the complete verification process"""
        print("🔍 JSON DATABASE SYNCHRONIZATION VERIFICATION")
        print("=" * 60)
        
        # Load JSON data
        json_data = self.load_json_data()
        if not json_data:
            return False
        
        # Verify course info
        course_ok = self.verify_course_info(json_data)
        
        # Verify lessons
        lessons_ok = self.verify_lessons(json_data)
        
        # Verify quizzes and questions
        quizzes_ok = self.verify_quizzes_and_questions(json_data)
        
        # Generate report
        success = self.generate_verification_report()
        
        return success

if __name__ == "__main__":
    verifier = JSONDatabaseVerifier()
    success = verifier.execute_verification()
    
    if success:
        print(f"\n🎉 VERIFICATION COMPLETED SUCCESSFULLY!")
        print(f"✅ JSON file perfectly synchronized with production database")
        print(f"✅ All content, styling, and quiz data verified")
    else:
        print(f"\n⚠️ VERIFICATION COMPLETED WITH ISSUES")
        print(f"❌ Some discrepancies detected between JSON and database")
