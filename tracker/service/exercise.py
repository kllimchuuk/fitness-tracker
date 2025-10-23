from django.forms.models import model_to_dict

from .exceptions import ServiceError
from ..models import Exercise


def get_exercise_by_id(exercise_id: int) -> dict:
    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except Exercise.DoesNotExist:
        raise ServiceError(f"Exercise with id {exercise_id} not found", code=404)
    return model_to_dict(exercise)


def create_exercise(payload: dict) -> dict:
    missing_fields = []
    if "name" not in payload:
        missing_fields.append("name")
    if "type" not in payload:
        missing_fields.append("type")

    if missing_fields:
        raise ServiceError(f"Missing required fields: {', '.join(missing_fields)}", code=400)

    exercise = Exercise.objects.create(name=payload["name"], type=payload["type"], description=payload.get("description", ""))
    return model_to_dict(exercise)


def update_exercise(exercise_id: int, payload: dict, full: bool = False) -> dict:
    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except Exercise.DoesNotExist:
        raise ServiceError(f"Exercise with id {exercise_id} not found", code=404)

    if full:
        missing_fields = []
        if "name" not in payload:
            missing_fields.append("name")
        if "type" not in payload:
            missing_fields.append("type")

        if missing_fields:
            raise ServiceError(f"Missing required fields: {', '.join(missing_fields)}", code=400)

    exercise.name = payload.get("name", exercise.name)
    exercise.type = payload.get("type", exercise.type)
    exercise.description = payload.get("description", exercise.description)
    exercise.save()
    return model_to_dict(exercise)


def delete_exercise(exercise_id: int) -> None:
    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except Exercise.DoesNotExist:
        raise ServiceError(f"Exercise with id {exercise_id} not found", code=404)
    exercise.delete()
