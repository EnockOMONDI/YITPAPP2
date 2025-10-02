from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Quiz, Question, Assignment
from courses.models import Course, Lesson
from progress.models import Enrollment, QuizAttempt
from .models import AssignmentSubmission


class AssessmentDashboardView(LoginRequiredMixin, TemplateView):
    """Assessment dashboard"""
    template_name = 'lms/assessments/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's quiz attempts
        quiz_attempts = QuizAttempt.objects.filter(student=user)
        context['total_quizzes_taken'] = quiz_attempts.count()
        context['passed_quizzes'] = quiz_attempts.filter(is_passed=True).count()

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

    def get(self, request, *args, **kwargs):
        """Handle GET request with enrollment and attempt checks"""
        quiz = self.get_object()
        user = request.user

        # Check enrollment
        try:
            enrollment = Enrollment.objects.get(
                student=user,
                course=quiz.lesson.module.course,
                status='active'
            )
        except Enrollment.DoesNotExist:
            messages.error(request, 'You must be enrolled in this course to take quizzes.')
            return redirect('courses:course_detail', slug=quiz.lesson.module.course.slug)

        # Check if user can take the quiz
        attempts = QuizAttempt.objects.filter(student=user, quiz=quiz)
        if quiz.max_attempts > 0 and attempts.count() >= quiz.max_attempts:
            messages.error(request, 'You have reached the maximum number of attempts for this quiz.')
            return redirect('assessments:quiz_detail', quiz_id=quiz.id)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.object

        # Get quiz questions
        questions = quiz.questions.all().order_by('sort_order')
        context['questions'] = questions

        return context

    def post(self, request, quiz_id):
        """Submit quiz answers"""
        quiz = self.get_object()
        user = request.user

        # Get user's enrollment for this course
        try:
            enrollment = Enrollment.objects.get(student=user, course=quiz.lesson.module.course)
        except Enrollment.DoesNotExist:
            messages.error(request, 'You must be enrolled in this course to take the quiz.')
            return redirect('courses:course_detail', course_id=quiz.lesson.module.course.id)

        # Create quiz attempt
        attempt = QuizAttempt.objects.create(
            student=user,
            quiz=quiz,
            enrollment=enrollment,
            started_at=timezone.now()
        )

        # Process answers and calculate score using QuizAttempt's grading logic
        answers = {}

        for question in quiz.questions.all():
            user_answer = request.POST.get(f'question_{question.id}')
            if user_answer:
                answers[str(question.id)] = user_answer

        # Store answers in attempt
        attempt.answers = answers

        # Calculate score using the proper grading method
        score = attempt.calculate_score()
        passed = attempt.is_passed

        # Mark attempt as completed
        attempt.mark_completed()
        attempt.save()

        if passed:
            # Award points and achievements for passing quiz
            from progress.services import GamificationService
            gamification_result = GamificationService.award_lesson_completion_points(
                user, quiz.lesson
            )

            # Store gamification data in session for success page
            request.session['quiz_success_data'] = {
                'points_awarded': gamification_result['points_awarded'],
                'total_points': gamification_result['total_points'],
                'current_streak': gamification_result['current_streak'],
                'new_achievements': [
                    {
                        'title': achievement.title,
                        'description': achievement.description,
                        'badge_icon': achievement.badge_icon,
                        'points': achievement.points
                    } for achievement in gamification_result['new_achievements']
                ]
            }

            messages.success(request, f'Congratulations! You passed with {score:.1f}%!')
            return redirect('assessments:quiz_success', attempt_id=attempt.id)
        else:
            messages.error(request, f'Quiz score: {score:.1f}%. You need {quiz.passing_score}% to pass. Try again!')
            return redirect('assessments:quiz_results', attempt_id=attempt.id)


