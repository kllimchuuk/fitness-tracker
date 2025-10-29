from django.forms.models import model_to_dict

from .exceptions import ServiceError
from ..models import WorkoutPlan


def get_workout_plan_by_id(plan_id: int) -> dict:
    try:
        plan = WorkoutPlan.objects.get(id=plan_id)
    except WorkoutPlan.DoesNotExist:
        raise ServiceError(f"Workout plan with id {plan_id} not found", code=404)

    return model_to_dict(plan, fields=["id", "name", "version", "description"])


def create_workout_plan(user_id: int, payload: dict) -> dict:
    missing_fields = []
    if "name" not in payload:
        missing_fields.append("name")
    if "description" not in payload:
        missing_fields.append("description")

    if missing_fields:
        raise ServiceError(f"Missing required fields: {','.join(missing_fields)}", code=400)

    plan = WorkoutPlan.objects.create(
        creator_id=user_id,
        name=payload["name"],
        description=payload["description"],
    )
    return model_to_dict(plan, fields=["id", "name", "version", "description"])


def update_workout_plan(plan_id: int, payload: dict, full: bool = False) -> dict:
    try:
        plan = WorkoutPlan.objects.get(id=plan_id)
    except WorkoutPlan.DoesNotExist:
        raise ServiceError(f"Workout plan with id {plan_id} not found", code=404)

    if full:
        missing_fields = []
        if "name" not in payload:
            missing_fields.append("name")
        if "description" not in payload:
            missing_fields.append("description")

        if missing_fields:
            raise ServiceError(f"Missing required fields: {','.join(missing_fields)} ", code=400)

    plan.name = payload.get("name", plan.name)
    plan.description = payload.get("description", plan.description)
    plan.version = payload.get("version", plan.version)
    plan.save()

    return model_to_dict(plan, fields=["id", "name", "version", "description"])


def delete_workout_plan(plan_id: int):
    try:
        plan = WorkoutPlan.objects.get(id=plan_id)
    except WorkoutPlan.DoesNotExist:
        raise ServiceError(f"Workout plan with id {plan_id} not found", code=404)
    plan.delete()
