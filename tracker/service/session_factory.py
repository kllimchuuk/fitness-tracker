from tracker.repository.session_repository import get_session_repository
from tracker.service.session import WorkoutSessionService
from tracker.service.session import WorkoutSessionServiceImpl


def get_session_service() -> WorkoutSessionService:
    repo = get_session_repository()
    return WorkoutSessionServiceImpl(repo)
