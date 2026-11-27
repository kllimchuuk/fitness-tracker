from http import HTTPStatus

from django.db import models
from django.db.models import ProtectedError
from django.db.models import RestrictedError
from django.utils import timezone

from authentication.models import User
from tracker.schemas.exercise_schema import ExerciseSchema

from .exceptions import ServiceError
from ..models import Exercise
from ..models import ExerciseSet


def validate_choice(payload: dict, field: str, choices: type[models.TextChoices]) -> None:
    if field in payload and payload[field] not in choices.values:
        raise ServiceError(f"Invalid {field}: {payload[field]}", code=400)


def get_visible_exercise(exercise_id: int, user: User) -> Exercise:
    try:
        return Exercise.objects.visible_to(user).get(id=exercise_id)
    except Exercise.DoesNotExist:
        raise ServiceError(f"Exercise with id {exercise_id} not found", code=404)


def get_manageable_exercise(exercise_id: int, user: User) -> Exercise:
    exercise = get_visible_exercise(exercise_id, user)
    if not exercise.can_be_managed_by(user):
        raise ServiceError(f"No permission to modify exercise {exercise_id}", code=HTTPStatus.FORBIDDEN)
    return exercise


def get_exercise_by_id(exercise_id: int, user: User) -> ExerciseSchema:
    return ExerciseSchema.model_validate(get_visible_exercise(exercise_id, user))


def create_exercise(payload: dict, user: User) -> ExerciseSchema:
    missing_fields = []
    if "name" not in payload:
        missing_fields.append("name")
    if "type" not in payload:
        missing_fields.append("type")

    if missing_fields:
        raise ServiceError(f"Missing required fields: {', '.join(missing_fields)}", code=400)

    validate_choice(payload, "primary_muscle", Exercise.Muscle)
    validate_choice(payload, "equipment", Exercise.Equipment)

    exercise = Exercise.objects.create(
        name=payload["name"],
        type=payload["type"],
        description=payload.get("description", ""),
        primary_muscle=payload.get("primary_muscle", Exercise.Muscle.OTHER),
        equipment=payload.get("equipment", Exercise.Equipment.OTHER),
        owner=Exercise.owner_for(user),
    )
    return ExerciseSchema.model_validate(exercise)


def update_exercise(exercise_id: int, payload: dict, user: User, full: bool = False) -> ExerciseSchema:
    exercise = get_manageable_exercise(exercise_id, user)

    if full:
        missing_fields = []
        if "name" not in payload:
            missing_fields.append("name")
        if "type" not in payload:
            missing_fields.append("type")

        if missing_fields:
            raise ServiceError(f"Missing required fields: {', '.join(missing_fields)}", code=400)

    validate_choice(payload, "primary_muscle", Exercise.Muscle)
    validate_choice(payload, "equipment", Exercise.Equipment)

    exercise.name = payload.get("name", exercise.name)
    exercise.type = payload.get("type", exercise.type)
    exercise.description = payload.get("description", exercise.description)
    exercise.primary_muscle = payload.get("primary_muscle", exercise.primary_muscle)
    exercise.equipment = payload.get("equipment", exercise.equipment)
    exercise.save()
    return ExerciseSchema.model_validate(exercise)


def archive_exercise(exercise_id: int, user: User) -> ExerciseSchema:
    exercise = get_manageable_exercise(exercise_id, user)
    exercise.archived_at = timezone.now()
    exercise.save(update_fields=["archived_at"])
    return ExerciseSchema.model_validate(exercise)


def unarchive_exercise(exercise_id: int, user: User) -> ExerciseSchema:
    exercise = get_manageable_exercise(exercise_id, user)
    exercise.archived_at = None
    exercise.save(update_fields=["archived_at"])
    return ExerciseSchema.model_validate(exercise)


def delete_exercise(exercise_id: int, user: User) -> None:
    exercise = get_manageable_exercise(exercise_id, user)
    try:
        exercise.delete()
    except (ProtectedError, RestrictedError):
        plans = ExerciseSet.objects.filter(exercise=exercise).count()
        if plans:
            raise ServiceError(f"Exercise is used in {plans} plan{'s' if plans != 1 else ''}", code=HTTPStatus.CONFLICT)
        raise ServiceError("Exercise has logged sets; archive it instead", code=HTTPStatus.CONFLICT)
