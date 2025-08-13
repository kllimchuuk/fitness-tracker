from typing import Any, cast

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import ForeignKey, Q
from django.forms.models import ModelChoiceField
from django.http import HttpRequest

from .models import (Exercise, ExerciseSet, Result, User, WeightTracker,
                     WorkoutPlan, WorkoutSession)


class UserAdmin(BaseUserAdmin):
    def get_fieldsets(self, request: HttpRequest, obj: Any = None) -> Any:
        base_fieldsets = super().get_fieldsets(request, obj)
        extra_fieldset = (
            "Additional information",
            {"fields": ("status", "age", "height", "goal")},
        )
        if isinstance(base_fieldsets, list):
            base_fieldsets = tuple(base_fieldsets)
        return cast(Any, base_fieldsets + (extra_fieldset,))

    list_display = ("username", "email", "status", "is_staff", "is_active")
    list_filter = ("status", "is_staff", "is_active")
    search_fields = ("username", "email")


class WorkoutPlanAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(
        self,
        db_field: ForeignKey,
        request: HttpRequest,
        **kwargs: Any,
    ) -> ModelChoiceField:
        if db_field.name == "creator":
            kwargs["queryset"] = User.objects.filter(
                Q(status="CUSTOMER") | Q(status="ADMIN")
            )
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if field is None:
            raise RuntimeError("formfield_for_foreignkey returned None unexpectedly")
        return field


admin.site.register(User, UserAdmin)
admin.site.register(WorkoutPlan, WorkoutPlanAdmin)

admin.site.register(Exercise)
admin.site.register(ExerciseSet)
admin.site.register(WorkoutSession)
admin.site.register(WeightTracker)
admin.site.register(Result)
