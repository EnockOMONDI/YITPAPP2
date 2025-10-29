#!/usr/bin/env python3
"""
Investigate Module 1 structure and implementation approach
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question

def investigate_module1():
    """Investigate Module 1 structure"""
    
    # Get course
    course = Course.objects.get(slug='youth-impact-training-programme-yitp')
    print(f"🎓 Course: {course.title}")
    
    # Check existing modules
    modules = Module.objects.filter(course=course).order_by('sort_order')
    print(f"\n📚 Total modules: {modules.count()}")
    
    for module in modules:
        lessons_count = Lesson.objects.filter(module=module).count()
        print(f"  Module {module.sort_order}: {module.title} (ID: {module.id}) - {lessons_count} lessons")
    
    # Focus on Module 1
    try:
        module1 = Module.objects.get(course=course, sort_order=1)
        print(f"\n🔍 ANALYZING MODULE 1: {module1.title}")
        print(f"   ID: {module1.id}")
        print(f"   Description: {module1.description[:100]}...")
        print(f"   Duration: {module1.estimated_duration} minutes")
        print(f"   Published: {module1.is_published}")
        
        # Get Module 1 lessons
        lessons = Lesson.objects.filter(module=module1).order_by('sort_order')
        print(f"\n📋 Module 1 Lessons ({lessons.count()} total):")
        
        for lesson in lessons:
            quiz = Quiz.objects.filter(lesson=lesson).first()
            quiz_info = f"Quiz ID: {quiz.id}" if quiz else "No quiz"
            
            print(f"\n  📖 Lesson {lesson.sort_order}: {lesson.title}")
            print(f"      ID: {lesson.id}")
            print(f"      Content Type: {lesson.content_type}")
            print(f"      Duration: {lesson.estimated_duration} minutes")
            print(f"      Published: {lesson.is_published}")
            print(f"      Mandatory: {lesson.is_mandatory}")
            print(f"      Quiz: {quiz_info}")
            
            # Content analysis
            if lesson.content:
                content_length = len(lesson.content)
                print(f"      Content Length: {content_length} characters")
                
                # Check content structure
                if lesson.content.startswith('<div'):
                    print(f"      Content Format: HTML div-based")
                elif lesson.content.startswith('<h'):
                    print(f"      Content Format: HTML heading-based")
                elif '<iframe' in lesson.content:
                    print(f"      Content Format: iframe-based (Module 2 style)")
                else:
                    print(f"      Content Format: Plain text/other")
                
                # Show content preview
                preview = lesson.content[:150].replace('\n', ' ')
                print(f"      Content Preview: {preview}...")
            else:
                print(f"      Content: Empty")
            
            # Check other content fields
            if lesson.video_url:
                print(f"      Video URL: {lesson.video_url}")
            if lesson.document_url:
                print(f"      Document URL: {lesson.document_url}")
            if lesson.audio_url:
                print(f"      Audio URL: {lesson.audio_url}")
            if lesson.presentation_file:
                print(f"      Presentation File: {lesson.presentation_file}")
            
            # Quiz details
            if quiz:
                questions = Question.objects.filter(quiz=quiz)
                print(f"      Quiz Details:")
                print(f"        - Questions: {questions.count()}")
                print(f"        - Passing Score: {quiz.passing_score}%")
                print(f"        - Max Attempts: {quiz.max_attempts}")
                print(f"        - Time Limit: {quiz.time_limit or 'None'}")
                print(f"        - Randomized: {quiz.is_randomized}")
                print(f"        - Show Results: {quiz.show_results}")
        
    except Module.DoesNotExist:
        print("❌ Module 1 not found")
        return False
    
    # Check if Module 3 exists
    try:
        module3 = Module.objects.get(course=course, sort_order=3)
        print(f"\n⚠️  Module 3 already exists: {module3.title} (ID: {module3.id})")
        return False
    except Module.DoesNotExist:
        print(f"\n✅ Module 3 slot available for implementation")
        return True

if __name__ == "__main__":
    print("🔍 Investigating Module 1 Structure and Implementation Approach...")
    success = investigate_module1()
    if success:
        print("\n✅ Investigation complete - ready for Module 3 implementation!")
    else:
        print("\n⚠️  Investigation complete - check findings above.")
