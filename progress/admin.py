from django.contrib import admin
from .models import (
    Enrollment, LessonProgress, QuizAttempt, Certificate,
    Achievement, StudySession
)

# Simple admin registrations for immediate functionality
admin.site.register(Enrollment)
admin.site.register(LessonProgress)
admin.site.register(QuizAttempt)
admin.site.register(Certificate)
admin.site.register(Achievement)
admin.site.register(StudySession)