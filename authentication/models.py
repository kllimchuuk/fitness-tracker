from django.contrib.auth.models import AbstractUser
from django.db import models


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

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.username

    @property
    def is_admin(self) -> bool:
        return self.status == self.Status.ADMIN

    @property
    def is_customer(self) -> bool:
        return self.status == self.Status.CUSTOMER