class QuizResultsView(LoginRequiredMixin, DetailView):
    """Quiz results view"""
    model = QuizAttempt
    template_name = 'lms/assessments/quiz_results.html'
    context_object_name = 'attempt'
    pk_url_kwarg = 'attempt_id'

    def get_queryset(self):
        return QuizAttempt.objects.filter(student=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = self.object
        quiz = attempt.quiz
        lesson = quiz.lesson
        course = lesson.module.course

        # Add quiz, lesson, and course to context
        context['quiz'] = quiz
        context['lesson'] = lesson
        context['course'] = course

        # Calculate additional quiz statistics
        questions = quiz.questions.all()
        total_questions = questions.count()
        total_points = sum(q.points for q in questions)

        # Calculate correct answers count from attempt score
        # Use the score percentage to calculate correct answers
        score_percentage = float(attempt.score) if attempt.score else 0
        correct_answers = int((score_percentage / 100) * total_questions) if total_questions > 0 else 0

        # Add calculated values to context
        context['total_questions'] = total_questions
        context['total_points'] = total_points
        context['correct_answers'] = correct_answers
        context['score_percentage'] = score_percentage

        # Format time taken
        if attempt.time_taken:
            minutes = attempt.time_taken // 60
            seconds = attempt.time_taken % 60
            if minutes > 0:
                context['time_taken_formatted'] = f"{minutes}m {seconds}s"
            else:
                context['time_taken_formatted'] = f"{seconds}s"
        else:
            context['time_taken_formatted'] = "Not recorded"

        # Add retake functionality context
        from progress.models import QuizAttempt
        user_attempts = QuizAttempt.objects.filter(
            student=self.request.user,
            quiz=quiz
        ).count()

        context['can_retake'] = (
            quiz.max_attempts == 0 or  # Unlimited attempts
            user_attempts < quiz.max_attempts
        )
        context['attempts_used'] = user_attempts
        context['is_intro_course'] = 'Introduction to YITP' in course.title

        # Add question results for detailed review
        question_results = []
        if hasattr(attempt, 'answers') and attempt.answers:
            for question in questions:
                user_answer = attempt.answers.get(str(question.id))
                is_correct = user_answer == question.correct_answer if user_answer else False
                question_results.append({
                    'question': question,
                    'user_answer': user_answer,
                    'is_correct': is_correct,
                    'user_answer_id': user_answer
                })

        context['question_results'] = question_results

        return context


class QuizSuccessView(LoginRequiredMixin, DetailView):
    """Quiz success celebration page"""
    model = QuizAttempt
    template_name = 'lms/assessments/quiz_success.html'
    context_object_name = 'attempt'
    pk_url_kwarg = 'attempt_id'

    def get_queryset(self):
        return QuizAttempt.objects.filter(
            student=self.request.user,
            is_passed=True
        ).select_related('quiz__lesson__module__course')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = self.object
        quiz = attempt.quiz
        lesson = quiz.lesson
        course = lesson.module.course

        # Add quiz, lesson, and course to context
        context['quiz'] = quiz
        context['lesson'] = lesson
        context['course'] = course

        # Get gamification data from session
        gamification_data = self.request.session.pop('quiz_success_data', {})

        # Calculate score percentage for visual display
        context['score_percentage'] = (float(attempt.score) / 100) * 360  # For circular progress

        # Add gamification data
        context['points_awarded'] = gamification_data.get('points_awarded', 0)
        context['total_points'] = gamification_data.get('total_points', 0)
        context['current_streak'] = gamification_data.get('current_streak', 0)
        context['new_achievements'] = gamification_data.get('new_achievements', [])

        # Get course progress
        from progress.models import Enrollment, LessonProgress
        try:
            enrollment = Enrollment.objects.get(
                student=self.request.user,
                course=course,
                status='active'
            )

            completed_lessons = enrollment.lesson_progress.filter(status='completed').count()
            total_lessons = course.total_lessons
            progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

            context['course_progress'] = {
                'completed_lessons': completed_lessons,
                'total_lessons': total_lessons,
                'percentage': progress_percentage
            }
        except Enrollment.DoesNotExist:
            context['course_progress'] = {
                'completed_lessons': 0,
                'total_lessons': 0,
                'percentage': 0
            }

        # Check for next lesson
        next_lesson = lesson.get_next_lesson()
        if next_lesson:
            # Check if next lesson is accessible
            is_accessible, _ = next_lesson.is_accessible_for_user(self.request.user)
            if is_accessible:
                from django.urls import reverse
                context['next_lesson_url'] = reverse('courses:lesson_detail', kwargs={
                    'course_slug': course.slug,
                    'lesson_id': next_lesson.id
                })
                context['next_lesson_title'] = next_lesson.title

        return context


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
