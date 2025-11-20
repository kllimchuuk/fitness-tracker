from tracker.repository.session_repository_factory import get_session_repository
from tracker.service.session import AbstractWorkoutSessionService
from tracker.service.session import WorkoutSessionService


def get_session_service() -> AbstractWorkoutSessionService:
    repo = get_session_repository()
    return WorkoutSessionService(repo)
