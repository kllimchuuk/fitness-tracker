from tracker.repository.session_repository import AbstractWorkoutSessionRepository
from tracker.repository.session_repository import WorkoutSessionRepository


def get_session_repository() -> AbstractWorkoutSessionRepository:
    return WorkoutSessionRepository()
