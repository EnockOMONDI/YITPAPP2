#!/usr/bin/env python
"""
Comprehensive analysis of yitp_seed_module1.json for import into YITP platform
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
from courses.models import Course, Category, Module, Lesson
from assessments.models import Quiz, Question, Assignment
from content.models import ContentItem, LessonContent
from django.db import models

def analyze_json_structure():
    """Analyze the yitp_seed_module1.json file structure"""
    print("🔍 ANALYZING YITP SEED MODULE JSON STRUCTURE")
    print("=" * 70)
    
    try:
        with open('yitp_seed_module1.json', 'r') as f:
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
        print(f"  Estimated Duration: {course_data.get('estimated_duration')} minutes")
        print(f"  Price: ${course_data.get('price')}")
        print(f"  Instructor ID: {course_data.get('instructor')}")
        print(f"  Category ID: {course_data.get('category')}")
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
            print(f"    ID: {module.get('id')}")
            print(f"    Course Slug: {module.get('course_slug')}")
            print(f"    Sort Order: {module.get('sort_order')}")
            print(f"    Published: {module.get('is_published')}")
        
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
        
        # Show first few lessons as examples
        print(f"\n📖 SAMPLE LESSONS:")
        for i, lesson in enumerate(lessons[:5], 1):
            print(f"  {i}. {lesson.get('title')}")
            print(f"     Type: {lesson.get('content_type')}, Duration: {lesson.get('estimated_duration')}min")
            print(f"     Module: {lesson.get('module_id')}, Mandatory: {lesson.get('is_mandatory')}")
        
        if len(lessons) > 5:
            print(f"  ... and {len(lessons) - 5} more lessons")
        
        # Analyze assessments
        quizzes = data.get('quizzes', [])
        questions = data.get('questions', [])
        assignments = data.get('assignments', [])
        
        print(f"\n🎯 ASSESSMENTS ANALYSIS:")
        print(f"  Total Quizzes: {len(quizzes)}")
        print(f"  Total Questions: {len(questions)}")
        print(f"  Total Assignments: {len(assignments)}")
        
        # Question types analysis
        if questions:
            question_types = {}
            for question in questions:
                q_type = question.get('question_type')
                question_types[q_type] = question_types.get(q_type, 0) + 1
            print(f"  Question Types: {question_types}")
        
        # Assignment types analysis
        if assignments:
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
        
        if content_items:
            content_item_types = {}
            for item in content_items:
                item_type = item.get('content_type')
                content_item_types[item_type] = content_item_types.get(item_type, 0) + 1
            print(f"  Content Item Types: {content_item_types}")
        
        return data
        
    except Exception as e:
        print(f"❌ Error analyzing JSON: {str(e)}")
        return None

def investigate_production_database():
    """Investigate current production database state"""
    print("\n🗄️ INVESTIGATING PRODUCTION DATABASE")
    print("=" * 70)
    
    # Check available instructors
    print(f"👨‍🏫 AVAILABLE INSTRUCTORS:")
    instructors = User.objects.filter(is_staff=True, is_active=True)
    
    if instructors.exists():
        for instructor in instructors:
            print(f"  ID: {instructor.id} | Username: {instructor.username}")
            print(f"      Name: {instructor.get_full_name()} | Email: {instructor.email}")
            print(f"      Staff: {instructor.is_staff} | Superuser: {instructor.is_superuser}")
    else:
        print("  ❌ No staff users found")
        
        # Check all active users
        all_users = User.objects.filter(is_active=True)[:10]
        print(f"\n👤 AVAILABLE ACTIVE USERS (first 10):")
        for user in all_users:
            print(f"  ID: {user.id} | Username: {user.username}")
            print(f"      Name: {user.get_full_name()} | Email: {user.email}")
    
    # Check available categories
    print(f"\n📂 AVAILABLE CATEGORIES:")
    categories = Category.objects.all()
    
    if categories.exists():
        for category in categories:
            print(f"  ID: {category.id} | Name: {category.name} | Slug: {category.slug}")
    else:
        print("  ❌ No categories found")
    
    # Check if 'Virtual Training' category exists
    virtual_training_exists = Category.objects.filter(name='Virtual Training').exists()
    print(f"\n🎯 VIRTUAL TRAINING CATEGORY:")
    if virtual_training_exists:
        vt_category = Category.objects.get(name='Virtual Training')
        print(f"  ✅ Virtual Training category exists: ID {vt_category.id}")
    else:
        print(f"  ❌ Virtual Training category does NOT exist - needs to be created")
    
    # Check existing courses for conflicts
    print(f"\n📚 EXISTING COURSES (checking for conflicts):")
    existing_courses = Course.objects.all()
    
    if existing_courses.exists():
        for course in existing_courses:
            print(f"  ID: {course.id} | Title: {course.title}")
            print(f"      Slug: {course.slug} | Status: {course.status}")
    else:
        print("  ✅ No existing courses found")
    
    return {
        'instructors': list(instructors.values('id', 'username', 'first_name', 'last_name', 'email')),
        'categories': list(categories.values('id', 'name', 'slug')),
        'existing_courses': list(existing_courses.values('id', 'title', 'slug', 'status')),
        'virtual_training_exists': virtual_training_exists
    }

def create_virtual_training_category():
    """Create Virtual Training category if it doesn't exist"""
    print("\n📂 CREATING VIRTUAL TRAINING CATEGORY")
    print("=" * 70)
    
    try:
        category, created = Category.objects.get_or_create(
            name='Virtual Training',
            defaults={
                'slug': 'virtual-training',
                'description': 'Virtual training programs and online courses for skill development'
            }
        )
        
        if created:
            print(f"✅ Created new category: {category.name} (ID: {category.id})")
        else:
            print(f"✅ Category already exists: {category.name} (ID: {category.id})")
        
        return category.id
        
    except Exception as e:
        print(f"❌ Error creating category: {str(e)}")
        return None

