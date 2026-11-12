from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from academics.models import CourseOffering, Program


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="student_profile"
    )
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="students")
    student_number = models.CharField(
        max_length=32,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Za-z0-9-]+$",
                message="Student number may contain only letters, numbers, and hyphens.",
            )
        ],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("student_number",)

    def __str__(self):
        return f"{self.student_number} — {self.user.get_full_name() or self.user.username}"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ENROLLED = "ENROLLED", "Enrolled"
        DROPPED = "DROPPED", "Dropped"
        COMPLETED = "COMPLETED", "Completed"

    student = models.ForeignKey(
        StudentProfile, on_delete=models.PROTECT, related_name="enrollments"
    )
    offering = models.ForeignKey(
        CourseOffering, on_delete=models.PROTECT, related_name="enrollments"
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ENROLLED)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("student", "offering"), name="unique_student_enrollment")
        ]
        ordering = ("-offering__term__year", "offering__course__code", "student__student_number")

    def __str__(self):
        return f"{self.student} · {self.offering}"
