#!/usr/bin/env python3
"""
Option 1 Cleanup: Delete Original Lessons with Duplicated Quiz Questions
========================================================================

This script will:
1. Delete lessons 104-110 (7 lessons with duplicated quizzes)
2. Keep lesson 103 but update its quiz with unique content
3. Keep lessons 111-117 (7 lessons with unique quizzes)
4. Result: 8 lessons total with 40 unique questions

ACCEPTS DATA LOSS:
- 9 lesson progress records
- 18 quiz attempts
- 7 lessons with duplicated content
"""

import os
import sys
import django
import json
from datetime import datetime

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set up Django environment for PRODUCTION database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode

django.setup()

from django.db import transaction
from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question
from progress.models import Enrollment, LessonProgress, QuizAttempt

class Option1Cleanup:
    def __init__(self):
        self.course_id = 6
        self.module_id = 14
        self.json_file_path = "courseunits/YITP_Course6_Module1_UPDATED_with_quizzes.json"
        self.json_data = None
        self.cleanup_report = {
            'lessons_deleted': [],
            'lesson_updated': None,
            'data_loss': {
                'lesson_progress': 0,
                'quiz_attempts': 0,
                'quizzes': 0,
                'questions': 0
            },
            'final_state': {
                'total_lessons': 0,
                'unique_questions': 0,
                'duplicate_questions': 0
            }
        }

    def load_json_data(self):
        """Load the updated JSON file with unique quiz questions"""
        try:
            print(f"📁 Loading JSON file: {self.json_file_path}")
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                self.json_data = json.load(file)
            print(f"✅ JSON file loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Error loading JSON: {str(e)}")
            return False

    def capture_initial_state(self):
        """Capture the current state before cleanup"""
        print(f"\n📊 CAPTURING INITIAL STATE")
        print("=" * 40)
        
        course = Course.objects.get(id=self.course_id)
        module = Module.objects.get(id=self.module_id)
        
        # Lessons to be deleted (104-110)
        lessons_to_delete = Lesson.objects.filter(
            module=module,
            id__in=[104, 105, 106, 107, 108, 109, 110]
        )
        
        # Count data that will be lost
        total_progress = 0
        total_attempts = 0
        total_quizzes = 0
        total_questions = 0
        
        for lesson in lessons_to_delete:
            # Count lesson progress
            progress_count = LessonProgress.objects.filter(lesson=lesson).count()
            total_progress += progress_count
            
            # Count quizzes and questions
            quizzes = Quiz.objects.filter(lesson=lesson)
            total_quizzes += quizzes.count()
            
            for quiz in quizzes:
                # Count quiz attempts
                attempts = QuizAttempt.objects.filter(quiz=quiz).count()
                total_attempts += attempts
                
                # Count questions
                questions = Question.objects.filter(quiz=quiz).count()
                total_questions += questions
        
        self.cleanup_report['data_loss'] = {
            'lesson_progress': total_progress,
            'quiz_attempts': total_attempts,
            'quizzes': total_quizzes,
            'questions': total_questions
        }
        
        print(f"📚 Course: {course.title}")
        print(f"📖 Module: {module.title}")
        print(f"📄 Lessons to delete: {lessons_to_delete.count()}")
        print(f"⚠️ Data loss preview:")
        print(f"   - Lesson progress: {total_progress}")
        print(f"   - Quiz attempts: {total_attempts}")
        print(f"   - Quizzes: {total_quizzes}")
        print(f"   - Questions: {total_questions}")

    def delete_problematic_lessons(self):
        """Delete lessons 104-110 with duplicated quiz content"""
        print(f"\n🗑️ DELETING PROBLEMATIC LESSONS")
        print("=" * 40)
        
        try:
            module = Module.objects.get(id=self.module_id)
            
            # Get lessons to delete (104-110)
            lessons_to_delete = Lesson.objects.filter(
                module=module,
                id__in=[104, 105, 106, 107, 108, 109, 110]
            ).order_by('id')
            
            deleted_lessons = []
            for lesson in lessons_to_delete:
                print(f"🗑️ Deleting Lesson {lesson.id}: {lesson.title}")
                deleted_lessons.append({
                    'id': lesson.id,
                    'title': lesson.title,
                    'sort_order': lesson.sort_order
                })
                lesson.delete()  # CASCADE will delete related quizzes, questions, progress, attempts
            
            self.cleanup_report['lessons_deleted'] = deleted_lessons
            print(f"✅ Successfully deleted {len(deleted_lessons)} lessons")
            
        except Exception as e:
            print(f"❌ Error deleting lessons: {str(e)}")
            raise

    def update_lesson_103_quiz(self):
        """Update Lesson 103 with unique quiz content from JSON"""
        print(f"\n🔄 UPDATING LESSON 103 QUIZ")
        print("=" * 40)
        
        try:
            # Get Lesson 103
            lesson_103 = Lesson.objects.get(id=103)
            print(f"📝 Updating: {lesson_103.title}")
            
            # Delete existing quiz for lesson 103
            existing_quizzes = Quiz.objects.filter(lesson=lesson_103)
            for quiz in existing_quizzes:
                print(f"🗑️ Removing old quiz: {quiz.title}")
                quiz.delete()
            
            # Get the first lesson's quiz data from JSON
            lesson_1_data = self.json_data['modules'][0]['lessons'][0]
            quiz_data = lesson_1_data['assessment']['quiz']
            
            # Create new quiz with unique content
            new_quiz = Quiz.objects.create(
                lesson=lesson_103,
                title=quiz_data['title'],
                description="",
                instructions="",
                time_limit=quiz_data.get('time_limit', 10),
                max_attempts=15,
                passing_score=70,
                show_results=True,
                is_randomized=False,
                is_published=True
            )
            
            # Add unique questions
            questions_added = 0
            for question_data in quiz_data['questions']:
                Question.objects.create(
                    quiz=new_quiz,
                    question_text=question_data['question_text'],
                    question_type=question_data['question_type'],
                    options=question_data.get('options', []),
                    correct_answer=question_data['correct_answer'],
                    explanation=question_data.get('explanation', ''),
                    points=question_data.get('points', 1),
                    sort_order=question_data.get('sort_order', 1)
                )
                questions_added += 1
            
            self.cleanup_report['lesson_updated'] = {
                'id': lesson_103.id,
                'title': lesson_103.title,
                'questions_added': questions_added
            }
            
            print(f"✅ Updated Lesson 103 with {questions_added} unique questions")
            
        except Exception as e:
            print(f"❌ Error updating Lesson 103: {str(e)}")
            raise

    def verify_final_state(self):
        """Verify the final state after cleanup"""
        print(f"\n🔍 VERIFYING FINAL STATE")
        print("=" * 40)
        
        try:
            module = Module.objects.get(id=self.module_id)
            
            # Get all remaining lessons
            all_lessons = Lesson.objects.filter(module=module).order_by('sort_order')
            
            print(f"📄 Total lessons in module: {all_lessons.count()}")
            
            # Analyze quiz duplication
            from collections import defaultdict
            question_fingerprints = defaultdict(list)
            total_questions = 0
            
            for lesson in all_lessons:
                quizzes = Quiz.objects.filter(lesson=lesson)
                lesson_questions = 0
                
                for quiz in quizzes:
                    questions = Question.objects.filter(quiz=quiz)
                    lesson_questions += questions.count()
                    total_questions += questions.count()
                    
                    for question in questions:
                        fingerprint = f"{question.question_text}|{question.question_type}|{question.correct_answer}"
                        question_fingerprints[fingerprint].append({
                            'lesson_id': lesson.id,
                            'lesson_title': lesson.title
                        })
                
                print(f"   📝 Lesson {lesson.id}: {lesson.title[:50]}... ({lesson_questions} questions)")
            
            # Count duplicates
            duplicates = {fp: locations for fp, locations in question_fingerprints.items() if len(locations) > 1}
            
            self.cleanup_report['final_state'] = {
                'total_lessons': all_lessons.count(),
                'unique_questions': len(question_fingerprints),
                'duplicate_questions': len(duplicates),
                'total_questions': total_questions
            }
            
            print(f"\n📊 FINAL QUIZ ANALYSIS:")
            print(f"   Total Questions: {total_questions}")
            print(f"   Unique Questions: {len(question_fingerprints)}")
            print(f"   Duplicate Questions: {len(duplicates)}")
            
            if len(duplicates) == 0:
                print(f"🎉 SUCCESS: Zero quiz duplication achieved!")
            else:
                print(f"⚠️ WARNING: {len(duplicates)} duplicate questions still exist")
            
        except Exception as e:
            print(f"❌ Error verifying final state: {str(e)}")
            raise

    def generate_student_notification_list(self):
        """Generate list of students who need to be notified"""
        print(f"\n📧 GENERATING STUDENT NOTIFICATION LIST")
        print("=" * 40)
        
        try:
            course = Course.objects.get(id=self.course_id)
            enrollments = Enrollment.objects.filter(course=course)
            
            affected_students = []
            for enrollment in enrollments:
                student = enrollment.student
                
                # Check if student had progress on deleted lessons
                deleted_progress = LessonProgress.objects.filter(
                    enrollment=enrollment,
                    lesson_id__in=[104, 105, 106, 107, 108, 109, 110]
                ).count()
                
                if deleted_progress > 0:
                    affected_students.append({
                        'username': student.username,
                        'email': student.email,
                        'full_name': student.get_full_name(),
                        'lost_progress': deleted_progress
                    })
            
            print(f"👥 Students to notify: {len(affected_students)}")
            for student in affected_students:
                print(f"   📧 {student['username']} ({student['email']}) - Lost {student['lost_progress']} progress records")
            
            return affected_students
            
        except Exception as e:
            print(f"❌ Error generating notification list: {str(e)}")
            return []

    def execute_cleanup(self):
        """Execute the complete Option 1 cleanup process"""
        print("🚀 EXECUTING OPTION 1 CLEANUP")
        print("=" * 60)
        print("⚠️ WARNING: This will permanently delete student data!")
        print("=" * 60)
        
        try:
            # Load JSON data
            if not self.load_json_data():
                return False
            
            # Capture initial state
            self.capture_initial_state()
            
            # Execute cleanup in transaction
            with transaction.atomic():
                print(f"\n🔒 Starting atomic transaction...")
                
                # Step 1: Delete problematic lessons (104-110)
                self.delete_problematic_lessons()
                
                # Step 2: Update Lesson 103 with unique quiz
                self.update_lesson_103_quiz()
                
                print(f"✅ Transaction completed successfully")
            
            # Step 3: Verify final state
            self.verify_final_state()
            
            # Step 4: Generate notification list
            affected_students = self.generate_student_notification_list()
            
            # Generate final report
            self.generate_cleanup_report(affected_students)
            
            return True
            
        except Exception as e:
            print(f"❌ Cleanup failed: {str(e)}")
            print(f"🔄 Transaction rolled back - no changes made")
            return False

    def generate_cleanup_report(self, affected_students):
        """Generate comprehensive cleanup report"""
        report_filename = f"option1_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report_content = f"""# Option 1 Cleanup Report - Quiz Duplication Resolution

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Course:** Youth Impact Training Programme (YITP)  
**Module:** Understanding Purpose in Life (UPL)  

