import json
import logging
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
from .forms import WorkoutPlanForm
from .models import Exercise
from .models import ExerciseSet
from .models import WorkoutPlan
from .service.exceptions import ServiceError
from .service.exercise import create_exercise
from .service.exercise import delete_exercise
from .service.exercise import get_exercise_by_id
from .service.exercise import update_exercise
from .service.exercise_set import add_exercise_set
from .service.exercise_set import delete_exercise_set

logger = logging.getLogger(__name__)


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


class WorkoutPlanCreateView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("authentication:login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = WorkoutPlanForm()
        return render(request, "plans/form.html", {"form": form, "mode": "create"})

    def post(self, request):
        form = WorkoutPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.creator_id = request.session["user_id"]
            plan.save()
            messages.success(request, "Workout plan created.")
            return redirect("tracker:plans_list")
        return render(request, "plans/form.html", {"form": form, "mode": "create"})


class WorkoutPlanUpdateView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("authentication:login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, plan_id: int):
        plan = get_object_or_404(WorkoutPlan, id=plan_id, creator_id=request.session["user_id"])
        form = WorkoutPlanForm(instance=plan)
        return render(request, "plans/form.html", {"form": form, "mode": "update", "plan": plan})

    def post(self, request, plan_id: int):
        plan = get_object_or_404(WorkoutPlan, id=plan_id, creator_id=request.session["user_id"])
        form = WorkoutPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Workout plan updated.")
            return redirect("tracker:plan_detail", plan_id=plan.id)
        return render(request, "plans/form.html", {"form": form, "mode": "update", "plan": plan})


class WorkoutPlanDeleteView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("authentication:login")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, plan_id: int):
        plan = get_object_or_404(WorkoutPlan, id=plan_id, creator_id=request.session["user_id"])
        plan.delete()
        messages.success(request, "Workout plan deleted.")
        return redirect("tracker:plans_list")


class WorkoutPlanListView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("authentication:login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        user_id = request.session.get("user_id")
        plans = WorkoutPlan.objects.filter(creator_id=user_id).order_by("-id")
        return render(
            request,
            "plans/list.html",
            {"plans": plans, "user_id": user_id, "email": request.session.get("email")},
        )


class WorkoutPlanDetailView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("authentication:login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, plan_id: int):
        plan = get_object_or_404(WorkoutPlan, id=plan_id, creator_id=request.session["user_id"])
        sets_qs = ExerciseSet.objects.select_related("exercise").filter(workout_plan=plan).order_by("id")
        return render(
            request,
            "plans/detail.html",
            {"plan": plan, "sets": sets_qs, "user_id": request.session.get("user_id"), "email": request.session.get("email")},
        )


class WorkoutPlanAddExerciseView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("authentication:login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, plan_id: int):
        plan = get_object_or_404(WorkoutPlan, id=plan_id, creator_id=request.session["user_id"])
        exercises = Exercise.objects.all().order_by("name")
        return render(request, "plans/add_exercise.html", {"plan": plan, "exercises": exercises})

    def post(self, request, plan_id: int):
        plan = get_object_or_404(WorkoutPlan, id=plan_id, creator_id=request.session["user_id"])
        exercise_id = request.POST.get("exercise_id")
        sets = request.POST.get("sets", 3)
        reps = request.POST.get("reps", 10)
        weight = request.POST.get("weight", 0)

        if not exercise_id:
            messages.error(request, "Please select an exercise.")
            return redirect("tracker:plan_add_exercise", plan_id=plan.id)

        try:
            es = add_exercise_set(
                plan.id,
                {
                    "exercise_id": int(exercise_id),
                    "sets": int(sets),
                    "reps": int(reps),
                    "weight": float(weight),
                },
            )
        except ServiceError as e:
            logger.warning(f"Service error adding exercise to plan {plan.id}: {e}")
            messages.error(request, "Unable to add exercise to plan.")
            return redirect("tracker:plan_detail", plan_id=plan.id)

        messages.success(request, f"Exercise '{es.exercise_name}' added successfully!")
        return redirect("tracker:plan_detail", plan_id=plan.id)


class ApiExerciseListView(View):
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if not request.session.get("user_id"):
            return JsonResponse({"detail": "Authentication required"}, status=401)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> JsonResponse:
        search = request.GET.get("search", "")
        exercise_type = request.GET.get("type", "")

        qs = Exercise.objects.all()
        if search:
            qs = qs.filter(name__icontains=search)
        if exercise_type:
            qs = qs.filter(type=exercise_type)

        data = list(qs.values("id", "name", "type", "description"))
        return JsonResponse({"results": data}, status=200)

    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON"}, status=400)

        try:
            exercise = create_exercise(payload)
        except ServiceError as e:
            logger.warning(f"Service error creating exercise: {e}")
            return JsonResponse({"detail": "Failed to create exercise."}, status=e.code)

        return JsonResponse(exercise.model_dump(), status=201)


class ApiExerciseDetailView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return JsonResponse({"detail": "Authentication required"}, status=401)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, exercise_id: int) -> JsonResponse:
        try:
            exercise = get_exercise_by_id(exercise_id)
        except ServiceError as e:
            logger.warning(f"Service error loading exercise {exercise_id}: {e}")
            return JsonResponse({"detail": "Failed to load exercise."}, status=e.code)

        return JsonResponse(exercise.model_dump(), status=200)

    def put(self, request: HttpRequest, exercise_id: int) -> JsonResponse:
        return self.update(request, exercise_id, full=True)

    def patch(self, request: HttpRequest, exercise_id: int) -> JsonResponse:
        return self.update(request, exercise_id, full=False)

    def delete(self, request: HttpRequest, exercise_id: int) -> JsonResponse:
        try:
            delete_exercise(exercise_id)
        except ServiceError as e:
            logger.warning(f"Service error deleting exercise {exercise_id}: {e}")
            return JsonResponse({"detail": "Failed to delete exercise."}, status=e.code)

        return JsonResponse({"deleted": True}, status=204)

    def update(self, request: HttpRequest, exercise_id: int, full: bool) -> JsonResponse:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON"}, status=400)

        try:
            updated = update_exercise(exercise_id, payload, full=full)
        except ServiceError as e:
            logger.warning(f"Service error updating exercise {exercise_id}: {e}")
            return JsonResponse({"detail": "Failed to update exercise."}, status=e.code)

        return JsonResponse(updated.model_dump(), status=200)


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
        return render(request, "exercises/form.html", {"form": form, "mode": "update", "exercise": exercise})

    def post(self, request: HttpRequest, exercise_id: int) -> HttpResponse:
        exercise = get_object_or_404(Exercise, id=exercise_id)
        form = ExerciseForm(request.POST, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(request, "Exercise updated.")
            return redirect("tracker:exercise_detail", exercise_id=exercise.id)
        return render(request, "exercises/form.html", {"form": form, "mode": "update", "exercise": exercise})


class ExerciseDeleteView(View):
    def post(self, request: HttpRequest, exercise_id: int) -> HttpResponse:
        if not request.session.get("user_id"):
            return redirect("authentication:login")
        exercise = get_object_or_404(Exercise, id=exercise_id)
        exercise.delete()
        messages.success(request, "Exercise deleted.")
        return redirect("tracker:exercises_list")


class ExerciseSetDeleteView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("authentication:login")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, es_id: int):
        try:
            delete_exercise_set(es_id)
        except ServiceError as e:
            logger.warning(f"Service error deleting exercise set {es_id}: {e}")
            messages.error(request, "Unable to remove exercise from plan.")
            return redirect(request.META.get("HTTP_REFERER", "tracker:plans_list"))

        messages.success(request, "Exercise removed from plan.")
        return redirect(request.META.get("HTTP_REFERER", "tracker:plans_list"))
