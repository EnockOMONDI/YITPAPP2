from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.db.models import Avg
from .models import (
    Quiz, Question, Assignment, RubricCriteria, SelfAssessment,
    PeerReview, GradingScale, AssessmentTemplate, AssignmentSubmission,
    SelfAssessmentResponse
)


class QuestionInline(admin.TabularInline):
    """Inline admin for questions within quizzes"""
    model = Question
    extra = 1
    fields = ['question_text', 'question_type', 'points', 'sort_order']
    ordering = ['sort_order']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Enhanced quiz admin interface with instructor filtering"""
    list_display = [
        'title_with_link', 'lesson_course', 'total_questions_display',
        'passing_score', 'attempts_count', 'avg_score', 'is_published'
    ]
    list_filter = [
        'is_published', 'passing_score', 'max_attempts',
        'lesson__module__course', 'lesson__module__course__instructor'
    ]
    search_fields = [
        'title', 'description', 'lesson__title',
        'lesson__module__course__title', 'lesson__module__course__instructor__first_name'
    ]
    readonly_fields = ['attempts_count_display', 'performance_stats']
    inlines = [QuestionInline]

    fieldsets = (
        ('Quiz Information', {
            'fields': ('lesson', 'title', 'description', 'instructions')
        }),
        ('Settings', {
            'fields': ('time_limit', 'max_attempts', 'passing_score', 'is_randomized')
        }),
        ('Display Options', {
            'fields': ('show_results', 'is_published')
        }),
        ('Statistics', {
            'fields': ('attempts_count_display', 'performance_stats'),
            'classes': ('collapse',)
        }),
    )

    actions = ['publish_quizzes', 'unpublish_quizzes', 'reset_attempts']

    def get_queryset(self, request):
        """Filter quizzes based on instructor role"""
        qs = super().get_queryset(request)

        # System admins see all quizzes
        if request.user.is_superuser:
            return qs

        # Check if user has instructor profile
        try:
            instructor_profile = request.user.instructor_profile
            if instructor_profile.instructor_role == 'system_admin':
                return qs
            else:
                # Course instructors see only their course quizzes
                return qs.filter(lesson__module__course__instructor=request.user)
        except:
            # Regular staff users see no quizzes
            return qs.none()

    def title_with_link(self, obj):
        """Display quiz title with link"""
        return format_html(
            '<a href="{}" style="color: #ff5d15; font-weight: bold;">{}</a>',
            reverse('admin:assessments_quiz_change', args=[obj.pk]),
            obj.title
        )
    title_with_link.short_description = 'Quiz Title'
    title_with_link.admin_order_field = 'title'

    def lesson_course(self, obj):
        """Display lesson and course information"""
        course_url = reverse('admin:courses_course_change', args=[obj.lesson.module.course.pk])
        lesson_url = reverse('admin:courses_lesson_change', args=[obj.lesson.pk])

        return format_html(
            '<a href="{}" style="color: #1a2e53;">{}</a><br>'
            '<small><a href="{}" style="color: #6c757d;">{}</a></small>',
            course_url, obj.lesson.module.course.title,
            lesson_url, obj.lesson.title
        )
    lesson_course.short_description = 'Course / Lesson'

    def total_questions_display(self, obj):
        """Display total questions count"""
        count = obj.questions.count()
        if count > 0:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
                count
            )
        return format_html(
            '<span style="color: #dc3545; font-size: 11px;">No questions</span>'
        )
    total_questions_display.short_description = 'Questions'

    def attempts_count(self, obj):
        """Display attempts count"""
        count = obj.attempts.count()
        return format_html(
            '<span style="color: #007bff; font-weight: bold;">{}</span>',
            count
        )
    attempts_count.short_description = 'Attempts'

    def avg_score(self, obj):
        """Display average score"""
        attempts = obj.attempts.filter(completed_at__isnull=False)
        if attempts.exists():
            avg = attempts.aggregate(avg_score=Avg('score'))['avg_score']
            color = '#28a745' if avg >= obj.passing_score else '#dc3545'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color, avg
            )
        return '-'
    avg_score.short_description = 'Avg Score'

    def attempts_count_display(self, obj):
        """Display detailed attempts statistics"""
        total_attempts = obj.attempts.count()
        completed_attempts = obj.attempts.filter(completed_at__isnull=False).count()
        passed_attempts = obj.attempts.filter(is_passed=True).count()

        return f"Total: {total_attempts} | Completed: {completed_attempts} | Passed: {passed_attempts}"
    attempts_count_display.short_description = 'Attempt Statistics'

    def performance_stats(self, obj):
        """Display performance statistics"""
        attempts = obj.attempts.filter(completed_at__isnull=False)
        if attempts.exists():
            avg_score = attempts.aggregate(avg_score=Avg('score'))['avg_score']
            pass_rate = (attempts.filter(is_passed=True).count() / attempts.count()) * 100

            return format_html(
                'Average Score: <strong>{:.1f}%</strong><br>'
                'Pass Rate: <strong>{:.1f}%</strong><br>'
                'Total Attempts: <strong>{}</strong>',
                avg_score, pass_rate, attempts.count()
            )
        return "No attempts yet"
    performance_stats.short_description = 'Performance Statistics'

    def publish_quizzes(self, request, queryset):
        """Bulk action to publish quizzes"""
        updated = queryset.update(is_published=True)
        self.message_user(
            request,
            f'{updated} quiz(zes) have been published.',
            messages.SUCCESS
        )
    publish_quizzes.short_description = "Publish selected quizzes"

    def unpublish_quizzes(self, request, queryset):
        """Bulk action to unpublish quizzes"""
        updated = queryset.update(is_published=False)
        self.message_user(
            request,
            f'{updated} quiz(zes) have been unpublished.',
            messages.WARNING
        )
    unpublish_quizzes.short_description = "Unpublish selected quizzes"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Enhanced question admin interface"""
    list_display = [
        'question_preview', 'quiz_title', 'question_type',
        'points', 'sort_order'
    ]
    list_filter = [
        'question_type', 'points', 'quiz__lesson__module__course',
        'quiz__lesson__module__course__instructor'
    ]
    search_fields = [
        'question_text', 'quiz__title', 'quiz__lesson__title'
    ]

    fieldsets = (
        ('Question Details', {
            'fields': ('quiz', 'question_text', 'question_type', 'sort_order')
        }),
        ('Answer Configuration', {
            'fields': ('options', 'correct_answer', 'explanation')
        }),
        ('Scoring', {
            'fields': ('points',)
        }),
    )

    def get_queryset(self, request):
        """Filter questions based on instructor role"""
        qs = super().get_queryset(request)

        # System admins see all questions
        if request.user.is_superuser:
            return qs

        # Check if user has instructor profile
        try:
            instructor_profile = request.user.instructor_profile
            if instructor_profile.instructor_role == 'system_admin':
                return qs
            else:
                # Course instructors see only their course questions
                return qs.filter(quiz__lesson__module__course__instructor=request.user)
        except:
            # Regular staff users see no questions
            return qs.none()

    def question_preview(self, obj):
        """Display question text preview"""
        preview = obj.question_text[:100] + "..." if len(obj.question_text) > 100 else obj.question_text
        return format_html(
            '<div style="max-width: 300px;">{}</div>',
            preview
        )
    question_preview.short_description = 'Question'

    def quiz_title(self, obj):
        """Display quiz title with link"""
        quiz_url = reverse('admin:assessments_quiz_change', args=[obj.quiz.pk])
        return format_html(
            '<a href="{}" style="color: #ff5d15;">{}</a>',
            quiz_url,
            obj.quiz.title
        )
    quiz_title.short_description = 'Quiz'
    quiz_title.admin_order_field = 'quiz__title'


# Register other models with basic admin
admin.site.register(Assignment)
admin.site.register(RubricCriteria)
admin.site.register(SelfAssessment)
admin.site.register(PeerReview)
admin.site.register(GradingScale)
admin.site.register(AssessmentTemplate)
admin.site.register(AssignmentSubmission)
admin.site.register(SelfAssessmentResponse)