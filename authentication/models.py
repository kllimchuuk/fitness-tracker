from typing import Any, Optional

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager["User"]):
    def create_user(
        self, email: str, password: Optional[str] = None, **extra_fields: Any
    ) -> "User":
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: Optional[str] = None, **extra_fields: Any
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):

    class Status(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CUSTOMER = "CUSTOMER", "Customer"

    email = models.EmailField(unique=True, verbose_name="Email")
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.CUSTOMER
    )
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name="Вік")
    height = models.FloatField(null=True, blank=True, verbose_name="Зріст (см)")
    goal = models.CharField(max_length=256, null=True, blank=True, verbose_name="Мета")
    workout_plans = models.ManyToManyField(
        "tracker.WorkoutPlan", related_name="subscribers", blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    username = None  # type: ignore[assignment]

    objects: UserManager = UserManager()  # type: ignore[assignment,misc]
