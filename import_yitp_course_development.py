#!/usr/bin/env python
"""
Import YITP Course to Development Database
Imports exported course data with ID conflict resolution
"""

import os
import sys
import django
import json
from decimal import Decimal
from datetime import datetime
from django.utils import timezone

# Setup Django environment for DEVELOPMENT
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'development'  # Force development mode
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson, Category
from assessments.models import Quiz, Question, Assignment
from content.models import ContentItem, LessonContent
from django.db import transaction

class YITPCourseImporter:
    def __init__(self, export_file):
        self.export_file = export_file
        self.data = None
        self.course = None
        self.id_mappings = {
            'modules': {},
            'lessons': {},
            'quizzes': {},
            'content_items': {}
        }
    
    def load_export_data(self):
        """Load exported course data"""
        print("📂 Loading export data...")
        
        try:
            with open(self.export_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            print(f"✅ Export data loaded from {self.export_file}")
            
            # Validate export data
            required_sections = ['course', 'modules', 'lessons']
            for section in required_sections:
                if section not in self.data:
                    print(f"❌ Missing required section: {section}")
                    return False
            
            course_data = self.data['course']
            print(f"📋 Course to import: {course_data['title']}")
            print(f"   Original ID: {course_data['id']}")
            print(f"   Slug: {course_data['slug']}")
            
            return True
            
        except FileNotFoundError:
            print(f"❌ Export file not found: {self.export_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format: {str(e)}")
            return False
    
    def validate_prerequisites(self):
        """Validate that prerequisites exist in development database"""
        print("\n🔍 Validating prerequisites...")
        
        course_data = self.data['course']
        
        # Check if instructor exists, create if needed
        instructor_username = course_data['instructor_username']
        instructor_email = course_data['instructor_email']
        
        try:
            instructor = User.objects.get(username=instructor_username)
            print(f"✅ Instructor found: {instructor.username}")
        except User.DoesNotExist:
            # Create instructor user
            instructor = User.objects.create_user(
                username=instructor_username,
                email=instructor_email,
                first_name='YITP',
                last_name='Instructor'
            )
            print(f"✅ Created instructor: {instructor.username}")
        
        # Check if category exists, create if needed
        category_name = course_data['category_name']
        category_slug = course_data['category_slug']
        
        try:
            category = Category.objects.get(slug=category_slug)
            print(f"✅ Category found: {category.name}")
        except Category.DoesNotExist:
            # Create category
            category = Category.objects.create(
                name=category_name,
                slug=category_slug,
                description=f"Category for {category_name}"
            )
            print(f"✅ Created category: {category.name}")
        
        # Check for slug conflicts
        slug = course_data['slug']
        if Course.objects.filter(slug=slug).exists():
            # Generate new slug
            base_slug = slug
            counter = 1
            while Course.objects.filter(slug=f"{base_slug}-dev-{counter}").exists():
                counter += 1
            new_slug = f"{base_slug}-dev-{counter}"
            print(f"⚠️ Slug conflict resolved: {slug} → {new_slug}")
            course_data['slug'] = new_slug
        else:
            print(f"✅ Slug '{slug}' is available")
        
        return instructor, category
    
    def import_course(self, instructor, category):
        """Import the main course"""
        print("\n📋 Importing course...")
        
        course_data = self.data['course']
        
        try:
            self.course = Course.objects.create(
                title=course_data['title'],
                slug=course_data['slug'],
                description=course_data['description'],
                learning_objectives=course_data['learning_objectives'],
                prerequisites=course_data['prerequisites'],
                difficulty_level=course_data['difficulty_level'],
                estimated_duration=course_data['estimated_duration'],
                status=course_data['status'],
                is_published=course_data['is_published'],
                is_featured=course_data['is_featured'],
                enrollment_limit=course_data['enrollment_limit'],
                price=Decimal(course_data['price']),
                instructor=instructor,
                category=category,
                thumbnail=course_data['thumbnail'],
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            
            print(f"✅ Course imported: {self.course.title}")
            print(f"   New ID: {self.course.id}")
            print(f"   Slug: {self.course.slug}")
            print(f"   Status: {self.course.status}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error importing course: {str(e)}")
            return False
    
    def import_modules(self):
        """Import course modules"""
        print("\n📚 Importing modules...")
        
        modules_data = self.data['modules']
        
        for module_data in modules_data:
            try:
                module = Module.objects.create(
                    course=self.course,
                    title=module_data['title'],
                    description=module_data['description'],
                    sort_order=module_data['sort_order'],
                    is_published=module_data['is_published'],
                    unlock_criteria=module_data['unlock_criteria'],
                    estimated_duration=module_data['estimated_duration'],
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                
                # Store ID mapping
                self.id_mappings['modules'][module_data['id']] = module
                
                print(f"✅ Module imported: {module.title}")
                print(f"   Original ID: {module_data['id']} → New ID: {module.id}")
                
            except Exception as e:
                print(f"❌ Error importing module {module_data['id']}: {str(e)}")
                return False
        
        print(f"✅ All {len(modules_data)} modules imported successfully")
        return True
    
    def import_lessons(self):
        """Import lessons"""
        print("\n📖 Importing lessons...")
        
        lessons_data = self.data['lessons']
        
        for lesson_data in lessons_data:
            try:
                # Get the mapped module
                original_module_id = lesson_data['module_id']
                module = self.id_mappings['modules'].get(original_module_id)
                
                if not module:
                    print(f"❌ Module {original_module_id} not found for lesson {lesson_data['id']}")
                    continue
                
                lesson = Lesson.objects.create(
                    module=module,
                    title=lesson_data['title'],
                    content_type=lesson_data['content_type'],
                    content=lesson_data['content'],
                    video_url=lesson_data['video_url'],
                    presentation_file=lesson_data['presentation_file'],
                    sort_order=lesson_data['sort_order'],
                    is_published=lesson_data['is_published'],
                    is_mandatory=lesson_data['is_mandatory'],
                    estimated_duration=lesson_data['estimated_duration'],
                    learning_objectives=lesson_data['learning_objectives'],
                    resources=lesson_data['resources'],
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                
                # Store ID mapping
                self.id_mappings['lessons'][lesson_data['id']] = lesson
                
                print(f"✅ Lesson imported: {lesson.title}")
                print(f"   Original ID: {lesson_data['id']} → New ID: {lesson.id}")
                
            except Exception as e:
                print(f"❌ Error importing lesson {lesson_data['id']}: {str(e)}")
                return False
        
        print(f"✅ All {len(lessons_data)} lessons imported successfully")
        return True
    
    def import_content_items(self):
        """Import content items"""
        print("\n📎 Importing content items...")
        
        content_items_data = self.data.get('content_items', [])
        
        if not content_items_data:
            print("ℹ️ No content items to import")
            return True
        
        for item_data in content_items_data:
            try:
                content_item = ContentItem.objects.create(
                    title=item_data['title'],
                    content_type=item_data['content_type'],
                    content=item_data['content'],
                    file_path=item_data['file_path'],
                    external_url=item_data['external_url'],
                    metadata=item_data['metadata'],
                    tags=item_data['tags'],
                    is_public=item_data['is_public'],
                    created_by=self.course.instructor,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                
                # Store ID mapping
                self.id_mappings['content_items'][item_data['id']] = content_item
                
                print(f"✅ Content item imported: {content_item.title}")
                print(f"   Original ID: {item_data['id']} → New ID: {content_item.id}")
                
            except Exception as e:
                print(f"❌ Error importing content item {item_data['id']}: {str(e)}")
                return False
        
        print(f"✅ All {len(content_items_data)} content items imported successfully")
        return True
    
    def import_lesson_contents(self):
        """Import lesson-content relationships"""
        print("\n🔗 Importing lesson-content links...")
        
        lesson_contents_data = self.data.get('lesson_contents', [])
        
        if not lesson_contents_data:
            print("ℹ️ No lesson-content links to import")
            return True
        
        for link_data in lesson_contents_data:
            try:
                original_lesson_id = link_data['lesson_id']
                original_content_id = link_data['content_item_id']
                
                lesson = self.id_mappings['lessons'].get(original_lesson_id)
                content_item = self.id_mappings['content_items'].get(original_content_id)
                
                if not lesson:
                    print(f"❌ Lesson {original_lesson_id} not found")
                    continue
                    
                if not content_item:
                    print(f"❌ Content item {original_content_id} not found")
                    continue
                
                lesson_content = LessonContent.objects.create(
                    lesson=lesson,
                    content_item=content_item,
                    sort_order=link_data['sort_order'],
                    is_required=link_data['is_required']
                )
                
                print(f"✅ Lesson-content link imported: {lesson.title} → {content_item.title}")
                
            except Exception as e:
                print(f"❌ Error importing lesson-content link: {str(e)}")
                return False
        
        print(f"✅ All {len(lesson_contents_data)} lesson-content links imported successfully")
        return True

    def import_quizzes(self):
        """Import quizzes"""
        print("\n🎯 Importing quizzes...")

        quizzes_data = self.data.get('quizzes', [])

        if not quizzes_data:
            print("ℹ️ No quizzes to import")
            return True

        for quiz_data in quizzes_data:
            try:
                original_lesson_id = quiz_data['lesson_id']
                lesson = self.id_mappings['lessons'].get(original_lesson_id)

                if not lesson:
                    print(f"❌ Lesson {original_lesson_id} not found for quiz {quiz_data['id']}")
                    continue

                quiz = Quiz.objects.create(
                    lesson=lesson,
                    title=quiz_data['title'],
                    description=quiz_data['description'],
                    instructions=quiz_data['instructions'],
                    time_limit=quiz_data.get('time_limit'),
                    max_attempts=quiz_data['max_attempts'],
                    passing_score=quiz_data['passing_score'],
                    is_randomized=quiz_data['is_randomized'],
                    show_results=quiz_data['show_results'],
                    is_published=quiz_data['is_published'],
                    created_at=timezone.now()
                )

                # Store ID mapping
                self.id_mappings['quizzes'][quiz_data['id']] = quiz

                print(f"✅ Quiz imported: {quiz.title}")
                print(f"   Original ID: {quiz_data['id']} → New ID: {quiz.id}")

            except Exception as e:
                print(f"❌ Error importing quiz {quiz_data['id']}: {str(e)}")
                return False

        print(f"✅ All {len(quizzes_data)} quizzes imported successfully")
        return True

    def import_questions(self):
        """Import quiz questions"""
        print("\n❓ Importing questions...")

        questions_data = self.data.get('questions', [])

        if not questions_data:
            print("ℹ️ No questions to import")
            return True

        for question_data in questions_data:
            try:
                original_quiz_id = question_data['quiz_id']
                quiz = self.id_mappings['quizzes'].get(original_quiz_id)

                if not quiz:
                    print(f"❌ Quiz {original_quiz_id} not found for question")
                    continue

                question = Question.objects.create(
                    quiz=quiz,
                    question_text=question_data['question_text'],
                    question_type=question_data['question_type'],
                    options=question_data.get('options', []),
                    correct_answer=question_data['correct_answer'],
                    explanation=question_data['explanation'],
                    points=question_data['points'],
                    sort_order=question_data['sort_order'],
                    created_at=timezone.now()
                )

                print(f"✅ Question imported: {question_data['question_type']} (New ID: {question.id})")

            except Exception as e:
                print(f"❌ Error importing question: {str(e)}")
                return False

        print(f"✅ All {len(questions_data)} questions imported successfully")
        return True

    def import_assignments(self):
        """Import assignments"""
        print("\n📝 Importing assignments...")

        assignments_data = self.data.get('assignments', [])

        if not assignments_data:
            print("ℹ️ No assignments to import")
            return True

        for assignment_data in assignments_data:
            try:
                original_lesson_id = assignment_data['lesson_id']
                lesson = self.id_mappings['lessons'].get(original_lesson_id)

                if not lesson:
                    print(f"❌ Lesson {original_lesson_id} not found for assignment {assignment_data['id']}")
                    continue

                assignment = Assignment.objects.create(
                    lesson=lesson,
                    title=assignment_data['title'],
                    description=assignment_data['description'],
                    instructions=assignment_data['instructions'],
                    assignment_type=assignment_data['assignment_type'],
                    submission_format=assignment_data['submission_format'],
                    max_file_size=assignment_data['max_file_size'],
                    allowed_file_types=assignment_data['allowed_file_types'],
                    due_date=assignment_data.get('due_date'),
                    max_score=assignment_data['max_score'],
                    rubric=assignment_data.get('rubric', {}),
                    created_at=timezone.now()
                )

                print(f"✅ Assignment imported: {assignment.title}")
                print(f"   Original ID: {assignment_data['id']} → New ID: {assignment.id}")

            except Exception as e:
                print(f"❌ Error importing assignment {assignment_data['id']}: {str(e)}")
                return False

        print(f"✅ All {len(assignments_data)} assignments imported successfully")
        return True

    def generate_import_report(self):
        """Generate comprehensive import report"""
        print("\n📊 DEVELOPMENT IMPORT REPORT")
        print("=" * 70)

        print(f"📋 Course: {self.course.title}")
        print(f"   New ID: {self.course.id}")
        print(f"   Slug: {self.course.slug}")
        print(f"   Status: {self.course.status}")
        print(f"   Instructor: {self.course.instructor.username}")
        print(f"   Category: {self.course.category.name}")
        print(f"   Duration: {self.course.estimated_duration} minutes")
        print(f"   Price: ${self.course.price}")
        print(f"   Published: {self.course.is_published}")

        print(f"\n📚 ID Mappings Summary:")
        print(f"   Modules: {len(self.id_mappings['modules'])} mapped")
        print(f"   Lessons: {len(self.id_mappings['lessons'])} mapped")
        print(f"   Quizzes: {len(self.id_mappings['quizzes'])} mapped")
        print(f"   Content Items: {len(self.id_mappings['content_items'])} mapped")

        print(f"\n🎯 Assessment Summary:")
        print(f"   Quizzes: {len(self.data.get('quizzes', []))}")
        print(f"   Questions: {len(self.data.get('questions', []))}")
        print(f"   Assignments: {len(self.data.get('assignments', []))}")

        print(f"\n✅ IMPORT COMPLETED SUCCESSFULLY!")
        print(f"   Development Course URL: /courses/{self.course.slug}/")
        print(f"   Development Admin URL: /admin/courses/course/{self.course.id}/change/")
        print(f"   Development LMS URL: /lms/courses/{self.course.slug}/")

    def run_import(self):
        """Run the complete import process"""
        print("📥 STARTING YITP COURSE IMPORT TO DEVELOPMENT")
        print("=" * 80)

        # Load export data
        if not self.load_export_data():
            return False

        # Validate prerequisites
        instructor, category = self.validate_prerequisites()

        try:
            with transaction.atomic():
                # Import in correct order
                if not self.import_course(instructor, category):
                    return False

                if not self.import_modules():
                    return False

                if not self.import_lessons():
                    return False

                if not self.import_content_items():
                    return False

                if not self.import_lesson_contents():
                    return False

                if not self.import_quizzes():
                    return False

                if not self.import_questions():
                    return False

                if not self.import_assignments():
                    return False

                # Generate report
                self.generate_import_report()

                return True

        except Exception as e:
            print(f"❌ Import failed with error: {str(e)}")
            print("🔄 All changes have been rolled back")
            return False

def main():
    """Main import function"""
    import glob

    # Find the most recent export file
    export_files = glob.glob('yitp_course_export_production_*.json')
    if not export_files:
        print("❌ No export files found!")
        print("   Please run export_yitp_course_production.py first")
        return False

    # Use the most recent export file
    export_file = max(export_files, key=os.path.getctime)
    print(f"📁 Using export file: {export_file}")

    importer = YITPCourseImporter(export_file)
    success = importer.run_import()

    if success:
        print("\n🎉 YITP Course import to development completed successfully!")
        print("📝 Next steps:")
        print("   1. Test course in development environment")
        print("   2. Verify all lessons and assessments work")
        print("   3. Test HTML content rendering")
        print("   4. Validate course navigation")
        print("   5. Make any necessary modifications")
    else:
        print("\n❌ YITP Course import failed!")
        print("📝 Please review errors above and fix issues")

    return success

if __name__ == '__main__':
    main()
