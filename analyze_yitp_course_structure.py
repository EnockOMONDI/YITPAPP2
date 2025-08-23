#!/usr/bin/env python
"""
Comprehensive Analysis of YITP Course Structure
Analyzes the imported YITP course (ID: 4) in development database
"""

import os
import sys
import django
from collections import defaultdict

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ.pop('DJANGO_ENV', None)  # Ensure development mode
django.setup()

from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question, Assignment
from progress.models import Enrollment, LessonProgress

def analyze_course_structure():
    """Analyze the complete YITP course structure"""
    print("🔍 YITP COURSE STRUCTURE ANALYSIS")
    print("=" * 80)
    
    try:
        # Get the YITP course
        course = Course.objects.get(id=4, slug='yitp-9-week-virtual-training')
        
        print(f"📋 COURSE OVERVIEW")
        print(f"   Title: {course.title}")
        print(f"   ID: {course.id}")
        print(f"   Slug: {course.slug}")
        print(f"   Price: ${course.price}")
        print(f"   Duration: {course.estimated_duration} hours")
        print(f"   Difficulty: {course.difficulty_level}")
        print(f"   Status: {course.status}")
        print(f"   Published: {course.is_published}")
        print(f"   Created: {course.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        return course
        
    except Course.DoesNotExist:
        print("❌ YITP course not found in development database")
        return None

def analyze_module_structure(course):
    """Analyze module organization and hierarchy"""
    print(f"\n📚 MODULE STRUCTURE ANALYSIS")
    print("=" * 80)
    
    modules = course.modules.all().order_by('sort_order')
    
    print(f"📊 MODULE OVERVIEW:")
    print(f"   Total Modules: {modules.count()}")
    
    module_data = []
    total_duration = 0
    
    for i, module in enumerate(modules, 1):
        lessons = module.lessons.all().order_by('sort_order')
        lesson_count = lessons.count()
        module_duration = module.estimated_duration
        total_duration += module_duration
        
        print(f"\n   📖 Module {i}: {module.title}")
        print(f"      ID: {module.id}")
        print(f"      Sort Order: {module.sort_order}")
        print(f"      Lessons: {lesson_count}")
        print(f"      Duration: {module_duration} minutes ({module_duration/60:.1f} hours)")
        print(f"      Published: {module.is_published}")
        print(f"      Description: {module.description[:100]}..." if module.description else "      Description: None")
        
        module_data.append({
            'module': module,
            'lesson_count': lesson_count,
            'duration': module_duration,
            'lessons': lessons
        })
    
    print(f"\n📊 MODULE SUMMARY:")
    print(f"   Total Duration: {total_duration} minutes ({total_duration/60:.1f} hours)")
    print(f"   Average Module Duration: {total_duration/modules.count():.1f} minutes")
    
    return module_data

def analyze_lesson_structure(module_data):
    """Analyze lesson organization and content types"""
    print(f"\n📖 LESSON STRUCTURE ANALYSIS")
    print("=" * 80)
    
    total_lessons = 0
    content_types = defaultdict(int)
    duration_distribution = []
    mandatory_count = 0
    published_count = 0
    
    for module_info in module_data:
        module = module_info['module']
        lessons = module_info['lessons']
        
        print(f"\n📚 {module.title} - LESSONS:")
        
        for i, lesson in enumerate(lessons, 1):
            total_lessons += 1
            content_types[lesson.content_type] += 1
            duration_distribution.append(lesson.estimated_duration)
            
            if lesson.is_mandatory:
                mandatory_count += 1
            if lesson.is_published:
                published_count += 1
            
            print(f"   {i:2d}. {lesson.title}")
            print(f"       ID: {lesson.id} | Type: {lesson.content_type} | Duration: {lesson.estimated_duration}min")
            print(f"       Mandatory: {lesson.is_mandatory} | Published: {lesson.is_published}")
            print(f"       Sort Order: {lesson.sort_order}")
            
            # Show content preview
            if lesson.content:
                content_preview = lesson.content[:100].replace('\n', ' ').replace('\r', '')
                print(f"       Content: {content_preview}...")
            
            if lesson.video_url:
                print(f"       Video: {lesson.video_url}")
            
            if lesson.learning_objectives:
                objectives_preview = lesson.learning_objectives[:80].replace('\n', ' ')
                print(f"       Objectives: {objectives_preview}...")
    
    print(f"\n📊 LESSON SUMMARY:")
    print(f"   Total Lessons: {total_lessons}")
    print(f"   Published Lessons: {published_count}/{total_lessons}")
    print(f"   Mandatory Lessons: {mandatory_count}/{total_lessons}")
    print(f"   Optional Lessons: {total_lessons - mandatory_count}/{total_lessons}")
    
    print(f"\n📋 CONTENT TYPE DISTRIBUTION:")
    for content_type, count in content_types.items():
        percentage = (count / total_lessons) * 100
        print(f"   {content_type}: {count} lessons ({percentage:.1f}%)")
    
    print(f"\n⏱️ DURATION ANALYSIS:")
    if duration_distribution:
        avg_duration = sum(duration_distribution) / len(duration_distribution)
        min_duration = min(duration_distribution)
        max_duration = max(duration_distribution)
        total_lesson_duration = sum(duration_distribution)
        
        print(f"   Total Lesson Duration: {total_lesson_duration} minutes ({total_lesson_duration/60:.1f} hours)")
        print(f"   Average Lesson Duration: {avg_duration:.1f} minutes")
        print(f"   Shortest Lesson: {min_duration} minutes")
        print(f"   Longest Lesson: {max_duration} minutes")
    
    return {
        'total_lessons': total_lessons,
        'content_types': dict(content_types),
        'duration_stats': {
            'total': sum(duration_distribution),
            'average': sum(duration_distribution) / len(duration_distribution) if duration_distribution else 0,
            'min': min(duration_distribution) if duration_distribution else 0,
            'max': max(duration_distribution) if duration_distribution else 0
        },
        'mandatory_count': mandatory_count,
        'published_count': published_count
    }

def analyze_assessment_integration(course):
    """Analyze quiz and assignment distribution"""
    print(f"\n🎯 ASSESSMENT INTEGRATION ANALYSIS")
    print("=" * 80)
    
    # Get all lessons for the course
    lesson_ids = []
    for module in course.modules.all():
        lesson_ids.extend(module.lessons.values_list('id', flat=True))
    
    # Analyze quizzes
    quizzes = Quiz.objects.filter(lesson_id__in=lesson_ids)
    assignments = Assignment.objects.filter(lesson_id__in=lesson_ids)
    
    print(f"📊 ASSESSMENT OVERVIEW:")
    print(f"   Total Quizzes: {quizzes.count()}")
    print(f"   Total Assignments: {assignments.count()}")
    
    # Quiz analysis
    if quizzes.exists():
        print(f"\n🧩 QUIZ DETAILS:")
        quiz_questions = 0
        
        for i, quiz in enumerate(quizzes.order_by('lesson__module__sort_order', 'lesson__sort_order'), 1):
            questions = quiz.questions.all()
            question_count = questions.count()
            quiz_questions += question_count
            
            print(f"   {i}. {quiz.title}")
            print(f"      Lesson: {quiz.lesson.title}")
            print(f"      Module: {quiz.lesson.module.title}")
            print(f"      Questions: {question_count}")
            print(f"      Passing Score: {quiz.passing_score}%")
            print(f"      Max Attempts: {quiz.max_attempts}")
            print(f"      Time Limit: {quiz.time_limit or 'No limit'}")
            print(f"      Published: {quiz.is_published}")
            
            # Question type breakdown
            if questions.exists():
                question_types = defaultdict(int)
                for question in questions:
                    question_types[question.question_type] += 1
                
                print(f"      Question Types: {dict(question_types)}")
        
        print(f"\n📊 QUIZ SUMMARY:")
        print(f"   Total Questions: {quiz_questions}")
        print(f"   Average Questions per Quiz: {quiz_questions/quizzes.count():.1f}")
    
    # Assignment analysis
    if assignments.exists():
        print(f"\n📝 ASSIGNMENT DETAILS:")
        
        assignment_types = defaultdict(int)
        
        for i, assignment in enumerate(assignments.order_by('lesson__module__sort_order', 'lesson__sort_order'), 1):
            assignment_types[assignment.assignment_type] += 1
            
            print(f"   {i}. {assignment.title}")
            print(f"      Lesson: {assignment.lesson.title}")
            print(f"      Module: {assignment.lesson.module.title}")
            print(f"      Type: {assignment.assignment_type}")
            print(f"      Max Score: {assignment.max_score}")
            print(f"      Submission Format: {assignment.submission_format}")
            print(f"      Due Date: {assignment.due_date or 'No deadline'}")
            # Check if assignment has is_published attribute
            if hasattr(assignment, 'is_published'):
                print(f"      Published: {assignment.is_published}")
            else:
                print(f"      Published: N/A")
        
        print(f"\n📊 ASSIGNMENT SUMMARY:")
        print(f"   Assignment Types: {dict(assignment_types)}")
    
    return {
        'quiz_count': quizzes.count(),
        'assignment_count': assignments.count(),
        'total_questions': quiz_questions if quizzes.exists() else 0
    }

def analyze_learning_progression(course):
    """Analyze sequential flow and prerequisites"""
    print(f"\n🔄 LEARNING PROGRESSION ANALYSIS")
    print("=" * 80)
    
    modules = course.modules.all().order_by('sort_order')
    
    print(f"📋 SEQUENTIAL FLOW:")
    
    for i, module in enumerate(modules, 1):
        lessons = module.lessons.all().order_by('sort_order')
        
        print(f"\n   Module {i}: {module.title}")
        print(f"   Sort Order: {module.sort_order}")
        
        # Check unlock criteria
        if module.unlock_criteria:
            print(f"   Unlock Criteria: {module.unlock_criteria}")
        else:
            print(f"   Unlock Criteria: None (immediately available)")
        
        # Lesson progression within module
        mandatory_lessons = lessons.filter(is_mandatory=True).count()
        optional_lessons = lessons.filter(is_mandatory=False).count()
        
        print(f"   Lesson Progression:")
        print(f"     - Mandatory Lessons: {mandatory_lessons}")
        print(f"     - Optional Lessons: {optional_lessons}")
        print(f"     - Total Lessons: {lessons.count()}")
        
        # Show lesson sequence
        print(f"   Lesson Sequence:")
        for j, lesson in enumerate(lessons, 1):
            status = "MANDATORY" if lesson.is_mandatory else "OPTIONAL"
            print(f"     {j:2d}. {lesson.title} [{status}]")
    
    print(f"\n📊 PROGRESSION SUMMARY:")
    total_mandatory = sum(module.lessons.filter(is_mandatory=True).count() for module in modules)
    total_optional = sum(module.lessons.filter(is_mandatory=False).count() for module in modules)
    
    print(f"   Course Progression Type: Sequential (Module-based)")
    print(f"   Total Mandatory Content: {total_mandatory} lessons")
    print(f"   Total Optional Content: {total_optional} lessons")
    print(f"   Completion Requirement: Complete all mandatory lessons")

def generate_comprehensive_report(course, module_data, lesson_stats, assessment_stats):
    """Generate final comprehensive report"""
    print(f"\n📊 COMPREHENSIVE COURSE ANALYSIS REPORT")
    print("=" * 80)
    
    print(f"🎯 COURSE: {course.title}")
    print(f"   Course ID: {course.id}")
    print(f"   Course Slug: {course.slug}")
    print(f"   Price: ${course.price}")
    print(f"   Estimated Duration: {course.estimated_duration} hours")
    
    print(f"\n📚 STRUCTURE OVERVIEW:")
    print(f"   Modules: {len(module_data)}")
    print(f"   Lessons: {lesson_stats['total_lessons']}")
    print(f"   Quizzes: {assessment_stats['quiz_count']}")
    print(f"   Assignments: {assessment_stats['assignment_count']}")
    print(f"   Quiz Questions: {assessment_stats['total_questions']}")
    
    print(f"\n⏱️ DURATION BREAKDOWN:")
    total_module_duration = sum(m['duration'] for m in module_data)
    print(f"   Total Module Duration: {total_module_duration} minutes ({total_module_duration/60:.1f} hours)")
    print(f"   Total Lesson Duration: {lesson_stats['duration_stats']['total']} minutes ({lesson_stats['duration_stats']['total']/60:.1f} hours)")
    print(f"   Average Lesson Duration: {lesson_stats['duration_stats']['average']:.1f} minutes")
    
    print(f"\n📋 CONTENT DISTRIBUTION:")
    for content_type, count in lesson_stats['content_types'].items():
        percentage = (count / lesson_stats['total_lessons']) * 100
        print(f"   {content_type.title()}: {count} lessons ({percentage:.1f}%)")
    
    print(f"\n🎯 LEARNING REQUIREMENTS:")
    print(f"   Mandatory Lessons: {lesson_stats['mandatory_count']}/{lesson_stats['total_lessons']}")
    print(f"   Optional Lessons: {lesson_stats['total_lessons'] - lesson_stats['mandatory_count']}/{lesson_stats['total_lessons']}")
    print(f"   Published Content: {lesson_stats['published_count']}/{lesson_stats['total_lessons']}")
    
    print(f"\n🏆 COURSE READINESS:")
    readiness_score = 0
    total_checks = 5
    
    if lesson_stats['published_count'] == lesson_stats['total_lessons']:
        print(f"   ✅ All lessons published")
        readiness_score += 1
    else:
        print(f"   ⚠️ {lesson_stats['total_lessons'] - lesson_stats['published_count']} lessons not published")
    
    if assessment_stats['quiz_count'] > 0:
        print(f"   ✅ Quizzes integrated ({assessment_stats['quiz_count']} quizzes)")
        readiness_score += 1
    else:
        print(f"   ⚠️ No quizzes found")
    
    if assessment_stats['assignment_count'] > 0:
        print(f"   ✅ Assignments integrated ({assessment_stats['assignment_count']} assignments)")
        readiness_score += 1
    else:
        print(f"   ⚠️ No assignments found")
    
    if lesson_stats['content_types']:
        print(f"   ✅ Content types diversified ({len(lesson_stats['content_types'])} types)")
        readiness_score += 1
    else:
        print(f"   ⚠️ Limited content type diversity")
    
    if course.is_published:
        print(f"   ✅ Course published and ready")
        readiness_score += 1
    else:
        print(f"   ⚠️ Course not published")
    
    readiness_percentage = (readiness_score / total_checks) * 100
    print(f"\n📊 OVERALL READINESS: {readiness_score}/{total_checks} ({readiness_percentage:.0f}%)")
    
    if readiness_percentage >= 80:
        print(f"   🎉 Course is ready for student enrollment!")
    elif readiness_percentage >= 60:
        print(f"   ⚠️ Course needs minor improvements before launch")
    else:
        print(f"   🔧 Course requires significant development before launch")

def main():
    """Main analysis function"""
    print("🔍 STARTING COMPREHENSIVE YITP COURSE ANALYSIS")
    print("=" * 80)
    
    # Step 1: Analyze course structure
    course = analyze_course_structure()
    if not course:
        return
    
    # Step 2: Analyze module structure
    module_data = analyze_module_structure(course)
    
    # Step 3: Analyze lesson structure
    lesson_stats = analyze_lesson_structure(module_data)
    
    # Step 4: Analyze assessment integration
    assessment_stats = analyze_assessment_integration(course)
    
    # Step 5: Analyze learning progression
    analyze_learning_progression(course)
    
    # Step 6: Generate comprehensive report
    generate_comprehensive_report(course, module_data, lesson_stats, assessment_stats)
    
    print(f"\n🎯 ANALYSIS COMPLETE!")
    print(f"   The YITP course structure has been comprehensively analyzed.")
    print(f"   Use this information to understand the course organization")
    print(f"   and as a reference for structuring new courses.")

if __name__ == '__main__':
    main()
