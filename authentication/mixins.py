from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse


class ApiLoginRequiredMixin(LoginRequiredMixin):
    """Answers 401 JSON instead of redirecting to the login page."""

    def handle_no_permission(self) -> JsonResponse:  # type: ignore[override]
        return JsonResponse({"detail": "Authentication required"}, status=401)
