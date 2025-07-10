from django.contrib import admin
from .models import (
    Quiz, Question, Assignment, RubricCriteria, SelfAssessment,
    PeerReview, GradingScale, AssessmentTemplate, AssignmentSubmission,
    SelfAssessmentResponse
)

# Simple admin registrations for immediate functionality
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Assignment)
admin.site.register(RubricCriteria)
admin.site.register(SelfAssessment)
admin.site.register(PeerReview)
admin.site.register(GradingScale)
admin.site.register(AssessmentTemplate)
admin.site.register(AssignmentSubmission)
admin.site.register(SelfAssessmentResponse)