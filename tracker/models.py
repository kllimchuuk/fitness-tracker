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

    def active(self) -> "ExerciseQuerySet":
        return self.filter(archived_at__isnull=True)


class Exercise(models.Model):
    class Muscle(models.TextChoices):
        CHEST = "chest", "Chest"
        BACK = "back", "Back"
        SHOULDERS = "shoulders", "Shoulders"
        BICEPS = "biceps", "Biceps"
        TRICEPS = "triceps", "Triceps"
        FOREARMS = "forearms", "Forearms"
        QUADS = "quads", "Quads"
        HAMSTRINGS = "hamstrings", "Hamstrings"
        GLUTES = "glutes", "Glutes"
        CALVES = "calves", "Calves"
        CORE = "core", "Core"
        FULL_BODY = "full_body", "Full body"
        OTHER = "other", "Other"

    class Equipment(models.TextChoices):
        BARBELL = "barbell", "Barbell"
        DUMBBELL = "dumbbell", "Dumbbell"
        MACHINE = "machine", "Machine"
        CABLE = "cable", "Cable"
        KETTLEBELL = "kettlebell", "Kettlebell"
        BAND = "band", "Band"
        BODYWEIGHT = "bodyweight", "Bodyweight"
        OTHER = "other", "Other"

    name = models.CharField(max_length=256)
    type = models.CharField(max_length=256)
    description = models.TextField()
    primary_muscle = models.CharField(max_length=16, choices=Muscle.choices, default=Muscle.OTHER)
    equipment = models.CharField(max_length=16, choices=Equipment.choices, default=Equipment.OTHER)
    archived_at = models.DateTimeField(null=True, blank=True)
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    weight = models.FloatField()


class WorkoutPlan(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    version = models.PositiveIntegerField(default=1)
    description = models.TextField()
    exercises: ManyToManyField
    exercises = models.ManyToManyField("Exercise", through="ExerciseSet", related_name="workout_plans")


class WorkoutSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey("WorkoutPlan", on_delete=models.PROTECT)
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


class SetLog(models.Model):
    session = models.ForeignKey("WorkoutSession", on_delete=models.CASCADE, related_name="set_logs")
    exercise = models.ForeignKey("Exercise", on_delete=models.PROTECT, related_name="set_logs")
    set_number = models.PositiveSmallIntegerField()
    reps = models.PositiveSmallIntegerField()
    weight_kg = models.FloatField()
    rpe = models.FloatField(null=True, blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("exercise_id", "set_number")
        constraints = [
            models.UniqueConstraint(fields=("session", "exercise", "set_number"), name="setlog_unique_set_number"),
            models.CheckConstraint(condition=Q(reps__gte=1), name="setlog_reps_positive"),
            models.CheckConstraint(condition=Q(weight_kg__gte=0), name="setlog_weight_not_negative"),
            models.CheckConstraint(
                condition=Q(rpe__isnull=True) | (Q(rpe__gte=6) & Q(rpe__lte=10)),
                name="setlog_rpe_range",
            ),
        ]
