#!/usr/bin/env python3
"""
List All Courses in YITP Database
=================================

This script lists all courses in the database to help identify the correct course names
for the quiz investigation.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course
from assessments.models import Quiz

def list_all_courses():
    """List all courses with their basic information"""
    print("📚 ALL COURSES IN YITP DATABASE")
    print("=" * 60)
    
    courses = Course.objects.all().order_by('created_at')
    
    if not courses:
        print("❌ No courses found in the database")
        return
    
    print(f"Found {courses.count()} courses:\n")
    
    for i, course in enumerate(courses, 1):
        print(f"{i}. **{course.title}**")
        print(f"   ID: {course.id}")
        print(f"   Slug: {course.slug}")
        print(f"   Published: {course.is_published}")
        print(f"   Created: {course.created_at.strftime('%Y-%m-%d')}")
        
        # Count modules, lessons, and quizzes
        modules = course.modules.filter(is_published=True)
        total_lessons = sum(module.lessons.filter(is_published=True).count() for module in modules)
        
        # Count quizzes
        total_quizzes = Quiz.objects.filter(
            lesson__module__course=course,
            is_published=True
        ).count()
        
        print(f"   Modules: {modules.count()}")
        print(f"   Lessons: {total_lessons}")
        print(f"   Quizzes: {total_quizzes}")
        
        # Show enrollments if any
        enrollments = course.enrollments.count()
        print(f"   Enrollments: {enrollments}")
        
        print()
    
    # Search for courses that might match the target names
    target_keywords = [
        'soft skills', 'streets', 'purpose', 'life', 'upl', 'mindset', 'power'
    ]
    
    print("\n🔍 SEARCHING FOR TARGET COURSE KEYWORDS")
    print("=" * 60)
    
    for keyword in target_keywords:
        matching_courses = Course.objects.filter(title__icontains=keyword)
        if matching_courses:
            print(f"Keyword '{keyword}' found in:")
            for course in matching_courses:
                print(f"   - {course.title} (ID: {course.id})")
        else:
            print(f"Keyword '{keyword}': No matches")
    
    print("\n📊 QUIZ DISTRIBUTION")
    print("=" * 60)
    
    courses_with_quizzes = []
    for course in courses:
        quiz_count = Quiz.objects.filter(
            lesson__module__course=course,
            is_published=True
        ).count()
        if quiz_count > 0:
            courses_with_quizzes.append((course, quiz_count))
    
    if courses_with_quizzes:
        print("Courses with quizzes:")
        for course, quiz_count in sorted(courses_with_quizzes, key=lambda x: x[1], reverse=True):
            print(f"   - {course.title}: {quiz_count} quizzes")
    else:
        print("No courses have published quizzes")

if __name__ == "__main__":
    list_all_courses()
