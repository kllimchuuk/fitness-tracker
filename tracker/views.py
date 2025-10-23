import json
from typing import Any

from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views import View
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from .forms import ExerciseForm
from .models import Exercise
from .models import WorkoutPlan
from .service.exercise import create_exercise
from .service.exercise import delete_exercise
from .service.exercise import get_exercise_by_id
from .service.exercise import update_exercise


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
    exercise = get_object_or_404(Exercise, id=exercise_id)
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


@require_http_methods(["GET", "POST"])
def api_exercises(request):
    if not request.session.get("user_id"):
        return JsonResponse({"detail": "Authentication required"}, status=401)

    if request.method == "GET":
        qs = Exercise.objects.all()
        search = request.GET.get("search", "")
        if search:
            qs = qs.filter(name__icontains=search)
        exercise_type = request.GET.get("type", "")
        if exercise_type:
            qs = qs.filter(type=exercise_type)
        data = list(qs.values("id", "name", "type", "description"))
        return JsonResponse({"results": data}, status=200)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    missing_fields = []
    if "name" not in payload:
        missing_fields.append("name")
    if "type" not in payload:
        missing_fields.append("type")

    if missing_fields:
        return HttpResponseBadRequest(f"Missing required fields: {', '.join(missing_fields)}")

    exercise = create_exercise(payload)
    return JsonResponse(exercise, status=201)


class ApiExerciseDetailView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return JsonResponse({"detail": "Authentication required"}, status=401)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, exercise_id):
        exercise = get_exercise_by_id(exercise_id)
        if not exercise:
            return JsonResponse({"detail": "Not found"}, status=404)
        return JsonResponse(exercise, status=200)

    def put(self, request, exercise_id):
        return self._update(request, exercise_id, full=True)

    def patch(self, request, exercise_id):
        return self._update(request, exercise_id, full=False)

    def delete(self, request, exercise_id):
        if delete_exercise(exercise_id):
            return JsonResponse({"deleted": True}, status=204)
        return JsonResponse({"detail": "Not found"}, status=404)

    def _update(self, request, exercise_id, full: bool):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        try:
            updated = update_exercise(exercise_id, payload, full=full)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        if not updated:
            return JsonResponse({"detail": "Not found"}, status=404)
        return JsonResponse(updated, status=200)


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
