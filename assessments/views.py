from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Quiz, Question, Assignment
from courses.models import Course, Lesson
from progress.models import Enrollment, QuizAttempt, AssignmentSubmission


class AssessmentDashboardView(LoginRequiredMixin, TemplateView):
    """Assessment dashboard"""
    template_name = 'lms/assessments/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's quiz attempts
        quiz_attempts = QuizAttempt.objects.filter(student=user)
        context['total_quizzes_taken'] = quiz_attempts.count()
        context['passed_quizzes'] = quiz_attempts.filter(passed=True).count()

        # Get assignment submissions
        submissions = AssignmentSubmission.objects.filter(student=user)
        context['total_assignments'] = submissions.count()
        context['graded_assignments'] = submissions.exclude(grade__isnull=True).count()

        # Recent activity
        context['recent_attempts'] = quiz_attempts.order_by('-completed_at')[:5]
        context['recent_submissions'] = submissions.order_by('-submitted_at')[:5]

        return context


class QuizListView(LoginRequiredMixin, ListView):
    """List available quizzes"""
    model = Quiz
    template_name = 'lms/assessments/quiz_list.html'
    context_object_name = 'quizzes'

    def get_queryset(self):
        # Only show quizzes from courses the user is enrolled in
        enrolled_courses = Enrollment.objects.filter(
            student=self.request.user,
            status='active'
        ).values_list('course', flat=True)

        return Quiz.objects.filter(
            lesson__module__course__in=enrolled_courses,
            is_published=True
        ).select_related('lesson__module__course')


class QuizDetailView(LoginRequiredMixin, DetailView):
    """Quiz detail and taking view"""
    model = Quiz
    template_name = 'lms/assessments/quiz_detail.html'
    context_object_name = 'quiz'
    pk_url_kwarg = 'quiz_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.object
        user = self.request.user

        # Check if user is enrolled in the course
        try:
            enrollment = Enrollment.objects.get(
                student=user,
                course=quiz.lesson.module.course,
                status='active'
            )
            context['enrollment'] = enrollment
        except Enrollment.DoesNotExist:
            context['enrollment'] = None

        # Get user's previous attempts
        attempts = QuizAttempt.objects.filter(
            student=user,
            quiz=quiz
        ).order_by('-started_at')

        context['attempts'] = attempts
        context['attempts_count'] = attempts.count()
        context['can_retake'] = (
            quiz.max_attempts == 0 or
            attempts.count() < quiz.max_attempts
        )

        # Get best score
        if attempts.exists():
            context['best_score'] = max(attempt.score for attempt in attempts)
        else:
            context['best_score'] = None

        return context


class TakeQuizView(LoginRequiredMixin, DetailView):
    """Take a quiz"""
    model = Quiz
    template_name = 'lms/assessments/take_quiz.html'
    context_object_name = 'quiz'
    pk_url_kwarg = 'quiz_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.object
        user = self.request.user

        # Check enrollment
        try:
            enrollment = Enrollment.objects.get(
                student=user,
                course=quiz.lesson.module.course,
                status='active'
            )
        except Enrollment.DoesNotExist:
            messages.error(self.request, 'You must be enrolled in this course to take quizzes.')
            return redirect('courses:course_detail', pk=quiz.lesson.module.course.id)

        # Check if user can take the quiz
        attempts = QuizAttempt.objects.filter(student=user, quiz=quiz)
        if quiz.max_attempts > 0 and attempts.count() >= quiz.max_attempts:
            messages.error(self.request, 'You have reached the maximum number of attempts for this quiz.')
            return redirect('assessments:quiz_detail', quiz_id=quiz.id)

        # Get quiz questions
        questions = quiz.questions.filter(is_active=True).order_by('order')
        context['questions'] = questions

        return context

    def post(self, request, quiz_id):
        """Submit quiz answers"""
        quiz = self.get_object()
        user = request.user

        # Create quiz attempt
        attempt = QuizAttempt.objects.create(
            student=user,
            quiz=quiz,
            started_at=timezone.now()
        )

        # Process answers and calculate score
        total_questions = quiz.questions.filter(is_active=True).count()
        correct_answers = 0

        for question in quiz.questions.filter(is_active=True):
            user_answer = request.POST.get(f'question_{question.id}')
            if user_answer == question.correct_answer:
                correct_answers += 1

        # Calculate score
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        passed = score >= quiz.passing_score

        # Update attempt
        attempt.score = score
        attempt.passed = passed
        attempt.completed_at = timezone.now()
        attempt.save()

        messages.success(request, f'Quiz completed! Your score: {score:.1f}%')
        return redirect('assessments:quiz_results', attempt_id=attempt.id)


