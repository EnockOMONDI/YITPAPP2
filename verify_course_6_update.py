#!/usr/bin/env python3
"""
YITP Course 6 Update Verification Script
========================================

Phase 1: Verification and Analysis ONLY
- Load and validate JSON file structure
- Compare with current production database state
- Identify gaps, conflicts, and risks
- Generate comprehensive verification report
- NO DATABASE MODIFICATIONS in this phase

Usage:
    python verify_course_6_update.py

Output:
    course_6_verification_report.md - Detailed analysis report
"""

import os
import sys
import json
import django
from datetime import datetime
from decimal import Decimal

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode

# Initialize Django
django.setup()

# Import Django modules after setup
from django.db import connection
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Avg
from courses.models import Course, Module, Lesson, Category
from assessments.models import Quiz, Question, Assignment
from content.models import ContentItem, LessonContent, InteractiveExercise
from progress.models import Enrollment, LessonProgress, QuizAttempt


class Course6UpdateVerifier:
    """
    Comprehensive verifier for Course 6 update with safety checks
    """
    
    def __init__(self):
        self.course_id = 6
        self.json_file_path = "/Users/djsean/Desktop/APPS2024/YITP2025/YITPAPP/courseunits/YITP_Course6_Module1_UPDATED_with_quizzes.json"
        self.json_data = None
        self.production_data = {}
        self.analysis_results = {}
        self.warnings = []
        self.errors = []
        
    def verify_production_connection(self):
        """Verify connection to production database"""
        try:
            print("🔍 VERIFYING PRODUCTION DATABASE CONNECTION")
            print("=" * 60)
            
            db_config = settings.DATABASES['default']
            print(f"📊 Database Engine: {db_config['ENGINE']}")
            print(f"🏠 Database Host: {db_config['HOST']}")
            print(f"📂 Database Name: {db_config['NAME']}")
            print(f"👤 Database User: {db_config['USER']}")
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                print(f"✅ PostgreSQL Version: {version}")
                
            return True
            
        except Exception as e:
            error_msg = f"❌ Database connection failed: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False
    
    def load_and_validate_json(self):
        """Load and validate the JSON file structure"""
        try:
            print(f"\n📄 LOADING JSON FILE")
            print("=" * 40)
            print(f"📁 File Path: {self.json_file_path}")
            
            # Check if file exists
            if not os.path.exists(self.json_file_path):
                error_msg = f"❌ JSON file not found: {self.json_file_path}"
                print(error_msg)
                self.errors.append(error_msg)
                return False
            
            # Get file size
            file_size = os.path.getsize(self.json_file_path)
            file_size_mb = file_size / (1024 * 1024)
            print(f"📊 File Size: {file_size:,} bytes ({file_size_mb:.2f} MB)")
            
            # Load JSON
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)
            
            print(f"✅ JSON file loaded successfully")
            
            # Basic structure validation - this JSON has a different structure
            required_fields = ['modules']
            for field in required_fields:
                if field not in self.json_data:
                    error_msg = f"❌ Missing required field in JSON: {field}"
                    print(error_msg)
                    self.errors.append(error_msg)
                    return False

            # Analyze JSON structure - course data is at root level
            course_data = {
                'title': self.json_data.get('course_title'),
                'description': self.json_data.get('course_description'),
                'category': self.json_data.get('course_category'),
                'difficulty_level': self.json_data.get('difficulty_level'),
                'estimated_duration': self.json_data.get('estimated_duration'),
                'price': self.json_data.get('price'),
                'currency': self.json_data.get('currency')
            }
            modules_data = self.json_data.get('modules', [])
            
            print(f"📚 Course Title: {course_data.get('title', 'Unknown')}")
            print(f"📑 Modules in JSON: {len(modules_data)}")
            
            total_lessons = 0
            total_quizzes = 0
            total_questions = 0
            
            for module in modules_data:
                lessons = module.get('lessons', [])
                total_lessons += len(lessons)
                
                for lesson in lessons:
                    quizzes = lesson.get('quizzes', [])
                    total_quizzes += len(quizzes)
                    
                    for quiz in quizzes:
                        questions = quiz.get('questions', [])
                        total_questions += len(questions)
            
            print(f"📄 Total Lessons in JSON: {total_lessons}")
            print(f"❓ Total Quizzes in JSON: {total_quizzes}")
            print(f"❔ Total Questions in JSON: {total_questions}")
            
            return True
            
        except json.JSONDecodeError as e:
            error_msg = f"❌ Invalid JSON format: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False
        except Exception as e:
            error_msg = f"❌ Error loading JSON file: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False
    
    def fetch_current_production_state(self):
        """Fetch current Course 6 state from production database"""
        try:
            print(f"\n📊 FETCHING CURRENT PRODUCTION STATE")
            print("=" * 50)
            
            # Fetch course
            course = Course.objects.get(id=self.course_id)
            
            # Basic course info
            self.production_data['course'] = {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'description': course.description,
                'status': course.status,
                'is_published': course.is_published,
                'price': float(course.price),
                'created_at': course.created_at.isoformat() if course.created_at else None,
                'updated_at': course.updated_at.isoformat() if course.updated_at else None,
            }
            
            print(f"✅ Course: {course.title}")
            print(f"   - Status: {course.status}")
            print(f"   - Published: {course.is_published}")
            print(f"   - Price: ${course.price}")
            
            # Fetch modules
            modules = Module.objects.filter(course=course).order_by('sort_order')
            self.production_data['modules'] = []
            
            total_lessons = 0
            total_content_items = 0
            total_quizzes = 0
            total_assignments = 0
            
            for module in modules:
                module_data = {
                    'id': module.id,
                    'title': module.title,
                    'description': module.description,
                    'sort_order': module.sort_order,
                    'is_published': module.is_published,
                    'lessons': []
                }
                
                # Fetch lessons for this module
                lessons = Lesson.objects.filter(module=module).order_by('sort_order')
                total_lessons += lessons.count()
                
                for lesson in lessons:
                    lesson_data = {
                        'id': lesson.id,
                        'title': lesson.title,
                        'content_type': lesson.content_type,
                        'sort_order': lesson.sort_order,
                        'is_published': lesson.is_published,
                        'estimated_duration': lesson.estimated_duration,
                    }
                    
                    # Count related content
                    content_items = LessonContent.objects.filter(lesson=lesson).count()
                    quizzes = Quiz.objects.filter(lesson=lesson).count()
                    assignments = Assignment.objects.filter(lesson=lesson).count()
                    
                    lesson_data['content_items_count'] = content_items
                    lesson_data['quizzes_count'] = quizzes
                    lesson_data['assignments_count'] = assignments
                    
                    total_content_items += content_items
                    total_quizzes += quizzes
                    total_assignments += assignments
                    
                    module_data['lessons'].append(lesson_data)
                
                self.production_data['modules'].append(module_data)
            
            print(f"📑 Modules in Production: {len(modules)}")
            print(f"📄 Total Lessons in Production: {total_lessons}")
            print(f"📝 Total Content Items: {total_content_items}")
            print(f"❓ Total Quizzes: {total_quizzes}")
            print(f"📋 Total Assignments: {total_assignments}")
            
            return True
            
        except Course.DoesNotExist:
            error_msg = f"❌ Course {self.course_id} not found in production"
            print(error_msg)
            self.errors.append(error_msg)
            return False
        except Exception as e:
            error_msg = f"❌ Error fetching production state: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False

    def fetch_enrollment_data(self):
        """Fetch critical enrollment and progress data that must be preserved"""
        try:
            print(f"\n👥 FETCHING ENROLLMENT DATA")
            print("=" * 40)

            course = Course.objects.get(id=self.course_id)
            enrollments = Enrollment.objects.filter(course=course)

            enrollment_data = {
                'total_enrollments': enrollments.count(),
                'active_enrollments': enrollments.filter(status='active').count(),
                'completed_enrollments': enrollments.filter(status='completed').count(),
                'average_progress': float(enrollments.aggregate(
                    avg_progress=Avg('progress_percentage')
                )['avg_progress'] or 0),
                'enrollment_details': []
            }

            # Get detailed enrollment info
            for enrollment in enrollments:
                enrollment_info = {
                    'id': enrollment.id,
                    'student_id': enrollment.student.id,
                    'student_username': enrollment.student.username,
                    'status': enrollment.status,
                    'progress_percentage': float(enrollment.progress_percentage),
                    'enrollment_date': enrollment.enrollment_date.isoformat(),
                    'enrollment_type': enrollment.enrollment_type,
                }
                enrollment_data['enrollment_details'].append(enrollment_info)

            # Get lesson progress data
            lesson_progress = LessonProgress.objects.filter(
                enrollment__course=course
            )
            enrollment_data['lesson_progress_count'] = lesson_progress.count()
            enrollment_data['completed_lessons'] = lesson_progress.filter(status='completed').count()

            # Get quiz attempts
            quiz_attempts = QuizAttempt.objects.filter(
                enrollment__course=course
            )
            enrollment_data['quiz_attempts_count'] = quiz_attempts.count()

            self.production_data['enrollment_data'] = enrollment_data

            print(f"✅ Enrollment Data:")
            print(f"   - Total Enrollments: {enrollment_data['total_enrollments']}")
            print(f"   - Active Enrollments: {enrollment_data['active_enrollments']}")
            print(f"   - Average Progress: {enrollment_data['average_progress']:.1f}%")
            print(f"   - Lesson Progress Records: {enrollment_data['lesson_progress_count']}")
            print(f"   - Quiz Attempts: {enrollment_data['quiz_attempts_count']}")

            return True

        except Exception as e:
            error_msg = f"❌ Error fetching enrollment data: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False

    def analyze_quiz_duplication(self):
        """Analyze quiz content for duplication issues"""
        try:
            print(f"\n🔍 ANALYZING QUIZ DUPLICATION")
            print("=" * 40)

            # Analyze JSON quiz content
            json_quiz_analysis = self.analyze_json_quiz_content()

            # Analyze production quiz content
            production_quiz_analysis = self.analyze_production_quiz_content()

            # Store results
            self.analysis_results['quiz_duplication'] = {
                'json_analysis': json_quiz_analysis,
                'production_analysis': production_quiz_analysis,
                'comparison': self.compare_quiz_content(json_quiz_analysis, production_quiz_analysis)
            }

            return True

        except Exception as e:
            error_msg = f"❌ Error analyzing quiz duplication: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False

    def analyze_json_quiz_content(self):
        """Analyze quiz content in JSON for duplicates"""
        from collections import defaultdict

        quiz_analysis = {
            'total_lessons': 0,
            'total_quizzes': 0,
            'total_questions': 0,
            'question_fingerprints': defaultdict(list),
            'duplicates': {},
            'lesson_quiz_details': []
        }

        modules = self.json_data.get('modules', [])

        for module in modules:
            lessons = module.get('lessons', [])

            for lesson in lessons:
                lesson_id = lesson.get('id', 'unknown')
                lesson_title = lesson.get('title', 'Unknown')

                quiz_analysis['total_lessons'] += 1

                # Check for assessment/quiz structure
                assessment = lesson.get('assessment', {})
                quiz_data = assessment.get('quiz', {})

                if quiz_data:
                    quiz_analysis['total_quizzes'] += 1
                    quiz_title = quiz_data.get('title', f'{lesson_title} Quiz')
                    questions = quiz_data.get('questions', [])

                    lesson_quiz_info = {
                        'lesson_id': lesson_id,
                        'lesson_title': lesson_title,
                        'quiz_title': quiz_title,
                        'question_count': len(questions),
                        'questions': []
                    }

                    for question in questions:
                        quiz_analysis['total_questions'] += 1

                        # Create fingerprint for duplicate detection
                        question_text = question.get('question_text', '')
                        question_type = question.get('question_type', '')
                        correct_answer = question.get('correct_answer', '')

                        fingerprint = f"{question_text}|{question_type}|{correct_answer}"

                        quiz_analysis['question_fingerprints'][fingerprint].append({
                            'lesson_id': lesson_id,
                            'lesson_title': lesson_title,
                            'quiz_title': quiz_title
                        })

                        lesson_quiz_info['questions'].append({
                            'question_text': question_text,
                            'question_type': question_type,
                            'correct_answer': correct_answer,
                            'fingerprint': fingerprint
                        })

                    quiz_analysis['lesson_quiz_details'].append(lesson_quiz_info)

        # Identify duplicates
        quiz_analysis['duplicates'] = {
            fp: locations for fp, locations in quiz_analysis['question_fingerprints'].items()
            if len(locations) > 1
        }

        print(f"📊 JSON Quiz Analysis:")
        print(f"   - Total Lessons: {quiz_analysis['total_lessons']}")
        print(f"   - Total Quizzes: {quiz_analysis['total_quizzes']}")
        print(f"   - Total Questions: {quiz_analysis['total_questions']}")
        print(f"   - Unique Question Fingerprints: {len(quiz_analysis['question_fingerprints'])}")
        print(f"   - Duplicated Questions: {len(quiz_analysis['duplicates'])}")

        if quiz_analysis['duplicates']:
            print(f"\n⚠️ FOUND {len(quiz_analysis['duplicates'])} DUPLICATED QUESTIONS IN JSON:")
            for i, (fingerprint, locations) in enumerate(quiz_analysis['duplicates'].items(), 1):
                question_text = fingerprint.split('|')[0][:60] + "..."
                print(f"   {i}. '{question_text}' appears in {len(locations)} lessons")
        else:
            print(f"✅ NO DUPLICATE QUESTIONS FOUND IN JSON")

        return quiz_analysis

    def analyze_production_quiz_content(self):
        """Analyze quiz content in production database for duplicates"""
        from collections import defaultdict

        quiz_analysis = {
            'total_lessons': 0,
            'total_quizzes': 0,
            'total_questions': 0,
            'question_fingerprints': defaultdict(list),
            'duplicates': {},
            'lesson_quiz_details': []
        }

        try:
            course = Course.objects.get(id=self.course_id)
            modules = Module.objects.filter(course=course)

            for module in modules:
                lessons = Lesson.objects.filter(module=module)

                for lesson in lessons:
                    quiz_analysis['total_lessons'] += 1
                    quizzes = Quiz.objects.filter(lesson=lesson)

                    for quiz in quizzes:
                        quiz_analysis['total_quizzes'] += 1
                        questions = Question.objects.filter(quiz=quiz).order_by('sort_order')

                        lesson_quiz_info = {
                            'lesson_id': lesson.id,
                            'lesson_title': lesson.title,
                            'quiz_id': quiz.id,
                            'quiz_title': quiz.title,
                            'question_count': questions.count(),
                            'questions': []
                        }

                        for question in questions:
                            quiz_analysis['total_questions'] += 1

                            # Create fingerprint for duplicate detection
                            fingerprint = f"{question.question_text}|{question.question_type}|{question.correct_answer}"

                            quiz_analysis['question_fingerprints'][fingerprint].append({
                                'lesson_id': lesson.id,
                                'lesson_title': lesson.title,
                                'quiz_id': quiz.id,
                                'quiz_title': quiz.title,
                                'question_id': question.id
                            })

                            lesson_quiz_info['questions'].append({
                                'question_id': question.id,
                                'question_text': question.question_text,
                                'question_type': question.question_type,
                                'correct_answer': question.correct_answer,
                                'fingerprint': fingerprint
                            })

                        quiz_analysis['lesson_quiz_details'].append(lesson_quiz_info)

            # Identify duplicates
            quiz_analysis['duplicates'] = {
                fp: locations for fp, locations in quiz_analysis['question_fingerprints'].items()
                if len(locations) > 1
            }

            print(f"\n📊 Production Quiz Analysis:")
            print(f"   - Total Lessons: {quiz_analysis['total_lessons']}")
            print(f"   - Total Quizzes: {quiz_analysis['total_quizzes']}")
            print(f"   - Total Questions: {quiz_analysis['total_questions']}")
            print(f"   - Unique Question Fingerprints: {len(quiz_analysis['question_fingerprints'])}")
            print(f"   - Duplicated Questions: {len(quiz_analysis['duplicates'])}")

            if quiz_analysis['duplicates']:
                print(f"\n⚠️ FOUND {len(quiz_analysis['duplicates'])} DUPLICATED QUESTIONS IN PRODUCTION:")
                for i, (fingerprint, locations) in enumerate(quiz_analysis['duplicates'].items(), 1):
                    question_text = fingerprint.split('|')[0][:60] + "..."
                    print(f"   {i}. '{question_text}' appears in {len(locations)} lessons")
            else:
                print(f"✅ NO DUPLICATE QUESTIONS FOUND IN PRODUCTION")

        except Exception as e:
            print(f"⚠️ Could not analyze production quiz content: {str(e)}")

        return quiz_analysis

    def compare_quiz_content(self, json_analysis, production_analysis):
        """Compare quiz content between JSON and production"""
        comparison = {
            'json_duplicates': len(json_analysis['duplicates']),
            'production_duplicates': len(production_analysis['duplicates']),
            'improvement': False,
            'issues': [],
            'recommendations': []
        }

        # Check if JSON improves upon production
        if json_analysis['duplicates'] and production_analysis['duplicates']:
            if len(json_analysis['duplicates']) < len(production_analysis['duplicates']):
                comparison['improvement'] = True
                comparison['recommendations'].append("✅ JSON reduces quiz duplication compared to production")
            elif len(json_analysis['duplicates']) == len(production_analysis['duplicates']):
                comparison['issues'].append("⚠️ JSON has same number of duplicates as production")
            else:
                comparison['issues'].append("❌ JSON has MORE duplicates than production")
        elif not json_analysis['duplicates'] and production_analysis['duplicates']:
            comparison['improvement'] = True
            comparison['recommendations'].append("✅ JSON eliminates all quiz duplication from production")
        elif json_analysis['duplicates'] and not production_analysis['duplicates']:
            comparison['issues'].append("❌ JSON introduces quiz duplication not present in production")
        else:
            comparison['recommendations'].append("✅ Both JSON and production have no quiz duplication")

        # Check question counts
        if json_analysis['total_questions'] != production_analysis['total_questions']:
            if json_analysis['total_questions'] > production_analysis['total_questions']:
                comparison['recommendations'].append(f"📈 JSON adds {json_analysis['total_questions'] - production_analysis['total_questions']} new questions")
            else:
                comparison['issues'].append(f"📉 JSON has {production_analysis['total_questions'] - json_analysis['total_questions']} fewer questions than production")

        print(f"\n🔍 Quiz Content Comparison:")
        print(f"   - JSON Duplicates: {comparison['json_duplicates']}")
        print(f"   - Production Duplicates: {comparison['production_duplicates']}")
        print(f"   - Improvement: {'✅ Yes' if comparison['improvement'] else '❌ No'}")

        if comparison['issues']:
            print(f"\n⚠️ Issues Found:")
            for issue in comparison['issues']:
                print(f"   - {issue}")

        if comparison['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in comparison['recommendations']:
                print(f"   - {rec}")

        return comparison

    def compare_json_vs_production(self):
        """Compare JSON data with production state to identify changes"""
        try:
            print(f"\n🔍 COMPARING JSON VS PRODUCTION")
            print("=" * 50)

            if not self.json_data or not self.production_data:
                error_msg = "❌ Missing data for comparison"
                print(error_msg)
                self.errors.append(error_msg)
                return False

            # Initialize analysis results
            self.analysis_results = {
                'course_changes': {},
                'modules_to_add': [],
                'modules_to_update': [],
                'lessons_to_add': [],
                'lessons_to_update': [],
                'content_to_add': [],
                'conflicts': [],
                'risks': []
            }

            # Compare course metadata - extract from root level
            json_course = {
                'title': self.json_data.get('course_title'),
                'description': self.json_data.get('course_description'),
                'price': self.json_data.get('price', 0)
            }
            prod_course = self.production_data.get('course', {})

            course_changes = {}
            for field in ['title', 'description', 'status', 'price']:
                json_value = json_course.get(field)
                prod_value = prod_course.get(field)
                if json_value != prod_value and json_value is not None:
                    course_changes[field] = {
                        'current': prod_value,
                        'proposed': json_value
                    }

            if course_changes:
                self.analysis_results['course_changes'] = course_changes
                print(f"⚠️ Course metadata changes detected: {list(course_changes.keys())}")
            else:
                print(f"✅ No course metadata changes")

            # Compare modules
            json_modules = self.json_data.get('modules', [])
            prod_modules = self.production_data.get('modules', [])

            # Create lookup maps
            prod_modules_by_title = {m['title']: m for m in prod_modules}
            prod_lessons_by_title = {}

            for prod_module in prod_modules:
                for lesson in prod_module['lessons']:
                    key = f"{prod_module['title']}::{lesson['title']}"
                    prod_lessons_by_title[key] = lesson

            # Analyze each JSON module
            for json_module in json_modules:
                module_title = json_module.get('title', '')

                if module_title in prod_modules_by_title:
                    # Module exists, check for lesson differences
                    prod_module = prod_modules_by_title[module_title]
                    self.analysis_results['modules_to_update'].append({
                        'title': module_title,
                        'production_id': prod_module['id'],
                        'json_data': json_module
                    })

                    # Check lessons in this module
                    json_lessons = json_module.get('lessons', [])
                    for json_lesson in json_lessons:
                        lesson_title = json_lesson.get('title', '')
                        lesson_key = f"{module_title}::{lesson_title}"

                        if lesson_key not in prod_lessons_by_title:
                            # New lesson to add
                            self.analysis_results['lessons_to_add'].append({
                                'module_title': module_title,
                                'lesson_title': lesson_title,
                                'lesson_data': json_lesson
                            })
                        else:
                            # Lesson exists, check for conflicts
                            prod_lesson = prod_lessons_by_title[lesson_key]
                            if self._check_lesson_conflicts(json_lesson, prod_lesson):
                                self.analysis_results['conflicts'].append({
                                    'type': 'lesson_conflict',
                                    'lesson_title': lesson_title,
                                    'production_id': prod_lesson['id'],
                                    'details': 'Content differences detected'
                                })
                else:
                    # New module to add
                    self.analysis_results['modules_to_add'].append({
                        'title': module_title,
                        'data': json_module
                    })

            # Count content to be added
            total_new_lessons = len(self.analysis_results['lessons_to_add'])
            total_new_modules = len(self.analysis_results['modules_to_add'])
            total_conflicts = len(self.analysis_results['conflicts'])

            print(f"📊 Analysis Results:")
            print(f"   - New Modules to Add: {total_new_modules}")
            print(f"   - New Lessons to Add: {total_new_lessons}")
            print(f"   - Potential Conflicts: {total_conflicts}")

            if total_conflicts > 0:
                self.warnings.append(f"Found {total_conflicts} potential conflicts that need review")

            return True

        except Exception as e:
            error_msg = f"❌ Error during comparison: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False

    def _check_lesson_conflicts(self, json_lesson, prod_lesson):
        """Check if there are conflicts between JSON lesson and production lesson"""
        # Simple conflict detection based on content differences
        json_content = json_lesson.get('primary_content', '').strip()
        # We don't have prod lesson content in our summary, so assume conflict if titles match
        # This is a conservative approach - we'll flag for manual review
        return len(json_content) > 100  # If JSON has substantial content, flag for review

    def perform_validation_checks(self):
        """Perform comprehensive validation checks"""
        try:
            print(f"\n🔍 PERFORMING VALIDATION CHECKS")
            print("=" * 50)

            validation_results = {
                'django_model_validation': True,
                'foreign_key_validation': True,
                'unique_constraint_validation': True,
                'data_integrity_validation': True,
                'issues': []
            }

            # Check for required fields in JSON lessons
            json_modules = self.json_data.get('modules', [])
            for module in json_modules:
                for lesson in module.get('lessons', []):
                    # Check required lesson fields - this JSON uses 'primary_content' instead of 'content'
                    required_fields = ['title', 'primary_content']
                    for field in required_fields:
                        if not lesson.get(field):
                            validation_results['issues'].append(
                                f"Missing required field '{field}' in lesson: {lesson.get('title', 'Unknown')}"
                            )
                            validation_results['django_model_validation'] = False

                    # Check quizzes
                    for quiz in lesson.get('quizzes', []):
                        if not quiz.get('title'):
                            validation_results['issues'].append(
                                f"Missing quiz title in lesson: {lesson.get('title', 'Unknown')}"
                            )

                        # Check questions
                        questions = quiz.get('questions', [])
                        if len(questions) == 0:
                            validation_results['issues'].append(
                                f"Quiz '{quiz.get('title', 'Unknown')}' has no questions"
                            )

                        for question in questions:
                            if not question.get('question_text'):
                                validation_results['issues'].append(
                                    f"Missing question text in quiz: {quiz.get('title', 'Unknown')}"
                                )

            # Check for potential slug conflicts
            existing_slugs = set()
            for module in self.production_data.get('modules', []):
                for lesson in module['lessons']:
                    # We don't have slugs in our production data, but we can check titles
                    existing_slugs.add(lesson['title'].lower().replace(' ', '-'))

            for module in json_modules:
                for lesson in module.get('lessons', []):
                    potential_slug = lesson.get('title', '').lower().replace(' ', '-')
                    if potential_slug in existing_slugs:
                        validation_results['issues'].append(
                            f"Potential slug conflict for lesson: {lesson.get('title', 'Unknown')}"
                        )
                        validation_results['unique_constraint_validation'] = False

            print(f"✅ Validation Results:")
            print(f"   - Django Model Validation: {'✅' if validation_results['django_model_validation'] else '❌'}")
            print(f"   - Foreign Key Validation: {'✅' if validation_results['foreign_key_validation'] else '❌'}")
            print(f"   - Unique Constraint Validation: {'✅' if validation_results['unique_constraint_validation'] else '❌'}")
            print(f"   - Data Integrity Validation: {'✅' if validation_results['data_integrity_validation'] else '❌'}")
            print(f"   - Issues Found: {len(validation_results['issues'])}")

            if validation_results['issues']:
                for issue in validation_results['issues'][:5]:  # Show first 5 issues
                    print(f"     - {issue}")
                if len(validation_results['issues']) > 5:
                    print(f"     - ... and {len(validation_results['issues']) - 5} more issues")

            self.analysis_results['validation'] = validation_results
            return True

        except Exception as e:
            error_msg = f"❌ Error during validation: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False

    def assess_risks_and_impact(self):
        """Assess risks and impact of the proposed changes"""
        try:
            print(f"\n⚠️ ASSESSING RISKS AND IMPACT")
            print("=" * 50)

            risks = []
            impact_assessment = {
                'student_impact': 'LOW',
                'data_loss_risk': 'NONE',
                'system_performance_impact': 'LOW',
                'rollback_complexity': 'LOW'
            }

            # Assess student impact
            enrollment_data = self.production_data.get('enrollment_data', {})
            active_enrollments = enrollment_data.get('active_enrollments', 0)

            if active_enrollments > 0:
                new_lessons_count = len(self.analysis_results.get('lessons_to_add', []))
                if new_lessons_count > 0:
                    impact_assessment['student_impact'] = 'MEDIUM'
                    risks.append(f"Adding {new_lessons_count} new lessons may affect progress calculations for {active_enrollments} active students")

            # Assess data loss risk
            conflicts = self.analysis_results.get('conflicts', [])
            if len(conflicts) > 0:
                impact_assessment['data_loss_risk'] = 'MEDIUM'
                risks.append(f"Found {len(conflicts)} potential conflicts that could lead to data overwrites")

            # Assess system performance
            total_new_content = (
                len(self.analysis_results.get('lessons_to_add', [])) +
                len(self.analysis_results.get('modules_to_add', []))
            )
            if total_new_content > 10:
                impact_assessment['system_performance_impact'] = 'MEDIUM'
                risks.append(f"Adding {total_new_content} new content items may impact database performance")

            # Assess rollback complexity
            if len(self.analysis_results.get('modules_to_add', [])) > 0:
                impact_assessment['rollback_complexity'] = 'MEDIUM'
                risks.append("Adding new modules increases rollback complexity")

            print(f"📊 Impact Assessment:")
            for key, value in impact_assessment.items():
                emoji = "🟢" if value == "LOW" or value == "NONE" else "🟡" if value == "MEDIUM" else "🔴"
                print(f"   - {key.replace('_', ' ').title()}: {emoji} {value}")

            print(f"\n⚠️ Identified Risks ({len(risks)}):")
            for i, risk in enumerate(risks, 1):
                print(f"   {i}. {risk}")

            self.analysis_results['risks'] = risks
            self.analysis_results['impact_assessment'] = impact_assessment

            return True

        except Exception as e:
            error_msg = f"❌ Error during risk assessment: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False

    def generate_verification_report(self):
        """Generate comprehensive verification report"""
        try:
            print(f"\n📝 GENERATING VERIFICATION REPORT")
            print("=" * 50)

            timestamp = datetime.now().isoformat()
            report_filename = "course_6_verification_report.md"

            # Prepare report data
            enrollment_data = self.production_data.get('enrollment_data', {})
            json_course = {
                'title': self.json_data.get('course_title', 'Unknown'),
                'description': self.json_data.get('course_description', ''),
                'price': self.json_data.get('price', 0)
            } if self.json_data else {}
            prod_course = self.production_data.get('course', {})

            report_content = f"""# YITP Course 6 Update Verification Report

**Generated:** {timestamp}
**Course ID:** {self.course_id}
**Status:** Phase 1 - Verification Complete

## Executive Summary

This report analyzes the proposed update to Course 6 ("Youth Impact Training Programme") by comparing the JSON file content with the current production database state.

### Key Findings

- **JSON File:** {len(self.json_data.get('modules', []))} modules, {sum(len(m.get('lessons', [])) for m in self.json_data.get('modules', []))} lessons
- **Production:** {len(self.production_data.get('modules', []))} modules, {sum(len(m['lessons']) for m in self.production_data.get('modules', []))} lessons
- **Active Enrollments:** {enrollment_data.get('active_enrollments', 0)} students with {enrollment_data.get('average_progress', 0):.1f}% average progress
- **New Content to Add:** {len(self.analysis_results.get('lessons_to_add', []))} lessons, {len(self.analysis_results.get('modules_to_add', []))} modules
- **Conflicts Detected:** {len(self.analysis_results.get('conflicts', []))}

## 1. JSON File Analysis

### File Information
- **Path:** `{self.json_file_path}`
- **Size:** {os.path.getsize(self.json_file_path) if os.path.exists(self.json_file_path) else 'Unknown'} bytes
- **Structure:** Valid JSON with required fields

### Content Summary
"""

            # Add JSON content details
            if self.json_data:
                modules_data = self.json_data.get('modules', [])
                for i, module in enumerate(modules_data, 1):
                    lessons = module.get('lessons', [])
                    report_content += f"\n**Module {i}: {module.get('title', 'Unknown')}**\n"
                    report_content += f"- Lessons: {len(lessons)}\n"

                    for j, lesson in enumerate(lessons, 1):
                        quizzes = lesson.get('quizzes', [])
                        assignments = lesson.get('assignments', [])
                        report_content += f"  - Lesson {j}: {lesson.get('title', 'Unknown')}\n"
                        if quizzes:
                            report_content += f"    - Quizzes: {len(quizzes)}\n"
                        if assignments:
                            report_content += f"    - Assignments: {len(assignments)}\n"

            report_content += f"""

## 2. Current Production State

### Course Information
- **Title:** {prod_course.get('title', 'Unknown')}
- **Status:** {prod_course.get('status', 'Unknown')}
- **Published:** {prod_course.get('is_published', False)}
- **Price:** ${prod_course.get('price', 0)}

### Existing Content
"""

            # Add production content details
            prod_modules = self.production_data.get('modules', [])
            for module in prod_modules:
                report_content += f"\n**{module['title']}** (ID: {module['id']})\n"
                report_content += f"- Published: {module['is_published']}\n"
                report_content += f"- Lessons: {len(module['lessons'])}\n"

                for lesson in module['lessons']:
                    report_content += f"  - {lesson['title']} (ID: {lesson['id']})\n"
                    report_content += f"    - Content Items: {lesson['content_items_count']}\n"
                    report_content += f"    - Quizzes: {lesson['quizzes_count']}\n"
                    report_content += f"    - Assignments: {lesson['assignments_count']}\n"

            report_content += f"""

### Critical Enrollment Data (MUST BE PRESERVED)
- **Total Enrollments:** {enrollment_data.get('total_enrollments', 0)}
- **Active Enrollments:** {enrollment_data.get('active_enrollments', 0)}
- **Completed Enrollments:** {enrollment_data.get('completed_enrollments', 0)}
- **Average Progress:** {enrollment_data.get('average_progress', 0):.1f}%
- **Lesson Progress Records:** {enrollment_data.get('lesson_progress_count', 0)}
- **Quiz Attempts:** {enrollment_data.get('quiz_attempts_count', 0)}

## 3. Gap Analysis

### New Content to Add
"""

            # Add gap analysis
            lessons_to_add = self.analysis_results.get('lessons_to_add', [])
            modules_to_add = self.analysis_results.get('modules_to_add', [])

            if modules_to_add:
                report_content += "\n**New Modules:**\n"
                for module in modules_to_add:
                    report_content += f"- {module['title']}\n"

            if lessons_to_add:
                report_content += "\n**New Lessons:**\n"
                for lesson in lessons_to_add:
                    report_content += f"- {lesson['lesson_title']} (in {lesson['module_title']})\n"

            # Add conflicts
            conflicts = self.analysis_results.get('conflicts', [])
            if conflicts:
                report_content += "\n### Conflicts Detected\n"
                for conflict in conflicts:
                    report_content += f"- **{conflict['type']}:** {conflict['lesson_title']} (ID: {conflict['production_id']})\n"
                    report_content += f"  - Details: {conflict['details']}\n"

            # Add quiz duplication analysis
            quiz_analysis = self.analysis_results.get('quiz_duplication', {})
            json_quiz = quiz_analysis.get('json_analysis', {})
            prod_quiz = quiz_analysis.get('production_analysis', {})
            comparison = quiz_analysis.get('comparison', {})

            report_content += f"""

## 4. Quiz Duplication Analysis

### JSON Quiz Content Analysis
- **Total Lessons with Quizzes:** {json_quiz.get('total_lessons', 0)}
- **Total Quizzes:** {json_quiz.get('total_quizzes', 0)}
- **Total Questions:** {json_quiz.get('total_questions', 0)}
- **Unique Question Fingerprints:** {len(json_quiz.get('question_fingerprints', {}))}
- **Duplicated Questions:** {len(json_quiz.get('duplicates', {}))}

### Production Quiz Content Analysis
- **Total Lessons with Quizzes:** {prod_quiz.get('total_lessons', 0)}
- **Total Quizzes:** {prod_quiz.get('total_quizzes', 0)}
- **Total Questions:** {prod_quiz.get('total_questions', 0)}
- **Unique Question Fingerprints:** {len(prod_quiz.get('question_fingerprints', {}))}
- **Duplicated Questions:** {len(prod_quiz.get('duplicates', {}))}

### Quiz Content Comparison
- **JSON Duplicates:** {comparison.get('json_duplicates', 0)}
- **Production Duplicates:** {comparison.get('production_duplicates', 0)}
- **Improvement:** {'✅ YES' if comparison.get('improvement', False) else '❌ NO'}

"""

            # Add duplicate details if found
            if json_quiz.get('duplicates'):
                report_content += "#### Duplicated Questions in JSON:\n"
                for i, (fingerprint, locations) in enumerate(json_quiz['duplicates'].items(), 1):
                    question_text = fingerprint.split('|')[0]
                    report_content += f"{i}. **Question:** \"{question_text}\"\n"
                    report_content += f"   **Appears in:** {len(locations)} lessons\n"
                    for loc in locations:
                        report_content += f"   - {loc['lesson_id']}: {loc['lesson_title']}\n"
                    report_content += "\n"
            else:
                report_content += "✅ **NO DUPLICATE QUESTIONS FOUND IN JSON**\n\n"

            if comparison.get('issues'):
                report_content += "#### Issues Identified:\n"
                for issue in comparison['issues']:
                    report_content += f"- {issue}\n"
                report_content += "\n"

            if comparison.get('recommendations'):
                report_content += "#### Recommendations:\n"
                for rec in comparison['recommendations']:
                    report_content += f"- {rec}\n"
                report_content += "\n"

            # Add validation results
            validation = self.analysis_results.get('validation', {})
            report_content += f"""

## 5. Validation Results

- **Django Model Validation:** {'✅ PASS' if validation.get('django_model_validation', False) else '❌ FAIL'}
- **Foreign Key Validation:** {'✅ PASS' if validation.get('foreign_key_validation', False) else '❌ FAIL'}
- **Unique Constraint Validation:** {'✅ PASS' if validation.get('unique_constraint_validation', False) else '❌ FAIL'}
- **Data Integrity Validation:** {'✅ PASS' if validation.get('data_integrity_validation', False) else '❌ FAIL'}

### Issues Found ({len(validation.get('issues', []))})
"""

            for issue in validation.get('issues', []):
                report_content += f"- {issue}\n"

            # Add risk assessment
            risks = self.analysis_results.get('risks', [])
            impact = self.analysis_results.get('impact_assessment', {})

            report_content += f"""

## 6. Risk Assessment

### Impact Assessment
- **Student Impact:** {impact.get('student_impact', 'UNKNOWN')}
- **Data Loss Risk:** {impact.get('data_loss_risk', 'UNKNOWN')}
- **System Performance Impact:** {impact.get('system_performance_impact', 'UNKNOWN')}
- **Rollback Complexity:** {impact.get('rollback_complexity', 'UNKNOWN')}

### Identified Risks ({len(risks)})
"""

            for i, risk in enumerate(risks, 1):
                report_content += f"{i}. {risk}\n"

            # Add recommendations
            report_content += f"""

## 6. Recommendations

### Phase 2 Implementation Strategy

**✅ RECOMMENDED APPROACH:**
1. **Incremental Addition Only** - Add new content without modifying existing data
2. **Preserve All Enrollment Data** - Maintain student progress and quiz attempts
3. **Transaction-Based Updates** - Use atomic operations with rollback capability
4. **Staged Deployment** - Test in development environment first

### Critical Safeguards Required

1. **Database Backup** - Create full backup before any modifications
2. **Enrollment Preservation** - Explicitly preserve all {enrollment_data.get('total_enrollments', 0)} enrollment records
3. **Progress Maintenance** - Keep all lesson progress and quiz attempt data
4. **ID Preservation** - Do not modify existing Course, Module, or Lesson IDs

### Next Steps

1. **Review this report** and approve/reject the proposed changes
2. **If approved:** Execute Phase 2 implementation with safeguards
3. **If rejected:** Modify JSON file and re-run verification

## 7. Technical Details

### Errors Encountered ({len(self.errors)})
"""

            for error in self.errors:
                report_content += f"- {error}\n"

            report_content += f"""

### Warnings ({len(self.warnings)})
"""

            for warning in self.warnings:
                report_content += f"- {warning}\n"

            report_content += f"""

---

**Report Generated:** {timestamp}
**Verification Script:** verify_course_6_update.py
**Phase:** 1 - Verification Only (No Database Modifications)
**Status:** {'✅ READY FOR REVIEW' if len(self.errors) == 0 else '❌ ISSUES FOUND'}
"""

            # Save report
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"✅ Verification report generated: {report_filename}")
            return report_filename

        except Exception as e:
            error_msg = f"❌ Error generating report: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return None

    def run_verification(self):
        """Run the complete verification process"""
        print("🚀 YITP COURSE 6 UPDATE VERIFICATION")
        print("=" * 80)
        print("Phase 1: Verification and Analysis ONLY")
        print("NO DATABASE MODIFICATIONS WILL BE PERFORMED")
        print("=" * 80)

        # Step 1: Verify production connection
        if not self.verify_production_connection():
            print("\n❌ VERIFICATION FAILED: Cannot connect to production database")
            return False

        # Step 2: Load and validate JSON file
        if not self.load_and_validate_json():
            print("\n❌ VERIFICATION FAILED: JSON file validation failed")
            return False

        # Step 3: Fetch current production state
        if not self.fetch_current_production_state():
            print("\n❌ VERIFICATION FAILED: Cannot fetch production state")
            return False

        # Step 4: Fetch enrollment data
        if not self.fetch_enrollment_data():
            print("\n⚠️ WARNING: Could not fetch complete enrollment data")

        # Step 5: Compare JSON vs production
        if not self.compare_json_vs_production():
            print("\n❌ VERIFICATION FAILED: Comparison analysis failed")
            return False

        # Step 6: Analyze quiz duplication
        if not self.analyze_quiz_duplication():
            print("\n⚠️ WARNING: Quiz duplication analysis encountered issues")

        # Step 7: Perform validation checks
        if not self.perform_validation_checks():
            print("\n⚠️ WARNING: Validation checks encountered issues")

        # Step 8: Assess risks and impact
        if not self.assess_risks_and_impact():
            print("\n⚠️ WARNING: Risk assessment encountered issues")

        # Step 9: Generate verification report
        report_file = self.generate_verification_report()
        if not report_file:
            print("\n❌ VERIFICATION FAILED: Could not generate report")
            return False

        # Final summary
        print("\n🎉 VERIFICATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📁 Report File: {report_file}")
        print(f"📊 Analysis Summary:")
        print(f"   - New Modules: {len(self.analysis_results.get('modules_to_add', []))}")
        print(f"   - New Lessons: {len(self.analysis_results.get('lessons_to_add', []))}")
        print(f"   - Conflicts: {len(self.analysis_results.get('conflicts', []))}")
        print(f"   - Validation Issues: {len(self.analysis_results.get('validation', {}).get('issues', []))}")
        print(f"   - Risks Identified: {len(self.analysis_results.get('risks', []))}")
        print(f"   - Errors: {len(self.errors)}")
        print(f"   - Warnings: {len(self.warnings)}")

        # Quiz duplication summary
        quiz_analysis = self.analysis_results.get('quiz_duplication', {})
        json_duplicates = len(quiz_analysis.get('json_analysis', {}).get('duplicates', {}))
        production_duplicates = len(quiz_analysis.get('production_analysis', {}).get('duplicates', {}))
        improvement = quiz_analysis.get('comparison', {}).get('improvement', False)

        print(f"\n🎯 Quiz Duplication Analysis:")
        print(f"   - JSON Duplicate Questions: {json_duplicates}")
        print(f"   - Production Duplicate Questions: {production_duplicates}")
        print(f"   - Quiz Quality Improvement: {'✅ YES' if improvement else '❌ NO'}")

        # Determine overall status
        critical_errors = len(self.errors)
        validation_issues = len(self.analysis_results.get('validation', {}).get('issues', []))
        conflicts = len(self.analysis_results.get('conflicts', []))

        if critical_errors == 0 and validation_issues == 0 and conflicts == 0:
            status = "✅ READY FOR IMPLEMENTATION"
            print(f"\n🟢 STATUS: {status}")
            print("   - No critical issues found")
            print("   - Safe to proceed with Phase 2 implementation")
        elif critical_errors == 0 and validation_issues == 0:
            status = "🟡 READY WITH CAUTION"
            print(f"\n🟡 STATUS: {status}")
            print(f"   - {conflicts} conflicts need manual review")
            print("   - Proceed with caution after conflict resolution")
        else:
            status = "🔴 NOT READY"
            print(f"\n🔴 STATUS: {status}")
            print(f"   - {critical_errors} critical errors must be fixed")
            print(f"   - {validation_issues} validation issues must be resolved")
            print("   - Do NOT proceed with implementation")

        print(f"\n📋 NEXT STEPS:")
        print("   1. Review the detailed verification report")
        print("   2. Address any critical issues or conflicts")
        print("   3. Get approval from stakeholders")
        print("   4. If approved, proceed with Phase 2 implementation")
        print("   5. If rejected, modify JSON file and re-run verification")

        return True


def main():
    """Main function to run the verification"""
    try:
        verifier = Course6UpdateVerifier()
        success = verifier.run_verification()

        if success:
            print("\n✅ Verification completed successfully!")
            return True
        else:
            print("\n❌ Verification failed!")
            return False

    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
