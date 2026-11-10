import json
import logging
from http import HTTPStatus

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from authentication.mixins import ApiLoginRequiredMixin

from .forms import ExerciseForm
from .forms import WorkoutPlanForm
from .models import Exercise
from .models import ExerciseSet
from .models import WorkoutPlan
from .models import WorkoutSession
from .repository.session import get_session_repository
from .schemas.workout_session_schema import WorkoutSessionSchema
from .service.exceptions import ServiceError
from .service.exercise import create_exercise
from .service.exercise import delete_exercise
from .service.exercise import get_exercise_by_id
from .service.exercise import get_manageable_exercise
from .service.exercise import update_exercise
from .service.exercise_set import add_exercise_set
from .service.exercise_set import delete_exercise_set
from .service.session import get_session_service
from .service.weight_tracker import get_weight_tracker_service

logger = logging.getLogger(__name__)
session_repo = get_session_repository()
session_service = get_session_service()
weight_tracker_service = get_weight_tracker_service()


def get_manageable_exercise_or_error(request: HttpRequest, exercise_id: int) -> Exercise:
    """404 if the exercise is not visible to the user, 403 if visible but not theirs to change."""
    try:
        return get_manageable_exercise(exercise_id, request.user)
    except ServiceError as e:
        if e.code == HTTPStatus.FORBIDDEN:
            raise PermissionDenied
        raise Http404


class IndexView(TemplateView):
    template_name = "index.html"


class ExerciseListView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        visible = Exercise.objects.visible_to(request.user)
        exercises = visible
        search = request.GET.get("search", "")
        if search:
            exercises = exercises.filter(name__icontains=search)

        exercise_type = request.GET.get("type", "")
        if exercise_type:
            exercises = exercises.filter(type=exercise_type)

        types = visible.values_list("type", flat=True).distinct()

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


class ExerciseDetailView(View):
    def get(self, request: HttpRequest, exercise_id: int) -> HttpResponse:
        exercise = get_object_or_404(Exercise.objects.visible_to(request.user), id=exercise_id)
        if request.user.is_authenticated:
            workout_plans = WorkoutPlan.objects.filter(exercises=exercise, creator=request.user)
        else:
            workout_plans = WorkoutPlan.objects.none()
        return render(
            request,
            "exercises/detail.html",
            {
                "exercise": exercise,
                "workout_plans": workout_plans,
                "can_manage": exercise.can_be_managed_by(request.user),
            },
        )


class WorkoutPlanCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = WorkoutPlanForm()
        return render(request, "plans/form.html", {"form": form, "mode": "create"})

    def post(self, request):
        form = WorkoutPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.creator_id = request.user.id
            plan.save()
            messages.success(request, "Workout plan created.")
            return redirect("tracker:plans_list")
        return render(request, "plans/form.html", {"form": form, "mode": "create"})


class WorkoutPlanUpdateView(LoginRequiredMixin, View):
    def get(self, request, plan_id: int):
        plan = get_object_or_404(WorkoutPlan, id=plan_id, creator_id=request.user.id)
        form = WorkoutPlanForm(instance=plan)
        return render(request, "plans/form.html", {"form": form, "mode": "update", "plan": plan})

    def post(self, request, plan_id: int):
        plan = get_object_or_404(WorkoutPlan, id=plan_id, creator_id=request.user.id)
        form = WorkoutPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Workout plan updated.")
            return redirect("tracker:plan_detail", plan_id=plan.id)
        return render(request, "plans/form.html", {"form": form, "mode": "update", "plan": plan})


class WorkoutPlanDeleteView(LoginRequiredMixin, View):
    def post(self, request, plan_id: int):
        plan = get_object_or_404(WorkoutPlan, id=plan_id, creator_id=request.user.id)
        plan.delete()
        messages.success(request, "Workout plan deleted.")
        return redirect("tracker:plans_list")


class WorkoutPlanListView(LoginRequiredMixin, View):
    def get(self, request):
        user_id = request.user.id
        plans = WorkoutPlan.objects.filter(creator_id=user_id).order_by("-id")

        start_mode = request.GET.get("start") == "true"

        return render(
            request,
            "plans/list.html",
            {
                "plans": plans,
                "start_mode": start_mode,
            },
        )


class WorkoutPlanDetailView(LoginRequiredMixin, View):
    def get(self, request, plan_id: int):
        plan = get_object_or_404(WorkoutPlan, id=plan_id, creator_id=request.user.id)
        sets_qs = ExerciseSet.objects.select_related("exercise").filter(workout_plan=plan).order_by("id")

        from_start_mode = request.GET.get("start") == "true"

        return render(
            request,
            "plans/detail.html",
            {
                "plan": plan,
                "sets": sets_qs,
                "from_start_mode": from_start_mode,
            },
        )


