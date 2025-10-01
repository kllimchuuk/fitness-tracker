from typing import Any

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import ForeignKey
from django.db.models import Q
from django.forms.models import ModelChoiceField
from django.http import HttpRequest

from .models import Exercise
from .models import ExerciseSet
from .models import WeightTracker
from .models import WorkoutPlan
from .models import WorkoutSession


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(
        self,
        db_field: ForeignKey,
        request: HttpRequest,
        **kwargs: Any,
    ) -> ModelChoiceField:
        if db_field.name == "creator":
            User = get_user_model()
            kwargs["queryset"] = User.objects.filter(Q(status="CUSTOMER") | Q(status="ADMIN"))
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if field is None:
            raise RuntimeError("formfield_for_foreignkey returned None unexpectedly")
        return field


admin.site.register(Exercise)
admin.site.register(ExerciseSet)
admin.site.register(WorkoutSession)
admin.site.register(WeightTracker)
