from http import HTTPStatus

from django.db.models import ProtectedError

from authentication.models import User

from .exceptions import ServiceError
from ..models import WorkoutPlan


def delete_workout_plan(plan_id: int, user: User) -> None:
    try:
        plan = WorkoutPlan.objects.get(id=plan_id, creator=user)
    except WorkoutPlan.DoesNotExist:
        raise ServiceError(f"Workout plan with id {plan_id} not found", code=HTTPStatus.NOT_FOUND)
    try:
        plan.delete()
    except ProtectedError:
        raise ServiceError("Workout plan has logged sessions", code=HTTPStatus.CONFLICT)
