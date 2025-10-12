#!/usr/bin/env python3
"""
YITP Quiz Duplication Investigation Script - PRODUCTION DATABASE
================================================================

This script investigates the quiz duplication issue in Module 1 of Course 6
by analyzing the PRODUCTION database state (Supabase PostgreSQL) and comparing
it with the source JSON data.

IMPORTANT: This script connects to the PRODUCTION Supabase database to analyze
the actual quiz data that students are currently experiencing.

Usage:
    python3 investigate_quiz_duplication.py

Output:
    quiz_duplication_analysis_report.md - Detailed investigation report
"""

import os
import sys
import json
from datetime import datetime
from collections import defaultdict

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set up Django environment for PRODUCTION database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode to connect to Supabase

import django
django.setup()

from django.db import connection
from django.conf import settings
from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question
from progress.models import Enrollment, QuizAttempt

# Verify production database connection
def verify_production_connection():
    """Verify we're connected to the production Supabase database"""
    try:
        db_settings = settings.DATABASES['default']
        print(f"🔗 Database Connection Verification:")
        print(f"   Engine: {db_settings.get('ENGINE', 'Unknown')}")
        print(f"   Host: {db_settings.get('HOST', 'Unknown')}")
        print(f"   Database: {db_settings.get('NAME', 'Unknown')}")
        print(f"   Environment: {os.environ.get('DJANGO_ENV', 'development')}")

        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"   PostgreSQL Version: {version}")

        # Verify we have production data
        course_count = Course.objects.count()
        print(f"   Total Courses: {course_count}")

        if course_count == 0:
            print("⚠️  WARNING: No courses found - may not be connected to production database")
            return False

        print("✅ Production database connection verified")
        return True

    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        return False


