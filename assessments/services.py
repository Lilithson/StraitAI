from django.db import transaction

from assessments.models import Grade


@transaction.atomic
def save_bulk_grades(assessment, cleaned_rows):
    """Save or clear a complete grade-entry form atomically."""
    grades_to_save = []
    enrollment_ids_to_clear = []

    for row in cleaned_rows:
        enrollment_id = row["enrollment_id"]
        score = row["score"]
        if score is None:
            enrollment_ids_to_clear.append(enrollment_id)
            continue
        grade = Grade.objects.filter(
            assessment=assessment, enrollment_id=enrollment_id
        ).first()
        if grade is None:
            grade = Grade(assessment=assessment, enrollment_id=enrollment_id, score=score)
        else:
            grade.score = score
        grade.full_clean()
        grades_to_save.append(grade)

    Grade.objects.filter(
        assessment=assessment, enrollment_id__in=enrollment_ids_to_clear
    ).delete()
    for grade in grades_to_save:
        grade.save()
