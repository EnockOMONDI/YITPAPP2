#!/usr/bin/env python
"""
Export YITP Course from Production Database
Exports Course ID 5 with all related data for development import
"""

import os
import sys
import django
import json
from datetime import datetime
from decimal import Decimal

# Setup Django environment for PRODUCTION
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson, Category
from assessments.models import Quiz, Question, Assignment
from content.models import ContentItem, LessonContent

class YITPCourseExporter:
    def __init__(self, course_id=5):
        self.course_id = course_id
        self.export_data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'source': 'production',
                'course_id': course_id,
                'exporter_version': '1.0'
            },
            'course': {},
            'modules': [],
            'lessons': [],
            'quizzes': [],
            'questions': [],
            'assignments': [],
            'content_items': [],
            'lesson_contents': []
        }
    
    def export_course(self):
        """Export the main course data"""
        print("📋 Exporting course data...")
        
        try:
            course = Course.objects.get(id=self.course_id)
            
            # Convert course to dict, handling special fields
            course_data = {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'description': course.description,
                'learning_objectives': course.learning_objectives,
                'prerequisites': course.prerequisites,
                'difficulty_level': course.difficulty_level,
                'estimated_duration': course.estimated_duration,
                'status': course.status,
                'is_published': course.is_published,
                'is_featured': course.is_featured,
                'enrollment_limit': course.enrollment_limit,
                'price': str(course.price),  # Convert Decimal to string
                'instructor_id': course.instructor.id,
                'instructor_username': course.instructor.username,
                'instructor_email': course.instructor.email,
                'category_id': course.category.id,
                'category_name': course.category.name,
                'category_slug': course.category.slug,
                'thumbnail': course.thumbnail.name if course.thumbnail else '',
                'created_at': course.created_at.isoformat() if course.created_at else None,
                'updated_at': course.updated_at.isoformat() if course.updated_at else None
            }
            
            self.export_data['course'] = course_data
            
            print(f"✅ Course exported: {course.title}")
            print(f"   ID: {course.id}")
            print(f"   Instructor: {course.instructor.username}")
            print(f"   Category: {course.category.name}")
            
            return course
            
        except Course.DoesNotExist:
            print(f"❌ Course with ID {self.course_id} not found")
            return None
    
    def export_modules(self, course):
        """Export course modules"""
        print("\n📚 Exporting modules...")
        
        modules = Module.objects.filter(course=course).order_by('sort_order')
        
        for module in modules:
            module_data = {
                'id': module.id,
                'course_id': module.course.id,
                'title': module.title,
                'description': module.description,
                'sort_order': module.sort_order,
                'is_published': module.is_published,
                'unlock_criteria': module.unlock_criteria,
                'estimated_duration': module.estimated_duration,
                'created_at': module.created_at.isoformat() if module.created_at else None,
                'updated_at': module.updated_at.isoformat() if module.updated_at else None
            }
            
            self.export_data['modules'].append(module_data)
            
            print(f"✅ Module exported: {module.title}")
            print(f"   ID: {module.id}, Order: {module.sort_order}")
        
        print(f"📊 Total modules exported: {len(self.export_data['modules'])}")
    
    def export_lessons(self, course):
        """Export course lessons"""
        print("\n📖 Exporting lessons...")
        
        lessons = Lesson.objects.filter(module__course=course).order_by('module__sort_order', 'sort_order')
        
        for lesson in lessons:
            lesson_data = {
                'id': lesson.id,
                'module_id': lesson.module.id,
                'title': lesson.title,
                'content_type': lesson.content_type,
                'content': lesson.content,
                'video_url': lesson.video_url,
                'presentation_file': lesson.presentation_file.name if lesson.presentation_file else '',
                'sort_order': lesson.sort_order,
                'is_published': lesson.is_published,
                'is_mandatory': lesson.is_mandatory,
                'estimated_duration': lesson.estimated_duration,
                'learning_objectives': lesson.learning_objectives,
                'resources': lesson.resources,
                'created_at': lesson.created_at.isoformat() if lesson.created_at else None,
                'updated_at': lesson.updated_at.isoformat() if lesson.updated_at else None
            }
            
            self.export_data['lessons'].append(lesson_data)
        
        print(f"📊 Total lessons exported: {len(self.export_data['lessons'])}")
        
        # Show content type breakdown
        content_types = {}
        for lesson_data in self.export_data['lessons']:
            content_type = lesson_data['content_type']
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        print(f"📊 Content types: {content_types}")
    
    def export_content_items(self, course):
        """Export content items related to the course"""
        print("\n📎 Exporting content items...")
        
        # Get content items created by the course instructor
        content_items = ContentItem.objects.filter(created_by=course.instructor)
        
        for item in content_items:
            item_data = {
                'id': item.id,
                'title': item.title,
                'content_type': item.content_type,
                'content': item.content,
                'file_path': item.file_path,
                'external_url': item.external_url,
                'metadata': item.metadata,
                'tags': item.tags,
                'is_public': item.is_public,
                'created_by_id': item.created_by.id,
                'created_by_username': item.created_by.username,
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'updated_at': item.updated_at.isoformat() if item.updated_at else None
            }
            
            self.export_data['content_items'].append(item_data)
        
        print(f"📊 Total content items exported: {len(self.export_data['content_items'])}")
    
    def export_lesson_contents(self, course):
        """Export lesson-content relationships"""
        print("\n🔗 Exporting lesson-content relationships...")
        
        lesson_contents = LessonContent.objects.filter(lesson__module__course=course)
        
        for link in lesson_contents:
            link_data = {
                'lesson_id': link.lesson.id,
                'content_item_id': link.content_item.id,
                'sort_order': link.sort_order,
                'is_required': link.is_required
            }
            
            self.export_data['lesson_contents'].append(link_data)
        
        print(f"📊 Total lesson-content links exported: {len(self.export_data['lesson_contents'])}")
    
    def export_quizzes(self, course):
        """Export quizzes"""
        print("\n🎯 Exporting quizzes...")
        
        quizzes = Quiz.objects.filter(lesson__module__course=course)
        
        for quiz in quizzes:
            quiz_data = {
                'id': quiz.id,
                'lesson_id': quiz.lesson.id,
                'title': quiz.title,
                'description': quiz.description,
                'instructions': quiz.instructions,
                'time_limit': quiz.time_limit,
                'max_attempts': quiz.max_attempts,
                'passing_score': quiz.passing_score,
                'is_randomized': quiz.is_randomized,
                'show_results': quiz.show_results,
                'is_published': quiz.is_published,
                'created_at': quiz.created_at.isoformat() if quiz.created_at else None
            }
            
            self.export_data['quizzes'].append(quiz_data)
        
        print(f"📊 Total quizzes exported: {len(self.export_data['quizzes'])}")
    
    def export_questions(self, course):
        """Export quiz questions"""
        print("\n❓ Exporting questions...")
        
        questions = Question.objects.filter(quiz__lesson__module__course=course)
        
        for question in questions:
            question_data = {
                'id': question.id,
                'quiz_id': question.quiz.id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'options': question.options,
                'correct_answer': question.correct_answer,
                'explanation': question.explanation,
                'points': question.points,
                'sort_order': question.sort_order,
                'created_at': question.created_at.isoformat() if question.created_at else None
            }
            
            self.export_data['questions'].append(question_data)
        
        print(f"📊 Total questions exported: {len(self.export_data['questions'])}")
    
    def export_assignments(self, course):
        """Export assignments"""
        print("\n📝 Exporting assignments...")
        
        assignments = Assignment.objects.filter(lesson__module__course=course)
        
        for assignment in assignments:
            assignment_data = {
                'id': assignment.id,
                'lesson_id': assignment.lesson.id,
                'title': assignment.title,
                'description': assignment.description,
                'instructions': assignment.instructions,
                'assignment_type': assignment.assignment_type,
                'submission_format': assignment.submission_format,
                'max_file_size': assignment.max_file_size,
                'allowed_file_types': assignment.allowed_file_types,
                'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                'max_score': assignment.max_score,
                'rubric': assignment.rubric,
                'created_at': assignment.created_at.isoformat() if assignment.created_at else None
            }
            
            self.export_data['assignments'].append(assignment_data)
        
        print(f"📊 Total assignments exported: {len(self.export_data['assignments'])}")
    
    def save_export(self, filename=None):
        """Save export data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'yitp_course_export_production_{timestamp}.json'
        
        print(f"\n💾 Saving export to {filename}...")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Export saved successfully")
        print(f"📁 File: {filename}")
        print(f"📊 File size: {os.path.getsize(filename)} bytes")
        
        return filename
    
    def generate_export_summary(self):
        """Generate export summary"""
        print(f"\n📊 EXPORT SUMMARY")
        print("=" * 60)
        
        course_data = self.export_data['course']
        print(f"📋 Course: {course_data['title']}")
        print(f"   ID: {course_data['id']}")
        print(f"   Slug: {course_data['slug']}")
        print(f"   Status: {course_data['status']}")
        print(f"   Published: {course_data['is_published']}")
        
        print(f"\n📊 Content Statistics:")
        print(f"   Modules: {len(self.export_data['modules'])}")
        print(f"   Lessons: {len(self.export_data['lessons'])}")
        print(f"   Content Items: {len(self.export_data['content_items'])}")
        print(f"   Lesson-Content Links: {len(self.export_data['lesson_contents'])}")
        
        print(f"\n🎯 Assessment Statistics:")
        print(f"   Quizzes: {len(self.export_data['quizzes'])}")
        print(f"   Questions: {len(self.export_data['questions'])}")
        print(f"   Assignments: {len(self.export_data['assignments'])}")
        
        print(f"\n✅ Export completed successfully!")
    
    def run_export(self):
        """Run the complete export process"""
        print("📤 STARTING YITP COURSE EXPORT FROM PRODUCTION")
        print("=" * 80)
        
        # Export course
        course = self.export_course()
        if not course:
            return False
        
        # Export all related data
        self.export_modules(course)
        self.export_lessons(course)
        self.export_content_items(course)
        self.export_lesson_contents(course)
        self.export_quizzes(course)
        self.export_questions(course)
        self.export_assignments(course)
        
        # Save export
        filename = self.save_export()
        
        # Generate summary
        self.generate_export_summary()
        
        return filename

def main():
    """Main export function"""
    exporter = YITPCourseExporter(course_id=5)
    filename = exporter.run_export()
    
    if filename:
        print(f"\n🎉 YITP Course export completed successfully!")
        print(f"📁 Export file: {filename}")
        print(f"📝 Ready for import to development database")
    else:
        print(f"\n❌ Export failed!")
    
    return filename is not None

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎯 Export ready for development import!")
    else:
        print("\n⚠️ Please fix export issues")
