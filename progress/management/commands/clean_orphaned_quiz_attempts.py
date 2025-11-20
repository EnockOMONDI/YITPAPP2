from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef

from assessments.models import Quiz
from progress.models import Enrollment, QuizAttempt


class Command(BaseCommand):
    help = "Remove quiz attempts that reference deleted students, quizzes, or enrollments."

    def handle(self, *args, **options):
        User = get_user_model()

        self.stdout.write(self.style.MIGRATE_HEADING("Scanning for orphaned quiz attempts..."))

        deleted_counts = {
            'students': self._delete_orphans(
                QuizAttempt.objects.annotate(
                    has_student=Exists(User.objects.filter(id=OuterRef('student_id')))
                ).filter(has_student=False),
                "student"
            ),
            'quizzes': self._delete_orphans(
                QuizAttempt.objects.annotate(
                    has_quiz=Exists(Quiz.objects.filter(id=OuterRef('quiz_id')))
                ).filter(has_quiz=False),
                "quiz"
            ),
            'enrollments': self._delete_orphans(
                QuizAttempt.objects.filter(enrollment_id__isnull=False).annotate(
                    has_enrollment=Exists(Enrollment.objects.filter(id=OuterRef('enrollment_id')))
                ).filter(has_enrollment=False),
                "enrollment"
            ),
        }

        total_deleted = sum(deleted_counts.values())

        for relation, count in deleted_counts.items():
            self.stdout.write(f" - Removed {count} attempts with missing {relation}.")

        self.stdout.write(self.style.SUCCESS(f"Cleanup complete. Total attempts removed: {total_deleted}"))

    def _delete_orphans(self, queryset, relation_name):
        count = queryset.count()
        if count:
            queryset.delete()
        return count
