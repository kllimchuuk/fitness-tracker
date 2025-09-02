from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "status",
        "is_staff",
        "is_active",
    )
    list_filter = ("status", "is_staff", "is_active", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Персональна інформація",
            {"fields": ("first_name", "last_name", "email", "age", "height", "goal")},
        ),
        ("Статус", {"fields": ("status", "is_active", "is_staff", "is_superuser")}),
        ("Важливі дати", {"fields": ("last_login", "date_joined")}),
        ("Групи та права", {"fields": ("groups", "user_permissions")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "status"),
            },
        ),
    )

    def get_queryset(self, request: Any) -> Any:
        return super().get_queryset(request)
