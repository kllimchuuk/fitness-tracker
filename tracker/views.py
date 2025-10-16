import json
from typing import Any

from django.contrib import messages
from django.forms.models import model_to_dict
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotAllowed
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from .forms import ExerciseForm
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
            "user_id": request.session.get("user_id"),
            "email": request.session.get("email"),
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
                "user_id": request.session.get("user_id"),
                "email": request.session.get("email"),
            },
        )
    except Exercise.DoesNotExist:
        return render(request, "404.html")


@require_http_methods(["GET", "POST"])
def api_exercises(request):
    if request.method == "GET":
        qs = Exercise.objects.all()
        search = request.GET.get("search", "")
        if search:
            qs = qs.filter(name__icontains=search)
        exercise_type = request.GET.get("type", "")
        if exercise_type:
            qs = qs.filter(type=exercise_type)
        data = [model_to_dict(e) for e in qs]
        return JsonResponse({"results": data}, status=200)

    if not request.session.get("user_id"):
        return JsonResponse({"detail": "Authentication required"}, status=401)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    name = payload.get("name", "")
    type_ = payload.get("type")
    description = payload.get("description", "")
    if not name or not type_:
        return HttpResponseBadRequest("Fields 'name' and 'type' are required.")

    exercise = Exercise.objects.create(name=name, type=type_, description=description)
    return JsonResponse(model_to_dict(exercise), status=201)


@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def api_exercise_detail(request, exercise_id: int):
    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except Exercise.DoesNotExist:
        return JsonResponse({"detail": "Not found"}, status=404)

    if request.method == "GET":
        return JsonResponse(model_to_dict(exercise), status=200)

    if not request.session.get("user_id"):
        return JsonResponse({"detail": "Authentication required"}, status=401)

    if request.method in ["PUT", "PATCH"]:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        if request.method == "PUT":
            for field in ("name", "type"):
                if field not in payload:
                    return HttpResponseBadRequest(f"Field '{field}' is required for PUT.")

        exercise.name = payload.get("name", exercise.name)
        exercise.type = payload.get("type", exercise.type)
        exercise.description = payload.get("description", exercise.description)
        exercise.save()
        return JsonResponse(model_to_dict(exercise), status=200)

    if request.method == "DELETE":
        exercise.delete()
        return JsonResponse({"deleted": True}, status=204)

    return HttpResponseNotAllowed(["GET", "PUT", "PATCH", "DELETE"])


@require_http_methods(["GET", "POST"])
def exercise_create(request):
    if not request.session.get("user_id"):
        return redirect("authentication:login")

    if request.method == "POST":
        form = ExerciseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Exercise created.")
            return redirect("tracker:exercises_list")
    else:
        form = ExerciseForm()

    return render(request, "exercises/form.html", {"form": form, "mode": "create"})


@require_http_methods(["GET", "POST"])
def exercise_update(request, exercise_id: int):
    if not request.session.get("user_id"):
        return redirect("authentication:login")

    exercise = get_object_or_404(Exercise, id=exercise_id)
    if request.method == "POST":
        form = ExerciseForm(request.POST, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(request, "Exercise updated.")
            return redirect("tracker:exercise_detail", exercise_id=exercise.id)
    else:
        form = ExerciseForm(instance=exercise)

    return render(
        request,
        "exercises/form.html",
        {"form": form, "mode": "update", "exercise": exercise},
    )


@require_POST
def exercise_delete(request, exercise_id: int):
    if not request.session.get("user_id"):
        return redirect("authentication:login")

    exercise = get_object_or_404(Exercise, id=exercise_id)
    exercise.delete()
    messages.success(request, "Exercise deleted.")
    return redirect("tracker:exercises_list")
