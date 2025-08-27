from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.sessions.models import Session
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone
from django.views import generic

from .models import Exercise, WeightTracker, WorkoutPlan, WorkoutSession
# Create your views here.

@login_required
def index(request):
    exercises_count = Exercise.objects.count()
    plans_count = WorkoutPlan.objects.count()
    active_sessions_count = WorkoutSession.objects.filter(
        status=WorkoutSession.Status.ACTIVE
    ).count()

    context = {
        "exercises_count": exercises_count,
        "plans_count": plans_count,
        "active_sessions_count": active_sessions_count,
    }
    return render(request, "tracker/index.html", context)


@login_required
def profile(request):
    user = request.user
    # активні сесії (непротерміновані)
    sessions = Session.objects.filter(expire_date__gt=timezone.now()).order_by("-expire_date")
    user_sessions = []
    for session in sessions:
        data = session.get_decoded()
        if data.get("_auth_user_id") == str(user.id):
            user_sessions.append(session)

    context = {
        "user": user,
        "subscriptions": user.workout_plans.all(),
        "sessions": user_sessions,
    }
    return render(request, "tracker/profile.html", context)


class WeightTrackerListView(LoginRequiredMixin, generic.ListView):
    model = WeightTracker
    template_name = "tracker/weight_list.html"
    context_object_name = "weights"

    def get_queryset(self):
        return WeightTracker.objects.filter(user=self.request.user).order_by("-date")


class WorkoutSessionListView(LoginRequiredMixin, generic.ListView):
    model = WorkoutSession
    template_name = "tracker/session_list.html"
    context_object_name = "sessions"

    def get_queryset(self):
        return WorkoutSession.objects.filter(user=self.request.user).order_by("-start_time")


class WorkoutPlanUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = WorkoutPlan
    fields = ["name", "description", "version", "exercises"]
    template_name = "tracker/workoutplan_form.html"
    context_object_name = "plan"
    success_url = "/"
    raise_exception = True  # 403 for forbidden

    def test_func(self):
        plan: WorkoutPlan = self.get_object()
        user = self.request.user
        return user.is_superuser or user.is_staff or plan.creator_id == user.id
