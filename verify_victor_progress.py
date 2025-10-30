#!/usr/bin/env python3
"""
Verify Victor's Progress Update
Check that all lessons are marked as completed and enrollment is at 100%
"""

import os
import sys
import django
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson
from progress.models import Enrollment, LessonProgress

User = get_user_model()

def verify_victor_progress():
    """Verify Victor's progress after the update"""
    
    print("=== Victor Progress Verification ===\n")
    
    try:
        # Find Victor
        victor = User.objects.get(email="info@youthimpactglobal.com")
        print(f"User: {victor.username} ({victor.email})")
        
        # Get the YITP course
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        print(f"Course: {course.title}")
        
        # Get enrollment
        enrollment = Enrollment.objects.get(
            student=victor,
            course=course,
            status__in=['active', 'completed']
        )
        print(f"Enrollment Status: {enrollment.status}")
        print(f"Progress Percentage: {enrollment.progress_percentage}%")
        print(f"Enrollment Date: {enrollment.enrollment_date}")
        
        # Get all modules and lessons
        modules = Module.objects.filter(
            course=course,
            is_published=True
        ).prefetch_related('lessons').order_by('sort_order')
        
        print(f"\n=== Detailed Progress by Module ===")
        
        total_lessons = 0
        total_completed = 0
        
        for module in modules:
            lessons = module.lessons.filter(is_published=True).order_by('sort_order')
            lesson_count = lessons.count()
            total_lessons += lesson_count
            
            # Get progress for this module
            module_progress = LessonProgress.objects.filter(
                enrollment=enrollment,
                lesson__module=module,
                status='completed'
            ).count()
            
            total_completed += module_progress
            
            status_icon = "✅" if module_progress == lesson_count else "❌"
            print(f"{status_icon} {module.title}: {module_progress}/{lesson_count} lessons completed")
            
            # Show individual lesson status
            for lesson in lessons:
                try:
                    progress = LessonProgress.objects.get(
                        enrollment=enrollment,
                        lesson=lesson
                    )
                    status = "✅" if progress.status == 'completed' else "❌"
                    completed_date = progress.completed_at.strftime("%Y-%m-%d %H:%M") if progress.completed_at else "Not completed"
                    print(f"    {status} {lesson.title} - {completed_date}")
                except LessonProgress.DoesNotExist:
                    print(f"    ❌ {lesson.title} - No progress record")
        
        print(f"\n=== Summary ===")
        print(f"Total Lessons: {total_lessons}")
        print(f"Completed Lessons: {total_completed}")
        print(f"Completion Rate: {(total_completed/total_lessons*100):.1f}%")
        print(f"Enrollment Progress: {enrollment.progress_percentage}%")
        
        # Final verification
        if total_completed == total_lessons and enrollment.progress_percentage == 100:
            print(f"\n✅ VERIFICATION SUCCESSFUL!")
            print(f"Victor has completed all {total_lessons} lessons across all 4 modules.")
            print(f"Enrollment shows 100% completion.")
            return True
        else:
            print(f"\n❌ VERIFICATION FAILED!")
            print(f"Expected: {total_lessons} completed lessons and 100% progress")
            print(f"Actual: {total_completed} completed lessons and {enrollment.progress_percentage}% progress")
            return False
        
    except User.DoesNotExist:
        print("ERROR: Victor not found!")
        return False
    except Course.DoesNotExist:
        print("ERROR: YITP course not found!")
        return False
    except Enrollment.DoesNotExist:
        print("ERROR: Victor's enrollment not found!")
        return False
    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_victor_progress()
    
    if success:
        print("\n🎉 Victor's course completion has been successfully verified!")
        print("\nVictor can now:")
        print("- Access all course content without restrictions")
        print("- Take all quizzes and assessments")
        print("- Generate and download completion certificates")
        print("- View his complete learning progress")
    else:
        print("\n⚠️  Verification failed. Please check the issues above.")
