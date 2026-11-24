from authentication.models import User
from tracker.repository.session import get_session_repository
from tracker.repository.set_log import get_set_log_repository
from tracker.schemas.set_log_schema import SetLogSchema

from .exceptions import ServiceError
from .exercise import get_visible_exercise
from ..models import WorkoutSession

RPE_MIN = 6
RPE_MAX = 10


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_set_payload(payload: dict) -> None:
    missing = [name for name in ("exercise_id", "reps", "weight_kg") if name not in payload]
    if missing:
        raise ServiceError(f"Missing required fields: {', '.join(missing)}", code=400)

    reps = payload["reps"]
    if not isinstance(reps, int) or isinstance(reps, bool) or reps < 1:
        raise ServiceError("reps must be an integer of at least 1", code=400)

    weight = payload["weight_kg"]
    if not is_number(weight) or weight < 0:
        raise ServiceError("weight_kg must be a number, zero or more", code=400)

    rpe = payload.get("rpe")
    if rpe is not None and (not is_number(rpe) or not RPE_MIN <= rpe <= RPE_MAX):
        raise ServiceError(f"rpe must be a number from {RPE_MIN} to {RPE_MAX}", code=400)


def log_set(session_id: int, payload: dict, user: User) -> SetLogSchema:
    session = get_session_repository().get_by_id_and_user(session_id, user.id)
    if not session:
        raise ServiceError("Session not found.", code=404)

    validate_set_payload(payload)

    if session.status != WorkoutSession.Status.ACTIVE:
        raise ServiceError("Sets can be logged only in an active session.", code=400)

    exercise = get_visible_exercise(payload["exercise_id"], user)

    repo = get_set_log_repository()
    top = repo.get_max_set_number(session.id, exercise.id)
    log = repo.create(
        session=session,
        exercise=exercise,
        set_number=(top or 0) + 1,
        reps=payload["reps"],
        weight_kg=float(payload["weight_kg"]),
        rpe=payload.get("rpe"),
    )
    return SetLogSchema.model_validate(log)


def list_set_logs(session_id: int, user: User) -> list[SetLogSchema]:
    session = get_session_repository().get_by_id_and_user(session_id, user.id)
    if not session:
        raise ServiceError("Session not found.", code=404)

    logs = get_set_log_repository().get_all_by_session(session.id)
    return [SetLogSchema.model_validate(log) for log in logs]
