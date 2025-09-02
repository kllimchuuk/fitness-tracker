from typing import Any

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import TemplateView

from authentication.views import (UserOwnsObjectMixin,
                                  WorkoutPlanOwnerOrAdminMixin)
from tracker.models import Exercise, WorkoutPlan, WorkoutSession


# Create your views here.
class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["exercise_count"] = Exercise.objects.count()
        context["workout_plan_count"] = WorkoutPlan.objects.count()
        context["active_workout_session_count"] = WorkoutSession.objects.filter(
            status=WorkoutSession.Status.ACTIVE
        ).count()
        return context


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Dashboard для авторизованих користувачів"""
    user = request.user
    assert user.is_authenticated  # для mypy

    # Отримуємо дані користувача
    user_workout_plans = WorkoutPlan.objects.filter(creator=user)
    user_sessions = WorkoutSession.objects.filter(user=user)
    active_sessions = user_sessions.filter(status=WorkoutSession.Status.ACTIVE)

    context = {
        "user_workout_plans": user_workout_plans,
        "user_sessions": user_sessions,
        "active_sessions": active_sessions,
    }

    return render(request, "tracker/dashboard.html", context)


@login_required
def create_workout_plan_view(request: HttpRequest) -> HttpResponse:
    user = request.user
    assert user.is_authenticated  # для mypy

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        if name:
            WorkoutPlan.objects.create(creator=user, name=name, description=description)
            return redirect("tracker:dashboard")
    return render(request, "tracker/workoutplan_create.html")


@login_required
def start_workout_session_view(request: HttpRequest) -> HttpResponse:
    user = request.user
    assert user.is_authenticated  # для mypy

    if request.method == "POST":
        plan_id = request.POST.get("plan_id")
        if plan_id:
            try:
                plan = WorkoutPlan.objects.get(id=plan_id, creator=user)
            except WorkoutPlan.DoesNotExist:
                return redirect("tracker:dashboard")
            WorkoutSession.objects.create(
                user=user,
                plan=plan,
                duration_minutes=0,
                status=WorkoutSession.Status.ACTIVE,
                start_time=timezone.now(),
            )
            return redirect("tracker:dashboard")
    user_plans = WorkoutPlan.objects.filter(creator=user)
    return render(
        request, "tracker/workoutsession_start.html", {"user_plans": user_plans}
    )
