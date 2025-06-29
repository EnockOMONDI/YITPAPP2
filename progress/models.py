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
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(default=timezone.now)
    completion_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    last_accessed = models.DateTimeField(null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)
    
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
        # For essay questions, manual grading is required
        return False
    
    class Meta:
        verbose_name = "Quiz Attempt"
        verbose_name_plural = "Quiz Attempts"
        ordering = ['-started_at']


class AssignmentSubmission(models.Model):
    """
    Student assignment submissions
    """
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('returned', 'Returned for Revision'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    submission_text = models.TextField(blank=True)
    file_path = models.FileField(upload_to='submissions/', blank=True, null=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions')
    graded_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assignment.title}"
    
    @property
    def is_late(self):
        """Check if submission was late"""
        if self.assignment.due_date:
            return self.submitted_at > self.assignment.due_date
        return False
    
    def grade_submission(self, score, feedback, graded_by):
        """Grade the submission"""
        self.score = score
        self.feedback = feedback
        self.graded_by = graded_by
        self.graded_at = timezone.now()
        self.status = 'graded'
        self.save(update_fields=['score', 'feedback', 'graded_by', 'graded_at', 'status'])
    
    class Meta:
        unique_together = ['student', 'assignment']
        verbose_name = "Assignment Submission"
        verbose_name_plural = "Assignment Submissions"
        ordering = ['-submitted_at']


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

