#!/usr/bin/env python3
"""
Module 2 JSON Validation Script
==============================

Comprehensive validation of YITP Course 6, Module 2 JSON file for production database import.
"""

import os
import sys
import django
import json
import re
from datetime import datetime

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set up Django environment for PRODUCTION database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode

django.setup()

from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question

class Module2JSONValidator:
    def __init__(self):
        self.module2_file = "courseunits/YITP_Course6_Module2_PI_ASSESSMENTS_import_ready.json"
        self.module1_file = "courseunits/YITP_Course6_Module1_UPDATED_with_quizzes.json"
        self.validation_results = {
            'json_structure': {'status': False, 'issues': []},
            'data_integrity': {'status': False, 'issues': []},
            'content_quality': {'status': False, 'issues': []},
            'quiz_validation': {'status': False, 'issues': []},
            'field_completeness': {'status': False, 'issues': []},
            'import_simulation': {'status': False, 'issues': []},
            'overall_status': 'UNKNOWN',
            'recommendation': 'UNKNOWN'
        }
        self.module2_data = None
        self.module1_data = None

    def load_json_files(self):
        """Load both JSON files for comparison"""
        print("📄 LOADING JSON FILES")
        print("=" * 50)
        
        try:
            # Load Module 2 JSON
            with open(self.module2_file, 'r', encoding='utf-8') as f:
                self.module2_data = json.load(f)
            print(f"✅ Module 2 JSON loaded: {os.path.getsize(self.module2_file):,} bytes")
            
            # Load Module 1 JSON for reference
            with open(self.module1_file, 'r', encoding='utf-8') as f:
                self.module1_data = json.load(f)
            print(f"✅ Module 1 JSON loaded: {os.path.getsize(self.module1_file):,} bytes")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading JSON files: {str(e)}")
            self.validation_results['json_structure']['issues'].append(f"JSON loading error: {str(e)}")
            return False

    def validate_json_structure(self):
        """Validate JSON structure against Module 1 reference"""
        print(f"\n🔍 VALIDATING JSON STRUCTURE")
        print("=" * 50)
        
        issues = []
        
        try:
            # Check top-level structure
            required_top_level = ['course_info', 'modules']
            for field in required_top_level:
                if field not in self.module2_data:
                    issues.append(f"Missing top-level field: {field}")
            
            # Check course_info structure
            if 'course_info' in self.module2_data:
                course_info = self.module2_data['course_info']
                if 'id' not in course_info or course_info['id'] != 6:
                    issues.append("course_info.id must be 6 for YITP")
            
            # Check modules structure
            if 'modules' in self.module2_data:
                modules = self.module2_data['modules']
                if not isinstance(modules, list) or len(modules) != 1:
                    issues.append("modules must be a list with exactly 1 module")
                
                if modules:
                    module = modules[0]
                    required_module_fields = ['title', 'description', 'sort_order', 'lessons']
                    for field in required_module_fields:
                        if field not in module:
                            issues.append(f"Missing module field: {field}")
                    
                    # Check lessons structure
                    if 'lessons' in module:
                        lessons = module['lessons']
                        if not isinstance(lessons, list):
                            issues.append("lessons must be a list")
                        
                        for i, lesson in enumerate(lessons):
                            required_lesson_fields = ['title', 'content', 'content_type', 'learning_objectives', 
                                                    'estimated_duration', 'sort_order', 'is_published', 'assessment']
                            for field in required_lesson_fields:
                                if field not in lesson:
                                    issues.append(f"Lesson {i+1} missing field: {field}")
                            
                            # Check assessment structure
                            if 'assessment' in lesson and 'quiz' in lesson['assessment']:
                                quiz = lesson['assessment']['quiz']
                                required_quiz_fields = ['title', 'questions', 'passing_score', 'max_attempts']
                                for field in required_quiz_fields:
                                    if field not in quiz:
                                        issues.append(f"Lesson {i+1} quiz missing field: {field}")
                                
                                # Check questions structure
                                if 'questions' in quiz:
                                    questions = quiz['questions']
                                    if not isinstance(questions, list):
                                        issues.append(f"Lesson {i+1} quiz questions must be a list")
                                    
                                    for j, question in enumerate(questions):
                                        required_question_fields = ['question_text', 'question_type', 'points', 'sort_order']
                                        for field in required_question_fields:
                                            if field not in question:
                                                issues.append(f"Lesson {i+1} question {j+1} missing field: {field}")
            
            self.validation_results['json_structure']['issues'] = issues
            self.validation_results['json_structure']['status'] = len(issues) == 0
            
            if len(issues) == 0:
                print("✅ JSON structure validation passed")
            else:
                print(f"❌ JSON structure validation failed ({len(issues)} issues)")
                for issue in issues[:5]:  # Show first 5 issues
                    print(f"   • {issue}")
                if len(issues) > 5:
                    print(f"   • ... and {len(issues) - 5} more issues")
            
            return len(issues) == 0
            
        except Exception as e:
            error_msg = f"JSON structure validation error: {str(e)}"
            self.validation_results['json_structure']['issues'].append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def validate_data_integrity(self):
        """Validate data integrity and uniqueness"""
        print(f"\n🔒 VALIDATING DATA INTEGRITY")
        print("=" * 50)
        
        issues = []
        
        try:
            # Get existing database IDs to check for conflicts
            existing_lesson_ids = set(Lesson.objects.values_list('id', flat=True))
            existing_quiz_ids = set(Quiz.objects.values_list('id', flat=True))
            existing_question_ids = set(Question.objects.values_list('id', flat=True))
            
            # Check Module 2 lesson IDs
            module = self.module2_data['modules'][0]
            lesson_ids = []
            quiz_ids = []
            question_ids = []
            sort_orders = []
            
            for lesson in module['lessons']:
                # Check lesson ID conflicts (if present)
                if 'id' in lesson:
                    lesson_id = lesson['id']
                    if lesson_id in existing_lesson_ids:
                        issues.append(f"Lesson ID {lesson_id} already exists in database")
                    if lesson_id in lesson_ids:
                        issues.append(f"Duplicate lesson ID {lesson_id} in JSON")
                    lesson_ids.append(lesson_id)
                
                # Check sort_order uniqueness
                sort_order = lesson.get('sort_order')
                if sort_order in sort_orders:
                    issues.append(f"Duplicate sort_order {sort_order}")
                sort_orders.append(sort_order)
                
                # Validate content_type
                valid_content_types = ['text', 'video', 'document', 'audio', 'presentation', 'exercise', 'quiz', 'assignment']
                content_type = lesson.get('content_type')
                if content_type not in valid_content_types:
                    issues.append(f"Invalid content_type '{content_type}' in lesson '{lesson.get('title', 'Unknown')}'")
                
                # Check quiz and question IDs
                if 'assessment' in lesson and 'quiz' in lesson['assessment']:
                    quiz = lesson['assessment']['quiz']
                    
                    if 'id' in quiz:
                        quiz_id = quiz['id']
                        if quiz_id in existing_quiz_ids:
                            issues.append(f"Quiz ID {quiz_id} already exists in database")
                        if quiz_id in quiz_ids:
                            issues.append(f"Duplicate quiz ID {quiz_id} in JSON")
                        quiz_ids.append(quiz_id)
                    
                    # Check questions
                    if 'questions' in quiz:
                        question_sort_orders = []
                        for question in quiz['questions']:
                            if 'id' in question:
                                question_id = question['id']
                                if question_id in existing_question_ids:
                                    issues.append(f"Question ID {question_id} already exists in database")
                                if question_id in question_ids:
                                    issues.append(f"Duplicate question ID {question_id} in JSON")
                                question_ids.append(question_id)
                            
                            # Check question sort_order uniqueness within quiz
                            q_sort_order = question.get('sort_order')
                            if q_sort_order in question_sort_orders:
                                issues.append(f"Duplicate question sort_order {q_sort_order} in quiz")
                            question_sort_orders.append(q_sort_order)
                            
                            # Validate question_type
                            valid_question_types = ['multiple_choice', 'true_false', 'short_answer', 'essay', 'matching', 'fill_blank']
                            question_type = question.get('question_type')
                            if question_type not in valid_question_types:
                                issues.append(f"Invalid question_type '{question_type}'")
            
            self.validation_results['data_integrity']['issues'] = issues
            self.validation_results['data_integrity']['status'] = len(issues) == 0
            
            if len(issues) == 0:
                print("✅ Data integrity validation passed")
                print(f"   • Lessons: {len(lesson_ids)} unique IDs")
                print(f"   • Quizzes: {len(quiz_ids)} unique IDs")
                print(f"   • Questions: {len(question_ids)} unique IDs")
            else:
                print(f"❌ Data integrity validation failed ({len(issues)} issues)")
                for issue in issues[:5]:
                    print(f"   • {issue}")
                if len(issues) > 5:
                    print(f"   • ... and {len(issues) - 5} more issues")
            
            return len(issues) == 0
            
        except Exception as e:
            error_msg = f"Data integrity validation error: {str(e)}"
            self.validation_results['data_integrity']['issues'].append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def validate_content_quality(self):
        """Validate content quality and YITP styling"""
        print(f"\n🎨 VALIDATING CONTENT QUALITY")
        print("=" * 50)
        
        issues = []
        
        try:
            module = self.module2_data['modules'][0]
            lessons_with_styling = 0
            lessons_with_gradients = 0
            lessons_with_colors = 0
            empty_content_lessons = 0
            
            for i, lesson in enumerate(module['lessons']):
                lesson_title = lesson.get('title', f'Lesson {i+1}')
                content = lesson.get('content', '')
                
                # Check for empty content
                if not content or content.strip() == '':
                    empty_content_lessons += 1
                    issues.append(f"Empty content in lesson: {lesson_title}")
                    continue
                
                # Check for YITP styling
                if 'yitp-lesson-content' in content:
                    lessons_with_styling += 1
                else:
                    issues.append(f"Missing YITP styling (yitp-lesson-content) in lesson: {lesson_title}")
                
                # Check for YITP gradient backgrounds
                if 'linear-gradient(135deg, #1a2e53 0%, #ff5d15 100%)' in content:
                    lessons_with_gradients += 1
                else:
                    issues.append(f"Missing YITP gradient background in lesson: {lesson_title}")
                
                # Check for YITP brand colors
                has_orange = '#ff5d15' in content
                has_blue = '#1a2e53' in content
                if has_orange and has_blue:
                    lessons_with_colors += 1
                else:
                    missing_colors = []
                    if not has_orange:
                        missing_colors.append('#ff5d15 (orange)')
                    if not has_blue:
                        missing_colors.append('#1a2e53 (blue)')
                    issues.append(f"Missing YITP brand colors {', '.join(missing_colors)} in lesson: {lesson_title}")
                
                # Check for required CSS classes
                required_classes = ['yitp-section-card', 'yitp-activity-box']
                for css_class in required_classes:
                    if css_class not in content:
                        issues.append(f"Missing CSS class '{css_class}' in lesson: {lesson_title}")
                
                # Check for placeholder content that needs replacement
                if '{VERBATIM_PLACEHOLDER_' in content:
                    issues.append(f"Unresolved placeholder content in lesson: {lesson_title}")
            
            total_lessons = len(module['lessons'])
            
            self.validation_results['content_quality']['issues'] = issues
            self.validation_results['content_quality']['status'] = len(issues) == 0
            
            print(f"📊 Content Quality Statistics:")
            print(f"   • Total lessons: {total_lessons}")
            print(f"   • Lessons with YITP styling: {lessons_with_styling}/{total_lessons}")
            print(f"   • Lessons with gradients: {lessons_with_gradients}/{total_lessons}")
            print(f"   • Lessons with brand colors: {lessons_with_colors}/{total_lessons}")
            print(f"   • Empty content lessons: {empty_content_lessons}")
            
            if len(issues) == 0:
                print("✅ Content quality validation passed")
            else:
                print(f"❌ Content quality validation failed ({len(issues)} issues)")
                for issue in issues[:3]:
                    print(f"   • {issue}")
                if len(issues) > 3:
                    print(f"   • ... and {len(issues) - 3} more issues")
            
            return len(issues) == 0
            
        except Exception as e:
            error_msg = f"Content quality validation error: {str(e)}"
            self.validation_results['content_quality']['issues'].append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def validate_quiz_structure(self):
        """Validate quiz and question structure"""
        print(f"\n🧩 VALIDATING QUIZ STRUCTURE")
        print("=" * 50)
        
        issues = []
        
        try:
            module = self.module2_data['modules'][0]
            total_lessons = len(module['lessons'])
            lessons_with_quizzes = 0
            total_questions = 0
            
            for i, lesson in enumerate(module['lessons']):
                lesson_title = lesson.get('title', f'Lesson {i+1}')
                
                if 'assessment' not in lesson or 'quiz' not in lesson['assessment']:
                    issues.append(f"Missing quiz in lesson: {lesson_title}")
                    continue
                
                lessons_with_quizzes += 1
                quiz = lesson['assessment']['quiz']
                
                # Validate quiz metadata
                passing_score = quiz.get('passing_score', 0)
                if not isinstance(passing_score, int) or passing_score < 0 or passing_score > 100:
                    issues.append(f"Invalid passing_score {passing_score} in lesson: {lesson_title}")
                
                max_attempts = quiz.get('max_attempts', 0)
                if not isinstance(max_attempts, int) or max_attempts < 1:
                    issues.append(f"Invalid max_attempts {max_attempts} in lesson: {lesson_title}")
                
                # Validate questions
                if 'questions' not in quiz:
                    issues.append(f"Missing questions in quiz for lesson: {lesson_title}")
                    continue
                
                questions = quiz['questions']
                if not questions:
                    issues.append(f"Empty questions list in quiz for lesson: {lesson_title}")
                    continue
                
                total_questions += len(questions)
                
                for j, question in enumerate(questions):
                    question_num = j + 1
                    
                    # Check required fields
                    if not question.get('question_text', '').strip():
                        issues.append(f"Empty question_text in lesson {lesson_title}, question {question_num}")
                    
                    question_type = question.get('question_type')
                    if question_type == 'multiple_choice':
                        # Multiple choice questions should have options and correct_answer
                        if 'options' not in question:
                            issues.append(f"Missing 'options' field for multiple_choice question in lesson {lesson_title}, question {question_num}")
                        elif not isinstance(question['options'], list) or len(question['options']) < 2:
                            issues.append(f"Invalid options for multiple_choice question in lesson {lesson_title}, question {question_num}")
                        
                        if 'correct_answer' not in question:
                            issues.append(f"Missing 'correct_answer' for multiple_choice question in lesson {lesson_title}, question {question_num}")
                    
                    elif question_type == 'true_false':
                        correct_answer = question.get('correct_answer', '').lower()
                        if correct_answer not in ['true', 'false']:
                            issues.append(f"Invalid correct_answer '{correct_answer}' for true_false question in lesson {lesson_title}, question {question_num}")
                    
                    elif question_type in ['short_answer', 'essay']:
                        # These should have correct_answer field (even if it's guidance)
                        if 'correct_answer' not in question:
                            issues.append(f"Missing 'correct_answer' field for {question_type} question in lesson {lesson_title}, question {question_num}")
                    
                    # Check points
                    points = question.get('points', 0)
                    if not isinstance(points, int) or points < 1:
                        issues.append(f"Invalid points {points} in lesson {lesson_title}, question {question_num}")
            
            self.validation_results['quiz_validation']['issues'] = issues
            self.validation_results['quiz_validation']['status'] = len(issues) == 0
            
            print(f"📊 Quiz Statistics:")
            print(f"   • Total lessons: {total_lessons}")
            print(f"   • Lessons with quizzes: {lessons_with_quizzes}/{total_lessons}")
            print(f"   • Total questions: {total_questions}")
            print(f"   • Average questions per quiz: {total_questions/lessons_with_quizzes:.1f}" if lessons_with_quizzes > 0 else "   • No quizzes found")
            
            if len(issues) == 0:
                print("✅ Quiz validation passed")
            else:
                print(f"❌ Quiz validation failed ({len(issues)} issues)")
                for issue in issues[:3]:
                    print(f"   • {issue}")
                if len(issues) > 3:
                    print(f"   • ... and {len(issues) - 3} more issues")
            
            return len(issues) == 0
            
        except Exception as e:
            error_msg = f"Quiz validation error: {str(e)}"
            self.validation_results['quiz_validation']['issues'].append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def validate_field_completeness(self):
        """Validate field completeness and format"""
        print(f"\n📋 VALIDATING FIELD COMPLETENESS")
        print("=" * 50)

        issues = []

        try:
            module = self.module2_data['modules'][0]

            for i, lesson in enumerate(module['lessons']):
                lesson_title = lesson.get('title', f'Lesson {i+1}')

                # Check required fields
                required_fields = {
                    'title': str,
                    'content': str,
                    'learning_objectives': str,
                    'estimated_duration': int,
                    'content_type': str,
                    'sort_order': int,
                    'is_published': bool
                }

                for field, expected_type in required_fields.items():
                    if field not in lesson:
                        issues.append(f"Missing required field '{field}' in lesson: {lesson_title}")
                    elif not isinstance(lesson[field], expected_type):
                        issues.append(f"Invalid type for '{field}' in lesson: {lesson_title} (expected {expected_type.__name__})")

                # Check optional fields format
                optional_url_fields = ['video_url', 'document_url', 'audio_url']
                for field in optional_url_fields:
                    if field in lesson and lesson[field]:
                        url = lesson[field]
                        if not isinstance(url, str) or not (url.startswith('http://') or url.startswith('https://')):
                            issues.append(f"Invalid URL format for '{field}' in lesson: {lesson_title}")

                # Check resources field
                if 'resources' in lesson:
                    if not isinstance(lesson['resources'], list):
                        issues.append(f"'resources' must be a list in lesson: {lesson_title}")

                # Check estimated_duration is reasonable
                duration = lesson.get('estimated_duration', 0)
                if duration < 5 or duration > 300:  # 5 minutes to 5 hours
                    issues.append(f"Unreasonable estimated_duration {duration} minutes in lesson: {lesson_title}")

            self.validation_results['field_completeness']['issues'] = issues
            self.validation_results['field_completeness']['status'] = len(issues) == 0

            if len(issues) == 0:
                print("✅ Field completeness validation passed")
            else:
                print(f"❌ Field completeness validation failed ({len(issues)} issues)")
                for issue in issues[:3]:
                    print(f"   • {issue}")
                if len(issues) > 3:
                    print(f"   • ... and {len(issues) - 3} more issues")

            return len(issues) == 0

        except Exception as e:
            error_msg = f"Field completeness validation error: {str(e)}"
            self.validation_results['field_completeness']['issues'].append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def simulate_import(self):
        """Simulate the import process (dry run)"""
        print(f"\n🔄 SIMULATING IMPORT PROCESS")
        print("=" * 50)

        issues = []

        try:
            # Check if Course 6 exists
            try:
                course = Course.objects.get(id=6)
                print(f"✅ Course 6 found: {course.title}")
            except Course.DoesNotExist:
                issues.append("Course 6 does not exist in database")
                return False

            # Check module sort_order conflicts
            module_data = self.module2_data['modules'][0]
            sort_order = module_data.get('sort_order', 2)

            existing_module = Module.objects.filter(course=course, sort_order=sort_order).first()
            if existing_module:
                issues.append(f"Module with sort_order {sort_order} already exists: {existing_module.title}")

            # Simulate lesson creation
            lessons_data = module_data.get('lessons', [])
            print(f"📝 Simulating import of {len(lessons_data)} lessons...")

            for i, lesson_data in enumerate(lessons_data):
                lesson_title = lesson_data.get('title', f'Lesson {i+1}')

                # Check if lesson ID conflicts (if provided)
                if 'id' in lesson_data:
                    lesson_id = lesson_data['id']
                    if Lesson.objects.filter(id=lesson_id).exists():
                        issues.append(f"Lesson ID {lesson_id} already exists")

                # Check sort_order conflicts within course
                sort_order = lesson_data.get('sort_order')
                if Lesson.objects.filter(module__course=course, sort_order=sort_order).exists():
                    issues.append(f"Lesson sort_order {sort_order} already exists in course")

                # Simulate quiz creation
                if 'assessment' in lesson_data and 'quiz' in lesson_data['assessment']:
                    quiz_data = lesson_data['assessment']['quiz']

                    if 'id' in quiz_data:
                        quiz_id = quiz_data['id']
                        if Quiz.objects.filter(id=quiz_id).exists():
                            issues.append(f"Quiz ID {quiz_id} already exists")

                    # Simulate question creation
                    questions_data = quiz_data.get('questions', [])
                    for j, question_data in enumerate(questions_data):
                        if 'id' in question_data:
                            question_id = question_data['id']
                            if Question.objects.filter(id=question_id).exists():
                                issues.append(f"Question ID {question_id} already exists")

            self.validation_results['import_simulation']['issues'] = issues
            self.validation_results['import_simulation']['status'] = len(issues) == 0

            if len(issues) == 0:
                print("✅ Import simulation passed - no conflicts detected")
            else:
                print(f"❌ Import simulation failed ({len(issues)} conflicts)")
                for issue in issues[:3]:
                    print(f"   • {issue}")
                if len(issues) > 3:
                    print(f"   • ... and {len(issues) - 3} more conflicts")

            return len(issues) == 0

        except Exception as e:
            error_msg = f"Import simulation error: {str(e)}"
            self.validation_results['import_simulation']['issues'].append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        print(f"\n📄 GENERATING VALIDATION REPORT")
        print("=" * 50)

        # Count total issues
        total_issues = sum(len(result['issues']) for result in self.validation_results.values() if isinstance(result, dict) and 'issues' in result)

        # Determine priority issues
        critical_issues = []
        warning_issues = []

        for category, result in self.validation_results.items():
            if isinstance(result, dict) and 'issues' in result:
                for issue in result['issues']:
                    if any(keyword in issue.lower() for keyword in ['missing', 'invalid', 'conflict', 'already exists']):
                        critical_issues.append(f"[{category.upper()}] {issue}")
                    else:
                        warning_issues.append(f"[{category.upper()}] {issue}")

        # Generate report content
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report_content = f"""# Module 2 JSON Validation Report

**Validation Date:** {timestamp}
**JSON File:** {self.module2_file}
**Reference File:** {self.module1_file}

## 🎯 Overall Validation Results

**Status:** {self.validation_results['overall_status']}
**Recommendation:** {self.validation_results['recommendation']}
**Total Issues:** {total_issues}

## 📊 Validation Categories

### 1. JSON Structure
- **Status:** {'✅ PASS' if self.validation_results['json_structure']['status'] else '❌ FAIL'}
- **Issues:** {len(self.validation_results['json_structure']['issues'])}

### 2. Data Integrity
- **Status:** {'✅ PASS' if self.validation_results['data_integrity']['status'] else '❌ FAIL'}
- **Issues:** {len(self.validation_results['data_integrity']['issues'])}

### 3. Content Quality
- **Status:** {'✅ PASS' if self.validation_results['content_quality']['status'] else '❌ FAIL'}
- **Issues:** {len(self.validation_results['content_quality']['issues'])}

### 4. Quiz Validation
- **Status:** {'✅ PASS' if self.validation_results['quiz_validation']['status'] else '❌ FAIL'}
- **Issues:** {len(self.validation_results['quiz_validation']['issues'])}

### 5. Field Completeness
- **Status:** {'✅ PASS' if self.validation_results['field_completeness']['status'] else '❌ FAIL'}
- **Issues:** {len(self.validation_results['field_completeness']['issues'])}

### 6. Import Simulation
- **Status:** {'✅ PASS' if self.validation_results['import_simulation']['status'] else '❌ FAIL'}
- **Issues:** {len(self.validation_results['import_simulation']['issues'])}

## 🚨 Critical Issues ({len(critical_issues)})

{chr(10).join([f"- {issue}" for issue in critical_issues[:10]]) if critical_issues else "✅ No critical issues detected"}

{f"... and {len(critical_issues) - 10} more critical issues" if len(critical_issues) > 10 else ""}

## ⚠️ Warning Issues ({len(warning_issues)})

{chr(10).join([f"- {issue}" for issue in warning_issues[:5]]) if warning_issues else "✅ No warning issues detected"}

{f"... and {len(warning_issues) - 5} more warning issues" if len(warning_issues) > 5 else ""}

## 📋 Import Readiness Checklist

- {'✅' if self.validation_results['json_structure']['status'] else '❌'} JSON structure is valid
- {'✅' if self.validation_results['data_integrity']['status'] else '❌'} No ID conflicts with existing data
- {'✅' if self.validation_results['content_quality']['status'] else '❌'} YITP styling is consistent
- {'✅' if self.validation_results['quiz_validation']['status'] else '❌'} Quiz structure is valid
- {'✅' if self.validation_results['field_completeness']['status'] else '❌'} All required fields are present
- {'✅' if self.validation_results['import_simulation']['status'] else '❌'} Import simulation successful

## 🎯 Final Recommendation

**Import Status:** {'🟢 READY FOR IMPORT' if self.validation_results['recommendation'] == 'SAFE TO IMPORT' else '🔴 NOT READY - FIXES REQUIRED'}

{f"**Required Actions:** Fix {len(critical_issues)} critical issues before import" if critical_issues else "**Status:** File is ready for production import"}

---
**Validation Status:** {'✅ SUCCESS' if self.validation_results['overall_status'] == 'PASS' else '❌ FAILED'}
"""

        # Save report
        report_filename = f"module2_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"📄 Validation report saved: {report_filename}")

        return report_filename

    def execute_validation(self):
        """Execute the complete validation process"""
        print("🔍 MODULE 2 JSON VALIDATION")
        print("=" * 60)

        # Load JSON files
        if not self.load_json_files():
            return False

        # Run all validation checks
        structure_ok = self.validate_json_structure()
        integrity_ok = self.validate_data_integrity()
        content_ok = self.validate_content_quality()
        quiz_ok = self.validate_quiz_structure()
        fields_ok = self.validate_field_completeness()
        import_ok = self.simulate_import()

        # Determine overall status
        all_passed = structure_ok and integrity_ok and content_ok and quiz_ok and fields_ok and import_ok

        if all_passed:
            self.validation_results['overall_status'] = 'PASS'
            self.validation_results['recommendation'] = 'SAFE TO IMPORT'
        else:
            self.validation_results['overall_status'] = 'FAIL'
            self.validation_results['recommendation'] = 'ISSUES MUST BE FIXED'

        # Generate detailed report
        report_file = self.generate_validation_report()

        return all_passed

if __name__ == "__main__":
    validator = Module2JSONValidator()
    success = validator.execute_validation()

    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Overall Status: {validator.validation_results['overall_status']}")
    print(f"Recommendation: {validator.validation_results['recommendation']}")

    if success:
        print(f"\n🎉 VALIDATION COMPLETED SUCCESSFULLY!")
        print(f"✅ Module 2 JSON is ready for production import")
    else:
        print(f"\n⚠️ VALIDATION COMPLETED WITH ISSUES")
        print(f"❌ Module 2 JSON requires fixes before import")
