from collections import defaultdict

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
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
        enrolled_courses = Enrollment.objects.filter(
            student=self.request.user,
            status='active'
        ).values_list('course', flat=True)

        return Quiz.objects.filter(
            lesson__module__course__in=enrolled_courses,
            is_published=True
        ).select_related('lesson__module__course')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        quizzes = list(context.get('quizzes') or context.get('object_list') or [])

        attempts_map = defaultdict(list)
        if quizzes:
            for attempt in QuizAttempt.objects.filter(
                student=user,
                quiz__in=quizzes
            ).order_by('-started_at'):
                attempts_map[attempt.quiz_id].append(attempt)

        for quiz in quizzes:
            attempts = attempts_map.get(quiz.id, [])
            attempts_count = len(attempts)
            passed_attempt = next((a for a in attempts if a.is_passed), None)
            best_score = max((a.score for a in attempts if a.score is not None), default=None)
            last_attempt = attempts[0] if attempts else None

            quiz.user_attempts = attempts_count
            quiz.best_score = best_score
            quiz.is_completed = passed_attempt is not None
            quiz.is_available = quiz.is_published
            quiz.can_attempt = (
                not quiz.is_completed and
                (quiz.max_attempts == 0 or attempts_count < quiz.max_attempts)
            )
            quiz.last_attempt_id = last_attempt.id if last_attempt else None

        context['quizzes'] = quizzes
        context['object_list'] = quizzes

        user_attempts = QuizAttempt.objects.filter(student=user)
        context['total_attempts'] = user_attempts.count()
        context['completed_attempts'] = user_attempts.filter(is_passed=True).count()
        context['active_courses_count'] = Enrollment.objects.filter(
            student=user,
            status='active'
        ).count()
        return context


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

        attempts_count = attempts.count()
        has_passed = attempts.filter(is_passed=True).exists()
        can_attempt = (not has_passed) and (quiz.max_attempts == 0 or attempts_count < quiz.max_attempts)

        context['attempts'] = attempts
        context['attempts_count'] = attempts_count
        context['can_retake'] = can_attempt

        # Get best score
        if attempts.exists():
            context['best_score'] = max(attempt.score for attempt in attempts)
        else:
            context['best_score'] = None

        # Expose status flags on the quiz object for templates that expect them
        quiz.user_attempts = attempts_count
        quiz.is_completed = has_passed
        quiz.is_available = quiz.is_published
        quiz.can_attempt = can_attempt
        quiz.last_attempt_id = attempts.first().id if attempts else None

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
        passed_attempt = attempts.filter(is_passed=True).order_by('-completed_at').first()
        if passed_attempt:
            messages.info(
                request,
                'You have already passed this quiz. Review your results or continue to the next lesson.'
            )
            return redirect('assessments:quiz_results', attempt_id=passed_attempt.id)

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
            # Mark the lesson as completed when quiz is passed
            from progress.models import LessonProgress
            lesson_progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=quiz.lesson,
                defaults={
                    'status': 'completed',
                    'completed_at': timezone.now(),
                    'score': score
                }
            )

            # If lesson progress already exists but wasn't completed, mark it as completed
            if not created and lesson_progress.status != 'completed':
                lesson_progress.status = 'completed'
                lesson_progress.completed_at = timezone.now()
                lesson_progress.score = score
                lesson_progress.save()

            # Update enrollment progress
            enrollment.update_progress()

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
            score_percentage < quiz.passing_score and (
                quiz.max_attempts == 0 or user_attempts < quiz.max_attempts
            )
        )
        context['attempts_used'] = user_attempts
        context['is_intro_course'] = 'Introduction to YITP' in course.title

        # Add question results for detailed review
        question_results = []
        answer_map = attempt.answers or {}

        def _normalize_option(option):
            if isinstance(option, dict):
                return option.get('text') or option.get('label') or option.get('value') or ''
            return str(option)

        for idx, question in enumerate(questions, start=1):
            user_answer = answer_map.get(str(question.id))
            normalized_correct = (question.correct_answer or '').strip().lower()
            normalized_user = (user_answer or '').strip().lower()
            is_correct = normalized_user == normalized_correct if user_answer else False

            result_entry = {
                'number': idx,
                'question': question,
                'user_answer': user_answer,
                'is_correct': is_correct,
                'choices': [],
                'correct_answer_display': question.correct_answer,
            }

            if question.question_type == 'multiple_choice':
                for option in question.options or []:
                    text = _normalize_option(option)
                    normalized_text = text.strip().lower()
                    result_entry['choices'].append({
                        'text': text,
                        'is_correct': normalized_text == normalized_correct,
                        'is_selected': normalized_text == normalized_user
                    })
            elif question.question_type == 'true_false':
                result_entry['choices'] = [
                    {
                        'text': 'True',
                        'is_correct': normalized_correct == 'true',
                        'is_selected': normalized_user == 'true'
                    },
                    {
                        'text': 'False',
                        'is_correct': normalized_correct == 'false',
                        'is_selected': normalized_user == 'false'
                    }
                ]

            question_results.append(result_entry)

        context['question_results'] = question_results
        context['question_overview'] = [
            {
                'number': result['number'],
                'is_correct': result['is_correct']
            }
            for result in question_results
        ]

        # Determine next lesson for pass state
        next_lesson = lesson.get_next_lesson()
        if next_lesson:
            is_accessible, _ = next_lesson.is_accessible_for_user(self.request.user)
            if is_accessible:
                context['next_lesson_url'] = reverse(
                    'courses:lesson_detail',
                    kwargs={'course_slug': course.slug, 'lesson_id': next_lesson.id}
                )
                context['next_lesson_title'] = next_lesson.title

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
            lesson__module__course__in=enrolled_courses
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
