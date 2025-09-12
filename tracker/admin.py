from typing import Any, cast

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import ForeignKey, Q
from django.forms.models import ModelChoiceField
from django.http import HttpRequest

from .models import (Exercise, ExerciseSet, WeightTracker, WorkoutPlan,
                     WorkoutSession)


class WorkoutPlanAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(
        self,
        db_field: ForeignKey,
        request: HttpRequest,
        **kwargs: Any,
    ) -> ModelChoiceField:
        if db_field.name == "creator":
            User = get_user_model()
            kwargs["queryset"] = User.objects.filter(
                Q(status="CUSTOMER") | Q(status="ADMIN")
            )
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if field is None:
            raise RuntimeError("formfield_for_foreignkey returned None unexpectedly")
        return field


admin.site.register(WorkoutPlan, WorkoutPlanAdmin)

admin.site.register(Exercise)
admin.site.register(ExerciseSet)
admin.site.register(WorkoutSession)
admin.site.register(WeightTracker)