def identify_import_issues(json_data, db_data):
    """Identify potential import issues and recommend fixes"""
    print("\n⚠️ IDENTIFYING POTENTIAL IMPORT ISSUES")
    print("=" * 70)
    
    issues = []
    recommendations = []
    
    course_data = json_data.get('course', {})
    
    # Check instructor assignment
    instructor_id = course_data.get('instructor')
    if instructor_id is None:
        issues.append("❌ CRITICAL: instructor field is null")
        if db_data['instructors']:
            recommended_instructor = db_data['instructors'][0]
            recommendations.append(f"✅ RECOMMEND: Assign to instructor ID {recommended_instructor['id']} ({recommended_instructor['username']})")
        else:
            recommendations.append("⚠️ RECOMMEND: Create an instructor user first")
    else:
        # Check if instructor exists
        instructor_exists = any(inst['id'] == instructor_id for inst in db_data['instructors'])
        if instructor_exists:
            instructor_name = next(inst['username'] for inst in db_data['instructors'] if inst['id'] == instructor_id)
            print(f"✅ Instructor ID {instructor_id} ({instructor_name}) exists")
        else:
            issues.append(f"❌ CRITICAL: instructor ID {instructor_id} does not exist")
            if db_data['instructors']:
                recommended_instructor = db_data['instructors'][0]
                recommendations.append(f"✅ RECOMMEND: Change to instructor ID {recommended_instructor['id']} ({recommended_instructor['username']})")
    
    # Check category assignment
    category_id = course_data.get('category')
    if category_id is None:
        issues.append("❌ CRITICAL: category field is null")
        recommendations.append("✅ RECOMMEND: Assign to Virtual Training category (will be created)")
    else:
        # Check if category exists
        category_exists = any(cat['id'] == category_id for cat in db_data['categories'])
        if category_exists:
            category_name = next(cat['name'] for cat in db_data['categories'] if cat['id'] == category_id)
            print(f"✅ Category ID {category_id} ({category_name}) exists")
        else:
            issues.append(f"❌ CRITICAL: category ID {category_id} does not exist")
            recommendations.append("✅ RECOMMEND: Create Virtual Training category and assign")
    
    # Check for slug conflicts
    course_slug = course_data.get('slug')
    existing_slugs = [course['slug'] for course in db_data['existing_courses']]
    if course_slug in existing_slugs:
        issues.append(f"❌ CONFLICT: slug '{course_slug}' already exists")
        recommendations.append(f"✅ RECOMMEND: Change slug to '{course_slug}-2024' or '{course_slug}-v2'")
    else:
        print(f"✅ Slug '{course_slug}' is available")
    
    # Check for title conflicts
    course_title = course_data.get('title')
    existing_titles = [course['title'] for course in db_data['existing_courses']]
    if course_title in existing_titles:
        issues.append(f"❌ CONFLICT: title '{course_title}' already exists")
        recommendations.append(f"✅ RECOMMEND: Modify title to include version or year")
    else:
        print(f"✅ Title '{course_title}' is available")
    
    # Check required fields
    required_fields = ['title', 'description', 'learning_objectives']
    for field in required_fields:
        if not course_data.get(field):
            issues.append(f"❌ MISSING: {field} is required but empty")
            recommendations.append(f"✅ RECOMMEND: Provide content for {field}")
        else:
            print(f"✅ Required field '{field}' is populated")
    
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
    else:
        print(f"✅ Valid difficulty level: {course_data.get('difficulty_level')}")
    
    # Check status
    valid_statuses = ['draft', 'in_review', 'approved', 'published', 'rejected', 'archived']
    if course_data.get('status') not in valid_statuses:
        issues.append(f"❌ INVALID: status '{course_data.get('status')}' not in {valid_statuses}")
        recommendations.append("✅ RECOMMEND: Use 'draft' for initial import")
    else:
        print(f"✅ Valid status: {course_data.get('status')}")
    
    # Check price format
    try:
        price = float(course_data.get('price', 0))
        if price < 0:
            issues.append("❌ INVALID: price cannot be negative")
            recommendations.append("✅ RECOMMEND: Set price to 0.00 for free course")
        else:
            print(f"✅ Valid price: ${price}")
    except (ValueError, TypeError):
        issues.append("❌ INVALID: price must be a number")
        recommendations.append("✅ RECOMMEND: Set price to 0.00")
    
    # Check enrollment limit
    enrollment_limit = course_data.get('enrollment_limit', 0)
    if enrollment_limit < 0:
        issues.append("❌ INVALID: enrollment_limit cannot be negative")
        recommendations.append("✅ RECOMMEND: Set enrollment_limit to 0 for unlimited")
    else:
        print(f"✅ Valid enrollment limit: {enrollment_limit}")
    
    # Print issues and recommendations
    if issues:
        print(f"\n🚨 ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"\n✅ No critical issues found")
    
    if recommendations:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"  {rec}")
    
    return issues, recommendations

