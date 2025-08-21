#!/usr/bin/env python
"""
Analyze JSON course import requirements and database constraints
"""

import os
import sys
import django
import json
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, Category
from django.db import models

def analyze_json_structure():
    """Analyze the JSON file structure"""
    print("🔍 ANALYZING JSON FILE STRUCTURE")
    print("=" * 60)
    
    try:
        with open('new.json', 'r') as f:
            data = json.load(f)
        
        # Analyze course data
        course_data = data.get('course', {})
        print(f"📋 COURSE DATA ANALYSIS:")
        print(f"  Title: {course_data.get('title')}")
        print(f"  Slug: {course_data.get('slug')}")
        print(f"  Description Length: {len(course_data.get('description', ''))}")
        print(f"  Learning Objectives Length: {len(course_data.get('learning_objectives', ''))}")
        print(f"  Prerequisites: {course_data.get('prerequisites')}")
        print(f"  Difficulty Level: {course_data.get('difficulty_level')}")
        print(f"  Estimated Duration: {course_data.get('estimated_duration')}")
        print(f"  Price: {course_data.get('price')}")
        print(f"  Instructor: {course_data.get('instructor')}")
        print(f"  Category: {course_data.get('category')}")
        print(f"  Status: {course_data.get('status')}")
        print(f"  Is Published: {course_data.get('is_published')}")
        print(f"  Is Featured: {course_data.get('is_featured')}")
        print(f"  Enrollment Limit: {course_data.get('enrollment_limit')}")
        print(f"  Thumbnail: {course_data.get('thumbnail')}")
        
        # Analyze modules
        modules = data.get('modules', [])
        print(f"\n📚 MODULES ANALYSIS:")
        print(f"  Total Modules: {len(modules)}")
        for i, module in enumerate(modules, 1):
            print(f"  Module {i}: {module.get('title')} ({module.get('estimated_duration')} min)")
        
        # Analyze lessons
        lessons = data.get('lessons', [])
        print(f"\n📖 LESSONS ANALYSIS:")
        print(f"  Total Lessons: {len(lessons)}")
        
        content_types = {}
        mandatory_count = 0
        total_duration = 0
        
        for lesson in lessons:
            content_type = lesson.get('content_type')
            content_types[content_type] = content_types.get(content_type, 0) + 1
            
            if lesson.get('is_mandatory'):
                mandatory_count += 1
                
            duration = lesson.get('estimated_duration', 0)
            total_duration += duration
        
        print(f"  Content Types: {content_types}")
        print(f"  Mandatory Lessons: {mandatory_count}/{len(lessons)}")
        print(f"  Total Duration: {total_duration} minutes ({total_duration/60:.1f} hours)")
        
        # Analyze assessments
        quizzes = data.get('quizzes', [])
        questions = data.get('questions', [])
        assignments = data.get('assignments', [])
        
        print(f"\n🎯 ASSESSMENTS ANALYSIS:")
        print(f"  Total Quizzes: {len(quizzes)}")
        print(f"  Total Questions: {len(questions)}")
        print(f"  Total Assignments: {len(assignments)}")
        
        # Question types analysis
        question_types = {}
        for question in questions:
            q_type = question.get('question_type')
            question_types[q_type] = question_types.get(q_type, 0) + 1
        
        print(f"  Question Types: {question_types}")
        
        # Assignment types analysis
        assignment_types = {}
        for assignment in assignments:
            a_type = assignment.get('assignment_type')
            assignment_types[a_type] = assignment_types.get(a_type, 0) + 1
        
        print(f"  Assignment Types: {assignment_types}")
        
        # Content items analysis
        content_items = data.get('content_items', [])
        lesson_contents = data.get('lesson_contents', [])
        
        print(f"\n📎 CONTENT ITEMS ANALYSIS:")
        print(f"  Total Content Items: {len(content_items)}")
        print(f"  Total Lesson-Content Links: {len(lesson_contents)}")
        
        return data
        
    except Exception as e:
        print(f"❌ Error analyzing JSON: {str(e)}")
        return None

