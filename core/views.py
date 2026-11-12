from django.db import OperationalError, ProgrammingError
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from accounts.models import Enrollment, StudentProfile
from academics.models import CourseOffering, Program
from assessments.models import Assessment, AssessmentLearningOutcomeMapping, Grade


def home(request):
    """Render a public, aggregate-only snapshot of the live workspace."""
    context = {
        "database_ready": False,
        "metrics": [],
        "offerings": [],
        "demo_data_available": False,
    }
    try:
        program_count = Program.objects.count()
        student_count = StudentProfile.objects.filter(is_active=True).count()
        offering_count = CourseOffering.objects.count()
        assessment_count = Assessment.objects.count()
        grade_count = Grade.objects.count()
        mapping_count = AssessmentLearningOutcomeMapping.objects.count()
        context.update(
            {
                "database_ready": bool(program_count or student_count or offering_count),
                "demo_data_available": Program.objects.filter(code="DEMO-CSE").exists(),
                "metrics": [
                    {"label": "Active students", "value": student_count, "detail": "Student profiles ready"},
                    {"label": "Course offerings", "value": offering_count, "detail": "Across configured terms"},
                    {"label": "Assessments", "value": assessment_count, "detail": f"{grade_count} grades recorded"},
                    {"label": "Outcome mappings", "value": mapping_count, "detail": "Assessment evidence links"},
                ],
                "offerings": CourseOffering.objects.select_related("course__program", "term")
                .annotate(
                    active_student_count=Count(
                        "enrollments",
                        filter=Q(enrollments__status=Enrollment.Status.ENROLLED),
                        distinct=True,
                    ),
                    assessment_count=Count("assessments", distinct=True),
                    instructor_count=Count("instructors", distinct=True),
                )
                .order_by("-term__year", "term__season", "course__code", "section")[:5],
            }
        )
    except (OperationalError, ProgrammingError):
        # Keep the welcome page usable before migrations or the database are available.
        pass
    return render(request, "core/home.html", context)


@require_GET
def health_check(request):
    """Return a minimal response confirming that the web application is reachable."""
    return JsonResponse({"status": "ok"})