def validate_import_compatibility(json_data):
    """Validate JSON structure compatibility with YITP models"""
    print("\n🔍 VALIDATING IMPORT COMPATIBILITY")
    print("=" * 70)

    compatibility_issues = []

    # Check course structure
    course_data = json_data.get('course', {})
    required_course_fields = ['title', 'slug', 'description', 'learning_objectives']

    for field in required_course_fields:
        if field not in course_data:
            compatibility_issues.append(f"❌ Missing required course field: {field}")
        else:
            print(f"✅ Course field present: {field}")

    # Check modules structure
    modules = json_data.get('modules', [])
    if not modules:
        compatibility_issues.append("❌ No modules found - course needs at least one module")
    else:
        print(f"✅ Found {len(modules)} modules")

    for i, module in enumerate(modules, 1):
        if 'title' not in module or 'course_slug' not in module:
            compatibility_issues.append(f"❌ Module {i} missing required fields: title, course_slug")
        else:
            print(f"✅ Module {i} structure valid: {module.get('title')}")

    # Check lessons structure
    lessons = json_data.get('lessons', [])
    if not lessons:
        compatibility_issues.append("❌ No lessons found - course needs at least one lesson")
    else:
        print(f"✅ Found {len(lessons)} lessons")

    lesson_issues = 0
    for lesson in lessons:
        required_lesson_fields = ['title', 'module_id', 'content_type']
        for field in required_lesson_fields:
            if field not in lesson:
                lesson_issues += 1
                break

    if lesson_issues > 0:
        compatibility_issues.append(f"❌ {lesson_issues} lessons missing required fields")
    else:
        print(f"✅ All lessons have required fields")

    # Check assessment structure
    quizzes = json_data.get('quizzes', [])
    questions = json_data.get('questions', [])
    assignments = json_data.get('assignments', [])

    print(f"✅ Assessment structure: {len(quizzes)} quizzes, {len(questions)} questions, {len(assignments)} assignments")

    if quizzes and not questions:
        compatibility_issues.append("⚠️ Quizzes found but no questions - quizzes will be empty")

    # Check content items structure
    content_items = json_data.get('content_items', [])
    lesson_contents = json_data.get('lesson_contents', [])

    print(f"✅ Content structure: {len(content_items)} content items, {len(lesson_contents)} lesson-content links")

    # Print compatibility results
    if compatibility_issues:
        print(f"\n🚨 COMPATIBILITY ISSUES:")
        for issue in compatibility_issues:
            print(f"  {issue}")
    else:
        print(f"\n✅ JSON structure is compatible with YITP models")

    return compatibility_issues

