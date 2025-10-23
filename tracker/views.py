import json
from typing import Any

from django.contrib import messages
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views import View
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


class ExerciseListView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
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


class ExerciseDetailView(View):
    def get(self, request: HttpRequest, exercise_id: int) -> HttpResponse:
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


class ApiExerciseListView(View):
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if not request.session.get("user_id"):
            return JsonResponse({"detail": "Authentication required"}, status=401)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> JsonResponse:
        qs = Exercise.objects.all()

        search = request.GET.get("search", "")
        if search:
            qs = qs.filter(name__icontains=search)

        exercise_type = request.GET.get("type", "")
        if exercise_type:
            qs = qs.filter(type=exercise_type)

        data = list(qs.values("id", "name", "type", "description"))
        return JsonResponse({"results": data}, status=200)

    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse("Invalid JSON")

        missing_fields = []
        if "name" not in payload:
            missing_fields.append("name")
        if "type" not in payload:
            missing_fields.append("type")

        if missing_fields:
            return JsonResponse(f"Missing required fields: {', '.join(missing_fields)}")

        exercise = create_exercise(payload)
        return JsonResponse(exercise, status=201)


class ApiExerciseDetailView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return JsonResponse({"detail": "Authentication required"}, status=401)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, exercise_id: int) -> JsonResponse:
        exercise = get_exercise_by_id(exercise_id)
        if not exercise:
            return JsonResponse({"detail": "Not found"}, status=404)
        return JsonResponse(exercise, status=200)

    def put(self, request: HttpRequest, exercise_id: int) -> JsonResponse:
        return self.update(request, exercise_id, full=True)

    def patch(self, request: HttpRequest, exercise_id: int) -> JsonResponse:
        return self.update(request, exercise_id, full=False)

    def delete(self, request: HttpRequest, exercise_id: int) -> JsonResponse:
        if delete_exercise(exercise_id):
            return JsonResponse({"deleted": True}, status=204)
        return JsonResponse({"detail": "Not found"}, status=404)

    def update(self, request: HttpRequest, exercise_id: int, full: bool) -> JsonResponse:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse("Invalid JSON")

        try:
            updated = update_exercise(exercise_id, payload, full=full)
        except ValueError as e:
            return JsonResponse(str(e))

        if not updated:
            return JsonResponse({"detail": "Not found"}, status=404)
        return JsonResponse(updated, status=200)


class ExerciseCreateView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("authentication:login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> HttpResponse:
        form = ExerciseForm()
        return render(request, "exercises/form.html", {"form": form, "mode": "create"})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = ExerciseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Exercise created.")
            return redirect("tracker:exercises_list")
        return render(request, "exercises/form.html", {"form": form, "mode": "create"})


class ExerciseUpdateView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("authentication:login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, exercise_id: int) -> HttpResponse:
        exercise = get_object_or_404(Exercise, id=exercise_id)
        form = ExerciseForm(instance=exercise)
        return render(
            request,
            "exercises/form.html",
            {"form": form, "mode": "update", "exercise": exercise},
        )

    def post(self, request: HttpRequest, exercise_id: int) -> HttpResponse:
        exercise = get_object_or_404(Exercise, id=exercise_id)
        form = ExerciseForm(request.POST, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(request, "Exercise updated.")
            return redirect("tracker:exercise_detail", exercise_id=exercise.id)  # type: ignore[attr-defined]
        return render(
            request,
            "exercises/form.html",
            {"form": form, "mode": "update", "exercise": exercise},
        )


class ExerciseDeleteView(View):
    def post(self, request: HttpRequest, exercise_id: int) -> HttpResponse:
        if not request.session.get("user_id"):
            return redirect("authentication:login")
        exercise = get_object_or_404(Exercise, id=exercise_id)
        exercise.delete()
        messages.success(request, "Exercise deleted.")
        return redirect("tracker:exercises_list")
