#!/usr/bin/env python3
"""
Module 2 Phase 1 Production Database Import Script
=================================================

Imports Module 2 (Personal Initiative & Assessments) Phase 1 into the production
Supabase PostgreSQL database using the validated JSON file.

Requirements:
- JSON File: module2_phase1_complete_20251013_025946.json
- Module ID: 15 (next after Module 1 which is ID 14)
- Course ID: 6 (Youth Impact Training Programme - YITP)
- Total Lessons: 5
- Total Duration: 350 minutes
"""

import json
import os
import psycopg2
from datetime import datetime
import sys

class Module2Phase1Importer:
    def __init__(self):
        self.json_file = "module2_phase1_fixed_20251013_083218.json"
        self.course_id = 6  # YITP Course
        self.module_id = 15  # Next after Module 1 (ID: 14)
        self.connection = None
        self.cursor = None
        self.import_results = {
            'module_created': False,
            'lessons_imported': 0,
            'quizzes_imported': 0,
            'questions_imported': 0,
            'errors': [],
            'warnings': []
        }

    def connect_to_database(self):
        """Connect to production Supabase PostgreSQL database"""
        print("🔌 CONNECTING TO PRODUCTION DATABASE")
        print("=" * 60)

        try:
            # Production Supabase PostgreSQL connection
            self.connection = psycopg2.connect(
                host="aws-0-eu-west-1.pooler.supabase.com",
                port=6543,
                database="postgres",
                user="postgres.ovywuanlidncuecjlyve",
                password="_zi4DD9LBKAc@Pk",
                sslmode="require"
            )
            self.cursor = self.connection.cursor()

            print("✅ Successfully connected to production database")

            # Test connection with a simple query
            self.cursor.execute("SELECT version();")
            version = self.cursor.fetchone()
            print(f"📊 Database version: {version[0][:50]}...")

            return True

        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.import_results['errors'].append(f"Database connection failed: {e}")
            return False

    def load_json_data(self):
        """Load and validate the JSON file"""
        print(f"\n📄 LOADING JSON DATA")
        print("=" * 60)

        try:
            if not os.path.exists(self.json_file):
                raise FileNotFoundError(f"JSON file not found: {self.json_file}")

            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

            file_size = os.path.getsize(self.json_file)
            print(f"✅ JSON file loaded successfully")
            print(f"📊 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            print(f"📚 Module: {self.data['module_info']['title']}")
            print(f"📖 Lessons: {len(self.data['lessons'])}")

            return True

        except Exception as e:
            print(f"❌ Failed to load JSON: {e}")
            self.import_results['errors'].append(f"Failed to load JSON: {e}")
            return False

    def verify_course_exists(self):
        """Verify that Course 6 (YITP) exists in the database"""
        print(f"\n🔍 VERIFYING COURSE EXISTS")
        print("=" * 60)

        try:
            self.cursor.execute("""
                SELECT c.id, c.title, u.username
                FROM courses_course c
                JOIN auth_user u ON c.instructor_id = u.id
                WHERE c.id = %s
            """, (self.course_id,))

            course = self.cursor.fetchone()
            if course:
                print(f"✅ Course found: ID {course[0]} - {course[1]} by {course[2]}")
                return True
            else:
                print(f"❌ Course ID {self.course_id} not found")
                self.import_results['errors'].append(f"Course ID {self.course_id} not found")
                return False

        except Exception as e:
            print(f"❌ Error verifying course: {e}")
            self.import_results['errors'].append(f"Error verifying course: {e}")
            return False

    def check_module_exists(self):
        """Check if Module 15 already exists"""
        print(f"\n🔍 CHECKING MODULE EXISTENCE")
        print("=" * 60)

        try:
            self.cursor.execute("""
                SELECT id, title
                FROM courses_module
                WHERE id = %s
            """, (self.module_id,))

            module = self.cursor.fetchone()
            if module:
                print(f"⚠️ Module ID {self.module_id} already exists: {module[1]}")
                self.import_results['warnings'].append(f"Module ID {self.module_id} already exists")
                return True
            else:
                print(f"✅ Module ID {self.module_id} is available")
                return False

        except Exception as e:
            print(f"❌ Error checking module: {e}")
            self.import_results['errors'].append(f"Error checking module: {e}")
            return False

    def create_module(self):
        """Create Module 2 in the courses_module table"""
        print(f"\n📚 CREATING MODULE 2")
        print("=" * 60)

        try:
            module_info = self.data['module_info']

            # Insert module
            self.cursor.execute("""
                INSERT INTO courses_module (
                    id, title, description, course_id, sort_order,
                    is_published, unlock_criteria, estimated_duration, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.module_id,
                module_info['title'],
                module_info['description'],
                self.course_id,
                module_info['sort_order'],
                module_info['is_published'],
                '{}',  # Empty JSON object for unlock_criteria
                module_info.get('estimated_duration_minutes', 350),
                datetime.now(),
                datetime.now()
            ))

            print(f"✅ Module created: ID {self.module_id}")
            print(f"📝 Title: {module_info['title']}")
            print(f"📊 Sort order: {module_info['sort_order']}")

            self.import_results['module_created'] = True
            return True

        except Exception as e:
            print(f"❌ Error creating module: {e}")
            self.import_results['errors'].append(f"Error creating module: {e}")
            return False

    def import_lessons(self):
        """Import all 5 lessons into the courses_lesson table"""
        print(f"\n📖 IMPORTING LESSONS")
        print("=" * 60)

        try:
            lessons = self.data['lessons']

            for lesson in lessons:
                # Insert lesson
                self.cursor.execute("""
                    INSERT INTO courses_lesson (
                        id, title, content, content_type, learning_objectives,
                        estimated_duration, sort_order, is_published, is_mandatory,
                        module_id, video_url, document_url, audio_url, resources, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    lesson['id'],
                    lesson['title'],
                    lesson['content'],
                    lesson['content_type'],
                    lesson['learning_objectives'],
                    lesson['estimated_duration'],
                    lesson['sort_order'],
                    lesson['is_published'],
                    lesson['is_mandatory'],
                    self.module_id,
                    lesson.get('video_url', ''),  # video_url from JSON or empty string
                    lesson.get('document_url', ''),  # document_url from JSON or empty string
                    lesson.get('audio_url', ''),  # audio_url from JSON or empty string
                    json.dumps(lesson.get('resources', [])),  # resources as JSON string
                    datetime.now(),
                    datetime.now()
                ))

                print(f"✅ Lesson {lesson['sort_order']}: ID {lesson['id']} - {lesson['title'][:50]}...")
                print(f"   Duration: {lesson['estimated_duration']} minutes")
                print(f"   Content size: {len(lesson['content']):,} characters")

                self.import_results['lessons_imported'] += 1

            print(f"\n📊 Total lessons imported: {self.import_results['lessons_imported']}")
            return True

        except Exception as e:
            print(f"❌ Error importing lessons: {e}")
            self.import_results['errors'].append(f"Error importing lessons: {e}")
            return False

    def import_quizzes_and_questions(self):
        """Import all quizzes and questions into assessments tables"""
        print(f"\n❓ IMPORTING QUIZZES AND QUESTIONS")
        print("=" * 60)

        try:
            lessons = self.data['lessons']

            for lesson in lessons:
                if 'assessment' in lesson and 'quiz' in lesson['assessment']:
                    quiz = lesson['assessment']['quiz']

                    # Insert quiz
                    self.cursor.execute("""
                        INSERT INTO assessments_quiz (
                            id, title, description, instructions, lesson_id, passing_score, max_attempts,
                            time_limit, is_randomized, show_results, is_published, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        quiz['id'],
                        quiz['title'],
                        quiz.get('description', ''),  # Empty string if not provided
                        quiz.get('instructions', ''),  # Empty string if not provided
                        lesson['id'],
                        quiz['passing_score'],
                        quiz['max_attempts'],
                        quiz.get('time_limit'),
                        quiz.get('is_randomized', False),
                        quiz.get('show_results', True),
                        quiz.get('is_published', True),
                        datetime.now()
                    ))

                    print(f"✅ Quiz created for Lesson {lesson['sort_order']}: {quiz['title']}")
                    self.import_results['quizzes_imported'] += 1

                    # Import questions for this quiz
                    questions = quiz['questions']
                    for question in questions:
                        self.cursor.execute("""
                            INSERT INTO assessments_question (
                                question_text, question_type, options, correct_answer,
                                explanation, points, sort_order, quiz_id, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            question['question_text'],
                            question['question_type'],
                            json.dumps(question.get('options', [])),
                            question['correct_answer'],
                            question.get('explanation', ''),
                            question.get('points', 1),
                            question['sort_order'],
                            quiz['id'],
                            datetime.now()
                        ))

                        self.import_results['questions_imported'] += 1

                    print(f"   Questions imported: {len(questions)}")

            print(f"\n📊 Total quizzes imported: {self.import_results['quizzes_imported']}")
            print(f"📊 Total questions imported: {self.import_results['questions_imported']}")
            return True

        except Exception as e:
            print(f"❌ Error importing quizzes/questions: {e}")
            self.import_results['errors'].append(f"Error importing quizzes/questions: {e}")
            return False

    def verify_import(self):
        """Verify that all data was imported correctly"""
        print(f"\n✅ VERIFYING IMPORT")
        print("=" * 60)

        try:
            # Verify module
            self.cursor.execute("""
                SELECT id, title FROM courses_module WHERE id = %s
            """, (self.module_id,))
            module = self.cursor.fetchone()

            if not module:
                self.import_results['errors'].append("Module not found after import")
                return False

            print(f"✅ Module verified: ID {module[0]} - {module[1]}")

            # Verify lessons
            self.cursor.execute("""
                SELECT COUNT(*) FROM courses_lesson WHERE module_id = %s
            """, (self.module_id,))
            lesson_count = self.cursor.fetchone()[0]

            print(f"✅ Lessons verified: {lesson_count} lessons found")

            # Verify quizzes
            self.cursor.execute("""
                SELECT COUNT(*) FROM assessments_quiz q
                JOIN courses_lesson l ON q.lesson_id = l.id
                WHERE l.module_id = %s
            """, (self.module_id,))
            quiz_count = self.cursor.fetchone()[0]

            print(f"✅ Quizzes verified: {quiz_count} quizzes found")

            # Verify questions
            self.cursor.execute("""
                SELECT COUNT(*) FROM assessments_question q
                JOIN assessments_quiz qz ON q.quiz_id = qz.id
                JOIN courses_lesson l ON qz.lesson_id = l.id
                WHERE l.module_id = %s
            """, (self.module_id,))
            question_count = self.cursor.fetchone()[0]

            print(f"✅ Questions verified: {question_count} questions found")

            # Verify all questions have correct_answer
            self.cursor.execute("""
                SELECT COUNT(*) FROM assessments_question q
                JOIN assessments_quiz qz ON q.quiz_id = qz.id
                JOIN courses_lesson l ON qz.lesson_id = l.id
                WHERE l.module_id = %s AND (q.correct_answer IS NULL OR q.correct_answer = '')
            """, (self.module_id,))
            missing_answers = self.cursor.fetchone()[0]

            if missing_answers > 0:
                self.import_results['warnings'].append(f"{missing_answers} questions missing correct_answer")
                print(f"⚠️ Warning: {missing_answers} questions missing correct_answer")
            else:
                print(f"✅ All questions have correct_answer fields")

            return True

        except Exception as e:
            print(f"❌ Error verifying import: {e}")
            self.import_results['errors'].append(f"Error verifying import: {e}")
            return False

    def generate_import_report(self):
        """Generate comprehensive import report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"module2_phase1_import_report_{timestamp}.md"

        status = "✅ SUCCESS" if len(self.import_results['errors']) == 0 else "❌ FAILED"

        report_content = f"""# Module 2 Phase 1 Import Report

**Import Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**JSON File:** {self.json_file}
**Target Database:** Production Supabase PostgreSQL
**Overall Status:** {status}

## 📊 Import Summary

### Module Information
- **Module ID:** {self.module_id}
- **Course ID:** {self.course_id}
- **Module Title:** {self.data['module_info']['title']}
- **Module Created:** {'✅ Yes' if self.import_results['module_created'] else '❌ No'}

### Import Statistics
- **Lessons Imported:** {self.import_results['lessons_imported']}/5
- **Quizzes Imported:** {self.import_results['quizzes_imported']}/5
- **Questions Imported:** {self.import_results['questions_imported']}/25

### Lesson Details
{chr(10).join([f"- **Lesson {lesson['sort_order']}:** {lesson['title']} ({lesson['estimated_duration']} min)" for lesson in self.data['lessons']])}

## 🚨 Issues Found

### Critical Errors: {len(self.import_results['errors'])}
{chr(10).join([f"❌ {error}" for error in self.import_results['errors']]) if self.import_results['errors'] else "✅ No critical errors"}

### Warnings: {len(self.import_results['warnings'])}
{chr(10).join([f"⚠️ {warning}" for warning in self.import_results['warnings']]) if self.import_results['warnings'] else "✅ No warnings"}

## 🎯 Next Steps

{'### ✅ IMPORT SUCCESSFUL' if len(self.import_results['errors']) == 0 else '### ❌ IMPORT FAILED'}

{'**Recommended Actions:**' if len(self.import_results['errors']) == 0 else '**Required Actions:**'}
{chr(10).join([
    "1. Test lesson rendering in development environment",
    "2. Verify quiz functionality works correctly",
    "3. Check mobile responsiveness",
    "4. Validate progress tracking",
    "5. Deploy to production for user testing"
]) if len(self.import_results['errors']) == 0 else chr(10).join([
    "1. Review and fix critical errors above",
    "2. Re-run import script after fixes",
    "3. Verify data integrity",
    "4. Contact technical support if needed"
])}

## 📋 Database Verification

### Module 2 Access URLs
- **Development:** http://localhost:8000/lms/courses/lesson/118/
- **Production:** https://www.youthimpactglobal.com/lms/courses/lesson/118/

### Expected Behavior
- All 5 lessons should be visible in Course 6
- Each lesson should render with YITP styling
- Quizzes should function with 70% passing score
- Progress tracking should be enabled
- Content should be mobile-responsive

---
**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Import Status:** {status}
"""

        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return report_filename

    def execute_import(self):
        """Execute the complete import process"""
        print("🚀 MODULE 2 PHASE 1 PRODUCTION IMPORT")
        print("=" * 70)

        # Step 1: Connect to database
        if not self.connect_to_database():
            return False

        # Step 2: Load JSON data
        if not self.load_json_data():
            return False

        # Step 3: Verify course exists
        if not self.verify_course_exists():
            return False

        # Step 4: Check if module already exists
        module_exists = self.check_module_exists()

        try:
            # Begin transaction
            print(f"\n🔄 STARTING DATABASE TRANSACTION")
            print("=" * 60)

            # Step 5: Create module (if it doesn't exist)
            if not module_exists:
                if not self.create_module():
                    self.connection.rollback()
                    return False
            else:
                print(f"⚠️ Skipping module creation - already exists")

            # Step 6: Import lessons
            if not self.import_lessons():
                self.connection.rollback()
                return False

            # Step 7: Import quizzes and questions
            if not self.import_quizzes_and_questions():
                self.connection.rollback()
                return False

            # Step 8: Verify import
            if not self.verify_import():
                self.connection.rollback()
                return False

            # Commit transaction
            self.connection.commit()
            print(f"\n✅ TRANSACTION COMMITTED SUCCESSFULLY")

            # Step 9: Generate report
            report_file = self.generate_import_report()

            print(f"\n🎉 IMPORT COMPLETED SUCCESSFULLY!")
            print(f"📄 Import report: {report_file}")
            print(f"📊 Module 2 Phase 1 is now available in production")

            return True

        except Exception as e:
            print(f"\n❌ IMPORT FAILED: {e}")
            self.connection.rollback()
            self.import_results['errors'].append(f"Import failed: {e}")
            return False

        finally:
            if self.connection:
                self.connection.close()
                print(f"\n🔌 Database connection closed")

if __name__ == "__main__":
    importer = Module2Phase1Importer()
    success = importer.execute_import()

    if success:
        print(f"\n✅ SUCCESS: Module 2 Phase 1 imported to production")
        print(f"🌐 Access URL: https://www.youthimpactglobal.com/lms/courses/lesson/118/")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED: Import incomplete - review errors above")
        sys.exit(1)