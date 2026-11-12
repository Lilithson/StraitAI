from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from accounts.models import Enrollment
from academics.models import CourseOffering, LearningOutcome


class Assessment(models.Model):
    class Kind(models.TextChoices):
        EXAM = "EXAM", "Exam"
        QUIZ = "QUIZ", "Quiz"
        ASSIGNMENT = "ASSIGNMENT", "Assignment"
        PROJECT = "PROJECT", "Project"
        OTHER = "OTHER", "Other"

    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="assessments")
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.OTHER)
    max_score = models.DecimalField(
        max_digits=7, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    due_date = models.DateField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("offering", "title"), name="unique_assessment_title_per_offering"),
            models.CheckConstraint(condition=Q(max_score__gt=0), name="assessment_max_score_positive"),
        ]
        ordering = ("offering__course__code", "due_date", "title")

    def __str__(self):
        return f"{self.offering} — {self.title}"


class AssessmentLearningOutcomeMapping(models.Model):
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="learning_outcome_mappings"
    )
    learning_outcome = models.ForeignKey(
        LearningOutcome, on_delete=models.PROTECT, related_name="assessment_mappings"
    )
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("assessment", "learning_outcome"),
                name="unique_assessment_learning_outcome_mapping",
            ),
            models.CheckConstraint(condition=Q(weight__gte=0), name="assessment_lo_weight_non_negative"),
        ]

    def clean(self):
        super().clean()
        if (
            self.assessment_id
            and self.learning_outcome_id
            and self.assessment.offering.course_id != self.learning_outcome.course_id
        ):
            raise ValidationError(
                {"learning_outcome": "The learning outcome must belong to the assessment course."}
            )

    def __str__(self):
        return f"{self.assessment} → {self.learning_outcome} ({self.weight})"


class Grade(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="grades")
    enrollment = models.ForeignKey(Enrollment, on_delete=models.PROTECT, related_name="grades")
    score = models.DecimalField(
        max_digits=7, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    recorded_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("assessment", "enrollment"), name="unique_assessment_grade"),
            models.CheckConstraint(condition=Q(score__gte=0), name="grade_score_non_negative"),
        ]
        ordering = ("assessment", "enrollment__student__student_number")

    def clean(self):
        super().clean()
        errors = {}
        if self.assessment_id and self.enrollment_id:
            if self.assessment.offering_id != self.enrollment.offering_id:
                errors["enrollment"] = "The enrollment must belong to the assessment offering."
            if self.enrollment.status != Enrollment.Status.ENROLLED:
                errors["enrollment"] = "Grades can be entered only for active enrollments."
        if self.assessment_id and self.score is not None and self.score > self.assessment.max_score:
            errors["score"] = f"Score cannot exceed the maximum of {self.assessment.max_score}."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.assessment} · {self.enrollment.student} · {self.score}"
