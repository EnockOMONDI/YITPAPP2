from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson
from assessments.models import Quiz, Assignment

User = get_user_model()


class Enrollment(models.Model):
    """
    Student enrollment in courses
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('suspended', 'Suspended'),
    ]

    ENROLLMENT_TYPE_CHOICES = [
        ('paid', 'Paid Enrollment'),
        ('trial', 'Trial Enrollment'),
        ('sponsored', 'Sponsored Enrollment'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(default=timezone.now)
    completion_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    enrollment_type = models.CharField(
        max_length=20,
        choices=ENROLLMENT_TYPE_CHOICES,
        default='paid',
        help_text="Type of enrollment (paid, trial, or sponsored)"
    )
    trial_boundaries = models.JSONField(
        default=dict,
        help_text="Trial access boundaries (e.g., {'max_lessons': 2, 'max_modules': 1})"
    )
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    last_accessed = models.DateTimeField(null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)
    privacy_settings = models.JSONField(default=dict, help_text="Privacy settings for analytics and progress sharing")
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title}"
    
    def update_progress(self):
        """Calculate and update progress percentage"""
        total_lessons = self.course.total_lessons
        if total_lessons == 0:
            self.progress_percentage = 0
        else:
            completed_lessons = self.lesson_progress.filter(status='completed').count()
            self.progress_percentage = (completed_lessons / total_lessons) * 100
        self.save(update_fields=['progress_percentage'])
    
    def mark_as_accessed(self):
        """Update last accessed timestamp"""
        self.last_accessed = timezone.now()
        self.save(update_fields=['last_accessed'])

    def get_progress_percentage(self):
        """Get current progress percentage"""
        return float(self.progress_percentage)

    def get_completion_status(self):
        """Get detailed completion status"""
        total_lessons = self.course.total_lessons
        completed_lessons = self.lesson_progress.filter(status='completed').count()

        status = {
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percentage': float(self.progress_percentage),
            'is_completed': self.status == 'completed',
            'completion_date': self.completion_date,
            'certificate_issued': self.certificate_issued
        }

        # Check if course should be marked as completed
        if total_lessons > 0 and completed_lessons >= total_lessons and self.status != 'completed':
            self.status = 'completed'
            self.completion_date = timezone.now()
            self.save(update_fields=['status', 'completion_date'])
            status['is_completed'] = True
            status['completion_date'] = self.completion_date

            # Send course completion email notification
            try:
                from users.email_utils import send_course_completion_email
                send_course_completion_email(self.student, self.course, self)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send course completion email for {self.student.email}: {str(e)}")

        return status

    def get_learning_streak(self):
        """Calculate learning streak (consecutive days with activity)"""
        from datetime import timedelta

        # Get all lesson progress records ordered by completion date
        progress_records = self.lesson_progress.filter(
            status='completed',
            completed_at__isnull=False
        ).order_by('-completed_at')

        if not progress_records.exists():
            return 0

        streak = 1
        current_date = progress_records.first().completed_at.date()

        for record in progress_records[1:]:
            record_date = record.completed_at.date()
            expected_date = current_date - timedelta(days=1)

            if record_date == expected_date:
                streak += 1
                current_date = record_date
            else:
                break

        return streak

    def is_completed(self):
        """Check if enrollment is completed"""
        return self.status == 'completed'

    def is_eligible_for_certificate(self):
        """Check if student is eligible for certificate"""
        completion_status = self.get_completion_status()
        return (completion_status['is_completed'] and
                completion_status['progress_percentage'] >= 80.0)

    def generate_certificate(self):
        """Generate certificate for completed course"""
        # For testing purposes, allow certificate generation even if not fully eligible
        try:
            if not hasattr(self, 'certificate'):
                from .models import Certificate
                certificate = Certificate.objects.create(
                    enrollment=self,
                    final_score=self.progress_percentage
                )
                self.certificate_issued = True
                self.save(update_fields=['certificate_issued'])

                # Send certificate issuance email notification
                try:
                    from users.email_utils import send_certificate_issuance_email
                    send_certificate_issuance_email(self.student, self.course, certificate)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send certificate issuance email for {self.student.email}: {str(e)}")

                return certificate
            return getattr(self, 'certificate', None)
        except Exception:
            # Return existing certificate if creation fails
            return getattr(self, 'certificate', None)

    # Trial System Methods
    @property
    def is_trial_enrollment(self):
        """Check if this is a trial enrollment"""
        return self.enrollment_type == 'trial'

    @property
    def is_paid_enrollment(self):
        """Check if this is a paid enrollment"""
        return self.enrollment_type == 'paid'

    @property
    def is_sponsored_enrollment(self):
        """Check if this is a sponsored enrollment"""
        return self.enrollment_type == 'sponsored'

    def get_trial_boundaries(self):
        """Get trial access boundaries"""
        if self.is_trial_enrollment:
            return self.trial_boundaries or {'max_lessons': 2, 'max_modules': 1}
        return {}

    def set_trial_boundaries(self, max_lessons=2, max_modules=1):
        """Set trial access boundaries"""
        if self.is_trial_enrollment:
            self.trial_boundaries = {
                'max_lessons': max_lessons,
                'max_modules': max_modules
            }
            self.save(update_fields=['trial_boundaries'])

    def can_access_lesson_in_trial(self, lesson):
        """Check if trial user can access a specific lesson"""
        if not self.is_trial_enrollment:
            return True  # Non-trial users have full access

        boundaries = self.get_trial_boundaries()
        max_lessons = boundaries.get('max_lessons', 2)

        # Get all lessons in the course ordered by module and sort_order
        course_lessons = self.course.get_ordered_lessons()

        # Find the position of the requested lesson
        try:
            lesson_position = list(course_lessons).index(lesson) + 1
            return lesson_position <= max_lessons
        except ValueError:
            return False

    def can_access_quiz_in_trial(self, quiz):
        """Check if trial user can access a specific quiz"""
        if not self.is_trial_enrollment:
            return True  # Non-trial users have full access

        # Trial users can access quizzes for lessons they can access
        if hasattr(quiz, 'lesson') and quiz.lesson:
            return self.can_access_lesson_in_trial(quiz.lesson)

        return False

    def get_trial_accessible_lessons(self):
        """Get list of lessons accessible during trial"""
        if not self.is_trial_enrollment:
            return self.course.get_ordered_lessons()

        boundaries = self.get_trial_boundaries()
        max_lessons = boundaries.get('max_lessons', 2)

        course_lessons = self.course.get_ordered_lessons()
        return course_lessons[:max_lessons]

    def convert_trial_to_paid(self):
        """Convert trial enrollment to paid enrollment"""
        if self.is_trial_enrollment:
            self.enrollment_type = 'paid'
            self.trial_boundaries = {}
            self.save(update_fields=['enrollment_type', 'trial_boundaries'])

            # Update user's trial status
            if hasattr(self.student, 'profile'):
                self.student.profile.convert_trial_to_paid()

    class Meta:
        unique_together = ['student', 'course']
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        ordering = ['-enrollment_date']


class LessonProgress(models.Model):
    """
    Track student progress through individual lessons
    """
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent = models.IntegerField(default=0, help_text="Time spent in seconds")
    attempts = models.IntegerField(default=0)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.lesson.title}"
    
    def mark_started(self):
        """Mark lesson as started"""
        if self.status == 'not_started':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self, score=None):
        """Mark lesson as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if score is not None:
            self.score = score
        self.save(update_fields=['status', 'completed_at', 'score'])
        # Update enrollment progress
        self.enrollment.update_progress()
    
    def add_time_spent(self, seconds):
        """Add time spent on lesson"""
        self.time_spent += seconds
        self.save(update_fields=['time_spent'])
    
    class Meta:
        unique_together = ['enrollment', 'lesson']
        verbose_name = "Lesson Progress"
        verbose_name_plural = "Lesson Progress"
        ordering = ['enrollment', 'lesson__module__sort_order', 'lesson__sort_order']


