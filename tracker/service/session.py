from tracker.models import WorkoutPlan
from tracker.repository.session_repository import WorkoutSessionRepository

repo = WorkoutSessionRepository()


def get_workout_session_by_id(session_id: int, user_id: int):
    return repo.get_by_id_and_user(session_id, user_id)


def start_workout_session(user_id: int, plan_id: int):
    plan = WorkoutPlan.objects.get(id=plan_id, creator_id=user_id)
    return repo.start_session(user_id, plan)


def finish_workout_session(session_id: int, user_id: int):
    session = repo.get_by_id_and_user(session_id, user_id)
    if not session:
        raise ValueError("Session not found")
    return repo.finish_session(session)


def delete_workout_session(session_id: int, user_id: int):
    session = repo.get_by_id_and_user(session_id, user_id)
    if session:
        repo.delete(session)
