from tracker.models import WorkoutSession


def get_by_id(session_id: int, user_id: int) -> WorkoutSession:
    return WorkoutSession.objects.filter(id=session_id, user_id=user_id).first()


def get_active_by_user(user_id: int) -> WorkoutSession:
    return WorkoutSession.objects.filter(user_id=user_id, status=WorkoutSession.Status.ACTIVE).first()


def create(user_id: int, plan, start_time, status, duration_minutes=0) -> WorkoutSession:
    return WorkoutSession.objects.create(
        user_id=user_id,
        plan=plan,
        start_time=start_time,
        duration_minutes=duration_minutes,
        status=status,
    )


def update(session: WorkoutSession, **fields) -> WorkoutSession:
    for key, value in fields.items():
        setattr(session, key, value)
    session.save(update_fields=list(fields.keys()))
    return session


def delete(session: WorkoutSession):
    session.delete()
