from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class Program(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return f"{self.code} — {self.name}"


class AcademicTerm(models.Model):
    class Season(models.TextChoices):
        FALL = "FALL", "Fall"
        SPRING = "SPRING", "Spring"
        SUMMER = "SUMMER", "Summer"

    year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(9999)]
    )
    season = models.CharField(max_length=10, choices=Season.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("year", "season"), name="unique_academic_term")
        ]
        ordering = ("-year", "season")

    def __str__(self):
        return f"{self.get_season_display()} {self.year}"


class ProgramOutcome(models.Model):
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="outcomes")
    code = models.CharField(max_length=20)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("program", "code"), name="unique_program_outcome_code")
        ]
        ordering = ("program__code", "code")

    def __str__(self):
        return f"{self.program.code} {self.code}"


class Course(models.Model):
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="courses")
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    credit_hours = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(30)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("program", "code"), name="unique_course_code_per_program")
        ]
        ordering = ("program__code", "code")

    def __str__(self):
        return f"{self.code} — {self.title}"


class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="offerings")
    term = models.ForeignKey(AcademicTerm, on_delete=models.PROTECT, related_name="offerings")
    section = models.CharField(max_length=20, default="1")
    instructors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="instructed_offerings"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("course", "term", "section"), name="unique_course_offering"
            )
        ]
        ordering = ("-term__year", "term__season", "course__code", "section")

    def __str__(self):
        return f"{self.course.code} · {self.term} · Section {self.section}"


class LearningOutcome(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="learning_outcomes")
    code = models.CharField(max_length=20)
    description = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("course", "code"), name="unique_learning_outcome_code")
        ]
        ordering = ("course__code", "code")

    def __str__(self):
        return f"{self.course.code} {self.code}"


class LearningOutcomeProgramOutcomeMapping(models.Model):
    learning_outcome = models.ForeignKey(
        LearningOutcome, on_delete=models.CASCADE, related_name="program_outcome_mappings"
    )
    program_outcome = models.ForeignKey(
        ProgramOutcome, on_delete=models.PROTECT, related_name="learning_outcome_mappings"
    )
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("learning_outcome", "program_outcome"),
                name="unique_learning_outcome_program_outcome_mapping",
            ),
            models.CheckConstraint(condition=Q(weight__gte=0), name="lo_po_weight_non_negative"),
        ]

    def clean(self):
        super().clean()
        if (
            self.learning_outcome_id
            and self.program_outcome_id
            and self.learning_outcome.course.program_id != self.program_outcome.program_id
        ):
            raise ValidationError(
                {"program_outcome": "The outcome must belong to the learning outcome's program."}
            )

    def __str__(self):
        return f"{self.learning_outcome} → {self.program_outcome} ({self.weight})"


class CourseProgramOutcomeMapping(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="program_outcome_mappings"
    )
    program_outcome = models.ForeignKey(
        ProgramOutcome, on_delete=models.PROTECT, related_name="course_mappings"
    )
    weight = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(Decimal("1")), MaxValueValidator(Decimal("5"))],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("course", "program_outcome"), name="unique_course_program_outcome_mapping"
            ),
            models.CheckConstraint(
                condition=Q(weight__gte=1) & Q(weight__lte=5),
                name="course_po_weight_between_one_and_five",
            ),
        ]

    def clean(self):
        super().clean()
        if (
            self.course_id
            and self.program_outcome_id
            and self.course.program_id != self.program_outcome.program_id
        ):
            raise ValidationError(
                {"program_outcome": "The outcome must belong to the course's program."}
            )

    def __str__(self):
        return f"{self.course} → {self.program_outcome} ({self.weight})"
