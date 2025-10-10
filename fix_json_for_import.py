#!/usr/bin/env python
"""
Fix JSON file for successful import into YITP platform
"""

import json
import os

def fix_json_file():
    """Fix the JSON file with recommended corrections"""
    print("🔧 FIXING JSON FILE FOR IMPORT")
    print("=" * 50)
    
    # Load original JSON
    with open('new.json', 'r') as f:
        data = json.load(f)
    
    # Fix course data
    course_data = data['course']
    
    # Critical fixes
    course_data['instructor'] = 1  # Assign to yiptadmin00
    course_data['category'] = 1    # Assign to Platform Training
    
    # Prevent conflicts with existing course
    original_title = course_data['title']
    original_slug = course_data['slug']
    
    # Since there's already "Understanding Purpose In life", make this more specific
    course_data['title'] = "Understanding Purpose in Life (UPL) 101 - Complete Course"
    course_data['slug'] = "understanding-purpose-in-life-upl-101-complete"
    
    # Set safe initial status
    course_data['status'] = 'draft'
    course_data['is_published'] = False
    course_data['is_featured'] = False
    
    # Ensure price is proper decimal
    course_data['price'] = 0.00
    
    # Update module references to new course slug
    for module in data['modules']:
        module['course_slug'] = course_data['slug']
    
    print(f"✅ Fixed course title: '{original_title}' → '{course_data['title']}'")
    print(f"✅ Fixed course slug: '{original_slug}' → '{course_data['slug']}'")
    print(f"✅ Assigned instructor: ID {course_data['instructor']}")
    print(f"✅ Assigned category: ID {course_data['category']}")
    print(f"✅ Set status to: {course_data['status']}")
    
    # Save corrected JSON
    with open('new_corrected.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Corrected JSON saved as: new_corrected.json")
    
    return data

def validate_corrections():
    """Validate that corrections are properly applied"""
    print("\n🔍 VALIDATING CORRECTIONS")
    print("=" * 50)
    
    with open('new_corrected.json', 'r') as f:
        data = json.load(f)
    
    course_data = data['course']
    issues = []
    
    # Check critical fixes
    if course_data.get('instructor') is None:
        issues.append("❌ Instructor still null")
    else:
        print(f"✅ Instructor assigned: {course_data['instructor']}")
    
    if course_data.get('category') is None:
        issues.append("❌ Category still null")
    else:
        print(f"✅ Category assigned: {course_data['category']}")
    
    # Check slug uniqueness
    if course_data.get('slug') == 'understanding-purpose-in-life':
        issues.append("❌ Slug still conflicts with existing course")
    else:
        print(f"✅ Unique slug: {course_data['slug']}")
    
    # Check status
    if course_data.get('status') not in ['draft', 'in_review', 'approved', 'published']:
        issues.append("❌ Invalid status")
    else:
        print(f"✅ Valid status: {course_data['status']}")
    
    # Check module references
    course_slug = course_data['slug']
    for i, module in enumerate(data['modules'], 1):
        if module.get('course_slug') != course_slug:
            issues.append(f"❌ Module {i} has incorrect course_slug reference")
        else:
            print(f"✅ Module {i} correctly references course slug")
    
    if issues:
        print(f"\n🚨 REMAINING ISSUES:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print(f"\n🎉 ALL CORRECTIONS VALIDATED SUCCESSFULLY!")
        return True

def create_import_summary():
    """Create import summary with statistics"""
    print("\n📊 IMPORT SUMMARY")
    print("=" * 50)
    
    with open('new_corrected.json', 'r') as f:
        data = json.load(f)
    
    print(f"📋 Course: {data['course']['title']}")
    print(f"📚 Modules: {len(data['modules'])}")
    print(f"📖 Lessons: {len(data['lessons'])}")
    print(f"🎯 Quizzes: {len(data['quizzes'])}")
    print(f"❓ Questions: {len(data['questions'])}")
    print(f"📝 Assignments: {len(data['assignments'])}")
    print(f"📎 Content Items: {len(data['content_items'])}")
    print(f"🔗 Lesson-Content Links: {len(data['lesson_contents'])}")
    
    # Calculate total content
    total_lessons = len(data['lessons'])
    total_duration = sum(lesson.get('estimated_duration', 0) for lesson in data['lessons'])
    mandatory_lessons = sum(1 for lesson in data['lessons'] if lesson.get('is_mandatory', False))
    
    print(f"\n📈 CONTENT STATISTICS:")
    print(f"  Total Duration: {total_duration} minutes ({total_duration/60:.1f} hours)")
    print(f"  Mandatory Lessons: {mandatory_lessons}/{total_lessons}")
    print(f"  Optional Lessons: {total_lessons - mandatory_lessons}/{total_lessons}")
    
    # Assessment statistics
    question_types = {}
    for question in data['questions']:
        q_type = question.get('question_type')
        question_types[q_type] = question_types.get(q_type, 0) + 1
    
    assignment_types = {}
    for assignment in data['assignments']:
        a_type = assignment.get('assignment_type')
        assignment_types[a_type] = assignment_types.get(a_type, 0) + 1
    
    print(f"\n🎯 ASSESSMENT BREAKDOWN:")
    print(f"  Question Types: {question_types}")
    print(f"  Assignment Types: {assignment_types}")
    
    print(f"\n✅ READY FOR IMPORT!")
    print(f"  File: new_corrected.json")
    print(f"  Status: All critical issues resolved")
    print(f"  Next Step: Run import script")

def main():
    """Main function to fix and validate JSON"""
    print("🔧 YITP COURSE JSON CORRECTION TOOL")
    print("=" * 60)
    
    # Fix JSON file
    corrected_data = fix_json_file()
    
    # Validate corrections
    is_valid = validate_corrections()
    
    if is_valid:
        # Create import summary
        create_import_summary()
        return True
    else:
        print("❌ Corrections failed validation")
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎉 JSON file successfully corrected and ready for import!")
    else:
        print("\n❌ JSON correction failed - please review issues above")