def analyze_database_constraints():
    """Analyze current database state and constraints"""
    print("\n🗄️ ANALYZING DATABASE CONSTRAINTS")
    print("=" * 60)
    
    # Check Course model fields and constraints
    print("📋 COURSE MODEL ANALYSIS:")
    course_fields = Course._meta.get_fields()
    
    for field in course_fields:
        if hasattr(field, 'max_length'):
            print(f"  {field.name}: {field.__class__.__name__} (max_length: {field.max_length})")
        elif hasattr(field, 'null'):
            print(f"  {field.name}: {field.__class__.__name__} (null: {field.null})")
        else:
            print(f"  {field.name}: {field.__class__.__name__}")
    
    # Check available instructors
    print(f"\n👨‍🏫 AVAILABLE INSTRUCTORS:")
    instructors = User.objects.filter(is_staff=True, is_active=True)
    
    if instructors.exists():
        for instructor in instructors:
            print(f"  ID: {instructor.id} | Username: {instructor.username} | Name: {instructor.get_full_name()} | Email: {instructor.email}")
    else:
        print("  ❌ No staff users found")
        
        # Check all active users
        all_users = User.objects.filter(is_active=True)[:10]
        print(f"\n👤 AVAILABLE ACTIVE USERS (first 10):")
        for user in all_users:
            print(f"  ID: {user.id} | Username: {user.username} | Name: {user.get_full_name()} | Email: {user.email}")
    
    # Check available categories
    print(f"\n📂 AVAILABLE CATEGORIES:")
    categories = Category.objects.all()
    
    if categories.exists():
        for category in categories:
            print(f"  ID: {category.id} | Name: {category.name} | Slug: {category.slug}")
    else:
        print("  ❌ No categories found")
    
    # Check existing courses for conflicts
    print(f"\n📚 EXISTING COURSES (checking for conflicts):")
    existing_courses = Course.objects.all()
    
    if existing_courses.exists():
        for course in existing_courses:
            print(f"  ID: {course.id} | Title: {course.title} | Slug: {course.slug} | Status: {course.status}")
    else:
        print("  ✅ No existing courses found")
    
    return {
        'instructors': list(instructors.values('id', 'username', 'first_name', 'last_name', 'email')),
        'categories': list(categories.values('id', 'name', 'slug')),
        'existing_courses': list(existing_courses.values('id', 'title', 'slug', 'status'))
    }

def identify_import_issues(json_data, db_data):
    """Identify potential import issues"""
    print("\n⚠️ IDENTIFYING POTENTIAL IMPORT ISSUES")
    print("=" * 60)
    
    issues = []
    recommendations = []
    
    course_data = json_data.get('course', {})
    
    # Check instructor assignment
    if course_data.get('instructor') is None:
        issues.append("❌ CRITICAL: instructor field is null")
        if db_data['instructors']:
            recommended_instructor = db_data['instructors'][0]
            recommendations.append(f"✅ RECOMMEND: Assign to instructor ID {recommended_instructor['id']} ({recommended_instructor['username']})")
        else:
            recommendations.append("⚠️ RECOMMEND: Create an instructor user first")
    
    # Check category assignment
    if course_data.get('category') is None:
        issues.append("❌ CRITICAL: category field is null")
        if db_data['categories']:
            recommended_category = db_data['categories'][0]
            recommendations.append(f"✅ RECOMMEND: Assign to category ID {recommended_category['id']} ({recommended_category['name']})")
        else:
            recommendations.append("⚠️ RECOMMEND: Create a category first")
    
    # Check for slug conflicts
    course_slug = course_data.get('slug')
    existing_slugs = [course['slug'] for course in db_data['existing_courses']]
    if course_slug in existing_slugs:
        issues.append(f"❌ CONFLICT: slug '{course_slug}' already exists")
        recommendations.append(f"✅ RECOMMEND: Change slug to '{course_slug}-v2' or '{course_slug}-2024'")
    
    # Check for title conflicts
    course_title = course_data.get('title')
    existing_titles = [course['title'] for course in db_data['existing_courses']]
    if course_title in existing_titles:
        issues.append(f"❌ CONFLICT: title '{course_title}' already exists")
        recommendations.append(f"✅ RECOMMEND: Modify title to include version or year")
    
    # Check required fields
    required_fields = ['title', 'description', 'learning_objectives']
    for field in required_fields:
        if not course_data.get(field):
            issues.append(f"❌ MISSING: {field} is required but empty")
            recommendations.append(f"✅ RECOMMEND: Provide content for {field}")
    
    # Check field lengths
    if len(course_data.get('title', '')) > 200:
        issues.append("❌ LENGTH: title exceeds 200 characters")
        recommendations.append("✅ RECOMMEND: Shorten title to under 200 characters")
    
    if len(course_data.get('slug', '')) > 200:
        issues.append("❌ LENGTH: slug exceeds 200 characters")
        recommendations.append("✅ RECOMMEND: Shorten slug to under 200 characters")
    
    # Check difficulty level
    valid_difficulty_levels = ['beginner', 'intermediate', 'advanced']
    if course_data.get('difficulty_level') not in valid_difficulty_levels:
        issues.append(f"❌ INVALID: difficulty_level '{course_data.get('difficulty_level')}' not in {valid_difficulty_levels}")
        recommendations.append("✅ RECOMMEND: Use 'beginner', 'intermediate', or 'advanced'")
    
    # Check status
    valid_statuses = ['draft', 'in_review', 'approved', 'published', 'rejected', 'archived']
    if course_data.get('status') not in valid_statuses:
        issues.append(f"❌ INVALID: status '{course_data.get('status')}' not in {valid_statuses}")
        recommendations.append("✅ RECOMMEND: Use 'draft' for initial import")
    
    # Check price format
    try:
        price = float(course_data.get('price', 0))
        if price < 0:
            issues.append("❌ INVALID: price cannot be negative")
            recommendations.append("✅ RECOMMEND: Set price to 0.00 for free course")
    except (ValueError, TypeError):
        issues.append("❌ INVALID: price must be a number")
        recommendations.append("✅ RECOMMEND: Set price to 0.00")
    
    # Check enrollment limit
    enrollment_limit = course_data.get('enrollment_limit', 0)
    if enrollment_limit < 0:
        issues.append("❌ INVALID: enrollment_limit cannot be negative")
        recommendations.append("✅ RECOMMEND: Set enrollment_limit to 0 for unlimited")
    
    # Print issues and recommendations
    if issues:
        print("🚨 ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ No critical issues found")
    
    if recommendations:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"  {rec}")
    
    return issues, recommendations

