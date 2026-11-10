import pytest
from django.test import Client

from tests.factories.tracker_factories import ExerciseFactory
from tests.factories.tracker_factories import WeightTrackerFactory
from tests.factories.tracker_factories import WorkoutPlanFactory
from tests.factories.tracker_factories import WorkoutSessionFactory
from tests.factories.user_factory import UserFactory


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def staff_user(db):
    return UserFactory(is_staff=True)


@pytest.fixture
def staff_client(staff_user):
    client = Client()
    client.force_login(staff_user)
    return client


@pytest.fixture
def other_user(db):
    return UserFactory()


@pytest.fixture
def exercise(db):
    """A system exercise (no owner)."""
    return ExerciseFactory()


@pytest.fixture
def owned_exercise(db, user):
    return ExerciseFactory(owner=user)


@pytest.fixture
def other_exercise(db, other_user):
    return ExerciseFactory(owner=other_user)


@pytest.fixture
def plan(db, user):
    return WorkoutPlanFactory(creator=user)


@pytest.fixture
def active_session(db, user, plan):
    return WorkoutSessionFactory(user=user, plan=plan, status="active")


@pytest.fixture
def completed_session(db, user, plan):
    return WorkoutSessionFactory(user=user, plan=plan, status="completed", duration_minutes=30)


@pytest.fixture
def weight_entry(db, user):
    return WeightTrackerFactory(user=user)
