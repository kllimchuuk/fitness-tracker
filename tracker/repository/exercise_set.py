from abc import ABC
from abc import abstractmethod

from tracker.models import ExerciseSet


class ExerciseSetRepository(ABC):
    @abstractmethod
    def exists_in_plan(self, plan_id: int, exercise_id: int) -> bool:
        raise NotImplementedError()


class ExerciseSetRepositoryImpl(ExerciseSetRepository):
    def exists_in_plan(self, plan_id: int, exercise_id: int) -> bool:
        return ExerciseSet.objects.filter(workout_plan_id=plan_id, exercise_id=exercise_id).exists()


def get_exercise_set_repository() -> ExerciseSetRepository:
    return ExerciseSetRepositoryImpl()
