from django.utils import timezone

from tracker.models import WorkoutSession

from .base import BaseRepository


class WorkoutSessionRepository(BaseRepository[WorkoutSession]):
    def __init__(self):
        super().__init__(WorkoutSession)

    def get_by_id_and_user(self, session_id: int, user_id: int):
        return self.model.objects.filter(id=session_id, user_id=user_id).first()

    def get_all_by_user(self, user_id: int):
        return self.model.objects.filter(user_id=user_id).order_by("-start_time")

    def get_active_by_user(self, user_id: int):
        return self.model.objects.filter(user_id=user_id, status=WorkoutSession.Status.ACTIVE).first()

    def start_session(self, user_id: int, plan, duration_minutes=0):
        return self.create(
            user_id=user_id,
            plan=plan,
            start_time=timezone.now(),
            duration_minutes=duration_minutes,
            status=WorkoutSession.Status.ACTIVE,
        )

    def finish_session(self, session: WorkoutSession):
        end_time = timezone.now()
        duration = int((end_time - session.start_time).total_seconds() // 60)
        return self.update(session, status=WorkoutSession.Status.COMPLETED, duration_minutes=duration)
