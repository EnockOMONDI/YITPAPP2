from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from courses.models import Lesson

User = get_user_model()


class Quiz(models.Model):
    """
    Quiz assessments for lessons
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    time_limit = models.IntegerField(null=True, blank=True, help_text="Time limit in minutes")
    max_attempts = models.IntegerField(default=1)
    passing_score = models.IntegerField(default=70, help_text="Minimum score to pass (percentage)")
    is_randomized = models.BooleanField(default=False, help_text="Randomize question order")
    show_results = models.BooleanField(default=True, help_text="Show results immediately after completion")
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"
    
    @property
    def total_questions(self):
        return self.questions.count()
    
    @property
    def total_points(self):
        return sum(question.points for question in self.questions.all())
    
    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"


class Question(models.Model):
    """
    Individual questions within quizzes
    """
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
        ('matching', 'Matching'),
        ('fill_blank', 'Fill in the Blank'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    options = models.JSONField(default=list, blank=True, help_text="Options for multiple choice questions")
    correct_answer = models.TextField(help_text="Correct answer or answer key")
    explanation = models.TextField(blank=True, help_text="Explanation for the correct answer")
    points = models.IntegerField(default=1)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.quiz.title} - Question {self.sort_order + 1}"
    
    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['quiz', 'sort_order']


class Assignment(models.Model):
    """
    Assignment assessments for lessons
    """
    ASSIGNMENT_TYPES = [
        ('business_plan', 'Business Plan'),
        ('swot_analysis', 'SWOT Analysis'),
        ('case_study', 'Case Study Analysis'),
        ('reflection', 'Reflection Paper'),
        ('presentation', 'Presentation'),
        ('project', 'Project Work'),
        ('research', 'Research Assignment'),
    ]
    
    SUBMISSION_FORMATS = [
        ('text', 'Text Only'),
        ('file', 'File Upload Only'),
        ('both', 'Text and File'),
    ]
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField()
    assignment_type = models.CharField(max_length=30, choices=ASSIGNMENT_TYPES)
    submission_format = models.CharField(max_length=20, choices=SUBMISSION_FORMATS)
    max_file_size = models.IntegerField(default=10485760, help_text="Maximum file size in bytes (default 10MB)")
    allowed_file_types = models.JSONField(default=list, blank=True, help_text="Allowed file extensions")
    due_date = models.DateTimeField(null=True, blank=True)
    max_score = models.IntegerField(default=100)
    rubric = models.JSONField(default=dict, blank=True, help_text="Grading rubric")
    is_peer_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"
    
    @property
    def is_overdue(self):
        if self.due_date:
            return timezone.now() > self.due_date
        return False
    
    class Meta:
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"


class RubricCriteria(models.Model):
    """
    Grading criteria for assignments
    """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='rubric_criteria')
    criteria_name = models.CharField(max_length=100)
    description = models.TextField()
    max_points = models.IntegerField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, help_text="Weight in final grade")
    sort_order = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.assignment.title} - {self.criteria_name}"
    
    class Meta:
        verbose_name = "Rubric Criteria"
        verbose_name_plural = "Rubric Criteria"
        ordering = ['assignment', 'sort_order']


class SelfAssessment(models.Model):
    """
    Self-assessment tools for students
    """
    ASSESSMENT_TYPES = [
        ('personal_initiative', 'Personal Initiative'),
        ('innovation', 'Innovation and Creativity'),
        ('goal_setting', 'Goal Setting'),
        ('planning', 'Planning Skills'),
        ('financial_literacy', 'Financial Literacy'),
        ('leadership', 'Leadership Skills'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    assessment_type = models.CharField(max_length=30, choices=ASSESSMENT_TYPES)
    questions = models.JSONField(help_text="Self-assessment questions and scoring")
    scoring_guide = models.JSONField(help_text="How to interpret scores")
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_assessments')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Self Assessment"
        verbose_name_plural = "Self Assessments"


class PeerReview(models.Model):
    """
    Peer review assignments and criteria
    """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='peer_reviews')
    reviewer_count = models.IntegerField(default=3, help_text="Number of peer reviewers per submission")
    review_criteria = models.JSONField(help_text="Criteria for peer review")
    review_deadline = models.DateTimeField()
    is_anonymous = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Peer Review for {self.assignment.title}"
    
    class Meta:
        verbose_name = "Peer Review"
        verbose_name_plural = "Peer Reviews"


class GradingScale(models.Model):
    """
    Grading scales for different assessment types
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    scale_data = models.JSONField(help_text="Grade boundaries and descriptions")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Grading Scale"
        verbose_name_plural = "Grading Scales"


class AssessmentTemplate(models.Model):
    """
    Reusable assessment templates
    """
    TEMPLATE_TYPES = [
        ('quiz', 'Quiz Template'),
        ('assignment', 'Assignment Template'),
        ('rubric', 'Rubric Template'),
        ('self_assessment', 'Self-Assessment Template'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES)
    template_data = models.JSONField(help_text="Template structure and content")
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_templates')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Assessment Template"
        verbose_name_plural = "Assessment Templates"

