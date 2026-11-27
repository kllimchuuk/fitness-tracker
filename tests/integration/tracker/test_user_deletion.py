import pytest

from tests.factories.tracker_factories import ExerciseFactory
from tests.factories.tracker_factories import SetLogFactory
from tests.factories.tracker_factories import WorkoutPlanFactory
from tests.factories.tracker_factories import WorkoutSessionFactory
from tracker.models import Exercise
from tracker.models import SetLog
from tracker.models import WorkoutPlan
from tracker.models import WorkoutSession


@pytest.mark.django_db
class TestDeletingAUser:
    def test_user_with_plan_session_and_set_log_can_be_deleted(self, user):
        plan = WorkoutPlanFactory(creator=user)
        session = WorkoutSessionFactory(user=user, plan=plan)
        SetLogFactory(session=session)

        user.delete()

        assert not WorkoutPlan.objects.filter(id=plan.id).exists()
        assert not WorkoutSession.objects.filter(id=session.id).exists()
        assert SetLog.objects.count() == 0

    def test_user_with_set_log_on_a_private_exercise_can_be_deleted(self, user):
        exercise = ExerciseFactory(owner=user)
        plan = WorkoutPlanFactory(creator=user)
        session = WorkoutSessionFactory(user=user, plan=plan)
        SetLogFactory(session=session, exercise=exercise)

        user.delete()

        assert not Exercise.objects.filter(id=exercise.id).exists()
        assert SetLog.objects.count() == 0
