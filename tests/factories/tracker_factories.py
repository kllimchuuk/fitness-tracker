import datetime

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from tests.factories.user_factory import UserFactory
from tracker.models import Exercise
from tracker.models import ExerciseSet
from tracker.models import WeightTracker
from tracker.models import WorkoutPlan
from tracker.models import WorkoutSession


class ExerciseFactory(DjangoModelFactory):
    class Meta:
        model = Exercise

    name = factory.Sequence(lambda n: f"Exercise {n}")
    type = "strength"
    description = "Test exercise description"


class WorkoutPlanFactory(DjangoModelFactory):
    class Meta:
        model = WorkoutPlan

    name = factory.Sequence(lambda n: f"Plan {n}")
    description = "Test workout plan"
    version = 1
    creator = factory.SubFactory(UserFactory)


class ExerciseSetFactory(DjangoModelFactory):
    class Meta:
        model = ExerciseSet

    exercise = factory.SubFactory(ExerciseFactory)
    workout_plan = factory.SubFactory(WorkoutPlanFactory)
    sets = 3
    reps = 10
    weight = 50.0


class WorkoutSessionFactory(DjangoModelFactory):
    class Meta:
        model = WorkoutSession

    user = factory.SubFactory(UserFactory)
    plan = factory.SubFactory(WorkoutPlanFactory)
    status = WorkoutSession.Status.ACTIVE
    start_time = factory.LazyFunction(timezone.now)
    duration_minutes = 0


class WeightTrackerFactory(DjangoModelFactory):
    class Meta:
        model = WeightTracker

    user = factory.SubFactory(UserFactory)
    weight = 75.0
    date = factory.LazyFunction(datetime.date.today)