class WorkoutPlanAddExerciseView(LoginRequiredMixin, View):
    def get(self, request, plan_id: int):
        plan = get_object_or_404(WorkoutPlan, id=plan_id, creator_id=request.user.id)
        exercises = Exercise.objects.visible_to(request.user).order_by("name")
        return render(request, "plans/add_exercise.html", {"plan": plan, "exercises": exercises})

    def post(self, request, plan_id: int):
        plan = get_object_or_404(WorkoutPlan, id=plan_id, creator_id=request.user.id)
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
                request.user,
            )
        except ServiceError as e:
            logger.warning(f"Service error adding exercise to plan {plan.id}: {e}")
            messages.error(request, "Unable to add exercise to plan.")
            return redirect("tracker:plan_detail", plan_id=plan.id)

        messages.success(request, f"Exercise '{es.exercise_name}' added successfully!")
        return redirect("tracker:plan_detail", plan_id=plan.id)


class ApiExerciseListView(ApiLoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> JsonResponse:
        search = request.GET.get("search", "")
        exercise_type = request.GET.get("type", "")

        qs = Exercise.objects.visible_to(request.user)
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
            exercise = create_exercise(payload, request.user)
        except ServiceError as e:
            logger.warning(f"Service error creating exercise: {e}")
            return JsonResponse({"detail": "Failed to create exercise."}, status=e.code)

        return JsonResponse(exercise.model_dump(), status=201)


class ApiExerciseDetailView(ApiLoginRequiredMixin, View):
    def get(self, request: HttpRequest, exercise_id: int) -> JsonResponse:
        try:
            exercise = get_exercise_by_id(exercise_id, request.user)
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
            delete_exercise(exercise_id, request.user)
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
            updated = update_exercise(exercise_id, payload, request.user, full=full)
        except ServiceError as e:
            logger.warning(f"Service error updating exercise {exercise_id}: {e}")
            return JsonResponse({"detail": "Failed to update exercise."}, status=e.code)

        return JsonResponse(updated.model_dump(), status=200)


class ExerciseCreateView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        form = ExerciseForm()
        return render(request, "exercises/form.html", {"form": form, "mode": "create"})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = ExerciseForm(request.POST)
        if form.is_valid():
            exercise = form.save(commit=False)
            exercise.owner = Exercise.owner_for(request.user)
            exercise.save()
            messages.success(request, "Exercise created.")
            return redirect("tracker:exercises_list")
        return render(request, "exercises/form.html", {"form": form, "mode": "create"})


class ExerciseUpdateView(LoginRequiredMixin, View):
    def get_exercise(self, request: HttpRequest, exercise_id: int) -> Exercise:
        return get_manageable_exercise_or_error(request, exercise_id)

    def get(self, request: HttpRequest, exercise_id: int) -> HttpResponse:
        exercise = self.get_exercise(request, exercise_id)
        form = ExerciseForm(instance=exercise)
        return render(request, "exercises/form.html", {"form": form, "mode": "update", "exercise": exercise})

    def post(self, request: HttpRequest, exercise_id: int) -> HttpResponse:
        exercise = self.get_exercise(request, exercise_id)
        form = ExerciseForm(request.POST, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(request, "Exercise updated.")
            return redirect("tracker:exercise_detail", exercise_id=exercise.id)
        return render(request, "exercises/form.html", {"form": form, "mode": "update", "exercise": exercise})


class ExerciseDeleteView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, exercise_id: int) -> HttpResponse:
        try:
            delete_exercise(exercise_id, request.user)
        except ServiceError as e:
            if e.code == HTTPStatus.FORBIDDEN:
                raise PermissionDenied
            if e.code == HTTPStatus.CONFLICT:
                messages.error(request, f"Cannot delete: {e}.")
                return redirect("tracker:exercise_detail", exercise_id=exercise_id)
            raise Http404
        messages.success(request, "Exercise deleted.")
        return redirect("tracker:exercises_list")


class ExerciseSetDeleteView(LoginRequiredMixin, View):
    def post(self, request, es_id: int):
        try:
            delete_exercise_set(es_id, request.user)
        except ServiceError as e:
            logger.warning(f"Service error deleting exercise set {es_id}: {e}")
            messages.error(request, "Unable to remove exercise from plan.")
            return redirect(request.META.get("HTTP_REFERER", "tracker:plans_list"))

        messages.success(request, "Exercise removed from plan.")
        return redirect(request.META.get("HTTP_REFERER", "tracker:plans_list"))


class WorkoutSessionListView(LoginRequiredMixin, View):
    def get(self, request):
        user_id = request.user.id
        sessions = WorkoutSession.objects.filter(user_id=user_id).select_related("plan").order_by("-start_time")
        return render(
            request,
            "session/list.html",
            {
                "sessions": sessions,
                "now": timezone.now(),
            },
        )


class WorkoutSessionDetailView(LoginRequiredMixin, View):
    def handle_no_permission(self):
        if self.request.method == "PATCH":
            return JsonResponse({"detail": "Authentication required"}, status=401)
        return super().handle_no_permission()

    def get(self, request: HttpRequest, session_id: int) -> HttpResponse:
        user_id = request.user.id

        try:
            session = session_service.get_by_id(session_id, user_id)
        except ServiceError as e:
            logger.warning(f"Workout session load failed (session_id={session_id}, user_id={user_id}): {e}")
            messages.error(request, "Unable to load workout session.")
            return redirect("tracker:sessions_list")

        return render(
            request,
            "session/detail.html",
            {
                "session": session,
            },
        )

    def post(self, request: HttpRequest, session_id: int) -> HttpResponse:
        user_id = request.user.id

        action = request.POST.get("status")

        if action == "completed":
            service_action = session_service.finish_session
            success_message = "Workout session completed!"
        elif action == "delete":
            service_action = session_service.delete_session
            success_message = "Workout session deleted!"
        else:
            messages.warning(request, "Unknown action.")
            return redirect("tracker:sessions_list")

        try:
            service_action(session_id, user_id)
        except ServiceError as e:
            logger.warning(f"Workout session action failed (session_id={session_id}, user_id={user_id}): {e}")
            messages.error(request, "Unable to update session.")
        else:
            messages.success(request, success_message)

        return redirect("tracker:sessions_list")

    def patch(self, request: HttpRequest, session_id: int) -> JsonResponse:
        user_id = request.user.id

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

        new_status = payload.get("status")
        if not new_status:
            return JsonResponse({"detail": "Missing 'status' field"}, status=400)

        if new_status != "completed":
            return JsonResponse({"detail": "Only 'completed' status is supported."}, status=400)

        try:
            session = session_service.finish_session(session_id, user_id)
        except ServiceError as e:
            logger.warning(f"Workout session finish failed (session_id={session_id}, user_id={user_id}): {e}")
            return JsonResponse({"detail": "Unable to complete workout session."}, status=e.code)

        return JsonResponse(WorkoutSessionSchema.model_validate(session).model_dump(), status=200)


class WorkoutSessionStartView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, plan_id: int) -> HttpResponse:
        user_id = request.user.id

        try:
            session_service.start_session(user_id, plan_id)
        except ServiceError as e:
            logger.warning(f"Workout session start failed (plan_id={plan_id}, user_id={user_id}): {e}")
            messages.error(request, "Unable to start workout session.")
            return redirect("tracker:sessions_list")

        messages.success(request, "Workout session started successfully!")
        return redirect("tracker:sessions_list")


