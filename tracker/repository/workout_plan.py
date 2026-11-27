from abc import ABC
from abc import abstractmethod

from tracker.models import WorkoutPlan


class WorkoutPlanRepository(ABC):
    @abstractmethod
    def get_by_creator(self, plan_id: int, creator_id: int) -> WorkoutPlan | None:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, plan: WorkoutPlan) -> None:
        raise NotImplementedError()


class WorkoutPlanRepositoryImpl(WorkoutPlanRepository):
    def get_by_creator(self, plan_id: int, creator_id: int) -> WorkoutPlan | None:
        return WorkoutPlan.objects.filter(id=plan_id, creator_id=creator_id).first()

    def delete(self, plan: WorkoutPlan) -> None:
        plan.delete()


def get_workout_plan_repository() -> WorkoutPlanRepository:
    return WorkoutPlanRepositoryImpl()
