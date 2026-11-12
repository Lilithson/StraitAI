from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Enrollment, StudentProfile
from academics.models import AcademicTerm, Course, CourseOffering, LearningOutcome, Program
from assessments.models import Assessment, AssessmentLearningOutcomeMapping, Grade
from assessments.scoring import calculate_learning_outcome_scores
from assessments.services import save_bulk_grades


class GradeEntryTests(TestCase):
    def setUp(self):
        self.program = Program.objects.create(code="CSE", name="Computer Science")
        self.course = Course.objects.create(
            program=self.program, code="CSE321", title="Data Systems", credit_hours=3
        )
        self.other_course = Course.objects.create(
            program=self.program, code="CSE311", title="Software Engineering", credit_hours=3
        )
        self.term = AcademicTerm.objects.create(year=2026, season=AcademicTerm.Season.FALL)
        self.offering = CourseOffering.objects.create(course=self.course, term=self.term, section="1")
        self.other_offering = CourseOffering.objects.create(
            course=self.other_course, term=self.term, section="1"
        )
        user = User.objects.create_user(username="student")
        self.student = StudentProfile.objects.create(
            user=user, program=self.program, student_number="20260001"
        )
        self.enrollment = Enrollment.objects.create(student=self.student, offering=self.offering)
        self.other_enrollment = Enrollment.objects.create(
            student=self.student, offering=self.other_offering
        )
        self.assessment = Assessment.objects.create(
            offering=self.offering,
            title="Midterm",
            kind=Assessment.Kind.EXAM,
            max_score=Decimal("100.00"),
        )

    def test_grade_rejects_an_enrollment_from_another_offering(self):
        grade = Grade(
            assessment=self.assessment,
            enrollment=self.other_enrollment,
            score=Decimal("80.00"),
        )

        with self.assertRaises(ValidationError):
            grade.full_clean()

    def test_assessment_mapping_rejects_a_learning_outcome_from_another_course(self):
        learning_outcome = LearningOutcome.objects.create(
            course=self.other_course, code="LO1", description="Other course outcome"
        )
        mapping = AssessmentLearningOutcomeMapping(
            assessment=self.assessment,
            learning_outcome=learning_outcome,
            weight=Decimal("1.000"),
        )

        with self.assertRaises(ValidationError):
            mapping.full_clean()

    def test_bulk_grade_save_creates_then_updates_one_grade(self):
        save_bulk_grades(
            self.assessment,
            [{"enrollment_id": self.enrollment.pk, "score": Decimal("78.00")}],
        )
        save_bulk_grades(
            self.assessment,
            [{"enrollment_id": self.enrollment.pk, "score": Decimal("81.50")}],
        )

        self.assertEqual(Grade.objects.filter(assessment=self.assessment).count(), 1)
        self.assertEqual(
            Grade.objects.get(assessment=self.assessment, enrollment=self.enrollment).score,
            Decimal("81.50"),
        )

    def test_outcome_score_uses_weighted_grade_percentages_and_skips_missing_grades(self):
        learning_outcome = LearningOutcome.objects.create(
            course=self.course, code="LO1", description="Design a data model"
        )
        AssessmentLearningOutcomeMapping.objects.create(
            assessment=self.assessment, learning_outcome=learning_outcome, weight=Decimal("1.000")
        )
        final_exam = Assessment.objects.create(
            offering=self.offering,
            title="Final exam",
            kind=Assessment.Kind.EXAM,
            max_score=Decimal("50.00"),
        )
        AssessmentLearningOutcomeMapping.objects.create(
            assessment=final_exam, learning_outcome=learning_outcome, weight=Decimal("3.000")
        )
        ungraded_project = Assessment.objects.create(
            offering=self.offering,
            title="Ungraded project",
            kind=Assessment.Kind.PROJECT,
            max_score=Decimal("100.00"),
        )
        AssessmentLearningOutcomeMapping.objects.create(
            assessment=ungraded_project,
            learning_outcome=learning_outcome,
            weight=Decimal("10.000"),
        )
        Grade.objects.create(
            assessment=self.assessment, enrollment=self.enrollment, score=Decimal("80.00")
        )
        Grade.objects.create(
            assessment=final_exam, enrollment=self.enrollment, score=Decimal("25.00")
        )

        outcomes, student_scores = calculate_learning_outcome_scores(self.offering)

        self.assertEqual([outcome.code for outcome in outcomes], ["LO1"])
        self.assertEqual(student_scores[0].scores[0].score, Decimal("57.50"))
        self.assertEqual(student_scores[0].scores[0].graded_assessment_count, 2)
