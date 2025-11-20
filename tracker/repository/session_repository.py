from abc import ABC
from abc import abstractmethod
from typing import Sequence

from tracker.models import WorkoutSession

from .base_repository import BaseRepository


class AbstractWorkoutSessionRepository(ABC):
    @abstractmethod
    def get_by_id_and_user(self, session_id: int, user_id: int) -> WorkoutSession | None:
        raise NotImplementedError()

    @abstractmethod
    def get_all_by_user(self, user_id: int) -> Sequence[WorkoutSession]:
        raise NotImplementedError()

    @abstractmethod
    def get_active_by_user(self, user_id: int) -> WorkoutSession | None:
        raise NotImplementedError()


class WorkoutSessionRepository(BaseRepository[WorkoutSession], AbstractWorkoutSessionRepository):
    def __init__(self):
        super().__init__(WorkoutSession)

    def get_by_id_and_user(self, session_id: int, user_id: int):
        return self.model.objects.filter(id=session_id, user_id=user_id).first()

    def get_all_by_user(self, user_id: int):
        return self.model.objects.filter(user_id=user_id).order_by("-start_time")

    def get_active_by_user(self, user_id: int):
        return self.model.objects.filter(user_id=user_id, status=WorkoutSession.Status.ACTIVE).first()