class QuizResultsView(LoginRequiredMixin, DetailView):
    """Quiz results view"""
    model = QuizAttempt
    template_name = 'lms/assessments/quiz_results.html'
    context_object_name = 'attempt'
    pk_url_kwarg = 'attempt_id'

    def get_queryset(self):
        return QuizAttempt.objects.filter(student=self.request.user)


class AssignmentListView(LoginRequiredMixin, ListView):
    """List assignments"""
    model = Assignment
    template_name = 'lms/assessments/assignment_list.html'
    context_object_name = 'assignments'

    def get_queryset(self):
        # Only show assignments from courses the user is enrolled in
        enrolled_courses = Enrollment.objects.filter(
            student=self.request.user,
            status='active'
        ).values_list('course', flat=True)

        return Assignment.objects.filter(
            lesson__module__course__in=enrolled_courses,
            is_published=True
        ).select_related('lesson__module__course')


class AssignmentDetailView(LoginRequiredMixin, DetailView):
    """Assignment detail view"""
    model = Assignment
    template_name = 'lms/assessments/assignment_detail.html'
    context_object_name = 'assignment'
    pk_url_kwarg = 'assignment_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.object
        user = self.request.user

        # Check enrollment
        try:
            enrollment = Enrollment.objects.get(
                student=user,
                course=assignment.lesson.module.course,
                status='active'
            )
            context['enrollment'] = enrollment
        except Enrollment.DoesNotExist:
            context['enrollment'] = None

        # Get user's submission
        try:
            submission = AssignmentSubmission.objects.get(
                student=user,
                assignment=assignment
            )
            context['submission'] = submission
        except AssignmentSubmission.DoesNotExist:
            context['submission'] = None

        return context


class SubmitAssignmentView(LoginRequiredMixin, View):
    """Submit assignment"""

    def post(self, request, assignment_id):
        assignment = get_object_or_404(Assignment, id=assignment_id)

        # Check enrollment
        try:
            enrollment = Enrollment.objects.get(
                student=request.user,
                course=assignment.lesson.module.course,
                status='active'
            )
        except Enrollment.DoesNotExist:
            messages.error(request, 'You must be enrolled in this course to submit assignments.')
            return redirect('courses:course_detail', pk=assignment.lesson.module.course.id)

        # Check deadline
        if assignment.due_date and timezone.now() > assignment.due_date:
            messages.error(request, 'The deadline for this assignment has passed.')
            return redirect('assessments:assignment_detail', assignment_id=assignment.id)

        # Get or create submission
        submission, created = AssignmentSubmission.objects.get_or_create(
            student=request.user,
            assignment=assignment
        )

        # Update submission
        submission.content = request.POST.get('content', '')
        submission.submitted_at = timezone.now()
        submission.status = 'submitted'

        # Handle file upload if present
        if 'file' in request.FILES:
            submission.file = request.FILES['file']

        submission.save()

        messages.success(request, 'Assignment submitted successfully!')
        return redirect('assessments:assignment_detail', assignment_id=assignment.id)


class QuizResultsListView(LoginRequiredMixin, ListView):
    """List all quiz results for the user"""
    model = QuizAttempt
    template_name = 'lms/assessments/quiz_results.html'
    context_object_name = 'quiz_attempts'

    def get_queryset(self):
        return QuizAttempt.objects.filter(
            student=self.request.user
        ).order_by('-completed_at')


class QuizResultDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a specific quiz result"""
    model = QuizAttempt
    template_name = 'lms/assessments/quiz_result_detail.html'
    context_object_name = 'quiz_attempt'
    pk_url_kwarg = 'attempt_id'

    def get_queryset(self):
        return QuizAttempt.objects.filter(student=self.request.user)
