from abc import ABC
from abc import abstractmethod
from typing import Sequence

from django.db.models import Max

from tracker.models import SetLog

from .base import CRUDRepositorySQLAlchemy


class SetLogRepository(ABC):
    @abstractmethod
    def get_max_set_number(self, session_id: int, exercise_id: int) -> int | None:
        raise NotImplementedError()

    @abstractmethod
    def get_all_by_session(self, session_id: int) -> Sequence[SetLog]:
        raise NotImplementedError()


class SetLogRepositoryImpl(CRUDRepositorySQLAlchemy[SetLog], SetLogRepository):
    def __init__(self):
        super().__init__(SetLog)

    def get_max_set_number(self, session_id: int, exercise_id: int) -> int | None:
        return self.model.objects.filter(session_id=session_id, exercise_id=exercise_id).aggregate(top=Max("set_number"))["top"]

    def get_all_by_session(self, session_id: int) -> Sequence[SetLog]:
        return self.model.objects.filter(session_id=session_id).order_by("exercise_id", "set_number")


def get_set_log_repository() -> SetLogRepository:
    return SetLogRepositoryImpl()
