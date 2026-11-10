from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.db.models import ManyToManyField
from django.db.models import Q

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from authentication.models import User


class ExerciseQuerySet(models.QuerySet["Exercise"]):
    def visible_to(self, user: "User | AnonymousUser") -> "ExerciseQuerySet":
        """System exercises plus the user's own."""
        if user.is_authenticated:
            return self.filter(Q(owner__isnull=True) | Q(owner=user))
        return self.filter(owner__isnull=True)


class Exercise(models.Model):
    name = models.CharField(max_length=256)
    type = models.CharField(max_length=256)
    description = models.TextField()
    # null = system exercise, managed by staff only
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="exercises",
    )

    objects = ExerciseQuerySet.as_manager()

    @staticmethod
    def owner_for(user: "User") -> "User | None":
        """Staff create system exercises (no owner); everyone else creates private ones."""
        return None if user.is_staff else user

    def can_be_managed_by(self, user: "User | AnonymousUser") -> bool:
        if not user.is_authenticated:
            return False
        if self.owner_id is None:
            return user.is_staff
        return self.owner_id == user.id


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
    exercises: ManyToManyField
    exercises = models.ManyToManyField("Exercise", through="ExerciseSet", related_name="workout_plans")


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
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    start_time = models.DateTimeField()


class ExerciseSet(models.Model):
    exercise = models.ForeignKey("Exercise", on_delete=models.PROTECT)
    workout_plan = models.ForeignKey("WorkoutPlan", on_delete=models.CASCADE)
    sets = models.PositiveIntegerField()
    reps = models.PositiveIntegerField()
    weight = models.FloatField()

    class Meta:
        unique_together = ("exercise", "workout_plan")
