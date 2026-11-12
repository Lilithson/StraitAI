"""Derived program-outcome scoring from calculated learning-outcome scores."""

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from accounts.models import Enrollment
from academics.models import (
    CourseOffering,
    LearningOutcomeProgramOutcomeMapping,
    ProgramOutcome,
)
from assessments.scoring import (
    SCORE_PRECISION,
    calculate_learning_outcome_scores,
)


@dataclass(frozen=True)
class ProgramOutcomeScore:
    """One student's calculated score for a program outcome."""

    program_outcome: ProgramOutcome
    score: Decimal | None
    contributing_learning_outcome_count: int

    @property
    def display_score(self) -> str:
        if self.score is None:
            return "-"
        return f"{self.score:.2f}%"


@dataclass(frozen=True)
class StudentProgramOutcomeScores:
    """All program-outcome scores for one enrollment in an offering."""

    enrollment: Enrollment
    scores: tuple[ProgramOutcomeScore, ...]


def calculate_program_outcome_scores(
    offering: CourseOffering,
) -> tuple[list[ProgramOutcome], list[StudentProgramOutcomeScores]]:
    """Calculate program-outcome percentages for active students in an offering.

    Learning-outcome percentages are weighted by their learning-outcome-to-program-
    outcome mappings. Learning outcomes without graded evidence are excluded.
    """
    program_outcomes = list(
        ProgramOutcome.objects.filter(
            program=offering.course.program,
            is_active=True,
        ).order_by("code")
    )
    program_outcome_ids = {outcome.pk for outcome in program_outcomes}
    _, learning_outcome_scores = calculate_learning_outcome_scores(offering)
    learning_outcome_ids = {
        score.learning_outcome.pk
        for student_scores in learning_outcome_scores
        for score in student_scores.scores
    }
    mappings_by_learning_outcome = defaultdict(list)
    mappings = LearningOutcomeProgramOutcomeMapping.objects.filter(
        learning_outcome_id__in=learning_outcome_ids,
        program_outcome_id__in=program_outcome_ids,
        weight__gt=0,
    )
    for mapping in mappings:
        mappings_by_learning_outcome[mapping.learning_outcome_id].append(mapping)

    student_scores = []
    for learning_scores in learning_outcome_scores:
        weighted_totals = defaultdict(Decimal)
        weight_totals = defaultdict(Decimal)
        contributor_counts = defaultdict(int)

        for learning_score in learning_scores.scores:
            if learning_score.score is None:
                continue
            for mapping in mappings_by_learning_outcome[learning_score.learning_outcome.pk]:
                program_outcome_id = mapping.program_outcome_id
                weighted_totals[program_outcome_id] += learning_score.score * mapping.weight
                weight_totals[program_outcome_id] += mapping.weight
                contributor_counts[program_outcome_id] += 1

        scores = []
        for program_outcome in program_outcomes:
            total_weight = weight_totals[program_outcome.pk]
            score = None
            if total_weight:
                score = (weighted_totals[program_outcome.pk] / total_weight).quantize(
                    SCORE_PRECISION, rounding=ROUND_HALF_UP
                )
            scores.append(
                ProgramOutcomeScore(
                    program_outcome=program_outcome,
                    score=score,
                    contributing_learning_outcome_count=contributor_counts[program_outcome.pk],
                )
            )
        student_scores.append(
            StudentProgramOutcomeScores(
                enrollment=learning_scores.enrollment,
                scores=tuple(scores),
            )
        )

    return program_outcomes, student_scores
