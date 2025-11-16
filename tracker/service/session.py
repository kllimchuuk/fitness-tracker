from django.utils import timezone

from tracker.models import WorkoutPlan
from tracker.models import WorkoutSession
from tracker.repository.session_repository_interface import AbstractWorkoutSessionRepository
from tracker.service.exceptions import ServiceError


class WorkoutSessionService:
    def __init__(self, repo: AbstractWorkoutSessionRepository):
        self.repo = repo

    def start_session(self, user_id: int, plan_id: int):
        active_session = self.repo.get_active_by_user(user_id)
        if active_session:
            raise ServiceError("You already have an active session.", code=400)

        try:
            plan = WorkoutPlan.objects.get(id=plan_id)
        except WorkoutPlan.DoesNotExist:
            raise ServiceError(f"Workout plan {plan_id} not found.", code=404)

        return self.repo.create(
            user_id=user_id,
            plan=plan,
            start_time=timezone.now(),
            status=WorkoutSession.Status.ACTIVE,
            duration_minutes=0,
        )

    def finish_session(self, session_id: int, user_id: int):
        session = self.repo.get_by_id_and_user(session_id, user_id)
        if not session:
            raise ServiceError("Session not found.", code=404)

        if session.status != WorkoutSession.Status.ACTIVE:
            raise ServiceError("Only active sessions can be completed.", code=400)

        end_time = timezone.now()
        duration = int((end_time - session.start_time).total_seconds() // 60)

        return self.repo.update(
            session,
            status=WorkoutSession.Status.COMPLETED,
            duration_minutes=duration,
        )

    def delete_session(self, session_id: int, user_id: int):
        session = self.repo.get_by_id_and_user(session_id, user_id)
        if not session:
            raise ServiceError("Session not found.", code=404)

        return self.repo.delete(session)

    def get_by_id(self, session_id: int, user_id: int):
        session = self.repo.get_by_id_and_user(session_id, user_id)
        if not session:
            raise ServiceError("Session not found.", code=404)
        return session

    def get_all_by_user(self, user_id: int):
        return self.repo.get_all_by_user(user_id)