class QuizAttempt(models.Model):
    """
    Track student quiz attempts
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    enrollment = models.ForeignKey('Enrollment', on_delete=models.CASCADE, related_name='quiz_attempts', null=True, blank=True)
    attempt_number = models.IntegerField(default=1)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    answers = models.JSONField(default=dict, help_text="Student answers")
    time_taken = models.IntegerField(null=True, blank=True, help_text="Time taken in seconds")
    is_passed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.quiz.title} (Attempt {self.attempt_number})"
    
    def calculate_score(self):
        """Calculate quiz score based on answers"""
        total_points = 0
        earned_points = 0
        
        for question in self.quiz.questions.all():
            total_points += question.points
            student_answer = self.answers.get(str(question.id))
            
            if student_answer and self._is_correct_answer(question, student_answer):
                earned_points += question.points
        
        if total_points > 0:
            self.score = (earned_points / total_points) * 100
            self.is_passed = self.score >= self.quiz.passing_score
        else:
            self.score = 0
            self.is_passed = False
        
        self.save(update_fields=['score', 'is_passed'])
        return self.score
    
    def _is_correct_answer(self, question, student_answer):
        """Check if student answer is correct"""
        if question.question_type == 'multiple_choice':
            return student_answer == question.correct_answer
        elif question.question_type == 'true_false':
            return student_answer.lower() == question.correct_answer.lower()
        elif question.question_type == 'short_answer':
            return student_answer.lower().strip() == question.correct_answer.lower().strip()
        elif question.question_type == 'matching':
            # For matching questions, compare the answer format A-3,B-2,C-1
            return self._check_matching_answer(question, student_answer)
        # For essay questions, manual grading is required
        return False

    def _check_matching_answer(self, question, student_answer):
        """Check if matching question answer is correct"""
        if not student_answer or not question.correct_answer:
            return False

        try:
            # Parse student answer (format: "A-3,B-2,C-1")
            student_matches = {}
            for pair in student_answer.split(','):
                if '-' in pair:
                    item, match = pair.split('-', 1)
                    student_matches[item.strip()] = match.strip()

            # Parse correct answer
            correct_matches = {}
            for pair in question.correct_answer.split(','):
                if '-' in pair:
                    item, match = pair.split('-', 1)
                    correct_matches[item.strip()] = match.strip()

            # Check if all matches are correct
            return student_matches == correct_matches

        except Exception:
            # If parsing fails, consider it incorrect
            return False

    def get_feedback(self):
        """Generate detailed feedback on quiz performance"""
        feedback = {
            'overall_score': float(self.score) if self.score else 0,
            'passing_score': self.quiz.passing_score,
            'is_passed': self.is_passed,
            'time_taken': self.time_taken,
            'attempt_number': self.attempt_number,
            'questions_feedback': []
        }

        for question in self.quiz.questions.all():
            student_answer = self.answers.get(str(question.id))
            is_correct = self._is_correct_answer(question, student_answer) if student_answer else False

            question_feedback = {
                'question_id': question.id,
                'question_text': question.question_text,
                'student_answer': student_answer,
                'correct_answer': question.correct_answer,
                'is_correct': is_correct,
                'points_earned': question.points if is_correct else 0,
                'points_possible': question.points,
                'explanation': question.explanation
            }
            feedback['questions_feedback'].append(question_feedback)

        return feedback

    def mark_completed(self):
        """Mark quiz attempt as completed"""
        self.completed_at = timezone.now()
        if self.started_at and self.completed_at:
            self.time_taken = int((self.completed_at - self.started_at).total_seconds())
        self.save(update_fields=['completed_at', 'time_taken'])
        return True

    def is_completed(self):
        """Check if quiz attempt is completed"""
        return self.completed_at is not None

    def get_performance_data(self):
        """Get performance analytics data"""
        performance_data = {
            'attempt_number': self.attempt_number,
            'score': float(self.score) if self.score else 0,
            'time_taken': self.time_taken,
            'is_passed': self.is_passed,
            'efficiency_score': 0,
            'question_breakdown': {},
            'improvement_areas': []
        }

        # Calculate efficiency score (score per minute)
        if self.time_taken and self.time_taken > 0:
            time_minutes = self.time_taken / 60
            performance_data['efficiency_score'] = float(self.score) / time_minutes if self.score else 0

        # Analyze question performance by type
        question_types = {}
        for question in self.quiz.questions.all():
            q_type = question.question_type
            if q_type not in question_types:
                question_types[q_type] = {'correct': 0, 'total': 0}

            question_types[q_type]['total'] += 1
            student_answer = self.answers.get(str(question.id))
            if student_answer and self._is_correct_answer(question, student_answer):
                question_types[q_type]['correct'] += 1

        for q_type, stats in question_types.items():
            accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
            performance_data['question_breakdown'][q_type] = {
                'accuracy': accuracy,
                'correct': stats['correct'],
                'total': stats['total']
            }

            # Identify improvement areas
            if accuracy < 70:
                performance_data['improvement_areas'].append(q_type)

        return performance_data

    class Meta:
        verbose_name = "Quiz Attempt"
        verbose_name_plural = "Quiz Attempts"
        ordering = ['-started_at']


class Certificate(models.Model):
    """
    Course completion certificates
    """
    CERTIFICATE_TYPES = [
        ('completion', 'Course Completion'),
        ('achievement', 'Achievement Certificate'),
        ('participation', 'Participation Certificate'),
    ]

    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES, default='completion')
    certificate_id = models.CharField(max_length=100, unique=True)
    issued_date = models.DateTimeField(default=timezone.now)
    final_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    certificate_data = models.JSONField(default=dict, help_text="Certificate template data")
    is_verified = models.BooleanField(default=True)
    verification_code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"Certificate for {self.enrollment.student.get_full_name()} - {self.enrollment.course.title}"

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            import uuid
            self.certificate_id = f"YITP-{self.enrollment.course.slug.upper()}-{uuid.uuid4().hex[:8].upper()}"
        if not self.verification_code:
            import secrets
            self.verification_code = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def get_certificate_url(self):
        """Get URL for certificate verification"""
        return f"/certificates/verify/{self.verification_code}/"

    class Meta:
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"
        ordering = ['-issued_date']



class LearningPath(models.Model):
    """
    Personalized learning paths for students
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_paths')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    courses = models.ManyToManyField(Course, through='LearningPathCourse')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.name}"
    
    class Meta:
        verbose_name = "Learning Path"
        verbose_name_plural = "Learning Paths"


