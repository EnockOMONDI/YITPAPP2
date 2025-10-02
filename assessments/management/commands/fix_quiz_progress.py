from django.core.management.base import BaseCommand
from django.utils import timezone
from progress.models import Enrollment, LessonProgress, QuizAttempt


class Command(BaseCommand):
    help = 'Fix progress tracking for existing passed quiz attempts'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Fixing quiz progress tracking...')

        # Find all passed quiz attempts
        passed_attempts = QuizAttempt.objects.filter(is_passed=True).select_related(
            'student', 'quiz__lesson__module__course', 'enrollment'
        )

        fixed_count = 0
        total_attempts = passed_attempts.count()

        self.stdout.write(f'Found {total_attempts} passed quiz attempts')

        for attempt in passed_attempts:
            try:
                # Get the enrollment for this quiz attempt
                enrollment = attempt.enrollment
                if not enrollment:
                    # Try to find enrollment by student and course
                    try:
                        enrollment = Enrollment.objects.get(
                            student=attempt.student,
                            course=attempt.quiz.lesson.module.course
                        )
                    except Enrollment.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f'No enrollment found for {attempt.student.username} in {attempt.quiz.lesson.module.course.title}'
                            )
                        )
                        continue

                # Check if lesson progress already exists and is completed
                lesson_progress = LessonProgress.objects.filter(
                    enrollment=enrollment,
                    lesson=attempt.quiz.lesson
                ).first()

                if lesson_progress and lesson_progress.status == 'completed':
                    # Already completed, skip
                    continue

                # Create or update lesson progress
                if lesson_progress:
                    # Update existing progress
                    lesson_progress.status = 'completed'
                    lesson_progress.completed_at = attempt.completed_at or timezone.now()
                    lesson_progress.score = attempt.score
                    lesson_progress.save()
                else:
                    # Create new progress record
                    LessonProgress.objects.create(
                        enrollment=enrollment,
                        lesson=attempt.quiz.lesson,
                        status='completed',
                        completed_at=attempt.completed_at or timezone.now(),
                        score=attempt.score
                    )

                # Update enrollment progress
                enrollment.update_progress()

                fixed_count += 1
                self.stdout.write(
                    f'✅ Fixed progress for {attempt.student.username}: {attempt.quiz.lesson.title}'
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error fixing attempt {attempt.id}: {str(e)}'
                    )
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\\n🎉 Fixed {fixed_count} out of {total_attempts} quiz attempts'
            )
        )

        # Show updated progress for all enrollments
        enrollments = Enrollment.objects.filter(
            quiz_attempts__is_passed=True
        ).distinct().select_related('student', 'course')

        self.stdout.write('\\n📊 Updated enrollment progress:')
        for enrollment in enrollments:
            completed = enrollment.lesson_progress.filter(status='completed').count()
            total = enrollment.course.total_lessons
            progress = (completed / total * 100) if total > 0 else 0
            self.stdout.write(
                f'  {enrollment.student.username}: {completed}/{total} lessons ({progress:.1f}%)'
            )