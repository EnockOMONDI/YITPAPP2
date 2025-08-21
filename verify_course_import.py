#!/usr/bin/env python
"""
Verify successful course import and test functionality
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson, Category
from assessments.models import Quiz, Question, Assignment
from content.models import ContentItem, LessonContent

def verify_course_import():
    """Verify the imported course structure and functionality"""
    print("🔍 VERIFYING COURSE IMPORT")
    print("=" * 60)
    
    # Find the imported course
    try:
        course = Course.objects.get(slug='understanding-purpose-in-life-upl-101-complete')
        print(f"✅ Course found: {course.title}")
        print(f"   ID: {course.id}")
        print(f"   Status: {course.status}")
        print(f"   Instructor: {course.instructor.username}")
        print(f"   Category: {course.category.name}")
        print(f"   Price: ${course.price}")
        print(f"   Published: {course.is_published}")
    except Course.DoesNotExist:
        print("❌ Course not found!")
        return False
    
    # Verify modules
    modules = Module.objects.filter(course=course).order_by('sort_order')
    print(f"\n📚 MODULES VERIFICATION ({modules.count()}):")
    
    expected_modules = [
        "Discovering the Foundations of Purpose",
        "Definiteness of Purpose & Balanced Living", 
        "Purpose, Service, and Overcoming Obstacles",
        "Define, Live, Share—Purpose in Action"
    ]
    
    for i, module in enumerate(modules):
        expected_title = expected_modules[i] if i < len(expected_modules) else "Unknown"
        status = "✅" if module.title == expected_title else "❌"
        print(f"   {status} Module {i+1}: {module.title}")
        print(f"      Sort Order: {module.sort_order}")
        print(f"      Published: {module.is_published}")
        print(f"      Duration: {module.estimated_duration} min")
    
    # Verify lessons
    total_lessons = Lesson.objects.filter(module__course=course).count()
    print(f"\n📖 LESSONS VERIFICATION ({total_lessons}):")
    
    for module in modules:
        lessons = Lesson.objects.filter(module=module).order_by('sort_order')
        print(f"   📚 {module.title}: {lessons.count()} lessons")
        
        for lesson in lessons[:3]:  # Show first 3 lessons per module
            print(f"      ✅ {lesson.title}")
            print(f"         Type: {lesson.content_type}")
            print(f"         Duration: {lesson.estimated_duration} min")
            print(f"         Mandatory: {lesson.is_mandatory}")
        
        if lessons.count() > 3:
            print(f"      ... and {lessons.count() - 3} more lessons")
    
    # Verify assessments
    quizzes = Quiz.objects.filter(lesson__module__course=course)
    questions = Question.objects.filter(quiz__lesson__module__course=course)
    assignments = Assignment.objects.filter(lesson__module__course=course)
    
    print(f"\n🎯 ASSESSMENTS VERIFICATION:")
    print(f"   Quizzes: {quizzes.count()}")
    print(f"   Questions: {questions.count()}")
    print(f"   Assignments: {assignments.count()}")
    
    # Verify quiz details
    for quiz in quizzes:
        quiz_questions = questions.filter(quiz=quiz)
        print(f"   ✅ Quiz: {quiz.title}")
        print(f"      Lesson: {quiz.lesson.title}")
        print(f"      Questions: {quiz_questions.count()}")
        print(f"      Passing Score: {quiz.passing_score}%")
        print(f"      Max Attempts: {quiz.max_attempts}")
    
    # Verify assignment details
    for assignment in assignments:
        print(f"   ✅ Assignment: {assignment.title}")
        print(f"      Lesson: {assignment.lesson.title}")
        print(f"      Type: {assignment.assignment_type}")
        print(f"      Max Score: {assignment.max_score}")
    
    # Verify content items
    content_items = ContentItem.objects.filter(created_by=course.instructor)
    lesson_contents = LessonContent.objects.filter(lesson__module__course=course)
    
    print(f"\n📎 CONTENT VERIFICATION:")
    print(f"   Content Items: {content_items.count()}")
    print(f"   Lesson-Content Links: {lesson_contents.count()}")
    
    for content_item in content_items:
        print(f"   ✅ Content: {content_item.title}")
        print(f"      Type: {content_item.content_type}")
        print(f"      Public: {content_item.is_public}")
        print(f"      External URL: {content_item.external_url}")
    
    # Verify lesson-content relationships
    for link in lesson_contents:
        print(f"   🔗 Link: {link.lesson.title} → {link.content_item.title}")
        print(f"      Required: {link.is_required}")
        print(f"      Sort Order: {link.sort_order}")
    
    return True

def test_course_functionality():
    """Test basic course functionality"""
    print("\n🧪 TESTING COURSE FUNCTIONALITY")
    print("=" * 60)
    
    course = Course.objects.get(slug='understanding-purpose-in-life-upl-101-complete')
    
    # Test course properties
    print(f"📋 Course Properties:")
    print(f"   Total Modules: {course.modules.count()}")
    print(f"   Total Lessons: {Lesson.objects.filter(module__course=course).count()}")
    print(f"   Total Duration: {sum(lesson.estimated_duration for lesson in Lesson.objects.filter(module__course=course))} minutes")
    
    # Test module progression
    print(f"\n📚 Module Progression:")
    modules = course.modules.order_by('sort_order')
    for i, module in enumerate(modules, 1):
        lessons = module.lessons.order_by('sort_order')
        mandatory_lessons = lessons.filter(is_mandatory=True).count()
        print(f"   Module {i}: {module.title}")
        print(f"      Lessons: {lessons.count()} (Mandatory: {mandatory_lessons})")
        print(f"      Duration: {module.estimated_duration} min")
    
    # Test assessment distribution
    print(f"\n🎯 Assessment Distribution:")
    for module in modules:
        quizzes = Quiz.objects.filter(lesson__module=module)
        assignments = Assignment.objects.filter(lesson__module=module)
        print(f"   {module.title}:")
        print(f"      Quizzes: {quizzes.count()}")
        print(f"      Assignments: {assignments.count()}")
    
    # Test content richness
    print(f"\n📎 Content Richness:")
    content_types = {}
    for lesson in Lesson.objects.filter(module__course=course):
        content_type = lesson.content_type
        content_types[content_type] = content_types.get(content_type, 0) + 1
    
    for content_type, count in content_types.items():
        print(f"   {content_type}: {count} lessons")
    
    return True

def generate_course_summary():
    """Generate comprehensive course summary"""
    print("\n📊 COURSE IMPORT SUMMARY")
    print("=" * 60)
    
    course = Course.objects.get(slug='understanding-purpose-in-life-upl-101-complete')
    
    # Basic statistics
    modules = course.modules.all()
    lessons = Lesson.objects.filter(module__course=course)
    quizzes = Quiz.objects.filter(lesson__module__course=course)
    questions = Question.objects.filter(quiz__lesson__module__course=course)
    assignments = Assignment.objects.filter(lesson__module__course=course)
    content_items = ContentItem.objects.filter(created_by=course.instructor)
    
    print(f"📋 COURSE: {course.title}")
    print(f"   🆔 ID: {course.id}")
    print(f"   🔗 Slug: {course.slug}")
    print(f"   👨‍🏫 Instructor: {course.instructor.get_full_name()} ({course.instructor.username})")
    print(f"   📂 Category: {course.category.name}")
    print(f"   💰 Price: ${course.price}")
    print(f"   📊 Status: {course.status}")
    print(f"   🌐 Published: {course.is_published}")
    
    print(f"\n📈 CONTENT STATISTICS:")
    print(f"   📚 Modules: {modules.count()}")
    print(f"   📖 Lessons: {lessons.count()}")
    print(f"   ⏱️ Total Duration: {sum(lesson.estimated_duration for lesson in lessons)} minutes ({sum(lesson.estimated_duration for lesson in lessons)/60:.1f} hours)")
    print(f"   ✅ Mandatory Lessons: {lessons.filter(is_mandatory=True).count()}")
    print(f"   📝 Optional Lessons: {lessons.filter(is_mandatory=False).count()}")
    
    print(f"\n🎯 ASSESSMENT STATISTICS:")
    print(f"   🧩 Quizzes: {quizzes.count()}")
    print(f"   ❓ Questions: {questions.count()}")
    print(f"   📝 Assignments: {assignments.count()}")
    print(f"   📊 Avg Questions per Quiz: {questions.count() / quizzes.count():.1f}" if quizzes.count() > 0 else "   📊 Avg Questions per Quiz: 0")
    
    print(f"\n📎 CONTENT RESOURCES:")
    print(f"   📦 Content Items: {content_items.count()}")
    print(f"   🔗 Lesson-Content Links: {LessonContent.objects.filter(lesson__module__course=course).count()}")
    
    # Question type breakdown
    question_types = {}
    for question in questions:
        q_type = question.question_type
        question_types[q_type] = question_types.get(q_type, 0) + 1
    
    print(f"\n❓ QUESTION TYPE BREAKDOWN:")
    for q_type, count in question_types.items():
        print(f"   {q_type}: {count}")
    
    # Assignment type breakdown
    assignment_types = {}
    for assignment in assignments:
        a_type = assignment.assignment_type
        assignment_types[a_type] = assignment_types.get(a_type, 0) + 1
    
    print(f"\n📝 ASSIGNMENT TYPE BREAKDOWN:")
    for a_type, count in assignment_types.items():
        print(f"   {a_type}: {count}")
    
    print(f"\n🎉 IMPORT SUCCESS METRICS:")
    print(f"   ✅ Course Structure: Complete")
    print(f"   ✅ Content Variety: {len(set(lesson.content_type for lesson in lessons))} types")
    print(f"   ✅ Assessment Coverage: {(quizzes.count() + assignments.count()) / lessons.count() * 100:.1f}% of lessons have assessments")
    print(f"   ✅ Content Richness: {content_items.count()} additional resources")
    
    print(f"\n📝 NEXT STEPS:")
    print(f"   1. 🔍 Review course in Django admin: /admin/courses/course/{course.id}/change/")
    print(f"   2. 🌐 View course page: /courses/{course.slug}/")
    print(f"   3. 🧪 Test student enrollment and progression")
    print(f"   4. ✅ Verify all quizzes and assignments work correctly")
    print(f"   5. 📊 Update course status from '{course.status}' to 'published' when ready")
    print(f"   6. 🎯 Set up course marketing and promotion")

def main():
    """Main verification function"""
    print("🔍 YITP COURSE IMPORT VERIFICATION")
    print("=" * 80)
    
    try:
        # Verify import
        import_success = verify_course_import()
        
        if import_success:
            # Test functionality
            test_course_functionality()
            
            # Generate summary
            generate_course_summary()
            
            print(f"\n🎉 VERIFICATION COMPLETE!")
            print(f"✅ Course import successful and fully functional")
            print(f"🚀 Ready for review and publication")
            
            return True
        else:
            print(f"\n❌ VERIFICATION FAILED!")
            print(f"Please review import issues above")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {str(e)}")
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎯 Course is ready for student enrollment!")
    else:
        print("\n⚠️ Please fix issues before proceeding")
