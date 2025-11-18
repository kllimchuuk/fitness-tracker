from abc import ABC
from abc import abstractmethod

from tracker.models import WorkoutSession


class AbstractWorkoutSessionService(ABC):
    @abstractmethod
    def start_session(self, user_id: int, plan_id: int) -> WorkoutSession:
        pass

    @abstractmethod
    def finish_session(self, session_id: int, user_id: int) -> WorkoutSession:
        pass

    @abstractmethod
    def delete_session(self, session_id: int, user_id: int) -> None:
        pass

    @abstractmethod
    def get_by_id(self, session_id: int, user_id: int) -> WorkoutSession:
        pass

    @abstractmethod
    def get_all_by_user(self, user_id: int) -> list[WorkoutSession]:
        pass
