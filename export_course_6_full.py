#!/usr/bin/env python3
"""
YITP Course 6 Full Export Script
=================================

This script connects to the YITP production database (Supabase PostgreSQL) and exports
the complete course record for Course ID 6 ("Youth Impact Training Programme (YITP)"),
including all related data needed for a full course export.

Features:
- Complete course metadata and relationships
- All modules, lessons, content items, quizzes, assignments
- Enrollment and engagement statistics
- JSON export compatible with YITP import workflow
- Production database connection with proper error handling

Usage:
    python export_course_6_full.py

Output:
    course_6_full_export.json - Complete course export in JSON format
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
from progress.models import Enrollment


class Course6FullExporter:
    """
    Comprehensive exporter for Course ID 6 with all related data
    """
    
    def __init__(self):
        self.course_id = 6
        self.export_data = {}
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
    
    def fetch_course_metadata(self):
        """Fetch complete course metadata"""
        try:
            print(f"\n📚 FETCHING COURSE {self.course_id} METADATA")
            print("=" * 50)
            
            course = Course.objects.get(id=self.course_id)
            
            # Basic course data
            course_data = {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'description': course.description,
                'learning_objectives': course.learning_objectives,
                'prerequisites': course.prerequisites,
                'difficulty_level': course.difficulty_level,
                'estimated_duration': course.estimated_duration,
                'price': float(course.price) if course.price else 0.0,
                'thumbnail': course.thumbnail.url if course.thumbnail else None,
                'status': course.status,
                'is_published': course.is_published,
                'is_featured': course.is_featured,
                'enrollment_limit': course.enrollment_limit,
                'submitted_for_review_at': course.submitted_for_review_at.isoformat() if course.submitted_for_review_at else None,
                'reviewed_at': course.reviewed_at.isoformat() if course.reviewed_at else None,
                'reviewed_by': {
                    'id': course.reviewed_by.id,
                    'username': course.reviewed_by.username,
                    'full_name': course.reviewed_by.get_full_name() or course.reviewed_by.username,
                } if course.reviewed_by else None,
                'review_notes': course.review_notes,
                'created_at': course.created_at.isoformat() if course.created_at else None,
                'updated_at': course.updated_at.isoformat() if course.updated_at else None,
            }
            
            # Instructor details
            if course.instructor:
                instructor = course.instructor
                course_data['instructor'] = {
                    'id': instructor.id,
                    'username': instructor.username,
                    'email': instructor.email,
                    'first_name': instructor.first_name,
                    'last_name': instructor.last_name,
                    'full_name': instructor.get_full_name() or instructor.username,
                    'date_joined': instructor.date_joined.isoformat() if instructor.date_joined else None,
                }
            else:
                course_data['instructor'] = None
            
            # Category details
            if course.category:
                category = course.category
                course_data['category'] = {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'created_at': category.created_at.isoformat() if hasattr(category, 'created_at') and category.created_at else None,
                }
            else:
                course_data['category'] = None
            
            self.export_data.update(course_data)
            
            print(f"✅ Course metadata fetched: {course.title}")
            print(f"   - Instructor: {course_data['instructor']['full_name'] if course_data['instructor'] else 'None'}")
            print(f"   - Category: {course_data['category']['name'] if course_data['category'] else 'None'}")
            print(f"   - Status: {course.status}")
            print(f"   - Published: {course.is_published}")
            
            return True
            
        except Course.DoesNotExist:
            error_msg = f"❌ Course with ID {self.course_id} not found"
            print(error_msg)
            self.errors.append(error_msg)
            return False
        except Exception as e:
            error_msg = f"❌ Error fetching course metadata: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False
    
    def fetch_enrollment_statistics(self):
        """Fetch enrollment and engagement statistics"""
        try:
            print(f"\n📊 FETCHING ENROLLMENT STATISTICS")
            print("=" * 40)
            
            course = Course.objects.get(id=self.course_id)
            enrollments = Enrollment.objects.filter(course=course)
            
            stats = {
                'total_enrollments': enrollments.count(),
                'active_enrollments': enrollments.filter(status='active').count(),
                'completed_enrollments': enrollments.filter(status='completed').count(),
                'average_progress': float(enrollments.aggregate(
                    avg_progress=Avg('progress_percentage')
                )['avg_progress'] or 0),
                'enrollment_types': {
                    'paid': enrollments.filter(enrollment_type='paid').count(),
                    'trial': enrollments.filter(enrollment_type='trial').count(),
                    'sponsored': enrollments.filter(enrollment_type='sponsored').count(),
                }
            }
            
            self.export_data['enrollment_stats'] = stats
            
            print(f"✅ Enrollment statistics:")
            print(f"   - Total: {stats['total_enrollments']}")
            print(f"   - Active: {stats['active_enrollments']}")
            print(f"   - Completed: {stats['completed_enrollments']}")
            print(f"   - Average Progress: {stats['average_progress']:.1f}%")
            
            return True
            
        except Exception as e:
            error_msg = f"❌ Error fetching enrollment statistics: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False
    
    def fetch_content_items_for_lesson(self, lesson):
        """Fetch all content items for a specific lesson"""
        try:
            content_items = []
            lesson_contents = LessonContent.objects.filter(lesson=lesson).order_by('sort_order')
            
            for lesson_content in lesson_contents:
                content_item = lesson_content.content_item
                content_data = {
                    'id': content_item.id,
                    'title': content_item.title,
                    'content_type': content_item.content_type,
                    'content': content_item.content,
                    'file_path': content_item.file_path.url if content_item.file_path else None,
                    'external_url': content_item.external_url,
                    'metadata': content_item.metadata,
                    'tags': content_item.tags,
                    'is_public': content_item.is_public,
                    'sort_order': lesson_content.sort_order,
                    'is_required': lesson_content.is_required,
                    'created_at': content_item.created_at.isoformat() if content_item.created_at else None,
                    'updated_at': content_item.updated_at.isoformat() if content_item.updated_at else None,
                }
                content_items.append(content_data)
            
            return content_items
            
        except Exception as e:
            error_msg = f"Error fetching content items for lesson {lesson.id}: {str(e)}"
            self.errors.append(error_msg)
            return []
    
    def fetch_quizzes_for_lesson(self, lesson):
        """Fetch all quizzes for a specific lesson"""
        try:
            quizzes = []
            lesson_quizzes = Quiz.objects.filter(lesson=lesson).order_by('sort_order')
            
            for quiz in lesson_quizzes:
                # Fetch all questions for this quiz
                questions = []
                quiz_questions = Question.objects.filter(quiz=quiz).order_by('sort_order')
                
                for question in quiz_questions:
                    question_data = {
                        'id': question.id,
                        'question_text': question.question_text,
                        'question_type': question.question_type,
                        'answer_choices': question.answer_choices,
                        'correct_answer': question.correct_answer,
                        'explanation': question.explanation,
                        'points': question.points,
                        'sort_order': question.sort_order,
                        'created_at': question.created_at.isoformat() if question.created_at else None,
                    }
                    questions.append(question_data)
                
                quiz_data = {
                    'id': quiz.id,
                    'title': quiz.title,
                    'description': quiz.description,
                    'passing_score': quiz.passing_score,
                    'max_attempts': quiz.max_attempts,
                    'time_limit': quiz.time_limit,
                    'sort_order': quiz.sort_order,
                    'created_at': quiz.created_at.isoformat() if quiz.created_at else None,
                    'updated_at': quiz.updated_at.isoformat() if quiz.updated_at else None,
                    'questions': questions,
                    'total_questions': len(questions),
                }
                quizzes.append(quiz_data)
            
            return quizzes
            
        except Exception as e:
            error_msg = f"Error fetching quizzes for lesson {lesson.id}: {str(e)}"
            self.errors.append(error_msg)
            return []

    def fetch_assignments_for_lesson(self, lesson):
        """Fetch all assignments for a specific lesson"""
        try:
            assignments = []
            lesson_assignments = Assignment.objects.filter(lesson=lesson).order_by('sort_order')

            for assignment in lesson_assignments:
                assignment_data = {
                    'id': assignment.id,
                    'title': assignment.title,
                    'description': assignment.description,
                    'instructions': assignment.instructions,
                    'max_score': assignment.max_score,
                    'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                    'submission_type': assignment.submission_type,
                    'sort_order': assignment.sort_order,
                    'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
                    'updated_at': assignment.updated_at.isoformat() if assignment.updated_at else None,
                }
                assignments.append(assignment_data)

            return assignments

        except Exception as e:
            error_msg = f"Error fetching assignments for lesson {lesson.id}: {str(e)}"
            self.errors.append(error_msg)
            return []

    def fetch_interactive_exercises_for_lesson(self, lesson):
        """Fetch all interactive exercises for a specific lesson"""
        try:
            exercises = []
            lesson_exercises = InteractiveExercise.objects.filter(lesson=lesson)

            for exercise in lesson_exercises:
                exercise_data = {
                    'id': exercise.id,
                    'title': exercise.title,
                    'instructions': exercise.instructions,
                    'exercise_type': exercise.exercise_type,
                    'exercise_data': exercise.exercise_data,
                    'time_limit': exercise.time_limit,
                    'is_graded': exercise.is_graded,
                    'max_score': exercise.max_score,
                    'created_at': exercise.created_at.isoformat() if exercise.created_at else None,
                }
                exercises.append(exercise_data)

            return exercises

        except Exception as e:
            error_msg = f"Error fetching interactive exercises for lesson {lesson.id}: {str(e)}"
            self.errors.append(error_msg)
            return []

    def fetch_lessons_for_module(self, module):
        """Fetch all lessons for a specific module with all related content"""
        try:
            lessons = []
            module_lessons = Lesson.objects.filter(module=module).order_by('sort_order')

            for lesson in module_lessons:
                lesson_data = {
                    'id': lesson.id,
                    'title': lesson.title,
                    'content_type': lesson.content_type,
                    'content': lesson.content,
                    'video_url': lesson.video_url,
                    'document_url': lesson.document_url,
                    'audio_url': lesson.audio_url,
                    'presentation_file': lesson.presentation_file.url if lesson.presentation_file else None,
                    'sort_order': lesson.sort_order,
                    'is_published': lesson.is_published,
                    'is_mandatory': lesson.is_mandatory,
                    'estimated_duration': lesson.estimated_duration,
                    'learning_objectives': lesson.learning_objectives,
                    'resources': lesson.resources,
                    'created_at': lesson.created_at.isoformat() if lesson.created_at else None,
                    'updated_at': lesson.updated_at.isoformat() if lesson.updated_at else None,
                }

                # Fetch all related content
                lesson_data['content_items'] = self.fetch_content_items_for_lesson(lesson)
                lesson_data['quizzes'] = self.fetch_quizzes_for_lesson(lesson)
                lesson_data['assignments'] = self.fetch_assignments_for_lesson(lesson)
                lesson_data['interactive_exercises'] = self.fetch_interactive_exercises_for_lesson(lesson)

                # Add counts for summary
                lesson_data['total_content_items'] = len(lesson_data['content_items'])
                lesson_data['total_quizzes'] = len(lesson_data['quizzes'])
                lesson_data['total_assignments'] = len(lesson_data['assignments'])
                lesson_data['total_interactive_exercises'] = len(lesson_data['interactive_exercises'])

                lessons.append(lesson_data)

            return lessons

        except Exception as e:
            error_msg = f"Error fetching lessons for module {module.id}: {str(e)}"
            self.errors.append(error_msg)
            return []

    def fetch_modules_and_content(self):
        """Fetch all modules and their complete content structure"""
        try:
            print(f"\n📑 FETCHING MODULES AND CONTENT")
            print("=" * 40)

            course = Course.objects.get(id=self.course_id)
            modules = Module.objects.filter(course=course).order_by('sort_order')

            modules_data = []
            total_lessons = 0
            total_content_items = 0
            total_quizzes = 0
            total_assignments = 0
            total_exercises = 0

            for module in modules:
                print(f"   📂 Processing Module: {module.title}")

                module_data = {
                    'id': module.id,
                    'title': module.title,
                    'description': module.description,
                    'sort_order': module.sort_order,
                    'is_published': module.is_published,
                    'unlock_criteria': module.unlock_criteria,
                    'estimated_duration': module.estimated_duration,
                    'created_at': module.created_at.isoformat() if module.created_at else None,
                    'updated_at': module.updated_at.isoformat() if module.updated_at else None,
                }

                # Fetch all lessons for this module
                lessons = self.fetch_lessons_for_module(module)
                module_data['lessons'] = lessons
                module_data['total_lessons'] = len(lessons)

                # Aggregate counts
                total_lessons += len(lessons)
                for lesson in lessons:
                    total_content_items += lesson['total_content_items']
                    total_quizzes += lesson['total_quizzes']
                    total_assignments += lesson['total_assignments']
                    total_exercises += lesson['total_interactive_exercises']

                modules_data.append(module_data)
                print(f"      ✅ {len(lessons)} lessons processed")

            self.export_data['modules'] = modules_data
            self.export_data['total_modules'] = len(modules_data)
            self.export_data['total_lessons'] = total_lessons
            self.export_data['total_content_items'] = total_content_items
            self.export_data['total_quizzes'] = total_quizzes
            self.export_data['total_assignments'] = total_assignments
            self.export_data['total_interactive_exercises'] = total_exercises

            print(f"✅ Content structure fetched:")
            print(f"   - Modules: {len(modules_data)}")
            print(f"   - Lessons: {total_lessons}")
            print(f"   - Content Items: {total_content_items}")
            print(f"   - Quizzes: {total_quizzes}")
            print(f"   - Assignments: {total_assignments}")
            print(f"   - Interactive Exercises: {total_exercises}")

            return True

        except Exception as e:
            error_msg = f"❌ Error fetching modules and content: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False

    def add_export_metadata(self):
        """Add export metadata and summary information"""
        try:
            self.export_data['export_metadata'] = {
                'export_timestamp': datetime.now().isoformat(),
                'export_version': '1.0',
                'source_database': 'YITP Production (Supabase PostgreSQL)',
                'exporter_script': 'export_course_6_full.py',
                'course_id': self.course_id,
                'total_errors': len(self.errors),
                'errors': self.errors if self.errors else None,
            }

            return True

        except Exception as e:
            error_msg = f"❌ Error adding export metadata: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return False

    def save_export_to_json(self):
        """Save the complete export data to JSON file"""
        try:
            print(f"\n💾 SAVING EXPORT TO JSON FILE")
            print("=" * 40)

            filename = "course_6_full_export.json"

            # Custom JSON encoder to handle Decimal and other types
            class CustomJSONEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, Decimal):
                        return float(obj)
                    return super().default(obj)

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.export_data, f, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)

            file_size = os.path.getsize(filename)
            file_size_mb = file_size / (1024 * 1024)

            print(f"✅ Export saved successfully!")
            print(f"   - File: {filename}")
            print(f"   - Size: {file_size:,} bytes ({file_size_mb:.2f} MB)")
            print(f"   - Course: {self.export_data.get('title', 'Unknown')}")
            print(f"   - Modules: {self.export_data.get('total_modules', 0)}")
            print(f"   - Lessons: {self.export_data.get('total_lessons', 0)}")

            return filename

        except Exception as e:
            error_msg = f"❌ Error saving export to JSON: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return None

    def run_full_export(self):
        """Run the complete course export process"""
        print("🚀 STARTING YITP COURSE 6 FULL EXPORT")
        print("=" * 80)

        # Step 1: Verify production connection
        if not self.verify_production_connection():
            print("❌ Cannot proceed without production database connection")
            return False

        # Step 2: Fetch course metadata
        if not self.fetch_course_metadata():
            print("❌ Failed to fetch course metadata")
            return False

        # Step 3: Fetch enrollment statistics
        if not self.fetch_enrollment_statistics():
            print("⚠️ Continuing without enrollment statistics")

        # Step 4: Fetch modules and all content
        if not self.fetch_modules_and_content():
            print("❌ Failed to fetch course content")
            return False

        # Step 5: Add export metadata
        if not self.add_export_metadata():
            print("⚠️ Continuing without complete metadata")

        # Step 6: Save to JSON file
        filename = self.save_export_to_json()
        if not filename:
            print("❌ Failed to save export")
            return False

        # Final summary
        print("\n🎉 COURSE 6 EXPORT COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📁 Export File: {filename}")
        print(f"📊 Course: {self.export_data.get('title', 'Unknown')}")
        print(f"📑 Modules: {self.export_data.get('total_modules', 0)}")
        print(f"📄 Lessons: {self.export_data.get('total_lessons', 0)}")
        print(f"📝 Content Items: {self.export_data.get('total_content_items', 0)}")
        print(f"❓ Quizzes: {self.export_data.get('total_quizzes', 0)}")
        print(f"📋 Assignments: {self.export_data.get('total_assignments', 0)}")
        print(f"🎮 Interactive Exercises: {self.export_data.get('total_interactive_exercises', 0)}")
        print(f"👥 Total Enrollments: {self.export_data.get('enrollment_stats', {}).get('total_enrollments', 0)}")

        if self.errors:
            print(f"\n⚠️ Warnings/Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"   - {error}")

        print("\n🔗 NEXT STEPS:")
        print("   • Review the exported JSON file")
        print("   • Use for course backup/migration")
        print("   • Import into other environments")
        print("   • Share with stakeholders for documentation")

        return True


def main():
    """Main function to run the Course 6 export"""
    try:
        exporter = Course6FullExporter()
        success = exporter.run_full_export()

        if success:
            print("\n✅ Export completed successfully!")
            return True
        else:
            print("\n❌ Export failed!")
            return False

    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
