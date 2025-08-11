from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


# Create your models here.
class User(AbstractUser):
    class Status(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CUSTOMER = "CUSTOMER", "Customer"

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.CUSTOMER
    )
    age = models.PositiveIntegerField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    goal = models.CharField(max_length=256, null=True, blank=True)


class Exercise(models.Model):
    name = models.CharField(max_length=256)
    type = models.CharField(max_length=256)
    description = models.TextField()


class WeightTracker(models.Model):
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, limit_choices_to={"status": "CUSTOMER"}
    )
    date = models.DateField()
    weight = models.FloatField()


class WorkoutPlan(models.Model):
    creator = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        limit_choices_to=Q(status="CUSTOMER") | Q(status="ADMIN"),
    )
    name = models.CharField(max_length=256)
    version = models.PositiveIntegerField(default=1)


class WorkoutSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, limit_choices_to={"status": "CUSTOMER"}
    )
    plan = models.ForeignKey("WorkoutPlan", on_delete=models.CASCADE)
    duration_minutes = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE
    )


class Combination(models.Model):
    plan = models.ForeignKey("WorkoutPlan", on_delete=models.CASCADE)
    exercise = models.ForeignKey("Exercise", on_delete=models.CASCADE)
    sets = models.PositiveIntegerField()
    reps = models.PositiveIntegerField()
    weight = models.FloatField()


class Result(models.Model):
    session = models.ForeignKey("WorkoutSession", on_delete=models.CASCADE)
    exercise = models.ForeignKey("Exercise", on_delete=models.CASCADE)
    sets = models.PositiveIntegerField()
    reps = models.PositiveIntegerField()
    weight = models.FloatField()
