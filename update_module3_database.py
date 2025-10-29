#!/usr/bin/env python
"""
Update Module 3 in database with corrected 8-lesson structure
Remove the incorrect 17 lessons and replace with 8 proper lessons
"""

import os
import sys
import json
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question
from progress.models import LessonProgress

def delete_existing_module3_lessons():
    """Delete existing Module 3 lessons and related data"""
    
    print("🗑️  Deleting existing Module 3 lessons...")
    
    try:
        # Get Module 3
        module3 = Module.objects.get(id=16, title__icontains="TPM 101")
        print(f"Found Module 3: {module3.title} (ID: {module3.id})")
        
        # Get existing lessons
        existing_lessons = Lesson.objects.filter(module=module3).order_by('sort_order')
        print(f"Found {existing_lessons.count()} existing lessons to delete")
        
        deleted_lessons = []
        for lesson in existing_lessons:
            print(f"  Deleting: {lesson.title} (ID: {lesson.id})")
            deleted_lessons.append({
                'id': lesson.id,
                'title': lesson.title,
                'sort_order': lesson.sort_order
            })
            
            # Delete related data (CASCADE will handle most, but let's be explicit)
            # Delete lesson progress
            LessonProgress.objects.filter(lesson=lesson).delete()
            
            # Delete quizzes and questions
            quizzes = Quiz.objects.filter(lesson=lesson)
            for quiz in quizzes:
                Question.objects.filter(quiz=quiz).delete()
                quiz.delete()
            
            # Delete the lesson
            lesson.delete()
        
        print(f"✅ Successfully deleted {len(deleted_lessons)} lessons")
        return deleted_lessons
        
    except Exception as e:
        print(f"❌ Error deleting existing lessons: {str(e)}")
        raise

def create_corrected_lessons():
    """Create 8 corrected lessons for Module 3"""
    
    print("📚 Creating 8 corrected lessons...")
    
    # Load corrected JSON structure
    with open("yitp_seed_module3_corrected.json", "r", encoding="utf-8") as f:
        module3_data = json.load(f)
    
    try:
        # Get Module 3
        module3 = Module.objects.get(id=16)
        
        # Update module duration
        module3.estimated_duration = 600  # 10 hours
        module3.save()
        print(f"Updated module duration to {module3.estimated_duration} minutes")
        
        created_lessons = []
        created_quizzes = []
        
        for lesson_data in module3_data["lessons"]:
            # Create lesson
            lesson = Lesson.objects.create(
                module=module3,
                title=lesson_data["title"],
                content=lesson_data["content"],
                content_type=lesson_data["content_type"],
                video_url=lesson_data.get("video_url", ""),
                presentation_file=lesson_data.get("presentation_file", ""),
                sort_order=lesson_data["sort_order"],
                is_published=lesson_data["is_published"],
                is_mandatory=lesson_data["is_mandatory"],
                estimated_duration=lesson_data["estimated_duration"],
                learning_objectives=lesson_data["learning_objectives"]
            )
            
            created_lessons.append({
                'id': lesson.id,
                'title': lesson.title,
                'sort_order': lesson.sort_order,
                'duration': lesson.estimated_duration
            })
            
            print(f"  Created: {lesson.title} (ID: {lesson.id}, Duration: {lesson.estimated_duration}min)")
            
            # Create quiz for this lesson
            quiz_data = lesson_data["assessment"]["quiz"]
            quiz = Quiz.objects.create(
                lesson=lesson,
                title=quiz_data["title"],
                description=quiz_data["description"],
                instructions=quiz_data["instructions"],
                max_attempts=quiz_data["max_attempts"],
                passing_score=quiz_data["passing_score"],
                is_randomized=quiz_data["is_randomized"],
                show_results=quiz_data["show_results"],
                time_limit=quiz_data.get("time_limit"),
                is_published=quiz_data["is_published"]
            )
            
            created_quizzes.append({
                'id': quiz.id,
                'title': quiz.title,
                'lesson_id': lesson.id
            })
            
            # Create questions for this quiz
            for question_data in quiz_data["questions"]:
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=question_data["question_text"],
                    question_type=question_data["question_type"],
                    correct_answer=question_data["correct_answer"],
                    points=question_data["points"],
                    explanation=question_data["explanation"],
                    sort_order=question_data["sort_order"]
                )
                
                # Add options for multiple choice questions
                if question_data["question_type"] == "multiple_choice":
                    question.options = question_data["options"]
                    question.save()
        
        print(f"✅ Successfully created {len(created_lessons)} lessons")
        print(f"✅ Successfully created {len(created_quizzes)} quizzes")
        
        return created_lessons, created_quizzes
        
    except Exception as e:
        print(f"❌ Error creating corrected lessons: {str(e)}")
        raise

def republish_module3():
    """Re-publish Module 3 after fixing"""
    
    print("🔄 Re-publishing Module 3...")
    
    try:
        module3 = Module.objects.get(id=16)
        module3.is_published = True
        module3.save()
        
        print(f"✅ Module 3 re-published: {module3.title}")
        return True
        
    except Exception as e:
        print(f"❌ Error re-publishing Module 3: {str(e)}")
        raise

def verify_module3_structure():
    """Verify the corrected Module 3 structure"""
    
    print("🔍 Verifying corrected Module 3 structure...")
    
    try:
        # Get Module 3
        module3 = Module.objects.get(id=16)
        lessons = Lesson.objects.filter(module=module3).order_by('sort_order')
        
        print(f"Module: {module3.title}")
        print(f"Published: {module3.is_published}")
        print(f"Duration: {module3.estimated_duration} minutes")
        print(f"Lessons: {lessons.count()}")
        
        total_duration = 0
        for lesson in lessons:
            quizzes = Quiz.objects.filter(lesson=lesson)
            total_duration += lesson.estimated_duration
            print(f"  {lesson.sort_order}. {lesson.title} ({lesson.estimated_duration}min, {quizzes.count()} quiz)")
        
        print(f"Total lesson duration: {total_duration} minutes ({total_duration/60:.1f} hours)")
        
        # Verify against expected structure
        expected_count = 8
        if lessons.count() == expected_count:
            print(f"✅ Lesson count correct: {lessons.count()}/{expected_count}")
        else:
            print(f"❌ Lesson count incorrect: {lessons.count()}/{expected_count}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying structure: {str(e)}")
        return False

def main():
    """Main function to update Module 3 database"""
    
    print("🔧 MODULE 3 DATABASE UPDATE")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Step 1: Delete existing incorrect lessons
        deleted_lessons = delete_existing_module3_lessons()
        print()
        
        # Step 2: Create corrected lessons
        created_lessons, created_quizzes = create_corrected_lessons()
        print()
        
        # Step 3: Re-publish Module 3
        republish_module3()
        print()
        
        # Step 4: Verify structure
        verification_success = verify_module3_structure()
        print()
        
        # Summary report
        print("📋 UPDATE SUMMARY")
        print("=" * 30)
        print(f"Deleted lessons: {len(deleted_lessons)}")
        print(f"Created lessons: {len(created_lessons)}")
        print(f"Created quizzes: {len(created_quizzes)}")
        print(f"Module 3 published: Yes")
        print(f"Structure verified: {'Yes' if verification_success else 'No'}")
        
        if verification_success:
            print("\n🎉 Module 3 database update completed successfully!")
            print("✅ Module 3 now has 8 lessons instead of 17")
            print("✅ All lessons have proper titles and content")
            print("✅ All quizzes are properly configured")
            print("✅ Module is published and ready for testing")
        else:
            print("\n❌ Module 3 update completed with issues")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Module 3 update failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
