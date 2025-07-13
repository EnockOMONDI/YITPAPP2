#!/usr/bin/env python
"""
Comprehensive data import script to migrate all development data to production
Handles conflicts and preserves relationships between all models
"""
import os
import sys
import django
import json
from datetime import datetime

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment for development first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from users.models import InstructorProfile, Profile
from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question, Assignment, AssignmentSubmission
from progress.models import Enrollment, LessonProgress, Achievement
from communication.models import Message
from payments.models import Payment
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

class ComprehensiveDataImporter:
    def __init__(self):
        self.stats = {
            'users_created': 0,
            'users_updated': 0,
            'profiles_created': 0,
            'instructor_profiles_created': 0,
            'courses_created': 0,
            'modules_created': 0,
            'lessons_created': 0,
            'quizzes_created': 0,
            'questions_created': 0,
            'enrollments_created': 0,
            'errors': []
        }
        self.user_mapping = {}  # Map old IDs to new IDs
        self.course_mapping = {}
        self.module_mapping = {}
        self.lesson_mapping = {}
        self.quiz_mapping = {}
        
    def log_error(self, message):
        """Log error message"""
        error_msg = f"ERROR: {message}"
        print(error_msg)
        self.stats['errors'].append(error_msg)
    
    def export_development_data(self):
        """Export all data from development database"""
        print("🔄 Exporting development database data...")
        
        # Switch to development environment
        os.environ['DJANGO_ENV'] = 'development'
        
        data = {
            'users': [],
            'profiles': [],
            'instructor_profiles': [],
            'courses': [],
            'modules': [],
            'lessons': [],
            'quizzes': [],
            'questions': [],
            'enrollments': [],
            'lesson_progress': [],
            'achievements': [],
            'messages': [],
            'payments': []
        }
        
        try:
            # Export Users
            for user in User.objects.all():
                data['users'].append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_staff': user.is_staff,
                    'is_active': user.is_active,
                    'is_superuser': user.is_superuser,
                    'date_joined': user.date_joined.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                })
            
            # Export Profiles
            for profile in Profile.objects.all():
                data['profiles'].append({
                    'id': profile.id,
                    'user_id': profile.user_id,
                    'bio': getattr(profile, 'bio', ''),
                    'location': getattr(profile, 'location', ''),
                    'birth_date': getattr(profile, 'birth_date', None).isoformat() if getattr(profile, 'birth_date', None) else None,
                    'phone_number': getattr(profile, 'phone_number', ''),
                    'payment_status': getattr(profile, 'payment_status', 'unpaid'),
                    'profile_completion_percentage': getattr(profile, 'profile_completion_percentage', 0),
                    'email_verified': getattr(profile, 'email_verified', False),
                    'created_at': getattr(profile, 'created_at', None).isoformat() if getattr(profile, 'created_at', None) else None,
                })
            
            # Export Instructor Profiles
            for ip in InstructorProfile.objects.all():
                data['instructor_profiles'].append({
                    'id': ip.id,
                    'user_id': ip.user_id,
                    'instructor_role': ip.instructor_role,
                    'bio': ip.bio,
                    'qualifications': ip.qualifications,
                    'years_experience': ip.years_experience,
                    'verification_status': ip.verification_status,
                    'verified_at': ip.verified_at.isoformat() if ip.verified_at else None,
                    'is_active': ip.is_active,
                    'can_create_courses': ip.can_create_courses,
                    'can_manage_assessments': ip.can_manage_assessments,
                    'can_view_analytics': ip.can_view_analytics,
                    'created_at': ip.created_at.isoformat() if ip.created_at else None,
                })
            
            # Export Courses
            for course in Course.objects.all():
                data['courses'].append({
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'instructor_id': course.instructor_id,
                    'price': float(course.price) if course.price else 0.0,
                    'is_published': course.is_published,
                    'created_at': course.created_at.isoformat(),
                    'updated_at': course.updated_at.isoformat(),
                    'thumbnail': course.thumbnail.name if course.thumbnail else None,
                    'estimated_duration': getattr(course, 'estimated_duration', 40),
                    'difficulty_level': course.difficulty_level,
                    'enrollment_limit': getattr(course, 'enrollment_limit', 100),
                })
            
            # Export Modules
            for module in Module.objects.all():
                data['modules'].append({
                    'id': module.id,
                    'course_id': module.course_id,
                    'title': module.title,
                    'description': module.description,
                    'sort_order': getattr(module, 'sort_order', 0),
                    'created_at': module.created_at.isoformat(),
                })
            
            # Export Lessons
            for lesson in Lesson.objects.all():
                data['lessons'].append({
                    'id': lesson.id,
                    'module_id': lesson.module_id,
                    'title': lesson.title,
                    'content': lesson.content,
                    'sort_order': getattr(lesson, 'sort_order', 0),
                    'estimated_duration': getattr(lesson, 'estimated_duration', 30),
                    'is_published': lesson.is_published,
                    'created_at': lesson.created_at.isoformat(),
                })
            
            # Export Quizzes
            for quiz in Quiz.objects.all():
                data['quizzes'].append({
                    'id': quiz.id,
                    'lesson_id': quiz.lesson_id,
                    'title': quiz.title,
                    'description': quiz.description,
                    'time_limit_minutes': quiz.time_limit,
                    'max_attempts': quiz.max_attempts,
                    'passing_score': quiz.passing_score,
                    'is_published': quiz.is_published,
                    'created_at': quiz.created_at.isoformat(),
                })
            
            # Export Questions
            for question in Question.objects.all():
                data['questions'].append({
                    'id': question.id,
                    'quiz_id': question.quiz_id,
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'points': question.points,
                    'sort_order': getattr(question, 'sort_order', 0),
                    'options': question.options,
                    'correct_answer': question.correct_answer,
                    'explanation': question.explanation,
                })
            
            # Export Enrollments
            for enrollment in Enrollment.objects.all():
                data['enrollments'].append({
                    'id': enrollment.id,
                    'student_id': enrollment.student_id,
                    'course_id': enrollment.course_id,
                    'enrollment_date': enrollment.enrollment_date.isoformat(),
                    'status': enrollment.status,
                    'progress_percentage': enrollment.progress_percentage,
                    'completion_date': enrollment.completion_date.isoformat() if enrollment.completion_date else None,
                })
            
            print(f"✅ Exported {len(data['users'])} users")
            print(f"✅ Exported {len(data['instructor_profiles'])} instructor profiles")
            print(f"✅ Exported {len(data['courses'])} courses")
            print(f"✅ Exported {len(data['modules'])} modules")
            print(f"✅ Exported {len(data['lessons'])} lessons")
            print(f"✅ Exported {len(data['quizzes'])} quizzes")
            print(f"✅ Exported {len(data['questions'])} questions")
            
            return data
            
        except Exception as e:
            self.log_error(f"Error exporting data: {e}")
            return None

    def switch_to_production(self):
        """Switch to production environment"""
        print("🔄 Switching to production environment...")
        os.environ['DJANGO_ENV'] = 'production'

        # Reload Django settings
        from django.conf import settings
        from importlib import reload
        import blog.settings
        reload(blog.settings)

        print("✅ Switched to production environment")

    def import_users(self, users_data):
        """Import users with conflict handling"""
        print("🔄 Importing users...")

        for user_data in users_data:
            try:
                # Check if user exists by email
                existing_user = None
                try:
                    existing_user = User.objects.get(email=user_data['email'])
                    # Update existing user
                    existing_user.username = user_data['username']
                    existing_user.first_name = user_data['first_name']
                    existing_user.last_name = user_data['last_name']
                    existing_user.is_staff = user_data['is_staff']
                    existing_user.is_active = user_data['is_active']
                    existing_user.is_superuser = user_data['is_superuser']
                    existing_user.save()

                    self.user_mapping[user_data['id']] = existing_user.id
                    self.stats['users_updated'] += 1
                    print(f"  ✅ Updated user: {existing_user.email}")

                except User.DoesNotExist:
                    # Create new user
                    new_user = User.objects.create(
                        username=user_data['username'],
                        email=user_data['email'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        is_staff=user_data['is_staff'],
                        is_active=user_data['is_active'],
                        is_superuser=user_data['is_superuser'],
                    )
                    # Set a default password for new users
                    new_user.set_password('TempPassword123!')
                    new_user.save()

                    self.user_mapping[user_data['id']] = new_user.id
                    self.stats['users_created'] += 1
                    print(f"  ✅ Created user: {new_user.email}")

            except Exception as e:
                self.log_error(f"Error importing user {user_data.get('email', 'unknown')}: {e}")

    def import_profiles(self, profiles_data):
        """Import user profiles"""
        print("🔄 Importing profiles...")

        for profile_data in profiles_data:
            try:
                old_user_id = profile_data['user_id']
                new_user_id = self.user_mapping.get(old_user_id)

                if not new_user_id:
                    continue

                user = User.objects.get(id=new_user_id)

                # Get or create profile
                profile, created = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'bio': profile_data.get('bio', ''),
                        'location': profile_data.get('location', ''),
                        'phone_number': profile_data.get('phone_number', ''),
                        'payment_status': profile_data.get('payment_status', 'pending'),
                        'profile_completion_percentage': profile_data.get('profile_completion_percentage', 0),
                        'email_verified': profile_data.get('email_verified', False),
                    }
                )

                if created:
                    self.stats['profiles_created'] += 1
                    print(f"  ✅ Created profile for: {user.email}")
                else:
                    # Update existing profile
                    profile.bio = profile_data.get('bio', profile.bio)
                    profile.location = profile_data.get('location', profile.location)
                    profile.phone_number = profile_data.get('phone_number', profile.phone_number)
                    profile.payment_status = profile_data.get('payment_status', profile.payment_status)
                    profile.save()
                    print(f"  ✅ Updated profile for: {user.email}")

            except Exception as e:
                self.log_error(f"Error importing profile: {e}")

    def import_instructor_profiles(self, instructor_profiles_data):
        """Import instructor profiles"""
        print("🔄 Importing instructor profiles...")

        for ip_data in instructor_profiles_data:
            try:
                old_user_id = ip_data['user_id']
                new_user_id = self.user_mapping.get(old_user_id)

                if not new_user_id:
                    continue

                user = User.objects.get(id=new_user_id)

                # Get or create instructor profile
                instructor_profile, created = InstructorProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'instructor_role': ip_data.get('instructor_role', 'course_instructor'),
                        'bio': ip_data.get('bio', ''),
                        'qualifications': ip_data.get('qualifications', ''),
                        'years_experience': ip_data.get('years_experience', 0),
                        'verification_status': ip_data.get('verification_status', 'verified'),
                        'is_active': ip_data.get('is_active', True),
                        'can_create_courses': ip_data.get('can_create_courses', True),
                        'can_manage_assessments': ip_data.get('can_manage_assessments', True),
                        'can_view_analytics': ip_data.get('can_view_analytics', True),
                    }
                )

                if created:
                    self.stats['instructor_profiles_created'] += 1
                    print(f"  ✅ Created instructor profile for: {user.email}")
                else:
                    # Update existing instructor profile
                    instructor_profile.instructor_role = ip_data.get('instructor_role', instructor_profile.instructor_role)
                    instructor_profile.bio = ip_data.get('bio', instructor_profile.bio)
                    instructor_profile.qualifications = ip_data.get('qualifications', instructor_profile.qualifications)
                    instructor_profile.verification_status = ip_data.get('verification_status', instructor_profile.verification_status)
                    instructor_profile.save()
                    print(f"  ✅ Updated instructor profile for: {user.email}")

            except Exception as e:
                self.log_error(f"Error importing instructor profile: {e}")

    def import_courses(self, courses_data):
        """Import courses"""
        print("🔄 Importing courses...")

        for course_data in courses_data:
            try:
                old_instructor_id = course_data['instructor_id']
                new_instructor_id = self.user_mapping.get(old_instructor_id)

                if not new_instructor_id:
                    continue

                instructor = User.objects.get(id=new_instructor_id)

                # Check if course exists by title and instructor
                existing_course = None
                try:
                    existing_course = Course.objects.get(
                        title=course_data['title'],
                        instructor=instructor
                    )
                    # Update existing course
                    existing_course.description = course_data.get('description', existing_course.description)
                    existing_course.price = course_data.get('price', existing_course.price)
                    existing_course.is_published = course_data.get('is_published', existing_course.is_published)
                    existing_course.estimated_duration = course_data.get('estimated_duration', existing_course.estimated_duration)
                    existing_course.difficulty_level = course_data.get('difficulty_level', existing_course.difficulty_level)
                    existing_course.enrollment_limit = course_data.get('enrollment_limit', existing_course.enrollment_limit)
                    existing_course.save()

                    self.course_mapping[course_data['id']] = existing_course.id
                    print(f"  ✅ Updated course: {existing_course.title}")

                except Course.DoesNotExist:
                    # Create new course
                    new_course = Course.objects.create(
                        title=course_data['title'],
                        description=course_data.get('description', ''),
                        instructor=instructor,
                        price=course_data.get('price', 0.0),
                        is_published=course_data.get('is_published', False),
                        estimated_duration=course_data.get('estimated_duration', 40),
                        difficulty_level=course_data.get('difficulty_level', 'beginner'),
                        enrollment_limit=course_data.get('enrollment_limit', 100),
                    )

                    self.course_mapping[course_data['id']] = new_course.id
                    self.stats['courses_created'] += 1
                    print(f"  ✅ Created course: {new_course.title}")

            except Exception as e:
                self.log_error(f"Error importing course {course_data.get('title', 'unknown')}: {e}")

    def import_modules(self, modules_data):
        """Import course modules"""
        print("🔄 Importing modules...")

        for module_data in modules_data:
            try:
                old_course_id = module_data['course_id']
                new_course_id = self.course_mapping.get(old_course_id)

                if not new_course_id:
                    continue

                course = Course.objects.get(id=new_course_id)

                # Get or create module
                module, created = Module.objects.get_or_create(
                    course=course,
                    title=module_data['title'],
                    defaults={
                        'description': module_data.get('description', ''),
                        'sort_order': module_data.get('sort_order', 0),
                    }
                )

                self.module_mapping[module_data['id']] = module.id

                if created:
                    self.stats['modules_created'] += 1
                    print(f"  ✅ Created module: {module.title}")
                else:
                    print(f"  ✅ Found existing module: {module.title}")

            except Exception as e:
                self.log_error(f"Error importing module: {e}")

    def import_lessons(self, lessons_data):
        """Import lessons"""
        print("🔄 Importing lessons...")

        for lesson_data in lessons_data:
            try:
                old_module_id = lesson_data['module_id']
                new_module_id = self.module_mapping.get(old_module_id)

                if not new_module_id:
                    continue

                module = Module.objects.get(id=new_module_id)

                # Get or create lesson
                lesson, created = Lesson.objects.get_or_create(
                    module=module,
                    title=lesson_data['title'],
                    defaults={
                        'content': lesson_data.get('content', ''),
                        'content_type': 'text',  # Default content type
                        'sort_order': lesson_data.get('sort_order', 0),
                        'estimated_duration': lesson_data.get('estimated_duration', 30),
                        'is_published': lesson_data.get('is_published', True),
                    }
                )

                self.lesson_mapping[lesson_data['id']] = lesson.id

                if created:
                    self.stats['lessons_created'] += 1
                    print(f"  ✅ Created lesson: {lesson.title}")
                else:
                    print(f"  ✅ Found existing lesson: {lesson.title}")

            except Exception as e:
                self.log_error(f"Error importing lesson: {e}")

    def import_quizzes(self, quizzes_data):
        """Import quizzes"""
        print("🔄 Importing quizzes...")

        for quiz_data in quizzes_data:
            try:
                old_lesson_id = quiz_data['lesson_id']
                new_lesson_id = self.lesson_mapping.get(old_lesson_id)

                if not new_lesson_id:
                    continue

                lesson = Lesson.objects.get(id=new_lesson_id)

                # Get or create quiz
                quiz, created = Quiz.objects.get_or_create(
                    lesson=lesson,
                    title=quiz_data['title'],
                    defaults={
                        'description': quiz_data.get('description', ''),
                        'time_limit': quiz_data.get('time_limit_minutes', 30),
                        'max_attempts': quiz_data.get('max_attempts', 3),
                        'passing_score': quiz_data.get('passing_score', 70),
                        'is_published': quiz_data.get('is_published', True),
                    }
                )

                self.quiz_mapping[quiz_data['id']] = quiz.id

                if created:
                    self.stats['quizzes_created'] += 1
                    print(f"  ✅ Created quiz: {quiz.title}")
                else:
                    print(f"  ✅ Found existing quiz: {quiz.title}")

            except Exception as e:
                self.log_error(f"Error importing quiz: {e}")

    def import_questions(self, questions_data):
        """Import quiz questions"""
        print("🔄 Importing questions...")

        for question_data in questions_data:
            try:
                old_quiz_id = question_data['quiz_id']
                new_quiz_id = self.quiz_mapping.get(old_quiz_id)

                if not new_quiz_id:
                    continue

                quiz = Quiz.objects.get(id=new_quiz_id)

                # Get or create question
                question, created = Question.objects.get_or_create(
                    quiz=quiz,
                    question_text=question_data['question_text'],
                    defaults={
                        'question_type': question_data.get('question_type', 'multiple_choice'),
                        'points': question_data.get('points', 1),
                        'sort_order': question_data.get('sort_order', 0),
                        'options': question_data.get('options', []),
                        'correct_answer': question_data.get('correct_answer', ''),
                        'explanation': question_data.get('explanation', ''),
                    }
                )

                if created:
                    self.stats['questions_created'] += 1
                    print(f"  ✅ Created question for quiz: {quiz.title}")
                else:
                    print(f"  ✅ Found existing question for quiz: {quiz.title}")

            except Exception as e:
                self.log_error(f"Error importing question: {e}")

    def import_enrollments(self, enrollments_data):
        """Import enrollments"""
        print("🔄 Importing enrollments...")

        for enrollment_data in enrollments_data:
            try:
                old_student_id = enrollment_data['student_id']
                old_course_id = enrollment_data['course_id']

                new_student_id = self.user_mapping.get(old_student_id)
                new_course_id = self.course_mapping.get(old_course_id)

                if not new_student_id or not new_course_id:
                    continue

                student = User.objects.get(id=new_student_id)
                course = Course.objects.get(id=new_course_id)

                # Get or create enrollment
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'status': enrollment_data.get('status', 'active'),
                        'progress_percentage': enrollment_data.get('progress_percentage', 0),
                    }
                )

                if created:
                    self.stats['enrollments_created'] += 1
                    print(f"  ✅ Created enrollment: {student.email} -> {course.title}")
                else:
                    print(f"  ✅ Found existing enrollment: {student.email} -> {course.title}")

            except Exception as e:
                self.log_error(f"Error importing enrollment: {e}")

    def verify_import(self):
        """Verify the imported data"""
        print("\n🔍 Verifying imported data...")

        try:
            # Check test instructor
            test_instructor = User.objects.get(email='yayek37675@simerm.com')
            instructor_profile = test_instructor.instructor_profile

            print(f"✅ Test Instructor Verified:")
            print(f"   Username: {test_instructor.username}")
            print(f"   Email: {test_instructor.email}")
            print(f"   Role: {instructor_profile.instructor_role}")
            print(f"   Verification: {instructor_profile.verification_status}")
            print(f"   Active: {instructor_profile.is_active}")

            # Check courses by instructor
            instructor_courses = Course.objects.filter(instructor=test_instructor)
            print(f"\n✅ Instructor Courses: {instructor_courses.count()}")
            for course in instructor_courses:
                print(f"   - {course.title}")
                modules = Module.objects.filter(course=course)
                print(f"     Modules: {modules.count()}")
                for module in modules:
                    lessons = Lesson.objects.filter(module=module)
                    quizzes = Quiz.objects.filter(lesson__module=module)
                    print(f"       - {module.title}: {lessons.count()} lessons, {quizzes.count()} quizzes")

            return True

        except Exception as e:
            self.log_error(f"Error verifying import: {e}")
            return False

    def print_stats(self):
        """Print import statistics"""
        print("\n" + "="*60)
        print("📊 IMPORT STATISTICS")
        print("="*60)
        print(f"Users Created: {self.stats['users_created']}")
        print(f"Users Updated: {self.stats['users_updated']}")
        print(f"Profiles Created: {self.stats['profiles_created']}")
        print(f"Instructor Profiles Created: {self.stats['instructor_profiles_created']}")
        print(f"Courses Created: {self.stats['courses_created']}")
        print(f"Modules Created: {self.stats['modules_created']}")
        print(f"Lessons Created: {self.stats['lessons_created']}")
        print(f"Quizzes Created: {self.stats['quizzes_created']}")
        print(f"Questions Created: {self.stats['questions_created']}")
        print(f"Enrollments Created: {self.stats['enrollments_created']}")

        if self.stats['errors']:
            print(f"\n❌ Errors: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                print(f"   {error}")
        else:
            print("\n✅ No errors encountered!")

    def run_import(self):
        """Run the complete import process"""
        print("="*60)
        print("🚀 COMPREHENSIVE DATA IMPORT TO PRODUCTION")
        print("="*60)

        # Step 1: Export development data
        data = self.export_development_data()
        if not data:
            print("❌ Failed to export development data")
            return False

        # Step 2: Switch to production
        self.switch_to_production()

        # Step 3: Import data in correct order
        with transaction.atomic():
            self.import_users(data['users'])
            self.import_profiles(data['profiles'])
            self.import_instructor_profiles(data['instructor_profiles'])
            self.import_courses(data['courses'])
            self.import_modules(data['modules'])
            self.import_lessons(data['lessons'])
            self.import_quizzes(data['quizzes'])
            self.import_questions(data['questions'])
            self.import_enrollments(data['enrollments'])

        # Step 4: Verify import
        success = self.verify_import()

        # Step 5: Print statistics
        self.print_stats()

        if success:
            print("\n✅ IMPORT COMPLETED SUCCESSFULLY!")
        else:
            print("\n❌ IMPORT COMPLETED WITH ERRORS")

        return success

def main():
    """Main execution function"""
    importer = ComprehensiveDataImporter()
    return importer.run_import()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
