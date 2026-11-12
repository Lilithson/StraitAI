from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


def home(request):
    """Render a database-free preview of the StraitAI dashboard."""
    return render(
        request,
        "core/home.html",
        {
            "outcomes": [
                {"label": "LO 1 · Problem analysis", "score": 89},
                {"label": "LO 2 · System design", "score": 84},
                {"label": "LO 3 · Data fluency", "score": 78},
                {"label": "LO 4 · Teamwork", "score": 92},
            ],
        },
    )


@require_GET
def health_check(request):
    """Return a minimal response confirming that the web application is reachable."""
    return JsonResponse({"status": "ok"})
