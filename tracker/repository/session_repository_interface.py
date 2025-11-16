from abc import ABC
from abc import abstractmethod
from typing import Sequence

from tracker.models import WorkoutSession


class AbstractWorkoutSessionRepository(ABC):
    @abstractmethod
    def get_by_id_and_user(self, session_id: int, user_id: int) -> WorkoutSession | None:
        pass

    @abstractmethod
    def get_all_by_user(self, user_id: int) -> Sequence[WorkoutSession]:
        pass

    @abstractmethod
    def get_active_by_user(self, user_id: int) -> WorkoutSession | None:
        pass
