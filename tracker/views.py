from django.views.generic import TemplateView

from tracker.models import Exercise, WorkoutPlan, WorkoutSession


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exercise_count"] = Exercise.objects.count()
        context["workout_plan_count"] = WorkoutPlan.objects.count()
        context["active_workout_session_count"] = WorkoutSession.objects.filter(
            status=WorkoutSession.Status.ACTIVE
        ).count()
        return context
