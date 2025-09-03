from typing import Any

from django.conf import settings
from django.db import models
from django.db.models import ManyToManyField, Q


# Create your models here.
class Exercise(models.Model):
    name = models.CharField(max_length=256)
    type = models.CharField(max_length=256)
    description = models.TextField()


class WeightTracker(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to=Q(status="CUSTOMER") | Q(status="ADMIN"),
    )
    date = models.DateField()
    weight = models.FloatField()


class WorkoutPlan(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to=Q(status="CUSTOMER") | Q(status="ADMIN"),
    )
    name = models.CharField(max_length=256)
    version = models.PositiveIntegerField(default=1)
    description = models.TextField()
    exercises: Any = models.ManyToManyField(
        "Exercise", through="ExerciseSet", related_name="workout_plans"
    )


class WorkoutSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to=Q(status="CUSTOMER") | Q(status="ADMIN"),
    )
    plan = models.ForeignKey("WorkoutPlan", on_delete=models.CASCADE)
    duration_minutes = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE
    )
    start_time = models.DateTimeField()


class ExerciseSet(models.Model):
    exercise = models.ForeignKey("Exercise", on_delete=models.CASCADE)
    workout_plan = models.ForeignKey("WorkoutPlan", on_delete=models.CASCADE)
    sets = models.PositiveIntegerField()
    reps = models.PositiveIntegerField()
    weight = models.FloatField()

    class Meta:
        unique_together = ("exercise", "workout_plan")
