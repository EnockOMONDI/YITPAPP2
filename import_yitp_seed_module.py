#!/usr/bin/env python
"""
Import YITP Seed Module from yitp_seed_module1.json into YITP platform
"""

import os
import sys
import django
import json
from decimal import Decimal
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson, Category
from assessments.models import Quiz, Question, Assignment
from content.models import ContentItem, LessonContent
from django.db import transaction

class YITPSeedImporter:
    def __init__(self, json_file='yitp_seed_module1.json'):
        self.json_file = json_file
        self.data = None
        self.course = None
        self.modules = {}
        self.lessons = {}
        self.quizzes = {}
        self.content_items = {}
        
    def load_json(self):
        """Load and validate JSON data"""
        print("📂 Loading YITP Seed Module JSON data...")
        
        try:
            with open(self.json_file, 'r') as f:
                self.data = json.load(f)
            print(f"✅ JSON loaded successfully from {self.json_file}")
            
            # Quick validation
            if 'course' not in self.data:
                print("❌ Invalid JSON: missing 'course' section")
                return False
            
            course_title = self.data['course'].get('title', 'Unknown')
            print(f"📋 Course to import: {course_title}")
            return True
            
        except FileNotFoundError:
            print(f"❌ File not found: {self.json_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format: {str(e)}")
            return False
    
    def validate_prerequisites(self):
        """Validate that all prerequisites exist in database"""
        print("🔍 Validating prerequisites...")
        
        course_data = self.data['course']
        
        # Check instructor exists
        instructor_id = course_data.get('instructor')
        try:
            instructor = User.objects.get(id=instructor_id)
            print(f"✅ Instructor found: {instructor.username} (ID: {instructor.id})")
        except User.DoesNotExist:
            print(f"❌ Instructor ID {instructor_id} not found")
            return False
        
        # Check category exists
        category_id = course_data.get('category')
        try:
            category = Category.objects.get(id=category_id)
            print(f"✅ Category found: {category.name} (ID: {category.id})")
        except Category.DoesNotExist:
            print(f"❌ Category ID {category_id} not found")
            return False
        
        # Check for slug conflicts
        slug = course_data.get('slug')
        if Course.objects.filter(slug=slug).exists():
            print(f"❌ Course with slug '{slug}' already exists")
            return False
        else:
            print(f"✅ Slug '{slug}' is available")
        
        return True
    
    def import_course(self):
        """Import the main course object"""
        print("📋 Importing YITP course...")
        
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
                price=Decimal(str(course_data['price'])),
                instructor_id=course_data['instructor'],
                category_id=course_data['category'],
                thumbnail=course_data.get('thumbnail', ''),
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            
            print(f"✅ Course created: {self.course.title}")
            print(f"   ID: {self.course.id}")
            print(f"   Slug: {self.course.slug}")
            print(f"   Status: {self.course.status}")
            print(f"   Duration: {self.course.estimated_duration} minutes")
            return True
            
        except Exception as e:
            print(f"❌ Error creating course: {str(e)}")
            return False
    
    def import_modules(self):
        """Import course modules"""
        print("📚 Importing modules...")
        
        modules_data = self.data['modules']
        
        for module_data in modules_data:
            try:
                module = Module.objects.create(
                    course=self.course,
                    title=module_data['title'],
                    description=module_data['description'],
                    sort_order=module_data['sort_order'],
                    is_published=module_data['is_published'],
                    unlock_criteria=module_data.get('unlock_criteria', {}),
                    estimated_duration=module_data['estimated_duration']
                )
                
                # Store module reference for lessons
                self.modules[module_data['id']] = module
                
                print(f"✅ Module created: {module.title}")
                print(f"   ID: {module.id}")
                print(f"   Duration: {module.estimated_duration} minutes")
                
            except Exception as e:
                print(f"❌ Error creating module {module_data['id']}: {str(e)}")
                return False
        
        print(f"✅ All {len(modules_data)} modules imported successfully")
        return True
    
    def import_lessons(self):
        """Import lessons"""
        print("📖 Importing lessons...")
        
        lessons_data = self.data['lessons']
        
        for lesson_data in lessons_data:
            try:
                # Get the module for this lesson
                module = self.modules.get(lesson_data['module_id'])
                if not module:
                    print(f"❌ Module {lesson_data['module_id']} not found for lesson {lesson_data['id']}")
                    continue
                
                lesson = Lesson.objects.create(
                    module=module,
                    title=lesson_data['title'],
                    content_type=lesson_data['content_type'],
                    content=lesson_data['content'],
                    video_url=lesson_data.get('video_url', ''),
                    presentation_file=lesson_data.get('presentation_file', ''),
                    sort_order=lesson_data['sort_order'],
                    is_published=lesson_data['is_published'],
                    is_mandatory=lesson_data['is_mandatory'],
                    estimated_duration=lesson_data['estimated_duration'],
                    learning_objectives=lesson_data['learning_objectives'],
                    resources=lesson_data.get('resources', [])
                )
                
                # Store lesson reference for assessments
                self.lessons[lesson_data['id']] = lesson
                
                print(f"✅ Lesson created: {lesson.title}")
                print(f"   ID: {lesson.id}, Type: {lesson.content_type}, Duration: {lesson.estimated_duration}min")
                
            except Exception as e:
                print(f"❌ Error creating lesson {lesson_data['id']}: {str(e)}")
                return False
        
        print(f"✅ All {len(lessons_data)} lessons imported successfully")
        return True
    
    def import_content_items(self):
        """Import content items"""
        print("📎 Importing content items...")
        
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
                    file_path=item_data.get('file_path', ''),
                    external_url=item_data.get('external_url', ''),
                    metadata=item_data.get('metadata', {}),
                    tags=item_data.get('tags', []),
                    is_public=item_data['is_public'],
                    created_by=self.course.instructor  # Use course instructor as creator
                )
                
                # Store content item reference
                self.content_items[item_data['id']] = content_item
                
                print(f"✅ Content item created: {content_item.title}")
                print(f"   ID: {content_item.id}, Type: {content_item.content_type}")
                
            except Exception as e:
                print(f"❌ Error creating content item {item_data['id']}: {str(e)}")
                return False
        
        print(f"✅ All {len(content_items_data)} content items imported successfully")
        return True
    
    def import_lesson_contents(self):
        """Import lesson-content relationships"""
        print("🔗 Importing lesson-content links...")
        
        lesson_contents_data = self.data.get('lesson_contents', [])
        
        if not lesson_contents_data:
            print("ℹ️ No lesson-content links to import")
            return True
        
        for link_data in lesson_contents_data:
            try:
                lesson = self.lessons.get(link_data['lesson_id'])
                content_item = self.content_items.get(link_data['content_item_id'])
                
                if not lesson:
                    print(f"❌ Lesson {link_data['lesson_id']} not found")
                    continue
                    
                if not content_item:
                    print(f"❌ Content item {link_data['content_item_id']} not found")
                    continue
                
                lesson_content = LessonContent.objects.create(
                    lesson=lesson,
                    content_item=content_item,
                    sort_order=link_data['sort_order'],
                    is_required=link_data['is_required']
                )
                
                print(f"✅ Lesson-content link created: {lesson.title} → {content_item.title}")
                
            except Exception as e:
                print(f"❌ Error creating lesson-content link: {str(e)}")
                return False
        
        print(f"✅ All {len(lesson_contents_data)} lesson-content links imported successfully")
        return True

    def import_quizzes(self):
        """Import quizzes"""
        print("🎯 Importing quizzes...")

        quizzes_data = self.data.get('quizzes', [])

        if not quizzes_data:
            print("ℹ️ No quizzes to import")
            return True

        for quiz_data in quizzes_data:
            try:
                lesson = self.lessons.get(quiz_data['lesson_id'])
                if not lesson:
                    print(f"❌ Lesson {quiz_data['lesson_id']} not found for quiz {quiz_data['id']}")
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
                    is_published=quiz_data['is_published']
                )

                # Store quiz reference for questions
                self.quizzes[quiz_data['id']] = quiz

                print(f"✅ Quiz created: {quiz.title}")
                print(f"   ID: {quiz.id}, Lesson: {lesson.title}")

            except Exception as e:
                print(f"❌ Error creating quiz {quiz_data['id']}: {str(e)}")
                return False

        print(f"✅ All {len(quizzes_data)} quizzes imported successfully")
        return True

    def import_questions(self):
        """Import quiz questions"""
        print("❓ Importing questions...")

        questions_data = self.data.get('questions', [])

        if not questions_data:
            print("ℹ️ No questions to import")
            return True

        for question_data in questions_data:
            try:
                quiz = self.quizzes.get(question_data['quiz_id'])
                if not quiz:
                    print(f"❌ Quiz {question_data['quiz_id']} not found for question")
                    continue

                question = Question.objects.create(
                    quiz=quiz,
                    question_text=question_data['question_text'],
                    question_type=question_data['question_type'],
                    options=question_data.get('options', []),
                    correct_answer=question_data['correct_answer'],
                    explanation=question_data['explanation'],
                    points=question_data['points'],
                    sort_order=question_data['sort_order']
                )

                print(f"✅ Question created: {question_data['question_type']} (ID: {question.id})")

            except Exception as e:
                print(f"❌ Error creating question: {str(e)}")
                return False

        print(f"✅ All {len(questions_data)} questions imported successfully")
        return True

    def import_assignments(self):
        """Import assignments"""
        print("📝 Importing assignments...")

        assignments_data = self.data.get('assignments', [])

        if not assignments_data:
            print("ℹ️ No assignments to import")
            return True

        for assignment_data in assignments_data:
            try:
                lesson = self.lessons.get(assignment_data['lesson_id'])
                if not lesson:
                    print(f"❌ Lesson {assignment_data['lesson_id']} not found for assignment {assignment_data['id']}")
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
                    rubric=assignment_data.get('rubric', {})
                )

                print(f"✅ Assignment created: {assignment.title}")
                print(f"   ID: {assignment.id}, Type: {assignment.assignment_type}")

            except Exception as e:
                print(f"❌ Error creating assignment {assignment_data['id']}: {str(e)}")
                return False

        print(f"✅ All {len(assignments_data)} assignments imported successfully")
        return True

    def generate_import_report(self):
        """Generate comprehensive import report"""
        print("\n📊 YITP SEED MODULE IMPORT REPORT")
        print("=" * 70)

        print(f"📋 Course: {self.course.title}")
        print(f"   ID: {self.course.id}")
        print(f"   Slug: {self.course.slug}")
        print(f"   Status: {self.course.status}")
        print(f"   Instructor: {self.course.instructor.username}")
        print(f"   Category: {self.course.category.name}")
        print(f"   Duration: {self.course.estimated_duration} minutes ({self.course.estimated_duration/60:.1f} hours)")
        print(f"   Price: ${self.course.price}")
        print(f"   Published: {self.course.is_published}")

        print(f"\n📚 Modules: {len(self.modules)}")
        for module_id, module in self.modules.items():
            print(f"   {module_id}: {module.title} (ID: {module.id})")

        print(f"\n📖 Lessons: {len(self.lessons)}")
        lesson_count_by_type = {}
        mandatory_count = 0
        for lesson_id, lesson in self.lessons.items():
            content_type = lesson.content_type
            lesson_count_by_type[content_type] = lesson_count_by_type.get(content_type, 0) + 1
            if lesson.is_mandatory:
                mandatory_count += 1

        print(f"   Content Types: {lesson_count_by_type}")
        print(f"   Mandatory: {mandatory_count}/{len(self.lessons)}")
        print(f"   Optional: {len(self.lessons) - mandatory_count}/{len(self.lessons)}")

        print(f"\n🎯 Assessments:")
        print(f"   Quizzes: {len(self.quizzes)}")
        print(f"   Questions: {len(self.data.get('questions', []))}")
        print(f"   Assignments: {len(self.data.get('assignments', []))}")

        print(f"\n📎 Content:")
        print(f"   Content Items: {len(self.content_items)}")
        print(f"   Lesson-Content Links: {len(self.data.get('lesson_contents', []))}")

        print(f"\n✅ IMPORT COMPLETED SUCCESSFULLY!")
        print(f"   Course URL: /courses/{self.course.slug}/")
        print(f"   Admin URL: /admin/courses/course/{self.course.id}/change/")
        print(f"   LMS URL: /lms/courses/{self.course.slug}/")

    def run_import(self):
        """Run the complete import process"""
        print("🚀 STARTING YITP SEED MODULE IMPORT")
        print("=" * 80)

        # Load and validate JSON
        if not self.load_json():
            return False

        if not self.validate_prerequisites():
            return False

        try:
            with transaction.atomic():
                # Import in correct order
                if not self.import_course():
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
    importer = YITPSeedImporter()
    success = importer.run_import()

    if success:
        print("\n🎉 YITP Seed Module import completed successfully!")
        print("📝 Next steps:")
        print("   1. Review course in Django admin")
        print("   2. Test course progression in LMS")
        print("   3. Verify all assessments work")
        print("   4. Update status to 'published' when ready")
        print("   5. Enable course for student enrollment")
    else:
        print("\n❌ YITP Seed Module import failed!")
        print("📝 Please review errors above and fix issues")

    return success

if __name__ == '__main__':
    main()
