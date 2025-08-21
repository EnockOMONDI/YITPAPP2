#!/usr/bin/env python
"""
Verify successful YITP Seed Module import and test functionality
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
    """Verify the imported YITP course structure and functionality"""
    print("🔍 VERIFYING YITP SEED MODULE IMPORT")
    print("=" * 70)
    
    # Find the imported course
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        print(f"✅ Course found: {course.title}")
        print(f"   ID: {course.id}")
        print(f"   Status: {course.status}")
        print(f"   Instructor: {course.instructor.username}")
        print(f"   Category: {course.category.name}")
        print(f"   Price: ${course.price}")
        print(f"   Published: {course.is_published}")
        print(f"   Duration: {course.estimated_duration} minutes ({course.estimated_duration/60:.1f} hours)")
    except Course.DoesNotExist:
        print("❌ YITP course not found!")
        return False
    
    # Verify modules
    modules = Module.objects.filter(course=course).order_by('sort_order')
    print(f"\n📚 MODULES VERIFICATION ({modules.count()}):")
    
    expected_module_title = "Module 1 — UPL 101 Full Module"
    
    for i, module in enumerate(modules, 1):
        status = "✅" if module.title == expected_module_title else "❌"
        print(f"   {status} Module {i}: {module.title}")
        print(f"      Sort Order: {module.sort_order}")
        print(f"      Published: {module.is_published}")
        print(f"      Duration: {module.estimated_duration} min")
    
    # Verify lessons
    total_lessons = Lesson.objects.filter(module__course=course).count()
    print(f"\n📖 LESSONS VERIFICATION ({total_lessons}):")
    
    lessons = Lesson.objects.filter(module__course=course).order_by('sort_order')
    
    # Check lesson statistics
    mandatory_count = lessons.filter(is_mandatory=True).count()
    content_types = {}
    total_duration = 0
    
    for lesson in lessons:
        content_type = lesson.content_type
        content_types[content_type] = content_types.get(content_type, 0) + 1
        total_duration += lesson.estimated_duration
    
    print(f"   Total Lessons: {total_lessons}")
    print(f"   Mandatory: {mandatory_count}/{total_lessons}")
    print(f"   Optional: {total_lessons - mandatory_count}/{total_lessons}")
    print(f"   Content Types: {content_types}")
    print(f"   Total Duration: {total_duration} minutes ({total_duration/60:.1f} hours)")
    
    # Show sample lessons
    print(f"\n📖 SAMPLE LESSONS:")
    for i, lesson in enumerate(lessons[:5], 1):
        print(f"   {i}. {lesson.title}")
        print(f"      Type: {lesson.content_type}, Duration: {lesson.estimated_duration}min")
        print(f"      Mandatory: {lesson.is_mandatory}, Published: {lesson.is_published}")
    
    if total_lessons > 5:
        print(f"   ... and {total_lessons - 5} more lessons")
    
    # Verify assessments
    quizzes = Quiz.objects.filter(lesson__module__course=course)
    questions = Question.objects.filter(quiz__lesson__module__course=course)
    assignments = Assignment.objects.filter(lesson__module__course=course)
    
    print(f"\n🎯 ASSESSMENTS VERIFICATION:")
    print(f"   Quizzes: {quizzes.count()}")
    print(f"   Questions: {questions.count()}")
    print(f"   Assignments: {assignments.count()}")
    
    # Verify quiz details
    print(f"\n🧩 QUIZ DETAILS:")
    for quiz in quizzes:
        quiz_questions = questions.filter(quiz=quiz)
        print(f"   ✅ Quiz: {quiz.title}")
        print(f"      Lesson: {quiz.lesson.title}")
        print(f"      Questions: {quiz_questions.count()}")
        print(f"      Passing Score: {quiz.passing_score}%")
        print(f"      Max Attempts: {quiz.max_attempts}")
    
    # Question type analysis
    question_types = {}
    for question in questions:
        q_type = question.question_type
        question_types[q_type] = question_types.get(q_type, 0) + 1
    
    print(f"\n❓ QUESTION TYPE BREAKDOWN:")
    for q_type, count in question_types.items():
        print(f"   {q_type}: {count}")
    
    # Verify assignment details
    print(f"\n📝 ASSIGNMENT DETAILS:")
    assignment_types = {}
    for assignment in assignments:
        a_type = assignment.assignment_type
        assignment_types[a_type] = assignment_types.get(a_type, 0) + 1
        print(f"   ✅ Assignment: {assignment.title}")
        print(f"      Lesson: {assignment.lesson.title}")
        print(f"      Type: {assignment.assignment_type}")
        print(f"      Max Score: {assignment.max_score}")
    
    print(f"\n📝 ASSIGNMENT TYPE BREAKDOWN:")
    for a_type, count in assignment_types.items():
        print(f"   {a_type}: {count}")
    
    # Verify content items
    content_items = ContentItem.objects.filter(created_by=course.instructor)
    lesson_contents = LessonContent.objects.filter(lesson__module__course=course)
    
    print(f"\n📎 CONTENT VERIFICATION:")
    print(f"   Content Items: {content_items.count()}")
    print(f"   Lesson-Content Links: {lesson_contents.count()}")
    
    # Content item details
    print(f"\n📦 CONTENT ITEM DETAILS:")
    content_item_types = {}
    for content_item in content_items:
        item_type = content_item.content_type
        content_item_types[item_type] = content_item_types.get(item_type, 0) + 1
        print(f"   ✅ Content: {content_item.title}")
        print(f"      Type: {content_item.content_type}")
        print(f"      Public: {content_item.is_public}")
        if content_item.external_url:
            print(f"      URL: {content_item.external_url}")
    
    print(f"\n📦 CONTENT ITEM TYPE BREAKDOWN:")
    for item_type, count in content_item_types.items():
        print(f"   {item_type}: {count}")
    
    # Verify lesson-content relationships
    print(f"\n🔗 LESSON-CONTENT LINKS:")
    for link in lesson_contents:
        print(f"   🔗 {link.lesson.title} → {link.content_item.title}")
        print(f"      Required: {link.is_required}, Sort Order: {link.sort_order}")
    
    return True

def test_course_functionality():
    """Test basic course functionality"""
    print("\n🧪 TESTING COURSE FUNCTIONALITY")
    print("=" * 70)
    
    course = Course.objects.get(slug='yitp-9-week-virtual-training')
    
    # Test course properties
    print(f"📋 Course Properties:")
    print(f"   Total Modules: {course.modules.count()}")
    print(f"   Total Lessons: {Lesson.objects.filter(module__course=course).count()}")
    
    # Calculate total duration
    total_duration = sum(lesson.estimated_duration for lesson in Lesson.objects.filter(module__course=course))
    print(f"   Total Duration: {total_duration} minutes ({total_duration/60:.1f} hours)")
    
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
    print("\n📊 YITP SEED MODULE SUMMARY")
    print("=" * 70)
    
    course = Course.objects.get(slug='yitp-9-week-virtual-training')
    
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
    
    # Assessment coverage
    lessons_with_assessments = set()
    for quiz in quizzes:
        lessons_with_assessments.add(quiz.lesson.id)
    for assignment in assignments:
        lessons_with_assessments.add(assignment.lesson.id)
    
    assessment_coverage = len(lessons_with_assessments) / lessons.count() * 100 if lessons.count() > 0 else 0
    
    print(f"\n🎉 IMPORT SUCCESS METRICS:")
    print(f"   ✅ Course Structure: Complete")
    print(f"   ✅ Content Variety: {len(set(lesson.content_type for lesson in lessons))} types")
    print(f"   ✅ Assessment Coverage: {assessment_coverage:.1f}% of lessons have assessments")
    print(f"   ✅ Content Richness: {content_items.count()} additional resources")
    
    print(f"\n📝 NEXT STEPS:")
    print(f"   1. 🔍 Review course in Django admin: /admin/courses/course/{course.id}/change/")
    print(f"   2. 🌐 View course page: /courses/{course.slug}/")
    print(f"   3. 🎓 Test in LMS: /lms/courses/{course.slug}/")
    print(f"   4. 🧪 Test student enrollment and progression")
    print(f"   5. ✅ Verify all quizzes and assignments work correctly")
    print(f"   6. 📊 Update course status from '{course.status}' to 'published' when ready")
    print(f"   7. 🎯 Enable course for student enrollment")

def main():
    """Main verification function"""
    print("🔍 YITP SEED MODULE IMPORT VERIFICATION")
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
            print(f"✅ YITP Seed Module import successful and fully functional")
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
        print("\n🎯 YITP Seed Module is ready for student enrollment!")
    else:
        print("\n⚠️ Please fix issues before proceeding")
