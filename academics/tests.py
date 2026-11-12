from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

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
