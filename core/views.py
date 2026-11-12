from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """Return a minimal response confirming that the web application is reachable."""
    return JsonResponse({"status": "ok"})
