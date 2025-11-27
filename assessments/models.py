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
    max_attempts = models.IntegerField(default=15, help_text="Maximum number of attempts allowed (0 for unlimited)")
    passing_score = models.IntegerField(default=70, help_text="Minimum score to pass (percentage)")
    is_randomized = models.BooleanField(default=False, help_text="Randomize question order")
    show_results = models.BooleanField(default=True, help_text="Show results immediately after completion")
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def course(self):
        """Get the course this quiz belongs to through its lesson"""
        return self.lesson.module.course
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"
    
    @property
    def total_questions(self):
        return self.questions.count()
    
    @property
    def total_points(self):
        return sum(question.points for question in self.questions.all())

    def is_accessible_for_user(self, user):
        """
        Check if quiz is accessible for the given user based on trial boundaries and enrollment
        """
        from courses.trial_service import TrialAccessService

        # Check trial access boundaries
        trial_access = TrialAccessService.can_access_quiz(user, self)
        if trial_access['is_trial_user']:
            if not trial_access['can_access']:
                return False, trial_access['reason']
            # Trial user can access this quiz, continue with normal checks

        # Check if user can access the associated lesson
        lesson_access, lesson_message = self.lesson.is_accessible_for_user(user)
        if not lesson_access:
            return False, f"Cannot access quiz: {lesson_message}"

        return True, "Quiz is accessible."

    def can_user_attempt(self, user):
        """
        Check if user can attempt this quiz (considering attempt limits and trial access)
        """
        from progress.models import QuizAttempt

        # First check basic accessibility
        can_access, access_message = self.is_accessible_for_user(user)
        if not can_access:
            return False, access_message

        # Check attempt limits
        attempts = QuizAttempt.objects.filter(student=user, quiz=self)
        if attempts.filter(is_passed=True).exists():
            return False, "You have already passed this quiz."
        if self.max_attempts > 0 and attempts.count() >= self.max_attempts:
            return False, f"Maximum attempts ({self.max_attempts}) reached for this quiz."

        return True, "Quiz attempt allowed."

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



class AssignmentSubmission(models.Model):
    """
    Student assignment submissions
    """
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('returned', 'Returned for Revision'),
        ('late', 'Late Submission'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions')
    submission_text = models.TextField(blank=True, help_text="Text submission content")
    submission_file = models.FileField(upload_to='assignments/', blank=True, null=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True, help_text="Instructor feedback")
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_assignments')
    graded_at = models.DateTimeField(null=True, blank=True)
    is_late = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assignment.title}"

    def save(self, *args, **kwargs):
        # Check if submission is late
        if self.assignment.due_date and self.submitted_at > self.assignment.due_date:
            self.is_late = True
            self.status = 'late'

        # Update graded_at when grade is added
        if self.grade is not None and not self.graded_at:
            self.graded_at = timezone.now()
            self.status = 'graded'

        super().save(*args, **kwargs)

    @property
    def is_graded(self):
        """Check if assignment is graded"""
        return self.grade is not None

    @property
    def grade_percentage(self):
        """Calculate grade as percentage"""
        if self.grade and self.assignment.max_score:
            return (self.grade / self.assignment.max_score) * 100
        return 0

    class Meta:
        verbose_name = "Assignment Submission"
        verbose_name_plural = "Assignment Submissions"
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student']


class SelfAssessmentResponse(models.Model):
    """
    Student responses to self-assessments
    """
    assessment = models.ForeignKey(SelfAssessment, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='self_assessment_responses')
    responses = models.JSONField(help_text="User responses to assessment questions")
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    completed_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, help_text="Additional notes from the user")

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.assessment.title}"

    def calculate_score(self):
        """Calculate assessment score based on responses"""
        if not self.responses or not self.assessment.scoring_guide:
            return 0

        total_score = 0
        max_score = 0

        scoring_guide = self.assessment.scoring_guide

        for question_id, response in self.responses.items():
            if question_id in scoring_guide:
                question_scoring = scoring_guide[question_id]
                max_score += question_scoring.get('max_points', 0)

                # Simple scoring logic - can be enhanced based on question type
                if isinstance(response, (int, float)):
                    total_score += min(response, question_scoring.get('max_points', 0))
                elif isinstance(response, str) and response.lower() in ['yes', 'true', 'agree']:
                    total_score += question_scoring.get('max_points', 0)

        if max_score > 0:
            self.score = (total_score / max_score) * 100
        else:
            self.score = 0

        self.save(update_fields=['score'])
        return self.score

    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        if not self.assessment.questions or not self.responses:
            return 0

        total_questions = len(self.assessment.questions)
        answered_questions = len([r for r in self.responses.values() if r])

        return (answered_questions / total_questions) * 100 if total_questions > 0 else 0

    class Meta:
        verbose_name = "Self Assessment Response"
        verbose_name_plural = "Self Assessment Responses"
        ordering = ['-completed_at']
        unique_together = ['assessment', 'user']


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