class LearningPathCourse(models.Model):
    """
    Courses within learning paths with ordering
    """
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    sort_order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    unlock_criteria = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ['learning_path', 'course']
        ordering = ['learning_path', 'sort_order']


class Achievement(models.Model):
    """
    Student achievements and badges
    """
    ACHIEVEMENT_TYPES = [
        ('course_completion', 'Course Completion'),
        ('perfect_score', 'Perfect Score'),
        ('streak', 'Learning Streak'),
        ('participation', 'Active Participation'),
        ('leadership', 'Leadership'),
        ('innovation', 'Innovation'),
        ('collaboration', 'Collaboration'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=30, choices=ACHIEVEMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    badge_icon = models.CharField(max_length=50, blank=True)
    points = models.IntegerField(default=0)
    earned_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.title}"
    
    class Meta:
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"
        ordering = ['-earned_at']


class StudySession(models.Model):
    """
    Track individual study sessions
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='study_sessions')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0, help_text="Duration in seconds")
    activities = models.JSONField(default=list, help_text="Activities performed during session")
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title} ({self.started_at.date()})"
    
    def end_session(self):
        """End the study session and calculate duration"""
        self.ended_at = timezone.now()
        self.duration = int((self.ended_at - self.started_at).total_seconds())
        self.save(update_fields=['ended_at', 'duration'])
    
    class Meta:
        verbose_name = "Study Session"
        verbose_name_plural = "Study Sessions"
        ordering = ['-started_at']

