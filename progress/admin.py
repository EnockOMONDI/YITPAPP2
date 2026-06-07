from django.contrib import admin
from .models import (
    Enrollment, LessonProgress, QuizAttempt, Certificate,
    Achievement, StudySession
)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Optimized enrollment admin with query prefetches"""
    list_display = [
        'id', 'student_name', 'course_title', 'status',
        'enrollment_type', 'progress_percentage', 'enrollment_date', 'last_accessed'
    ]
    list_filter = ['status', 'enrollment_type', 'course']
    search_fields = ['student__email', 'student__username', 'student__first_name', 'student__last_name', 'course__title']
    list_select_related = ['student', 'course']
    list_per_page = 25
    ordering = ['-enrollment_date']

    def student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'student__username'

    def course_title(self, obj):
        return obj.course.title
    course_title.short_description = 'Course'
    course_title.admin_order_field = 'course__title'


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    """Optimized lesson progress admin to stop the 300+ N+1 query bottleneck"""
    list_display = [
        'id', 'student_name', 'course_title', 'lesson_title',
        'status', 'completed_at', 'time_spent_display'
    ]
    list_filter = ['status', 'lesson__module__course']
    search_fields = [
        'enrollment__student__email', 'enrollment__student__username',
        'enrollment__student__first_name', 'enrollment__student__last_name',
        'lesson__title', 'lesson__module__course__title'
    ]
    list_select_related = ['enrollment__student', 'lesson__module__course']
    list_per_page = 25
    ordering = ['enrollment', 'lesson__module__sort_order', 'lesson__sort_order']

    def student_name(self, obj):
        return obj.enrollment.student.get_full_name() or obj.enrollment.student.username
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'enrollment__student__username'

    def course_title(self, obj):
        return obj.lesson.module.course.title
    course_title.short_description = 'Course'
    course_title.admin_order_field = 'lesson__module__course__title'

    def lesson_title(self, obj):
        return obj.lesson.title
    lesson_title.short_description = 'Lesson'
    lesson_title.admin_order_field = 'lesson__title'

    def time_spent_display(self, obj):
        minutes = obj.time_spent // 60
        seconds = obj.time_spent % 60
        return f"{minutes}m {seconds}s"
    time_spent_display.short_description = 'Time Spent'
    time_spent_display.admin_order_field = 'time_spent'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    """Optimized quiz attempt admin with related joins"""
    list_display = [
        'id', 'student_name', 'quiz_title', 'attempt_number',
        'score', 'is_passed', 'started_at', 'completed_at'
    ]
    list_filter = ['is_passed', 'quiz__lesson__module__course']
    search_fields = [
        'student__email', 'student__username', 'student__first_name', 'student__last_name',
        'quiz__title', 'quiz__lesson__title'
    ]
    list_select_related = ['student', 'quiz__lesson__module__course']
    list_per_page = 25
    ordering = ['-started_at']

    def student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'student__username'

    def quiz_title(self, obj):
        return obj.quiz.title
    quiz_title.short_description = 'Quiz'
    quiz_title.admin_order_field = 'quiz__title'


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Optimized certificate admin"""
    list_display = ['certificate_id', 'student_name', 'course_title', 'certificate_type', 'issued_date', 'is_verified']
    list_filter = ['certificate_type', 'is_verified']
    search_fields = [
        'certificate_id', 'verification_code',
        'enrollment__student__email', 'enrollment__student__username',
        'enrollment__student__first_name', 'enrollment__student__last_name',
        'enrollment__course__title'
    ]
    list_select_related = ['enrollment__student', 'enrollment__course']
    list_per_page = 25
    ordering = ['-issued_date']

    def student_name(self, obj):
        return obj.enrollment.student.get_full_name() or obj.enrollment.student.username
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'enrollment__student__username'

    def course_title(self, obj):
        return obj.enrollment.course.title
    course_title.short_description = 'Course'
    course_title.admin_order_field = 'enrollment__course__title'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """Optimized achievement admin"""
    list_display = ['id', 'student_name', 'achievement_type', 'title', 'points', 'earned_at']
    list_filter = ['achievement_type']
    search_fields = [
        'student__email', 'student__username', 'student__first_name', 'student__last_name',
        'title', 'description'
    ]
    list_select_related = ['student']
    list_per_page = 25
    ordering = ['-earned_at']

    def student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'student__username'


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    """Optimized study session admin"""
    list_display = ['id', 'student_name', 'course_title', 'started_at', 'ended_at', 'duration_display']
    list_filter = ['course']
    search_fields = [
        'student__email', 'student__username', 'student__first_name', 'student__last_name',
        'course__title', 'lesson__title'
    ]
    list_select_related = ['student', 'course', 'lesson']
    list_per_page = 25
    ordering = ['-started_at']

    def student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'student__username'

    def course_title(self, obj):
        return obj.course.title
    course_title.short_description = 'Course'
    course_title.admin_order_field = 'course__title'

    def duration_display(self, obj):
        minutes = obj.duration // 60
        seconds = obj.duration % 60
        return f"{minutes}m {seconds}s"
    duration_display.short_description = 'Duration'
    duration_display.admin_order_field = 'duration'