from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from courses.models import Course, Module, Lesson

User = get_user_model()


class Quiz(models.Model):
    """
    Quiz model for assessments
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True, related_name='quizzes')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name='quizzes')
    time_limit = models.IntegerField(null=True, blank=True, help_text="Time limit in minutes")
    max_attempts = models.IntegerField(default=1)
    passing_score = models.FloatField(default=70.0, help_text="Passing score percentage")
    is_published = models.BooleanField(default=False)
    randomize_questions = models.BooleanField(default=False)
    show_results_immediately = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quizzes')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    @property
    def total_questions(self):
        return self.questions.count()

    @property
    def total_points(self):
        return sum(q.points for q in self.questions.all())

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"
        ordering = ['course', 'title']


class Question(models.Model):
    """
    Question model for quizzes
    """
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
        ('fill_blank', 'Fill in the Blank'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    explanation = models.TextField(blank=True, help_text="Explanation shown after answering")
    points = models.FloatField(default=1.0)
    order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.quiz.title} - Question {self.order}"

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['quiz', 'order']


class QuestionChoice(models.Model):
    """
    Multiple choice options for questions
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.question} - Choice {self.order}"

    class Meta:
        verbose_name = "Question Choice"
        verbose_name_plural = "Question Choices"
        ordering = ['question', 'order']


class QuizAttempt(models.Model):
    """
    Quiz attempt tracking
    """
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('timed_out', 'Timed Out'),
        ('abandoned', 'Abandoned'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    score = models.FloatField(null=True, blank=True)
    percentage = models.FloatField(null=True, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent = models.DurationField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.quiz.title} (Attempt)"

    def calculate_score(self):
        """Calculate the score for this attempt"""
        if self.status != 'completed':
            return 0

        total_points = 0
        earned_points = 0

        for answer in self.answers.all():
            total_points += answer.question.points
            if answer.is_correct:
                earned_points += answer.question.points

        if total_points > 0:
            self.percentage = (earned_points / total_points) * 100
            self.score = earned_points
            self.save(update_fields=['score', 'percentage'])
            return self.score
        return 0

    def is_completed(self):
        """Check if attempt is completed"""
        return self.status == 'completed'

    def get_feedback(self):
        """Get feedback for this attempt"""
        if not self.is_completed():
            return "Quiz not yet completed"

        if self.percentage >= self.quiz.passing_score:
            return f"Congratulations! You passed with {self.percentage:.1f}%"
        else:
            return f"You scored {self.percentage:.1f}%. Passing score is {self.quiz.passing_score}%"

    class Meta:
        verbose_name = "Quiz Attempt"
        verbose_name_plural = "Quiz Attempts"
        ordering = ['-started_at']


class QuizAnswer(models.Model):
    """
    User answers to quiz questions
    """
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(QuestionChoice, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.FloatField(default=0)
    answered_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.attempt} - {self.question}"

    class Meta:
        verbose_name = "Quiz Answer"
        verbose_name_plural = "Quiz Answers"
        unique_together = ['attempt', 'question']