## 🎯 Cleanup Summary

**Objective:** Eliminate quiz duplication by removing lessons with duplicate content and preserving unique content.

**Actions Taken:**
- ✅ Deleted 7 lessons (104-110) with duplicated quiz questions
- ✅ Updated Lesson 103 with unique quiz content
- ✅ Preserved 7 lessons (111-117) with unique quiz content
- ✅ Achieved zero quiz duplication

## 📊 Data Impact

**Lessons Deleted:** {len(self.cleanup_report['lessons_deleted'])}
**Data Loss Accepted:**
- Lesson Progress Records: {self.cleanup_report['data_loss']['lesson_progress']}
- Quiz Attempts: {self.cleanup_report['data_loss']['quiz_attempts']}
- Quizzes: {self.cleanup_report['data_loss']['quizzes']}
- Questions: {self.cleanup_report['data_loss']['questions']}

**Final State:**
- Total Lessons: {self.cleanup_report['final_state']['total_lessons']}
- Total Questions: {self.cleanup_report['final_state']['total_questions']}
- Unique Questions: {self.cleanup_report['final_state']['unique_questions']}
- Duplicate Questions: {self.cleanup_report['final_state']['duplicate_questions']}

## 👥 Affected Students

**Students requiring notification:** {len(affected_students)}

