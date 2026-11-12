from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from academics.models import (
    Course,
    CourseProgramOutcomeMapping,
    LearningOutcome,
    LearningOutcomeProgramOutcomeMapping,
    Program,
    ProgramOutcome,
)


class OutcomeMappingValidationTests(TestCase):
    def setUp(self):
        self.program = Program.objects.create(code="CSE", name="Computer Science and Engineering")
        self.other_program = Program.objects.create(code="EEE", name="Electrical Engineering")
        self.course = Course.objects.create(
            program=self.program, code="CSE321", title="Data Systems", credit_hours=3
        )
        self.learning_outcome = LearningOutcome.objects.create(
            course=self.course, code="LO1", description="Design a data model."
        )
        self.program_outcome = ProgramOutcome.objects.create(
            program=self.program, code="PO1", description="Apply computing knowledge."
        )
        self.other_program_outcome = ProgramOutcome.objects.create(
            program=self.other_program, code="PO1", description="Apply engineering knowledge."
        )

    def test_learning_outcome_mapping_rejects_an_outcome_from_another_program(self):
        mapping = LearningOutcomeProgramOutcomeMapping(
            learning_outcome=self.learning_outcome,
            program_outcome=self.other_program_outcome,
            weight=Decimal("1.000"),
        )

        with self.assertRaises(ValidationError):
            mapping.full_clean()

    def test_course_mapping_rejects_an_outcome_from_another_program(self):
        mapping = CourseProgramOutcomeMapping(
            course=self.course,
            program_outcome=self.other_program_outcome,
            weight=Decimal("1.0"),
        )

        with self.assertRaises(ValidationError):
            mapping.full_clean()

    def test_course_mapping_accepts_one_to_five_weight(self):
        mapping = CourseProgramOutcomeMapping(
            course=self.course,
            program_outcome=self.program_outcome,
            weight=Decimal("3.0"),
        )

        mapping.full_clean()


class AcademicSetupAccessTests(TestCase):
    def test_anonymous_user_is_redirected_to_sign_in(self):
        response = self.client.get(reverse("academics:setup"))

        self.assertRedirects(
            response, f"{reverse('accounts:login')}?next={reverse('academics:setup')}"
        )

    def test_superuser_can_open_setup_and_create_a_program(self):
        administrator = User.objects.create_superuser(username="admin", password="password")
        self.client.force_login(administrator)

        response = self.client.post(
            reverse("academics:program-add"), {"code": "CSE", "name": "Computer Science"}
        )

        self.assertRedirects(response, reverse("academics:setup"))
        self.assertTrue(Program.objects.filter(code="CSE").exists())
