from tracker.repository.session_repository import WorkoutSessionRepository
from tracker.repository.session_repository_interface import AbstractWorkoutSessionRepository


def get_session_repository() -> AbstractWorkoutSessionRepository:
    return WorkoutSessionRepository()
