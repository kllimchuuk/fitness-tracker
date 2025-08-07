from django.db import models


# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=256)
    last_Name = models.CharField(max_length=256)
    login = models.CharField(max_length=256, unique=True)
    password = models.CharField(max_length=256)


class Customer(User):
    age = models.PositiveIntegerField()
    height = models.FloatField()
    goal = models.CharField(max_length=256)


class Admin(User):
    email = models.EmailField(unique=True)


class Exercise(models.Model):
    name = models.CharField(max_length=256)
    type = models.CharField(max_length=256)
    description = models.TextField()


class WeightTracker(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    date = models.DateField()
    weight = models.FloatField()


class WorkoutPlan(models.Model):
    version = models.PositiveIntegerField()
    name = models.CharField(max_length=256)
    admin = models.ForeignKey("Admin", on_delete=models.CASCADE)


class WorkoutSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    admin = models.ForeignKey("Admin", on_delete=models.CASCADE)
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
