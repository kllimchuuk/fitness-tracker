from abc import ABC
from abc import abstractmethod
from typing import Sequence

from tracker.models import WeightTracker

from .base import CRUDRepositorySQLAlchemy


class WeightTrackerRepository(ABC):
    @abstractmethod
    def get_all_by_user(self, user_id: int) -> Sequence[WeightTracker]:
        raise NotImplementedError()

    @abstractmethod
    def get_by_id_and_user(self, entry_id: int, user_id: int) -> WeightTracker | None:
        raise NotImplementedError()


class WeightTrackerRepositoryImpl(CRUDRepositorySQLAlchemy[WeightTracker], WeightTrackerRepository):
    def __init__(self):
        super().__init__(WeightTracker)

    def get_all_by_user(self, user_id: int) -> Sequence[WeightTracker]:
        return self.model.objects.filter(user_id=user_id).order_by("-date")

    def get_by_id_and_user(self, entry_id: int, user_id: int) -> WeightTracker | None:
        return self.model.objects.filter(id=entry_id, user_id=user_id).first()


def get_weight_tracker_repository() -> WeightTrackerRepository:
    return WeightTrackerRepositoryImpl()
