#!/usr/bin/env python
"""
Export YITP Introductory Course Data for Production Deployment
Creates Django fixtures that can be imported into production
"""

import os
import sys
import django
from django.core.management import call_command

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    django.setup()

def export_course_data():
    """Export the introductory course data to fixtures"""
    print("📦 EXPORTING YITP INTRODUCTORY COURSE DATA")
    print("=" * 60)
    
    try:
        # First, ensure the course exists locally
        from courses.models import Course
        from django.contrib.auth.models import User
        
        # Check if course exists
        course = Course.objects.filter(title__icontains="Introduction to YITP").first()
        if not course:
            print("❌ Course not found locally. Creating it first...")
            call_command('create_intro_course')
            course = Course.objects.filter(title__icontains="Introduction to YITP").first()
        
        if course:
            print(f"✅ Found course: {course.title}")
            print(f"   Instructor: {course.instructor.username}")
            print(f"   Price: ${course.price}")
            print(f"   Status: {course.status}")
        
        # Export specific models related to the intro course
        print("\n📤 Exporting course data...")
        
        # Get the instructor user ID
        instructor = User.objects.get(username='yitpteam')
        instructor_id = instructor.id
        
        # Get the course ID
        course_id = course.id
        
        # Export instructor user
        print("   Exporting instructor user...")
        call_command(
            'dumpdata', 
            'auth.User',
            '--pks', str(instructor_id),
            '--output', 'instructor_user.json',
            '--indent', '2'
        )
        
        # Export instructor profile
        print("   Exporting instructor profile...")
        call_command(
            'dumpdata', 
            'users.InstructorProfile',
            '--output', 'instructor_profile.json',
            '--indent', '2'
        )
        
        # Export category
        print("   Exporting course category...")
        call_command(
            'dumpdata', 
            'courses.Category',
            '--output', 'course_category.json',
            '--indent', '2'
        )
        
        # Export course
        print("   Exporting course...")
        call_command(
            'dumpdata', 
            'courses.Course',
            '--pks', str(course_id),
            '--output', 'intro_course.json',
            '--indent', '2'
        )
        
        # Export modules
        print("   Exporting modules...")
        call_command(
            'dumpdata', 
            'courses.Module',
            '--output', 'course_modules.json',
            '--indent', '2'
        )
        
        # Export lessons
        print("   Exporting lessons...")
        call_command(
            'dumpdata', 
            'courses.Lesson',
            '--output', 'course_lessons.json',
            '--indent', '2'
        )
        
        # Export quizzes
        print("   Exporting quizzes...")
        call_command(
            'dumpdata', 
            'assessments.Quiz',
            '--output', 'course_quizzes.json',
            '--indent', '2'
        )
        
        # Export questions
        print("   Exporting questions...")
        call_command(
            'dumpdata', 
            'assessments.Question',
            '--output', 'course_questions.json',
            '--indent', '2'
        )
        
        # Create combined fixture
        print("   Creating combined fixture...")
        import json
        
        combined_data = []
        fixture_files = [
            'instructor_user.json',
            'instructor_profile.json', 
            'course_category.json',
            'intro_course.json',
            'course_modules.json',
            'course_lessons.json',
            'course_quizzes.json',
            'course_questions.json'
        ]
        
        for fixture_file in fixture_files:
            if os.path.exists(fixture_file):
                with open(fixture_file, 'r') as f:
                    data = json.load(f)
                    combined_data.extend(data)
                # Clean up individual files
                os.remove(fixture_file)
        
        # Write combined fixture
        with open('intro_course_complete.json', 'w') as f:
            json.dump(combined_data, f, indent=2)
        
        print(f"✅ Created combined fixture: intro_course_complete.json")
        print(f"   Total objects: {len(combined_data)}")
        
        # Show summary
        model_counts = {}
        for obj in combined_data:
            model = obj['model']
            model_counts[model] = model_counts.get(model, 0) + 1
        
        print("\n📊 Export Summary:")
        for model, count in model_counts.items():
            print(f"   {model}: {count} objects")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_import_instructions():
    """Create instructions for importing in production"""
    instructions = """
# YITP Introductory Course - Production Import Instructions

## Method 1: Using Django Migration (Recommended)

1. Deploy the code with the migration file to production
2. Run migrations in production:
   ```bash
   python manage.py migrate
   ```

## Method 2: Using Django Fixtures (Alternative)

1. Upload the intro_course_complete.json file to production
2. Import the data:
   ```bash
   python manage.py loaddata intro_course_complete.json
   ```

## Method 3: Using Management Command (Direct)

1. Run the management command directly in production:
   ```bash
   python manage.py create_intro_course
   ```

## Verification Steps

After deployment, verify the course:

1. Check course exists:
   ```bash
   python manage.py shell -c "
   from courses.models import Course
   course = Course.objects.get(title__icontains='Introduction to YITP')
   print(f'Course: {course.title}')
   print(f'Instructor: {course.instructor.username}')
   print(f'Price: ${course.price}')
   print(f'Status: {course.status}')
   "
   ```

2. Check quiz questions:
   ```bash
   python manage.py shell -c "
   from assessments.models import Quiz
   quiz = Quiz.objects.get(title__icontains='YITP Platform Knowledge')
   print(f'Quiz: {quiz.title}')
   print(f'Questions: {quiz.total_questions}')
   print(f'Passing Score: {quiz.passing_score}%')
   "
   ```

3. Test instructor login:
   - Username: yitpteam
   - Password: sLXSxmMg3tVeV64
   - Email: enockomondike@gmail.com

## Production URLs

- Admin: https://www.youthimpactglobal.com/admin/
- Course Catalog: https://www.youthimpactglobal.com/courses/
- Course should appear as "Introduction to YITP: Your Learning Journey Begins"

## Course Details

- Title: Introduction to YITP: Your Learning Journey Begins
- Type: Mandatory first course for all new students
- Duration: 25 minutes
- Price: Free ($0.00)
- Quiz: 8 questions, 70% passing score
- Instructor: yitpteam (enockomondike@gmail.com)
"""
    
    with open('PRODUCTION_IMPORT_INSTRUCTIONS.md', 'w') as f:
        f.write(instructions)
    
    print("✅ Created import instructions: PRODUCTION_IMPORT_INSTRUCTIONS.md")

def main():
    """Main execution function"""
    print("🎓 YITP INTRODUCTORY COURSE - DATA EXPORT")
    print("=" * 60)
    
    # Setup Django
    setup_django()
    
    # Export course data
    if export_course_data():
        print("\n✅ EXPORT SUCCESSFUL!")
        
        # Create import instructions
        create_import_instructions()
        
        print("\n📋 Files Created:")
        print("   • intro_course_complete.json - Complete course data fixture")
        print("   • PRODUCTION_IMPORT_INSTRUCTIONS.md - Import instructions")
        
        print("\n🚀 Next Steps:")
        print("   1. Upload intro_course_complete.json to production")
        print("   2. Run: python manage.py loaddata intro_course_complete.json")
        print("   3. Verify course appears in admin and course catalog")
        print("   4. Test instructor login and course functionality")
        
    else:
        print("\n❌ EXPORT FAILED!")
        print("Please check the errors above and try again.")

if __name__ == "__main__":
    main()
