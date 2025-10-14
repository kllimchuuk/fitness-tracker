from typing import Any

from django.shortcuts import render
from django.views.generic import TemplateView

from .models import Exercise
from .models import WorkoutPlan


# Create your views here.
class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["user_id"] = self.request.session.get("user_id")
        context["email"] = self.request.session.get("email")
        return context


def exercises_list(request):
    exercises = Exercise.objects.all()

    search = request.GET.get("search", "")
    if search:
        exercises = exercises.filter(name__icontains=search)

    exercise_type = request.GET.get("type", "")
    if exercise_type:
        exercises = exercises.filter(type=exercise_type)

    types = Exercise.objects.values_list("type", flat=True).distinct()

    return render(
        request,
        "exercises/list.html",
        {
            "exercises": exercises,
            "types": types,
            "search": search,
            "selected_type": exercise_type,
        },
    )


def exercise_detail(request, exercise_id):
    try:
        exercise = Exercise.objects.get(id=exercise_id)
        workout_plans = WorkoutPlan.objects.filter(exercises=exercise)
        return render(
            request,
            "exercises/detail.html",
            {
                "exercise": exercise,
                "workout_plans": workout_plans,
            },
        )
    except Exercise.DoesNotExist:
        return render(request, "404.html")