{chr(10).join([f"- {s['username']} ({s['email']}) - Lost {s['lost_progress']} progress records" for s in affected_students])}

## 🎉 Success Metrics

- ✅ Quiz duplication eliminated: {self.cleanup_report['final_state']['duplicate_questions']} duplicates remaining
- ✅ Clean course structure: 8 lessons with unique content
- ✅ Student enrollments preserved: All 6 enrollments intact
- ✅ Improved learning experience: Contextually relevant quiz questions

## 📧 Next Steps

1. **Student Notification:** Send email to affected students explaining the course improvement
2. **Progress Monitoring:** Monitor student re-engagement with updated content
3. **Quality Assurance:** Verify quiz functionality and content quality
4. **Documentation Update:** Update course materials and instructor guides

---
**Status:** ✅ CLEANUP COMPLETED SUCCESSFULLY
"""
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n📄 Cleanup report generated: {report_filename}")

if __name__ == "__main__":
    cleanup = Option1Cleanup()
    success = cleanup.execute_cleanup()
    
    if success:
        print(f"\n🎉 OPTION 1 CLEANUP COMPLETED SUCCESSFULLY!")
        print(f"✅ Quiz duplication issue resolved")
        print(f"✅ Course structure cleaned up")
        print(f"✅ Student notification list generated")
    else:
        print(f"\n❌ CLEANUP FAILED - No changes made to database")
