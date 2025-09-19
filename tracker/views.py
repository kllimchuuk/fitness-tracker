from typing import Any

from django.http import HttpRequest, HttpResponse
from django.views.generic import TemplateView

from tracker.models import Exercise, WorkoutPlan, WorkoutSession


# Create your views here.
class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["user_id"] = self.request.session.get("user_id")
        context["email"] = self.request.session.get("email")
        return context
