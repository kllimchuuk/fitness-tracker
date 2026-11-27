from http import HTTPStatus

from django.db.models import ProtectedError
from django.db.models import RestrictedError

from authentication.models import User
from tracker.repository.workout_plan import get_workout_plan_repository

from .exceptions import ServiceError


def delete_workout_plan(plan_id: int, user: User) -> None:
    repository = get_workout_plan_repository()
    plan = repository.get_by_creator(plan_id, user.id)
    if plan is None:
        raise ServiceError(f"Workout plan with id {plan_id} not found", code=HTTPStatus.NOT_FOUND)
    try:
        repository.delete(plan)
    except (ProtectedError, RestrictedError):
        raise ServiceError("Workout plan has logged sessions", code=HTTPStatus.CONFLICT)
