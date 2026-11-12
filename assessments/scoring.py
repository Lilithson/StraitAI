"""Derived learning-outcome scoring from assessments and recorded grades."""

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from accounts.models import Enrollment
from academics.models import CourseOffering, LearningOutcome
from assessments.models import Assessment


PERCENT = Decimal("100")
SCORE_PRECISION = Decimal("0.01")


@dataclass(frozen=True)
class LearningOutcomeScore:
    """One student's calculated score for a learning outcome."""

    learning_outcome: LearningOutcome
    score: Decimal | None
    graded_assessment_count: int

    @property
    def display_score(self) -> str:
        if self.score is None:
            return "—"
        return f"{self.score:.2f}%"


@dataclass(frozen=True)
class StudentLearningOutcomeScores:
    """All learning-outcome scores for one enrollment in an offering."""

    enrollment: Enrollment
    scores: tuple[LearningOutcomeScore, ...]


def calculate_learning_outcome_scores(
    offering: CourseOffering,
) -> tuple[LearningOutcome, list[StudentLearningOutcomeScores]]:
    """Calculate outcome percentages for the active students in an offering.

    Each recorded grade becomes a percentage of the assessment's maximum score.
    That percentage is weighted by the assessment-to-learning-outcome mapping.
    Assessments without a recorded grade are excluded rather than treated as zero.
    """
    learning_outcomes = list(
        LearningOutcome.objects.filter(course=offering.course).order_by("code")
    )
    outcome_ids = {outcome.pk for outcome in learning_outcomes}
    enrollments = list(
        Enrollment.objects.filter(
            offering=offering,
            status=Enrollment.Status.ENROLLED,
            student__is_active=True,
        ).select_related("student__user")
    )
    assessments = Assessment.objects.filter(offering=offering).prefetch_related(
        "learning_outcome_mappings__learning_outcome", "grades"
    )

    weighted_totals = {
        enrollment.pk: defaultdict(Decimal) for enrollment in enrollments
    }
    weight_totals = {
        enrollment.pk: defaultdict(Decimal) for enrollment in enrollments
    }
    evidence_counts = {
        enrollment.pk: defaultdict(int) for enrollment in enrollments
    }

    for assessment in assessments:
        mappings = [
            mapping
            for mapping in assessment.learning_outcome_mappings.all()
            if mapping.learning_outcome_id in outcome_ids and mapping.weight > 0
        ]
        if not mappings:
            continue

        grades_by_enrollment = {
            grade.enrollment_id: grade for grade in assessment.grades.all()
        }
        for enrollment in enrollments:
            grade = grades_by_enrollment.get(enrollment.pk)
            if grade is None:
                continue

            percentage = (grade.score / assessment.max_score) * PERCENT
            for mapping in mappings:
                outcome_id = mapping.learning_outcome_id
                weighted_totals[enrollment.pk][outcome_id] += percentage * mapping.weight
                weight_totals[enrollment.pk][outcome_id] += mapping.weight
                evidence_counts[enrollment.pk][outcome_id] += 1

    student_scores = []
    for enrollment in enrollments:
        scores = []
        for learning_outcome in learning_outcomes:
            outcome_id = learning_outcome.pk
            total_weight = weight_totals[enrollment.pk][outcome_id]
            score = None
            if total_weight:
                score = (weighted_totals[enrollment.pk][outcome_id] / total_weight).quantize(
                    SCORE_PRECISION, rounding=ROUND_HALF_UP
                )
            scores.append(
                LearningOutcomeScore(
                    learning_outcome=learning_outcome,
                    score=score,
                    graded_assessment_count=evidence_counts[enrollment.pk][outcome_id],
                )
            )
        student_scores.append(
            StudentLearningOutcomeScores(enrollment=enrollment, scores=tuple(scores))
        )

    return learning_outcomes, student_scores