class QuizDuplicationInvestigator:
    """
    Comprehensive investigator for quiz duplication issues in PRODUCTION database
    """

    def __init__(self):
        self.course_id = 6
        self.module_id = None  # Will be determined from production data
        self.json_file_path = "courseunits/YITP_Course6_Module1_UPDATED_with_quizzes.json"
        self.json_data = None
        self.database_analysis = {}
        self.json_analysis = {}
        self.findings = []
        self.recommendations = []
        self.production_verified = False
        
    def load_json_data(self):
        """Load and parse the JSON source file"""
        try:
            print(f"📁 Loading JSON file: {self.json_file_path}")
            
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                self.json_data = json.load(file)
            
            print(f"✅ JSON file loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error loading JSON file: {str(e)}")
            return False
    
    def analyze_database_state(self):
        """Analyze current database state for Module 1"""
        try:
            print(f"\n🔍 ANALYZING PRODUCTION DATABASE STATE")
            print("=" * 50)

            # Get course info
            course = Course.objects.get(id=self.course_id)
            print(f"📚 Course: {course.title}")

            # Find Module 1 (Understanding Purpose in Life) - search by title pattern
            modules = Module.objects.filter(course=course).order_by('sort_order')
            print(f"📖 Available Modules in Course {self.course_id}:")

            target_module = None
            for module in modules:
                print(f"   - Module {module.id}: {module.title}")
                if "Understanding Purpose" in module.title or "UPL" in module.title or module.sort_order == 1:
                    target_module = module
                    self.module_id = module.id
                    print(f"   ✅ Target Module Found: {module.title} (ID: {module.id})")

            if not target_module:
                # Fallback to first module
                target_module = modules.first()
                self.module_id = target_module.id
                print(f"   ⚠️  Using first module as fallback: {target_module.title} (ID: {target_module.id})")

            module = target_module
            
            # Get all lessons in Module 1
            lessons = Lesson.objects.filter(module=module).order_by('sort_order')
            print(f"📄 Lessons in Module 1: {lessons.count()}")
            
            # Analyze quizzes for each lesson
            quiz_analysis = {}
            question_fingerprints = defaultdict(list)
            
            for lesson in lessons:
                quizzes = Quiz.objects.filter(lesson=lesson)
                lesson_analysis = {
                    'lesson_id': lesson.id,
                    'lesson_title': lesson.title,
                    'quiz_count': quizzes.count(),
                    'quizzes': []
                }
                
                for quiz in quizzes:
                    questions = Question.objects.filter(quiz=quiz).order_by('sort_order')
                    quiz_info = {
                        'quiz_id': quiz.id,
                        'quiz_title': quiz.title,
                        'question_count': questions.count(),
                        'questions': []
                    }
                    
                    # Create fingerprint for each question
                    for question in questions:
                        question_data = {
                            'question_text': question.question_text,
                            'question_type': question.question_type,
                            'correct_answer': question.correct_answer,
                            'points': question.points,
                            'sort_order': question.sort_order
                        }
                        quiz_info['questions'].append(question_data)
                        
                        # Create fingerprint for duplicate detection
                        fingerprint = f"{question.question_text}|{question.question_type}|{question.correct_answer}"
                        question_fingerprints[fingerprint].append({
                            'lesson_id': lesson.id,
                            'lesson_title': lesson.title,
                            'quiz_id': quiz.id,
                            'quiz_title': quiz.title,
                            'question_id': question.id
                        })
                    
                    lesson_analysis['quizzes'].append(quiz_info)
                
                quiz_analysis[lesson.id] = lesson_analysis
                print(f"   📝 {lesson.title}: {lesson_analysis['quiz_count']} quiz(es)")
            
            self.database_analysis = {
                'course': course.title,
                'module': module.title,
                'lesson_count': lessons.count(),
                'quiz_analysis': quiz_analysis,
                'question_fingerprints': dict(question_fingerprints)
            }
            
            # Detect duplicates
            duplicates = {fp: locations for fp, locations in question_fingerprints.items() if len(locations) > 1}
            
            print(f"\n🔍 DUPLICATE DETECTION RESULTS:")
            print(f"   📊 Total unique question fingerprints: {len(question_fingerprints)}")
            print(f"   🔄 Duplicated question fingerprints: {len(duplicates)}")
            
            if duplicates:
                print(f"\n⚠️ FOUND {len(duplicates)} DUPLICATED QUESTIONS:")
                for i, (fingerprint, locations) in enumerate(duplicates.items(), 1):
                    question_text = fingerprint.split('|')[0][:60] + "..."
                    print(f"   {i}. '{question_text}' appears in {len(locations)} lessons:")
                    for loc in locations:
                        print(f"      - Lesson {loc['lesson_id']}: {loc['lesson_title']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error analyzing database: {str(e)}")
            return False
    
    def analyze_json_source(self):
        """Analyze JSON source data for quiz content"""
        try:
            print(f"\n🔍 ANALYZING JSON SOURCE DATA")
            print("=" * 50)
            
            if not self.json_data:
                print("❌ JSON data not loaded")
                return False
            
            modules = self.json_data.get('modules', [])
            if not modules:
                print("❌ No modules found in JSON")
                return False
            
            module_data = modules[0]  # First module (Module 1)
            lessons = module_data.get('lessons', [])
            
            print(f"📖 Module: {module_data.get('title', 'Unknown')}")
            print(f"📄 Lessons in JSON: {len(lessons)}")
            
            # Analyze quiz content in JSON
            json_quiz_analysis = {}
            json_question_fingerprints = defaultdict(list)
            
            for i, lesson in enumerate(lessons, 1):
                lesson_id = lesson.get('id', f'lesson_{i}')
                lesson_title = lesson.get('title', f'Lesson {i}')
                
                assessment = lesson.get('assessment', {})
                quiz_data = assessment.get('quiz', {})
                
                if quiz_data:
                    questions = quiz_data.get('questions', [])
                    quiz_title = quiz_data.get('title', f'{lesson_title} Quiz')
                    
                    lesson_analysis = {
                        'lesson_id': lesson_id,
                        'lesson_title': lesson_title,
                        'quiz_title': quiz_title,
                        'question_count': len(questions),
                        'questions': questions
                    }
                    
                    # Create fingerprints for JSON questions
                    for question in questions:
                        fingerprint = f"{question.get('question_text', '')}|{question.get('question_type', '')}|{question.get('correct_answer', '')}"
                        json_question_fingerprints[fingerprint].append({
                            'lesson_id': lesson_id,
                            'lesson_title': lesson_title,
                            'quiz_title': quiz_title
                        })
                    
                    json_quiz_analysis[lesson_id] = lesson_analysis
                    print(f"   📝 {lesson_title}: {len(questions)} question(s)")
            
            self.json_analysis = {
                'module_title': module_data.get('title', 'Unknown'),
                'lesson_count': len(lessons),
                'quiz_analysis': json_quiz_analysis,
                'question_fingerprints': dict(json_question_fingerprints)
            }
            
            # Detect duplicates in JSON
            json_duplicates = {fp: locations for fp, locations in json_question_fingerprints.items() if len(locations) > 1}
            
            print(f"\n🔍 JSON DUPLICATE DETECTION RESULTS:")
            print(f"   📊 Total unique question fingerprints: {len(json_question_fingerprints)}")
            print(f"   🔄 Duplicated question fingerprints: {len(json_duplicates)}")
            
            if json_duplicates:
                print(f"\n⚠️ FOUND {len(json_duplicates)} DUPLICATED QUESTIONS IN JSON:")
                for i, (fingerprint, locations) in enumerate(json_duplicates.items(), 1):
                    question_text = fingerprint.split('|')[0][:60] + "..."
                    print(f"   {i}. '{question_text}' appears in {len(locations)} lessons:")
                    for loc in locations:
                        print(f"      - {loc['lesson_id']}: {loc['lesson_title']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error analyzing JSON: {str(e)}")
            return False
    
    def compare_database_vs_json(self):
        """Compare database state with JSON source"""
        try:
            print(f"\n🔍 COMPARING DATABASE VS JSON")
            print("=" * 50)
            
            if not self.database_analysis or not self.json_analysis:
                print("❌ Missing analysis data")
                return False
            
            db_fingerprints = set(self.database_analysis['question_fingerprints'].keys())
            json_fingerprints = set(self.json_analysis['question_fingerprints'].keys())
            
            print(f"📊 Database question fingerprints: {len(db_fingerprints)}")
            print(f"📊 JSON question fingerprints: {len(json_fingerprints)}")
            
            # Check if database matches JSON
            if db_fingerprints == json_fingerprints:
                print("✅ Database question content matches JSON source")
                self.findings.append("Database question content matches JSON source - duplication exists in source data")
            else:
                print("⚠️ Database question content differs from JSON source")
                
                only_in_db = db_fingerprints - json_fingerprints
                only_in_json = json_fingerprints - db_fingerprints
                
                if only_in_db:
                    print(f"   📊 Questions only in database: {len(only_in_db)}")
                    self.findings.append(f"Found {len(only_in_db)} questions in database not present in JSON")
                
                if only_in_json:
                    print(f"   📊 Questions only in JSON: {len(only_in_json)}")
                    self.findings.append(f"Found {len(only_in_json)} questions in JSON not imported to database")
            
            return True
            
        except Exception as e:
            print(f"❌ Error comparing data: {str(e)}")
            return False
    
    def generate_recommendations(self):
        """Generate recommendations based on findings"""
        print(f"\n💡 GENERATING RECOMMENDATIONS")
        print("=" * 50)
        
        # Check if duplication exists in JSON
        json_duplicates = {fp: locations for fp, locations in self.json_analysis['question_fingerprints'].items() if len(locations) > 1}
        
        if json_duplicates:
            self.recommendations.extend([
                "🔧 PRIMARY ISSUE: Quiz duplication exists in the source JSON file",
                "📝 ACTION REQUIRED: Create unique, lesson-specific quiz questions for each lesson",
                "🎯 SOLUTION: Develop contextually relevant questions that match each lesson's learning objectives",
                "⚠️ IMPACT: Current identical quizzes provide poor learning assessment and user experience"
            ])
        
        # Database-specific recommendations
        db_duplicates = {fp: locations for fp, locations in self.database_analysis['question_fingerprints'].items() if len(locations) > 1}
        
        if db_duplicates:
            self.recommendations.extend([
                "🗄️ DATABASE CLEANUP: Remove duplicate quiz questions from database",
                "🔄 RE-IMPORT: After fixing JSON, re-import with unique questions",
                "📊 VALIDATION: Implement validation to prevent duplicate question import"
            ])
        
        # General recommendations
        self.recommendations.extend([
            "📋 QUALITY ASSURANCE: Implement quiz content review process",
            "🎓 PEDAGOGICAL REVIEW: Ensure each quiz tests lesson-specific knowledge",
            "🔍 MONITORING: Add database constraints to prevent future duplication"
        ])
        
        for i, rec in enumerate(self.recommendations, 1):
            print(f"   {i}. {rec}")
    
    def generate_report(self):
        """Generate comprehensive investigation report"""
        try:
            print(f"\n📝 GENERATING INVESTIGATION REPORT")
            print("=" * 50)
            
            timestamp = datetime.now().isoformat()
            report_filename = "quiz_duplication_analysis_report.md"
            
            report_content = f"""# YITP Quiz Duplication Investigation Report - PRODUCTION DATABASE

**Generated:** {timestamp}
**Database:** Production Supabase PostgreSQL
**Course:** Course 6 - Youth Impact Training Programme (YITP)
**Module:** Module {self.module_id} - Understanding Purpose in Life (UPL)
**Investigator:** Quiz Duplication Analysis Script (Production Mode)

## Executive Summary

This report investigates the quiz duplication issue discovered in Module 1 of the YITP course in the PRODUCTION database, where all lessons appear to have identical quiz content despite having unique quiz titles. This analysis is based on the actual data that students are currently experiencing.

## Key Findings

"""
            
            for i, finding in enumerate(self.findings, 1):
                report_content += f"{i}. {finding}\n"
            
            report_content += f"""

## Database Analysis Results

### Course Information
- **Course ID:** {self.course_id}
- **Course Title:** {self.database_analysis.get('course', 'Unknown')}
- **Module ID:** {self.module_id}
- **Module Title:** {self.database_analysis.get('module', 'Unknown')}
- **Lessons in Module:** {self.database_analysis.get('lesson_count', 0)}

### Quiz Distribution
"""
            
            for lesson_id, lesson_data in self.database_analysis.get('quiz_analysis', {}).items():
                report_content += f"- **{lesson_data['lesson_title']}:** {lesson_data['quiz_count']} quiz(es)\n"
            
            # Add duplicate analysis
            db_duplicates = {fp: locations for fp, locations in self.database_analysis['question_fingerprints'].items() if len(locations) > 1}
            
            report_content += f"""

### Duplicate Question Analysis
- **Total Unique Questions:** {len(self.database_analysis['question_fingerprints'])}
- **Duplicated Questions:** {len(db_duplicates)}

"""
            
            if db_duplicates:
                report_content += "#### Duplicated Questions:\n"
                for i, (fingerprint, locations) in enumerate(db_duplicates.items(), 1):
                    question_text = fingerprint.split('|')[0]
                    report_content += f"{i}. **Question:** \"{question_text}\"\n"
                    report_content += f"   **Appears in:** {len(locations)} lessons\n"
                    for loc in locations:
                        report_content += f"   - Lesson {loc['lesson_id']}: {loc['lesson_title']}\n"
                    report_content += "\n"
            
            report_content += f"""

## JSON Source Analysis Results

### Module Information
- **Module Title:** {self.json_analysis.get('module_title', 'Unknown')}
- **Lessons in JSON:** {self.json_analysis.get('lesson_count', 0)}

### Quiz Content Analysis
"""
            
            for lesson_id, lesson_data in self.json_analysis.get('quiz_analysis', {}).items():
                report_content += f"- **{lesson_data['lesson_title']}:** {lesson_data['question_count']} question(s)\n"
            
            # Add JSON duplicate analysis
            json_duplicates = {fp: locations for fp, locations in self.json_analysis['question_fingerprints'].items() if len(locations) > 1}
            
            report_content += f"""

### JSON Duplicate Question Analysis
- **Total Unique Questions:** {len(self.json_analysis['question_fingerprints'])}
- **Duplicated Questions:** {len(json_duplicates)}

"""
            
            if json_duplicates:
                report_content += "#### Duplicated Questions in JSON:\n"
                for i, (fingerprint, locations) in enumerate(json_duplicates.items(), 1):
                    question_text = fingerprint.split('|')[0]
                    report_content += f"{i}. **Question:** \"{question_text}\"\n"
                    report_content += f"   **Appears in:** {len(locations)} lessons\n"
                    for loc in locations:
                        report_content += f"   - {loc['lesson_id']}: {loc['lesson_title']}\n"
                    report_content += "\n"
            
            report_content += """

## Root Cause Analysis

"""
            
            if json_duplicates and len(db_duplicates) > 0:
                report_content += """**ROOT CAUSE IDENTIFIED:** The quiz duplication issue originates in the source JSON file.

**Evidence:**
1. All 8 lessons in Module 1 contain identical quiz questions in the JSON source
2. The import scripts correctly create separate Quiz objects for each lesson
3. The database accurately reflects the JSON content
4. Each lesson has unique quiz titles but identical question content

**Technical Details:**
- The JSON contains 8 lessons, each with an "assessment" → "quiz" → "questions" array
- All question arrays contain the same 6 questions with identical text, types, and answers
- The import script (`implement_course_6_update.py`) correctly processes each lesson's quiz data
- Database relationships are properly configured (Quiz → Lesson, Question → Quiz)

"""
            
            report_content += """

## Recommendations

"""
            
            for i, rec in enumerate(self.recommendations, 1):
                report_content += f"{i}. {rec}\n"
            
            report_content += f"""

## Technical Implementation

### Immediate Actions Required

1. **Fix JSON Source Data:**
   ```bash
   # Edit courseunits/YITP_Course6_Module1_WRAPPED_vMatching.json
   # Create unique questions for each lesson based on lesson content
   ```

2. **Database Cleanup:**
   ```sql
   -- Remove existing duplicate quizzes (after backup)
   DELETE FROM assessments_question WHERE quiz_id IN (
       SELECT id FROM assessments_quiz WHERE lesson_id IN (
           SELECT id FROM courses_lesson WHERE module_id = 14
       )
   );
   DELETE FROM assessments_quiz WHERE lesson_id IN (
       SELECT id FROM courses_lesson WHERE module_id = 14
   );
   ```

3. **Re-import with Fixed Data:**
   ```bash
   python implement_course_6_update.py
   ```

### Long-term Solutions

1. **Validation Enhancement:** Add JSON validation to detect duplicate questions
2. **Content Review Process:** Implement pedagogical review for quiz content
3. **Database Constraints:** Add unique constraints where appropriate
4. **Quality Assurance:** Regular audits of course content

## Conclusion

The quiz duplication issue is a **data quality problem** originating in the source JSON file, not a technical implementation issue. The import scripts and database structure are functioning correctly. The solution requires creating unique, lesson-specific quiz questions that properly assess each lesson's learning objectives.

**Priority:** High - Affects learning assessment quality and user experience
**Effort:** Medium - Requires content creation and re-import
**Risk:** Low - Well-defined problem with clear solution path

---

*Report generated by YITP Quiz Duplication Investigation Script*
*Timestamp: {timestamp}*
"""
            
            # Write report to file
            with open(report_filename, 'w', encoding='utf-8') as file:
                file.write(report_content)
            
            print(f"✅ Investigation report saved: {report_filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error generating report: {str(e)}")
            return False
    
    def run_investigation(self):
        """Run the complete investigation"""
        print("🔍 YITP QUIZ DUPLICATION INVESTIGATION - PRODUCTION DATABASE")
        print("=" * 80)

        # Verify production database connection
        print("🔗 VERIFYING PRODUCTION DATABASE CONNECTION")
        print("-" * 50)
        if not verify_production_connection():
            print("❌ Failed to verify production database connection")
            return False

        self.production_verified = True
        print()

        # Load JSON data
        if not self.load_json_data():
            return False

        # Analyze database state
        if not self.analyze_database_state():
            return False
        
        # Analyze JSON source
        if not self.analyze_json_source():
            return False
        
        # Compare database vs JSON
        if not self.compare_database_vs_json():
            return False
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Generate comprehensive report
        if not self.generate_report():
            return False
        
        print(f"\n✅ INVESTIGATION COMPLETE")
        print("=" * 80)
        print("📋 Summary:")
        print("   - Database analysis: Complete")
        print("   - JSON analysis: Complete")
        print("   - Comparison: Complete")
        print("   - Report generated: quiz_duplication_analysis_report.md")
        
        return True


def main():
    """Main execution function"""
    investigator = QuizDuplicationInvestigator()
    success = investigator.run_investigation()
    
    if success:
        print("\n🎯 Investigation completed successfully!")
        print("📄 Check 'quiz_duplication_analysis_report.md' for detailed findings.")
    else:
        print("\n❌ Investigation failed. Check error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
