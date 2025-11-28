from abc import ABC
from abc import abstractmethod
from datetime import date
from typing import Sequence

from tracker.models import WeightTracker
from tracker.repository.weight_tracker import WeightTrackerRepository
from tracker.repository.weight_tracker import get_weight_tracker_repository
from tracker.service.exceptions import ServiceError


class WeightTrackerService(ABC):
    @abstractmethod
    def create_weight_tracker(self, user_id: int, weight: float, entry_date: date | None) -> WeightTracker:
        raise NotImplementedError()

    @abstractmethod
    def delete_weight_tracker(self, weight_tracker_id: int, user_id: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_all_by_user(self, user_id: int) -> Sequence[WeightTracker]:
        raise NotImplementedError()

    @abstractmethod
    def get_by_id(self, weight_tracker_id: int, user_id: int) -> WeightTracker:
        raise NotImplementedError()


class WeightTrackerServiceImpl(WeightTrackerService):
    def __init__(self, repo: WeightTrackerRepository):
        self.repo = repo

    def create_weight_tracker(self, user_id: int, weight: float, entry_date: date | None) -> WeightTracker:
        if weight is None:
            raise ServiceError("Weight is required.", code=400)

        if entry_date is None:
            entry_date = date.today()

        return self.repo.create(
            user_id=user_id,
            weight=weight,
            date=entry_date,
        )

    def delete_weight_tracker(self, weight_tracker_id: int, user_id: int) -> None:
        weight_tracker = self.repo.get_by_id_and_user(weight_tracker_id, user_id)
        if not weight_tracker:
            raise ServiceError("Weight entry not found.", code=404)

        self.repo.delete(weight_tracker)

    def get_all_by_user(self, user_id: int) -> list[WeightTracker]:
        return self.repo.get_all_by_user(user_id)

    def get_by_id(self, weight_tracker_id: int, user_id: int) -> WeightTracker:
        weight_tracker = self.repo.get_by_id_and_user(weight_tracker_id, user_id)
        if not weight_tracker:
            raise ServiceError("Weight entry not found.", code=404)
        return weight_tracker


def get_weight_tracker_service() -> WeightTrackerService:
    repo = get_weight_tracker_repository()
    return WeightTrackerServiceImpl(repo)