class WorkoutSessionDeleteView(ApiLoginRequiredMixin, View):
    def delete(self, request: HttpRequest, session_id: int) -> JsonResponse:
        user_id = request.user.id

        try:
            session_service.delete_session(session_id, user_id)
        except ServiceError as e:
            logger.warning(f"Workout session delete failed (session_id={session_id}, user_id={user_id}): {e}")
            return JsonResponse({"detail": "Unable to delete workout session."}, status=e.code)

        return JsonResponse({"message": "Workout session deleted"}, status=204)


class WeightTrackerListView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        user_id = request.user.id

        try:
            weight_trackers = weight_tracker_service.get_all_by_user(user_id)
        except ServiceError as e:
            logger.warning(f"Weight tracker list load failed (user_id={user_id}): {e}")
            messages.error(request, "Unable to load weight tracker list.")
            return redirect("tracker:index")

        return render(
            request,
            "weight_tracker/list.html",
            {
                "weight_trackers": weight_trackers,
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        user_id = request.user.id

        weight = request.POST.get("weight")
        entry_date = request.POST.get("date")

        if not weight or not entry_date:
            messages.error(request, "Both date and weight are required.")
            return redirect("tracker:weight_tracker_list")

        try:
            weight_tracker_service.create_weight_tracker(
                user_id=user_id,
                weight=weight,
                entry_date=entry_date,
            )
        except ServiceError as e:
            logger.warning(f"Weight tracker create failed (user_id={user_id}, weight={weight}, date={entry_date}): {e}")
            messages.error(request, "Unable to add weight entry.")
            return redirect("tracker:weight_tracker_list")

        messages.success(request, "Weight entry added successfully!")
        return redirect("tracker:weight_tracker_list")


class WeightTrackerDetailView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, weight_tracker_id: int) -> HttpResponse:
        user_id = request.user.id

        try:
            wt = weight_tracker_service.get_by_id(weight_tracker_id, user_id)
        except ServiceError as e:
            logger.warning(f"Weight tracker load failed (id={weight_tracker_id}, user_id={user_id}): {e}")
            messages.error(request, "Unable to load weight entry.")
            return redirect("tracker:weight_tracker_list")

        return render(
            request,
            "weight_tracker/detail.html",
            {
                "weight": wt,
            },
        )

    def post(self, request: HttpRequest, weight_tracker_id: int) -> HttpResponse:
        user_id = request.user.id

        if request.POST.get("_method") == "delete":
            try:
                weight_tracker_service.delete_weight_tracker(weight_tracker_id, user_id)
            except ServiceError as e:
                logger.warning(f"Weight tracker delete failed (id={weight_tracker_id}, user_id={user_id}): {e}")
                messages.error(request, "Unable to delete weight entry.")
                return redirect("tracker:weight_tracker_detail", weight_tracker_id=weight_tracker_id)

            messages.success(request, "Weight entry deleted.")
            return redirect("tracker:weight_tracker_list")

        messages.error(request, "Unknown action.")
        return redirect("tracker:weight_tracker_detail", weight_tracker_id=weight_tracker_id)
