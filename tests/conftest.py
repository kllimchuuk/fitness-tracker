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
    """
    Simulates session-based login used by this project.
    Cannot use client.force_login() because views check request.session["user_id"],
    not request.user.
    """
    session = client.session
    session["user_id"] = user.id
    session["email"] = user.email
    session.save()
    return client


@pytest.fixture
def exercise(db):
    return ExerciseFactory()


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