def generate_import_recommendations(json_data, db_data, issues, recommendations):
    """Generate specific recommendations for successful import"""
    print("\n📋 IMPORT RECOMMENDATIONS SUMMARY")
    print("=" * 70)

    course_data = json_data.get('course', {})

    print("🔧 REQUIRED ACTIONS BEFORE IMPORT:")

    # Virtual Training category
    if not db_data['virtual_training_exists']:
        print("  1. ✅ Create 'Virtual Training' category (will be done automatically)")
    else:
        print("  1. ✅ Virtual Training category already exists")

    # Instructor assignment
    instructor_id = course_data.get('instructor')
    if instructor_id and any(inst['id'] == instructor_id for inst in db_data['instructors']):
        instructor_name = next(inst['username'] for inst in db_data['instructors'] if inst['id'] == instructor_id)
        print(f"  2. ✅ Instructor assignment valid: ID {instructor_id} ({instructor_name})")
    else:
        if db_data['instructors']:
            recommended = db_data['instructors'][0]
            print(f"  2. 🔧 Fix instructor assignment: Use ID {recommended['id']} ({recommended['username']})")
        else:
            print("  2. ❌ No instructors available - create instructor user first")

    # Category assignment
    category_id = course_data.get('category')
    if category_id and any(cat['id'] == category_id for cat in db_data['categories']):
        category_name = next(cat['name'] for cat in db_data['categories'] if cat['id'] == category_id)
        print(f"  3. ✅ Category assignment valid: ID {category_id} ({category_name})")
    else:
        print(f"  3. 🔧 Fix category assignment: Use Virtual Training category")

    # Slug conflicts
    course_slug = course_data.get('slug')
    existing_slugs = [course['slug'] for course in db_data['existing_courses']]
    if course_slug not in existing_slugs:
        print(f"  4. ✅ Slug is unique: {course_slug}")
    else:
        print(f"  4. 🔧 Fix slug conflict: Change '{course_slug}' to unique value")

    print(f"\n📝 SUGGESTED IMPORT PROCESS:")
    print(f"  1. Create Virtual Training category (if needed)")
    print(f"  2. Fix any data issues in JSON file")
    print(f"  3. Import course with corrected data")
    print(f"  4. Import modules linked to course")
    print(f"  5. Import lessons linked to modules")
    print(f"  6. Import quizzes and questions")
    print(f"  7. Import assignments")
    print(f"  8. Import content items and lesson-content links")
    print(f"  9. Test course structure and functionality")

    print(f"\n⚠️ IMPORTANT NOTES:")
    print(f"  - Course will be imported with status='{course_data.get('status')}' and is_published={course_data.get('is_published')}")
    print(f"  - Total content: {len(json_data.get('modules', []))} modules, {len(json_data.get('lessons', []))} lessons")
    print(f"  - Estimated duration: {course_data.get('estimated_duration')} minutes")
    print(f"  - Price: ${course_data.get('price')} (free course)")
    print(f"  - Test course progression before publishing")
    print(f"  - Verify all assessments work correctly")

def main():
    """Run comprehensive import analysis"""
    print("🔍 YITP SEED MODULE IMPORT ANALYSIS")
    print("=" * 80)

    # Analyze JSON structure
    json_data = analyze_json_structure()

    if json_data:
        # Investigate database
        db_data = investigate_production_database()

        # Create Virtual Training category if needed
        if not db_data['virtual_training_exists']:
            vt_category_id = create_virtual_training_category()
            if vt_category_id:
                db_data['categories'].append({
                    'id': vt_category_id,
                    'name': 'Virtual Training',
                    'slug': 'virtual-training'
                })
                db_data['virtual_training_exists'] = True

        # Identify import issues
        issues, recommendations = identify_import_issues(json_data, db_data)

        # Validate compatibility
        compatibility_issues = validate_import_compatibility(json_data)

        # Generate recommendations
        generate_import_recommendations(json_data, db_data, issues, recommendations)

        # Final summary
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"  Total Issues Found: {len(issues) + len(compatibility_issues)}")
        print(f"  Critical Issues: {len([i for i in issues if 'CRITICAL' in i])}")
        print(f"  Compatibility Issues: {len(compatibility_issues)}")
        print(f"  Recommendations: {len(recommendations)}")

        if len(issues) + len(compatibility_issues) == 0:
            print(f"\n🎉 READY FOR IMPORT!")
            print(f"✅ All prerequisites satisfied")
            print(f"✅ No critical issues found")
            print(f"✅ JSON structure compatible")
        else:
            print(f"\n⚠️ REQUIRES FIXES BEFORE IMPORT")
            print(f"🔧 Review issues and recommendations above")

    return json_data

if __name__ == '__main__':
    main()