def validate_import_compatibility(json_data):
    """Validate JSON structure compatibility with YITP models"""
    print("\n🔍 VALIDATING IMPORT COMPATIBILITY")
    print("=" * 60)
    
    compatibility_issues = []
    
    # Check course structure
    course_data = json_data.get('course', {})
    required_course_fields = ['title', 'slug', 'description', 'learning_objectives']
    
    for field in required_course_fields:
        if field not in course_data:
            compatibility_issues.append(f"❌ Missing required course field: {field}")
    
    # Check modules structure
    modules = json_data.get('modules', [])
    if not modules:
        compatibility_issues.append("❌ No modules found - course needs at least one module")
    
    for module in modules:
        if 'title' not in module or 'course_slug' not in module:
            compatibility_issues.append("❌ Module missing required fields: title, course_slug")
    
    # Check lessons structure
    lessons = json_data.get('lessons', [])
    if not lessons:
        compatibility_issues.append("❌ No lessons found - course needs at least one lesson")
    
    for lesson in lessons:
        required_lesson_fields = ['title', 'module_id', 'content_type']
        for field in required_lesson_fields:
            if field not in lesson:
                compatibility_issues.append(f"❌ Lesson missing required field: {field}")
    
    # Check assessment structure
    quizzes = json_data.get('quizzes', [])
    questions = json_data.get('questions', [])
    
    if quizzes and not questions:
        compatibility_issues.append("⚠️ Quizzes found but no questions - quizzes will be empty")
    
    # Print compatibility results
    if compatibility_issues:
        print("🚨 COMPATIBILITY ISSUES:")
        for issue in compatibility_issues:
            print(f"  {issue}")
    else:
        print("✅ JSON structure is compatible with YITP models")
    
    return compatibility_issues

def generate_import_recommendations():
    """Generate specific recommendations for successful import"""
    print("\n📋 IMPORT RECOMMENDATIONS SUMMARY")
    print("=" * 60)
    
    print("🔧 REQUIRED ACTIONS BEFORE IMPORT:")
    print("  1. Fix instructor assignment (assign to existing instructor)")
    print("  2. Fix category assignment (assign to existing category)")
    print("  3. Resolve any slug/title conflicts")
    print("  4. Validate all required fields are populated")
    print("  5. Ensure field lengths are within limits")
    
    print("\n📝 SUGGESTED IMPORT PROCESS:")
    print("  1. Create/update JSON with recommended fixes")
    print("  2. Import course first (without modules/lessons)")
    print("  3. Import modules linked to course")
    print("  4. Import lessons linked to modules")
    print("  5. Import quizzes and questions")
    print("  6. Import assignments")
    print("  7. Import content items and lesson-content links")
    print("  8. Test course structure and functionality")
    
    print("\n⚠️ IMPORTANT NOTES:")
    print("  - Start with status='draft' for testing")
    print("  - Set is_published=False initially")
    print("  - Test course progression before publishing")
    print("  - Verify all assessments work correctly")
    print("  - Check content display and formatting")

def main():
    """Run comprehensive import analysis"""
    print("🔍 YITP COURSE IMPORT ANALYSIS")
    print("=" * 80)
    
    # Analyze JSON structure
    json_data = analyze_json_structure()
    
    if json_data:
        # Analyze database constraints
        db_data = analyze_database_constraints()
        
        # Identify import issues
        issues, recommendations = identify_import_issues(json_data, db_data)
        
        # Validate compatibility
        compatibility_issues = validate_import_compatibility(json_data)
        
        # Generate recommendations
        generate_import_recommendations()
        
        # Final summary
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"  Total Issues Found: {len(issues) + len(compatibility_issues)}")
        print(f"  Critical Issues: {len([i for i in issues if 'CRITICAL' in i])}")
        print(f"  Compatibility Issues: {len(compatibility_issues)}")
        print(f"  Recommendations: {len(recommendations)}")
        
        if len(issues) + len(compatibility_issues) == 0:
            print(f"\n🎉 READY FOR IMPORT!")
        else:
            print(f"\n⚠️ REQUIRES FIXES BEFORE IMPORT")
    
    return json_data

if __name__ == '__main__':
    main()
