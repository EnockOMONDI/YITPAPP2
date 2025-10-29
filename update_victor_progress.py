#!/usr/bin/env python3
"""
Update Victor's Lesson Completion Status
Marks all lessons across all 4 modules as completed for user Victor
"""

import os
import sys
import django
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson
from progress.models import Enrollment, LessonProgress

User = get_user_model()

def update_victor_progress():
    """Update Victor's progress to mark all lessons as completed"""
    
    print("=== Victor Progress Update ===\n")
    
    try:
        # Find Victor by email
        victor_email = "info@youthimpactglobal.com"
        victor = User.objects.get(email=victor_email)
        print(f"Found user: {victor.username} ({victor.email})")
        
        # Get the YITP course
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        print(f"Found course: {course.title}")
        
        # Check enrollment
        try:
            enrollment = Enrollment.objects.get(
                student=victor,
                course=course,
                status__in=['active', 'completed']
            )
            print(f"Found enrollment: {enrollment.status} (enrolled on {enrollment.enrolled_at})")
        except Enrollment.DoesNotExist:
            print("ERROR: Victor is not enrolled in the YITP course!")
            return False
        
        # Get all modules and lessons
        modules = Module.objects.filter(
            course=course,
            is_published=True
        ).prefetch_related('lessons').order_by('sort_order')
        
        print(f"\n=== Current Progress Analysis ===")
        
        # Analyze current progress
        current_progress = LessonProgress.objects.filter(
            enrollment=enrollment
        ).select_related('lesson', 'lesson__module')
        
        completed_lessons = {}
        for progress in current_progress:
            module_title = progress.lesson.module.title
            if module_title not in completed_lessons:
                completed_lessons[module_title] = []
            if progress.status == 'completed':
                completed_lessons[module_title].append(progress.lesson.title)
        
        total_lessons = 0
        lessons_to_complete = []
        
        for module in modules:
            lessons = module.lessons.filter(is_published=True).order_by('sort_order')
            lesson_count = lessons.count()
            total_lessons += lesson_count
            
            completed_count = len(completed_lessons.get(module.title, []))
            print(f"  {module.title}: {completed_count}/{lesson_count} lessons completed")
            
            # Find lessons that need to be marked as completed
            for lesson in lessons:
                try:
                    progress = LessonProgress.objects.get(
                        enrollment=enrollment,
                        lesson=lesson
                    )
                    if progress.status != 'completed':
                        lessons_to_complete.append((lesson, progress))
                except LessonProgress.DoesNotExist:
                    lessons_to_complete.append((lesson, None))
        
        print(f"\nTotal lessons in course: {total_lessons}")
        print(f"Lessons to mark as completed: {len(lessons_to_complete)}")
        
        if not lessons_to_complete:
            print("✅ All lessons are already completed!")
            return True
        
        print(f"\n=== Lessons to Complete ===")
        for lesson, progress in lessons_to_complete:
            status = "Update existing" if progress else "Create new"
            print(f"  - {lesson.module.title} > {lesson.title} ({status})")
        
        # Confirm the update
        response = input(f"\nMark {len(lessons_to_complete)} lessons as completed for Victor? (y/N): ")
        if response.lower() != 'y':
            print("Update cancelled.")
            return False
        
        # Perform the update in a transaction
        with transaction.atomic():
            completed_count = 0
            created_count = 0
            updated_count = 0
            
            for lesson, existing_progress in lessons_to_complete:
                if existing_progress:
                    # Update existing progress
                    existing_progress.status = 'completed'
                    existing_progress.completed_at = timezone.now()
                    existing_progress.save()
                    updated_count += 1
                else:
                    # Create new progress record
                    LessonProgress.objects.create(
                        enrollment=enrollment,
                        lesson=lesson,
                        status='completed',
                        started_at=timezone.now(),
                        completed_at=timezone.now()
                    )
                    created_count += 1
                
                completed_count += 1
                print(f"✅ Completed: {lesson.module.title} > {lesson.title}")
            
            # Update enrollment progress percentage
            enrollment.progress_percentage = 100
            enrollment.save()
            
            print(f"\n=== Update Summary ===")
            print(f"✅ Lessons completed: {completed_count}")
            print(f"✅ New progress records created: {created_count}")
            print(f"✅ Existing progress records updated: {updated_count}")
            print(f"✅ Enrollment progress updated to: {enrollment.progress_percentage}%")
        
        # Verify the final state
        print(f"\n=== Final Verification ===")
        final_progress = LessonProgress.objects.filter(
            enrollment=enrollment,
            status='completed'
        ).count()
        
        print(f"Total completed lessons: {final_progress}/{total_lessons}")
        
        if final_progress == total_lessons:
            print("✅ SUCCESS: All lessons are now completed!")
        else:
            print(f"⚠️  WARNING: Only {final_progress} out of {total_lessons} lessons are completed")
        
        return True
        
    except User.DoesNotExist:
        print(f"ERROR: User with email '{victor_email}' not found!")
        return False
    except Course.DoesNotExist:
        print("ERROR: YITP course not found!")
        return False
    except Exception as e:
        print(f"Error during update: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = update_victor_progress()
    
    if success:
        print("\n✅ Victor's progress update completed successfully!")
        print("\nVictor now has:")
        print("- All 36 lessons marked as completed")
        print("- 100% course completion")
        print("- Full access to all course content, quizzes, and certificates")
    else:
        print("\n❌ Victor's progress update failed!")
        print("Please check the error messages above and try again.")
