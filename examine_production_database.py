#!/usr/bin/env python3
"""
Examine YITP Production Database Structure
Check current courses, modules, and lessons before UPL 101 integration
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment for PRODUCTION
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson, Category
from assessments.models import Quiz, Question
from django.db import connection

class ProductionDatabaseExaminer:
    def __init__(self):
        self.report = []
        
    def log(self, message):
        """Log message to both console and report"""
        print(message)
        self.report.append(message)
    
    def test_database_connection(self):
        """Test production database connection"""
        self.log("🔍 TESTING PRODUCTION DATABASE CONNECTION")
        self.log("=" * 60)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.log(f"✅ Database Connection: SUCCESS")
                self.log(f"   Database Version: {version}")
                
                # Get database name and host
                db_config = connection.settings_dict
                self.log(f"   Database Host: {db_config.get('HOST', 'Unknown')}")
                self.log(f"   Database Name: {db_config.get('NAME', 'Unknown')}")
                self.log(f"   Database User: {db_config.get('USER', 'Unknown')}")
                
                return True
        except Exception as e:
            self.log(f"❌ Database Connection: FAILED")
            self.log(f"   Error: {str(e)}")
            return False
    
    def examine_courses(self):
        """Examine existing courses in production"""
        self.log("\n📚 EXAMINING EXISTING COURSES")
        self.log("=" * 60)
        
        try:
            courses = Course.objects.all().order_by('id')
            self.log(f"Total Courses Found: {courses.count()}")
            
            if courses.count() == 0:
                self.log("   No courses found in database")
                return []
            
            course_data = []
            for course in courses:
                modules = course.modules.all()
                total_lessons = sum(module.lessons.count() for module in modules)
                
                course_info = {
                    'id': course.id,
                    'title': course.title,
                    'slug': course.slug,
                    'status': course.status,
                    'is_published': course.is_published,
                    'price': course.price,
                    'modules_count': modules.count(),
                    'lessons_count': total_lessons,
                    'instructor': course.instructor.username if course.instructor else 'None'
                }
                course_data.append(course_info)
                
                self.log(f"\n📖 Course {course.id}: {course.title}")
                self.log(f"   Slug: {course.slug}")
                self.log(f"   Status: {course.status} | Published: {course.is_published}")
                self.log(f"   Price: ${course.price}")
                self.log(f"   Instructor: {course.instructor.username if course.instructor else 'None'}")
                self.log(f"   Modules: {modules.count()} | Lessons: {total_lessons}")
                
                # Show modules
                for module in modules:
                    lessons = module.lessons.all()
                    self.log(f"     📁 Module {module.sort_order}: {module.title} ({lessons.count()} lessons)")
                    
                    # Show first few lessons
                    for lesson in lessons[:3]:
                        quizzes = lesson.quizzes.all()
                        self.log(f"       📄 Lesson {lesson.sort_order}: {lesson.title} ({quizzes.count()} quizzes)")
                    
                    if lessons.count() > 3:
                        self.log(f"       ... and {lessons.count() - 3} more lessons")
            
            return course_data
            
        except Exception as e:
            self.log(f"❌ Error examining courses: {str(e)}")
            return []
    
    def examine_main_yitp_course(self):
        """Examine the main YITP course specifically"""
        self.log("\n🎯 EXAMINING MAIN YITP COURSE")
        self.log("=" * 60)
        
        try:
            # Look for main YITP course
            yitp_courses = Course.objects.filter(
                title__icontains="Youth Impact Training Programme"
            ).order_by('id')
            
            if not yitp_courses.exists():
                # Try alternative names
                yitp_courses = Course.objects.filter(
                    title__icontains="YITP"
                ).order_by('id')
            
            if not yitp_courses.exists():
                self.log("❌ Main YITP course not found")
                self.log("   Searching for courses with 'youth' or 'impact' in title...")
                
                youth_courses = Course.objects.filter(
                    title__icontains="youth"
                ).order_by('id')
                
                if youth_courses.exists():
                    self.log(f"   Found {youth_courses.count()} courses with 'youth' in title:")
                    for course in youth_courses:
                        self.log(f"     - {course.title}")
                else:
                    self.log("   No courses found with 'youth' in title")
                
                return None
            
            # Examine the main YITP course
            main_course = yitp_courses.first()
            self.log(f"✅ Main YITP Course Found: {main_course.title}")
            self.log(f"   Course ID: {main_course.id}")
            self.log(f"   Slug: {main_course.slug}")
            self.log(f"   Status: {main_course.status}")
            self.log(f"   Published: {main_course.is_published}")
            self.log(f"   Price: ${main_course.price}")
            
            # Examine modules
            modules = main_course.modules.all().order_by('sort_order')
            self.log(f"\n📁 Current Modules ({modules.count()}):")
            
            for module in modules:
                lessons = module.lessons.all().order_by('sort_order')
                quizzes_count = sum(lesson.quizzes.count() for lesson in lessons)
                
                self.log(f"   Module {module.sort_order}: {module.title}")
                self.log(f"     Description: {module.description[:100]}...")
                self.log(f"     Lessons: {lessons.count()} | Quizzes: {quizzes_count}")
                self.log(f"     Duration: {module.estimated_duration} minutes")
                self.log(f"     Published: {module.is_published}")
                
                # Show lessons
                for lesson in lessons:
                    lesson_quizzes = lesson.quizzes.all()
                    self.log(f"       📄 Lesson {lesson.sort_order}: {lesson.title}")
                    self.log(f"         Type: {lesson.content_type} | Duration: {lesson.estimated_duration} min")
                    if lesson_quizzes.exists():
                        for quiz in lesson_quizzes:
                            questions_count = quiz.questions.count()
                            self.log(f"         🧩 Quiz: {quiz.title} ({questions_count} questions)")
            
            return main_course
            
        except Exception as e:
            self.log(f"❌ Error examining main YITP course: {str(e)}")
            return None
    
    def check_categories(self):
        """Check available categories"""
        self.log("\n📂 EXAMINING CATEGORIES")
        self.log("=" * 60)
        
        try:
            categories = Category.objects.all().order_by('name')
            self.log(f"Total Categories: {categories.count()}")
            
            for category in categories:
                courses_count = category.courses.count()
                self.log(f"   📂 {category.name}: {courses_count} courses")
                
            return categories
            
        except Exception as e:
            self.log(f"❌ Error examining categories: {str(e)}")
            return []
    
    def check_instructors(self):
        """Check available instructors"""
        self.log("\n👨‍🏫 EXAMINING INSTRUCTORS")
        self.log("=" * 60)
        
        try:
            instructors = User.objects.filter(
                instructor_courses__isnull=False
            ).distinct().order_by('username')
            
            self.log(f"Total Instructors: {instructors.count()}")
            
            for instructor in instructors:
                courses_count = instructor.instructor_courses.count()
                self.log(f"   👨‍🏫 {instructor.username} ({instructor.first_name} {instructor.last_name}): {courses_count} courses")
                
            return instructors
            
        except Exception as e:
            self.log(f"❌ Error examining instructors: {str(e)}")
            return []
    
    def generate_integration_recommendations(self, main_course):
        """Generate recommendations for UPL 101 integration"""
        self.log("\n💡 UPL 101 INTEGRATION RECOMMENDATIONS")
        self.log("=" * 60)
        
        if not main_course:
            self.log("❌ Cannot provide recommendations - Main YITP course not found")
            self.log("\n🔧 REQUIRED ACTIONS:")
            self.log("1. Create main YITP course first")
            self.log("2. Then integrate UPL 101 as Module 1")
            return
        
        current_modules = main_course.modules.all().order_by('sort_order')
        
        self.log(f"✅ Main YITP Course Found: {main_course.title}")
        self.log(f"   Current Modules: {current_modules.count()}")
        
        if current_modules.count() > 0:
            self.log("\n⚠️ EXISTING MODULES DETECTED:")
            for module in current_modules:
                lessons_count = module.lessons.count()
                self.log(f"   - Module {module.sort_order}: {module.title} ({lessons_count} lessons)")
            
            self.log("\n🔧 INTEGRATION STRATEGY:")
            self.log("1. BACKUP existing modules before integration")
            self.log("2. OPTION A: Replace existing modules with UPL 101")
            self.log("3. OPTION B: Insert UPL 101 as Module 1, shift others")
            self.log("4. OPTION C: Add UPL 101 as additional module")
        else:
            self.log("\n✅ NO EXISTING MODULES - CLEAN INTEGRATION POSSIBLE")
            self.log("   UPL 101 can be added as Module 1 without conflicts")
        
        self.log("\n📋 UPL 101 INTEGRATION PLAN:")
        self.log("1. Create Module: 'Understanding Purpose in Life (UPL 101)'")
        self.log("2. Add 8 lessons (Sessions 1-8)")
        self.log("3. Create 40 quiz questions (5 per session)")
        self.log("4. Set proper sequencing and prerequisites")
        self.log("5. Update course price to $39 USD")
        self.log("6. Verify all functionality")
    
    def save_report(self):
        """Save examination report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"production_database_examination_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# YITP Production Database Examination Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            for line in self.report:
                f.write(line + "\n")
        
        self.log(f"\n📄 Report saved: {filename}")
        return filename
    
    def run_complete_examination(self):
        """Run complete database examination"""
        self.log("🔍 YITP PRODUCTION DATABASE EXAMINATION")
        self.log("=" * 80)
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test connection
        if not self.test_database_connection():
            self.log("❌ Cannot proceed without database connection")
            return False
        
        # Examine database structure
        courses = self.examine_courses()
        main_course = self.examine_main_yitp_course()
        categories = self.check_categories()
        instructors = self.check_instructors()
        
        # Generate recommendations
        self.generate_integration_recommendations(main_course)
        
        # Save report
        report_file = self.save_report()
        
        self.log("\n" + "=" * 80)
        self.log("🎉 EXAMINATION COMPLETED SUCCESSFULLY")
        self.log(f"📄 Full report: {report_file}")
        
        return True

if __name__ == "__main__":
    examiner = ProductionDatabaseExaminer()
    examiner.run_complete_examination()
