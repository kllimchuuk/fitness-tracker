from authentication.models import User
from tracker.schemas.exercise_set_schema import ExerciseSetSchema

from .exceptions import ServiceError
from ..models import Exercise
from ..models import ExerciseSet
from ..models import WorkoutPlan


def add_exercise_set(plan_id: int, payload: dict, user: User) -> ExerciseSetSchema:
    if "exercise_id" not in payload:
        raise ServiceError("Missing required field: exercise_id", code=400)

    if not Exercise.objects.visible_to(user).filter(id=payload["exercise_id"]).exists():
        raise ServiceError(f"Exercise with id {payload['exercise_id']} not found", code=404)

    if not WorkoutPlan.objects.filter(id=plan_id, creator=user).exists():
        raise ServiceError(f"Workout plan with id {plan_id} not found", code=404)

    es, created = ExerciseSet.objects.get_or_create(
        workout_plan_id=plan_id,
        exercise_id=payload["exercise_id"],
        defaults={
            "sets": payload.get("sets", 3),
            "reps": payload.get("reps", 10),
            "weight": payload.get("weight", 0),
        },
    )

    if not created:
        update_fields(es, payload, ("sets", "reps", "weight"))

    return ExerciseSetSchema.model_validate(es)


def delete_exercise_set(es_id: int, user: User):
    try:
        es = ExerciseSet.objects.get(id=es_id, workout_plan__creator=user)
    except ExerciseSet.DoesNotExist:
        raise ServiceError(f"ExerciseSet with id {es_id} not found", code=404)
    es.delete()


def update_fields(instance, data: dict, fields: tuple[str, ...]):
    changed = False
    for field in fields:
        if field in data:
            setattr(instance, field, data[field])
            changed = True
    if changed:
        instance.save()
