from django.utils import timezone

from tracker.models import WorkoutPlan
from tracker.models import WorkoutSession
from tracker.repository import session as repo
from tracker.schemas.workout_session_schema import WorkoutSessionSchema

from .exceptions import ServiceError


def get_workout_session_by_id(session_id: int, user_id: int) -> WorkoutSessionSchema:
    session = repo.get_by_id(session_id, user_id)
    if not session:
        raise ServiceError(f"Workout session {session_id} not found", code=404)
    return WorkoutSessionSchema.model_validate(session)


def start_workout_session(user_id: int, plan_id: int) -> WorkoutSessionSchema:
    if repo.get_active_by_user(user_id):
        raise ServiceError("Active workout session already exists", code=400)

    try:
        plan = WorkoutPlan.objects.get(id=plan_id)
    except WorkoutPlan.DoesNotExist:
        raise ServiceError(f"Workout plan {plan_id} not found", code=404)

    session = repo.create(
        user_id=user_id,
        plan=plan,
        start_time=timezone.now(),
        status=WorkoutSession.Status.ACTIVE,
    )
    return WorkoutSessionSchema.model_validate(session)


def finish_workout_session(session_id: int, user_id: int) -> WorkoutSessionSchema:
    session = repo.get_by_id(session_id, user_id)
    if not session or session.status != WorkoutSession.Status.ACTIVE:
        raise ServiceError("Active workout session not found", code=404)

    elapsed = timezone.now() - session.start_time
    repo.update(
        session,
        duration_minutes=int(elapsed.total_seconds() // 60),
        status=WorkoutSession.Status.COMPLETED,
    )
    return WorkoutSessionSchema.model_validate(session)


def delete_workout_session(session_id: int, user_id: int):
    session = repo.get_by_id(session_id, user_id)
    if not session:
        raise ServiceError(f"Workout session {session_id} not found", code=404)
    repo.delete(session)
